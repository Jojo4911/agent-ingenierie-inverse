"""Bloc 3, couche de vérification : grandeurs attendues depuis les seules primitives.

Cette couche ne lit aucun fichier de vérité terrain. À l'exécution, l'agent
ne dispose que du plan : il juge son résultat sans référence extérieure. Le
corpus de vérité ne sert qu'aux runs d'évaluation du bloc 5, où deux solides
mesurés sont comparés l'un à l'autre.

Contrainte 1 appliquée ici : aucune grandeur dérivée lue sur le plan n'est
utilisée. Les champs bbox_x_mm, bbox_y_mm et bbox_z_mm du JSON d'extraction
sont délibérément ignorés, ce sont des valeurs lues donc invérifiables. Les
deux seules erreurs du spike portaient exactement sur ces valeurs-là.

Limite structurelle mesurée : le champ "profil" est du texte libre.
L'aire de la section n'est donc pas calculable, ce qui rend indisponibles
la bbox en X et en Y ainsi que le volume attendu. Cause unique, deux effets.
"""
from __future__ import annotations

from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN

from verify import load_solid, optimal_bbox, cylinders, count_holes

# Périmètre géométrique borné. Toute autre valeur est signalée plutôt
# qu'interprétée.
CORPS_SUPPORTES = {"contour_extrude", "cercle_extrude"}


def _nombre(valeur):
    """Retourne un flottant, ou None si la valeur est absente ou non numérique."""
    if isinstance(valeur, (int, float)) and not isinstance(valeur, bool):
        return float(valeur)
    return None


def _etendue_z(corps: list[dict]) -> float | None:
    """Hauteur hors tout, seule dimension portée par des champs numériques dédiés."""
    bases, sommets = [], []
    for c in corps:
        base = _nombre(c.get("z_base_mm"))
        hauteur = _nombre(c.get("hauteur_extrusion_mm"))
        if base is None or hauteur is None:
            return None
        bases.append(base)
        sommets.append(base + hauteur)
    if not bases:
        return None
    return max(sommets) - min(bases)


def attendu(primitives: dict) -> dict:
    """Calcule les grandeurs dérivées à partir des seules primitives extraites.

    Les grandeurs non calculables valent None et sont nommées dans
    "non_calculable". Un None est une absence déclarée, jamais une valeur
    par défaut : une couche de vérification qui comble un trou ne vérifie plus.
    """
    corps = primitives.get("corps") or []
    trous = primitives.get("trous") or []
    poches = primitives.get("poches") or []

    hors_perimetre = [
        f"corps {c.get('nom', '?')!r} de type {c.get('type', '?')!r}"
        for c in corps
        if c.get("type") not in CORPS_SUPPORTES
    ]

    bbox_z = _etendue_z(corps)
    non_calculable = [
        "bbox_x_mm et bbox_y_mm : le champ profil est du texte libre, "
        "l'aire de la section n'est pas dérivable",
        "volume_mm3 : dépend de l'aire de la section, même cause",
    ]
    if bbox_z is None:
        non_calculable.append(
            "bbox_z_mm : z_base_mm ou hauteur_extrusion_mm absent sur au moins un corps"
        )

    return {
        # Convention de comptage alignée sur les fichiers _verite.md, pas sur
        # verify.py du spike qui comptait les borgnes comme des trous. Le prompt
        # d'extraction définit trous comme les traversants uniquement, et poches
        # comme tout enlèvement non traversant : la sémantique est portée par le
        # prompt, le code se contente de compter.
        "nb_trous_traversants": len(trous),
        "nb_poches": len(poches),
        "bbox_mm": (None, None, bbox_z),
        "volume_mm3": None,
        "non_calculable": non_calculable,
        "hors_perimetre": hors_perimetre,
    }


