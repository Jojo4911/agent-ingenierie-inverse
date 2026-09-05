
import cadquery as cq
r = cq.Workplane("XY").box(20, 10)   # argument manquant, doit lever
cq.exporters.export(r, "/work/out.step")
