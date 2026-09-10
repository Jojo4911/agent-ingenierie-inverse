import cadquery as cq

# Profil de la plaque principale (vue de face, x vers la droite, y vers le haut)
profil_points = [
    (0.0, 0.0),
    (90.0, 0.0),
    (90.0, 40.0),
    (70.0, 60.0),
    (20.0, 60.0),
    (0.0, 40.0),
]

epaisseur = 20.0

result = (
    cq.Workplane("XY")
    .polyline(profil_points)
    .close()
    .extrude(epaisseur)
)

# Trous Ø10 traversants
result = (
    result.faces(">Z")
    .workplane(origin=(0, 0, 0))
    .pushPoints([(10.0, 10.0), (80.0, 10.0)])
    .hole(10.0)
)

# Poche carree 25 x 25, profondeur 5, depuis la face avant (z = 20)
poche_carree = (
    cq.Workplane("XY")
    .workplane(offset=epaisseur - 5.0)
    .center(45.0, 37.5)
    .rect(25.0, 25.0)
    .extrude(5.0)
)
result = result.cut(poche_carree)

# Logement circulaire Ø14, profondeur 12, depuis la face avant (z = 20)
logement_circ = (
    cq.Workplane("XY")
    .workplane(offset=epaisseur - 12.0)
    .center(45.0, 12.0)
    .circle(14.0 / 2.0)
    .extrude(12.0)
)
result = result.cut(logement_circ)

cq.exporters.export(result, "/work/out.step")