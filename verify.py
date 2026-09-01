"""Bloc 3 du spike P15 : vérification géometrique des STEP produits.

Usage :
    python verify.py                       # vérifie piece_A.step et piece_B.step
    python verify.py piece_B_e2e.step B    # vérifie un fichier contre la vérité de B
"""

import sys

import cadquery as cq
from OCP.Bnd import Bnd_Box
from OCP.BRep import BRep_Tool
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.BRepTools import BRepTools
from OCP.GeomAbs import GeomAbs_Cylinder
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN

# --- verite terrain, gelee avant execution ---
TRUTH = {
    "A": {"file": "piece_A.step", "bbox": (84.0, 52.0, 12.0), "holes": 2, "volume": 51054.0},
    "B": {"file": "piece_B.step", "bbox": (140.0, 64.0, 50.0), "holes": 1, "volume": 160339.0},
}
TOL_LIN = 0.5    # mm, C3
TOL_VOL = 0.01   # 1 %, C3

# Convention de comptage figee avant execution : un trou est une surface
# cylindrique dont la matiere se trouve du cote exterieur de la surface,
# debouchante ou borgne. Le bossage O64 de B n est pas un trou. Les encoches
# 30 x 20 sont prismatiques, elles ne comptent pas.


def load_solid(path):
    shape = cq.importers.importStep(path).val()
    solids = shape.Solids()
    if len(solids) != 1:
        print(f"  ATTENTION : {len(solids)} solides dans {path}, le premier est utilise")
    return solids[0]


def optimal_bbox(solid):
    bb = Bnd_Box()
    BRepBndLib.AddOptimal_s(solid.wrapped, bb)
    xmin, ymin, zmin, xmax, ymax, zmax = bb.Get()
    return (xmax - xmin, ymax - ymin, zmax - zmin)


def cylinders(solid):
    """Retourne (rayon, point sur l axe, direction, interieur) par face cylindrique."""
    out = []
    for f in solid.Faces():
        ad = BRepAdaptor_Surface(f.wrapped)
        if ad.GetType() != GeomAbs_Cylinder:
            continue
        cyl = ad.Cylinder()
        r = cyl.Radius()
        ax = cyl.Axis()
        loc, d = ax.Location(), ax.Direction()

        # point sur la surface, a mi-parametre
        u0, u1, v0, v1 = BRepTools.UVBounds_s(f.wrapped)
        p = BRep_Tool.Surface_s(f.wrapped).Value(0.5 * (u0 + u1), 0.5 * (v0 + v1))

        # pied de la perpendiculaire sur l axe
        vx, vy, vz = p.X() - loc.X(), p.Y() - loc.Y(), p.Z() - loc.Z()
        t = vx * d.X() + vy * d.Y() + vz * d.Z()
        foot = (loc.X() + t * d.X(), loc.Y() + t * d.Y(), loc.Z() + t * d.Z())

        # sonde a epsilon vers l axe : hors matiere => trou, dans la matiere => bossage
        eps = min(0.1, 0.2 * r)
        probe = gp_Pnt(
            p.X() + eps * (foot[0] - p.X()) / r,
            p.Y() + eps * (foot[1] - p.Y()) / r,
            p.Z() + eps * (foot[2] - p.Z()) / r,
        )
        clf = BRepClass3d_SolidClassifier(solid.wrapped)
        clf.Perform(probe, 1e-7)
        inner = clf.State() != TopAbs_IN

        out.append((r, foot, (d.X(), d.Y(), d.Z()), inner))
    return out


def count_holes(cyls):
    """Deduplique les faces coaxiales de meme rayon, un trou scinde ne compte qu une fois."""
    seen = set()
    for r, foot, d, inner in cyls:
        if not inner:
            continue
        sign = 1.0
        for c in d:
            if abs(c) > 1e-9:
                sign = 1.0 if c > 0 else -1.0
                break
        dc = tuple(round(c * sign, 4) for c in d)
        t = sum(foot[i] * dc[i] for i in range(3))
        anchor = tuple(round(foot[i] - t * dc[i], 3) for i in range(3))
        seen.add((round(r, 3), dc, anchor))
    return len(seen)


def check(path, key):
    ref = TRUTH[key]
    solid = load_solid(path)
    bbox = optimal_bbox(solid)
    vol = solid.Volume()
    cyls = cylinders(solid)
    holes = count_holes(cyls)

    print(f"\n=== {path}  (verite terrain : piece {key}) ===")
    print("  faces cylindriques detectees :")
    for r, foot, d, inner in sorted(cyls, key=lambda c: -c[0]):
        kind = "TROU   " if inner else "bossage"
        print(f"    {kind}  O{2*r:7.3f}  axe ({foot[0]:8.3f};{foot[1]:8.3f};{foot[2]:8.3f})"
              f"  dir ({d[0]:5.2f};{d[1]:5.2f};{d[2]:5.2f})")

    ok = True
    print(f"  {'grandeur':<14}{'mesure':>14}{'attendu':>14}{'ecart':>14}   verdict")
    for i, axis in enumerate("xyz"):
        e = bbox[i] - ref["bbox"][i]
        v = abs(e) <= TOL_LIN
        ok &= v
        print(f"  bbox {axis:<9}{bbox[i]:>14.3f}{ref['bbox'][i]:>14.3f}{e:>+14.3f}   "
              f"{'OK' if v else 'ECHEC'}")
    e = holes - ref["holes"]
    v = e == 0
    ok &= v
    print(f"  {'trous':<14}{holes:>14d}{ref['holes']:>14d}{e:>+14d}   {'OK' if v else 'ECHEC'}")
    e = vol - ref["volume"]
    rel = e / ref["volume"]
    v = abs(rel) <= TOL_VOL
    ok &= v
    print(f"  {'volume mm3':<14}{vol:>14.2f}{ref['volume']:>14.2f}{e:>+14.2f}   "
          f"{'OK' if v else 'ECHEC'}  ({rel:+.3%})")
    print(f"  --> C3 {'ACQUIS' if ok else 'ECHOUE'} sur {path}")
    return ok


if __name__ == "__main__":
    if len(sys.argv) == 3:
        check(sys.argv[1], sys.argv[2])
    else:
        for key, ref in TRUTH.items():
            check(ref["file"], key)