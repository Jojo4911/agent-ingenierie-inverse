import cadquery as cq

# Plaque de base : 120 x 80 x 15, coin inférieur gauche à l'origine, z de 0 à 15
result = cq.Workplane("XY").box(120, 80, 15, centered=(False, False, False))

# 4 trous traversants Ø8
result = (
    result.faces(">Z")
    .workplane(origin=(0, 0, 0))
    .pushPoints([(15, 15), (105, 15), (15, 65), (105, 65)])
    .hole(8)
)

# Poche rectangulaire 40 x 25, profondeur 6, depuis la face avant (z = 15)
result = (
    result.faces(">Z")
    .workplane(origin=(0, 0, 0))
    .center(55, 37.5)
    .rect(40, 25)
    .cutBlind(-6)
)

# Perçage borgne Ø12, profondeur 8, depuis la face avant (z = 15)
result = (
    result.faces(">Z")
    .workplane(origin=(0, 0, 0))
    .center(85, 60)
    .circle(6)
    .cutBlind(-8)
)

cq.exporters.export(result, "/work/out.step")