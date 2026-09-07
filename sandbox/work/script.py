import cadquery as cq

result = (
    cq.Workplane("XY")
    .box(84, 52, 12, centered=(False, False, False))
)

result = (
    result.faces(">Z")
    .workplane(origin=(0, 0, 0))
    .pushPoints([(18, 14), (66, 38)])
    .hole(8.5)
)

cq.exporters.export(result, "/work/out.step")