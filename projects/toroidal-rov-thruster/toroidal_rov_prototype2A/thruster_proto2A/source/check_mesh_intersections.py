"""Triangle-level collision check; shared-vertex pairs excluded as adjacency.
This supplements, but does not replace, exact BRep self-interference checking.
"""
import pathlib,json,numpy as np,vtk,time
from vtk.util.numpy_support import vtk_to_numpy
R=pathlib.Path(__file__).resolve().parents[1]
r=vtk.vtkSTLReader();r.SetFileName(str(R/'exports/rotor.stl'));r.MergingOn();r.Update();p=r.GetOutput();f=vtk_to_numpy(p.GetPolys().GetData()).reshape(-1,4)[:,1:]
c=vtk.vtkCollisionDetectionFilter();c.SetInputData(0,p);c.SetInputData(1,p);m=vtk.vtkMatrix4x4();m.Identity();c.SetMatrix(0,m);c.SetMatrix(1,m);c.SetCollisionModeToAllContacts();c.SetBoxTolerance(0);c.SetCellTolerance(0);c.SetNumberOfCellsPerNode(4);t=time.time();c.Update()
a=vtk_to_numpy(c.GetContactCells(0));b=vtk_to_numpy(c.GetContactCells(1));keep=a<b;a=a[keep];b=b[keep]
adj=np.any(f[a,:,None]==f[b,None,:],axis=(1,2));a=a[~adj];b=b[~adj]
out={'method':'VTK triangle collision, all contacts, identity transform; exclude pairs sharing any vertex','candidate_nonadjacent_intersections':int(len(a)),'pairs':np.column_stack([a,b]).tolist()[:200],'seconds':time.time()-t,'limitation':'Coplanar or numerical contacts require inspection; exact BRep self-interference remains a separate gate.'}
(R/'reports/rotor_mesh_intersections.json').write_text(json.dumps(out,indent=2));print(out,flush=True)
