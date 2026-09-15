"""Export the P2A CFD surfaces: rotating body and stationary body, metres, rotation axis +x.

rotor_p2a.stl   hub and loops with the M200 interface filled in, extended to cfd.split_z;
                the whole surface rotates (MRF zone).
stator_p2a.stl  duct fused with the motor support; the flooded shroud is filled into a
                solid pod and holes, slots and the cable boss are left out (first CFD model).

Frame: the design frame (mm, axis +Z, jet +Z) maps to OpenFOAM as
(x, y, z)_OF = 0.001 * (z, y, -x), the transform of the 1B-14 case. It is a proper rotation,
so forward rotation about -Z becomes omega < 0 about +x.

Run: python source/export_cfd.py [--case ../../prototype2A_M2_openFOAM]
Writes exports/cfd/ and, if the case folder exists, copies the STLs to its geometry/.
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import tempfile

import cadquery as cq
import numpy as np

import build as B
import rotor as RT

ROOT, P = RT.ROOT, RT.P
CFD = P['cfd']
OUT = ROOT / 'exports' / 'cfd'
TO_OF = 0.001 * np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], float)
DEFAULT_CASE = ROOT.parent.parent / 'prototype2A_M2_openFOAM'


def read_stl(path):
    b = pathlib.Path(path).read_bytes()
    n = int(np.frombuffer(b, np.uint32, 1, 80)[0])
    if 84 + 50 * n == len(b):
        rec = np.frombuffer(b, np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]), n, 84)
        v = rec['v'].reshape(-1, 3).astype(float)
    else:
        v = np.array([line.split()[1:4] for line in b.decode(errors='ignore').splitlines()
                      if line.strip().startswith('vertex')], float)
    pts, inv = np.unique(np.round(v, 6), axis=0, return_inverse=True)
    return pts, inv.reshape(-1, 3)


def write_stl(path, pts, tris, name):
    v = pts[tris].astype('<f4')
    nrm = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-30)
    rec = np.zeros(len(tris), np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
    rec['n'], rec['v'] = nrm, v.reshape(-1, 9)
    pathlib.Path(path).write_bytes(name.encode().ljust(80, b' ') + np.uint32(len(tris)).tobytes() + rec.tobytes())


def surface(shape, name):
    """Tessellate in mm, merge vertices, map to the OpenFOAM frame, orient outward."""
    assert shape.isValid() and len(shape.Solids()) == 1, name + ' must be one valid solid'
    with tempfile.TemporaryDirectory() as tmp:
        f = pathlib.Path(tmp) / 'part.stl'
        cq.exporters.export(shape, str(f), tolerance=CFD['stl_tolerance'], angularTolerance=CFD['stl_angular_tolerance'])
        pts, tris = read_stl(f)
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    _, undirected = np.unique(np.sort(e, axis=1), axis=0, return_counts=True)
    if (undirected != 2).any():
        raise SystemExit(f'{name}: tessellation not closed ({int((undirected != 2).sum())} open edges)')
    crossings = self_intersections(pts, tris)
    if crossings:
        raise SystemExit(f'{name}: tessellation has {crossings} self-intersecting triangle pairs '
                         '(OpenFOAM surfaceCheck would reject it)')
    pts = pts @ TO_OF.T
    v = pts[tris]
    if np.einsum('ij,ij->i', v[:, 0], np.cross(v[:, 1], v[:, 2])).sum() < 0:
        tris = tris[:, ::-1]
    return pts, tris


def self_intersections(pts, tris):
    import open3d as o3d
    mesh = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(pts), o3d.utility.Vector3iVector(tris))
    return len(np.asarray(mesh.get_self_intersecting_triangles()))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--case', default=str(DEFAULT_CASE), help='OpenFOAM case folder to copy the STLs into')
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    sec = RT.sections(RT.solve_apex())
    rotor, _ = RT.rotor_solid(sec, cfd=True)
    stator = B.duct(cfd=True).fuse(B.motor_support(cfd=True)).clean()
    info = {'revision': P['revision'], 'frame': '(x, y, z)_OF = 0.001 (z, y, -x); axis +x; jet +x; forward omega < 0',
            'split_z_mm': CFD['split_z']}
    for name, shape in (('rotor_p2a', rotor), ('stator_p2a', stator)):
        pts, tris = surface(shape, name)
        write_stl(OUT / f'{name}.stl', pts, tris, f'{name} {P["revision"]} m +x')
        info[name] = {'triangles': int(len(tris)), 'volume_mm3': shape.Volume(),
                      'x_range_mm': [float(pts[:, 0].min() * 1e3), float(pts[:, 0].max() * 1e3)],
                      'r_max_mm': float(np.hypot(pts[:, 1], pts[:, 2]).max() * 1e3),
                      'sha256': hashlib.sha256((OUT / f'{name}.stl').read_bytes()).hexdigest()}
        print(name, info[name], flush=True)
    (OUT / 'cfd_geometry.json').write_text(json.dumps(info, indent=2))
    case = pathlib.Path(args.case)
    if case.exists():
        (case / 'geometry').mkdir(exist_ok=True)
        for f in ('rotor_p2a.stl', 'stator_p2a.stl', 'cfd_geometry.json'):
            shutil.copy2(OUT / f, case / 'geometry' / f)
        print('copied to', case / 'geometry')


if __name__ == '__main__':
    main()
