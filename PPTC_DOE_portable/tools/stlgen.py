import gmsh, sys, time
h=float(sys.argv[1]) if len(sys.argv)>1 else 1.5
gmsh.initialize(); gmsh.option.setNumber('General.Terminal',1)
gmsh.model.occ.importShapes('../references/cad/PPTC_geo_no_gap.stp'); gmsh.model.occ.synchronize()
gmsh.option.setNumber('Mesh.Algorithm',6)
gmsh.option.setNumber('Mesh.MeshSizeMin',0.3*h); gmsh.option.setNumber('Mesh.MeshSizeMax',4*h)
gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',24)
# blade region finer: field box r<130 x in [-30,50]
f=gmsh.model.mesh.field.add('Box'); gmsh.model.mesh.field.setNumbers(f,'VIn',[h]) if False else None
gmsh.model.mesh.field.setNumber(f,'VIn',h); gmsh.model.mesh.field.setNumber(f,'VOut',4*h)
for k,v in dict(XMin=-30,XMax=50,YMin=-130,YMax=130,ZMin=-130,ZMax=130).items(): gmsh.model.mesh.field.setNumber(f,k,v)
gmsh.model.mesh.field.setAsBackgroundMesh(f)
gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0)
t=time.time(); gmsh.model.mesh.generate(2); print('meshed in',time.time()-t,flush=True)
gmsh.option.setNumber('Mesh.Binary',0)
gmsh.write(f'prop_h{h}.stl'); print('written',flush=True)
gmsh.finalize()
