raise RuntimeError('faute injectée, tentative 2')
import cadquery as cq

longueur = 84.0
hauteur = 52.0
epaisseur = 12.0

result = (
    cq.Workplane("XY")
    .box(longueur, hauteur, epaisseur, centered=(False, False, False))
)

trous = [
    (18.0, 14.0, 8.5),
    (66.0, 38.0, 8.5),
]

for x, y, d in trous:
    result = (
        result.faces(">Z")
        .workplane(origin=(0, 0, 0))
        .center(x, y)
        .hole(d)
    )

cq.exporters.export(result, "/work/out.step")