def _traversant(solid, foot, direction, n_echantillons=60):
    """Vrai si l'axe du cylindre ne rencontre aucune matière sur toute l'étendue
    de la pièce. Un trou borgne laisse de la matière au-delà de son fond.
    """
    bb = solid.BoundingBox()
    coins = [
        (x, y, z)
        for x in (bb.xmin, bb.xmax)
        for y in (bb.ymin, bb.ymax)
        for z in (bb.zmin, bb.zmax)
    ]
    # projection des huit coins sur l'axe : borne l'échantillonnage à la pièce
    ts = [sum((c[i] - foot[i]) * direction[i] for i in range(3)) for c in coins]
    t_min, t_max = min(ts), max(ts)

    clf = BRepClass3d_SolidClassifier(solid.wrapped)
    for k in range(n_echantillons + 1):
        t = t_min + (t_max - t_min) * k / n_echantillons
        p = gp_Pnt(*(foot[i] + t * direction[i] for i in range(3)))
        clf.Perform(p, 1e-7)
        if clf.State() == TopAbs_IN:
            return False
    return True


def mesure(step_path: str) -> dict:
    """Mesure sur le solide produit : boîte englobante et trous traversants.
    Ne lit aucune vérité terrain, ne juge pas, ne fait que constater.
    """
    solid = load_solid(step_path)
    x_mm, y_mm, z_mm = optimal_bbox(solid)

    # cylindres creux uniquement, puis traversants uniquement : la convention
    # des fichiers de vérité sépare trous traversants et poches
    cyls = [c for c in cylinders(solid) if c[3] and _traversant(solid, c[1], c[2])]

    return {
        "bbox_x_mm": x_mm,
        "bbox_y_mm": y_mm,
        "bbox_z_mm": z_mm,
        "nb_trous_traversants": count_holes(cyls),
        "nb_poches": None,       # non mesurable sur le solide
        "volume_mm3": None,      # renseigné en T36
    }


def _aplatir(d: dict) -> dict:
    """Ramène les deux formes de dictionnaire à un jeu de clés unique.

    attendu() porte la boîte englobante dans un tuple "bbox_mm", mesure() la
    porte en trois clés séparées. Sans cette normalisation, compare() ne trouve
    aucune bbox du côté attendu et déclare les trois axes non vérifiables sans
    rien signaler.
    """
    plat = dict(d)
    bbox = plat.pop("bbox_mm", None)
    if bbox is not None:
        plat["bbox_x_mm"], plat["bbox_y_mm"], plat["bbox_z_mm"] = bbox
    return plat


def compare(attendu: dict, mesure: dict, tol_mm: float = 0.5, tol_rel: float = 0.01) -> dict:
    """Confronte attendu et mesure champ par champ, en trois verdicts.
    Un champ absent d'un des deux côtés est déclaré non vérifiable, jamais conforme.
    """
    attendu, mesure = _aplatir(attendu), _aplatir(mesure)

    champs = [
        "bbox_x_mm",
        "bbox_y_mm",
        "bbox_z_mm",
        "nb_trous_traversants",
        "nb_poches",
        "volume_mm3",
    ]

    verdicts = {}
    for champ in champs:
        a, m = attendu.get(champ), mesure.get(champ)
        if a is None or m is None:
            verdicts[champ] = "non vérifiable"
        elif isinstance(a, int) and isinstance(m, int):
            verdicts[champ] = "conforme" if a == m else "non conforme"
        else:
            ecart = abs(float(a) - float(m))
            # les deux tolérances sont alternatives, pas cumulatives
            ok = ecart <= tol_mm or (a != 0 and ecart / abs(float(a)) <= tol_rel)
            verdicts[champ] = "conforme" if ok else "non conforme"

    controles = [v for v in verdicts.values() if v != "non vérifiable"]
    return {
        "verdicts": verdicts,
        "conforme": bool(controles) and all(v == "conforme" for v in controles),
        "nb_controles": len(controles),
        "nb_non_verifiables": len(verdicts) - len(controles),
    }