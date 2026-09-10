import cadquery as cq

# Dimensions
L = 84.0   # longueur (X)
H = 52.0   # hauteur (Y)
E = 12.0   # epaisseur (Z)

# Plaque rectangulaire, coin inferieur gauche a l'origine, face avant z=0
result = (
    cq.Workplane("XY")
    .moveTo(0, 0)
    .rect(L, H, centered=False)
    .extrude(E)
)

# Percages traversants Ø8.5
result = (
    result.faces(">Z")
    .workplane(origin=(0, 0, 0))
    .pushPoints([(18.0, 14.0), (66.0, 38.0)])
    .hole(8.5)
)

cq.exporters.export(result, "/work/out.step")