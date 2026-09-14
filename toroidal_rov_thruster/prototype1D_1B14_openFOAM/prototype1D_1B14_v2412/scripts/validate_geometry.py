#!/usr/bin/env python3
"""Mandatory geometry checks before meshing. Exits non-zero on the first failed check.

Reads geometry/rotor_1B14.stl and geometry/duct_1B14.stl (metres, rotation axis +x)
and the MRF cylinder in system/topoSetDict, then copies both STLs to
constant/triSurface/. The STLs are produced by scripts/make_geometry.py.
"""
from pathlib import Path
import re
import shutil
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'geometry'
DST = ROOT / 'constant' / 'triSurface'

ENVELOPE_MAX = 0.0500      # m, rotor radius (100 mm diameter)
THROAT_D = 0.104           # m, duct throat diameter for 1B-14
CLEARANCE_MIN = 0.0020     # m, rotor-to-duct radial gap over a full revolution
MRF_MARGIN = 0.0005        # m, MRF cylinder to rotor and to duct
TOLERANCE = 0.0005         # m


def fail(msg):
    sys.exit(f'GEOMETRY CHECK FAILED: {msg}')


def read_stl(path):
    if not path.exists():
        fail(f'missing {path}')
    b = path.read_bytes()
    n = int(np.frombuffer(b, np.uint32, 1, 80)[0]) if len(b) >= 84 else -1
    if 84 + 50 * n == len(b):
        rec = np.frombuffer(b, np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]), n, 84)
        v = rec['v'].reshape(-1, 3).astype(float)
    else:
        v = np.array([line.split()[1:4] for line in b.decode(errors='ignore').splitlines()
                      if line.strip().startswith('vertex')], float)
    if len(v) < 12 or not np.isfinite(v).all():
        fail(f'{path.name}: empty or non-finite STL')
    pts, inv = np.unique(np.round(v, 9), axis=0, return_inverse=True)
    return pts, inv.reshape(-1, 3)


def check_surface(name, pts, tris):
    """Metres, closed 2-manifold, one shell, consistent winding, outward normals."""
    span = np.ptp(pts, axis=0)
    if span.max() > 0.2 or span.max() < 0.01:
        fail(f'{name}: span {span} m - not in metres')
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    _, undirected = np.unique(np.sort(e, axis=1), axis=0, return_counts=True)
    if (undirected != 2).any():
        fail(f'{name}: not closed ({int((undirected != 2).sum())} edges not shared by two faces)')
    _, directed = np.unique(e, axis=0, return_counts=True)
    if (directed != 1).any():
        fail(f'{name}: inconsistent winding ({int((directed != 1).sum())} repeated directed edges)')
    parts = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])),
                                            shape=(len(pts),) * 2), directed=False)[0]
    if parts != 1:
        fail(f'{name}: {parts} separate shells, expected 1')
    v = pts[tris]
    volume = np.einsum('ij,ij->i', v[:, 0], np.cross(v[:, 1], v[:, 2])).sum() / 6
    if volume <= 0:
        fail(f'{name}: normals point inward (signed volume {volume:.3g} m3)')
    print(f'{name}: {len(tris)} triangles, closed, one shell, outward, volume {volume * 1e9:.0f} mm3')


def duct_inner_profile(pts):
    x = np.round(pts[:, 0], 6)
    stations = np.unique(x)
    return stations, np.array([np.hypot(*pts[x == s][:, 1:].T).min() for s in stations])


def mrf_cylinder():
    text = (ROOT / 'system' / 'topoSetDict').read_text()
    text = re.sub(r'//.*', '', text)
    vec = lambda key: [float(v) for v in re.search(rf'{key}\s*\(([^)]*)\)', text).group(1).split()]
    p1, p2 = vec('p1'), vec('p2')
    radius = float(re.search(r'radius\s+([-+0-9.eE]+)', text).group(1))
    if p1[1:] != [0, 0] or p2[1:] != [0, 0]:
        fail('topoSetDict: MRF cylinder is not on the x axis')
    return min(p1[0], p2[0]), max(p1[0], p2[0]), radius


def main():
    rotor, rtris = read_stl(SRC / 'rotor_1B14.stl')
    duct, dtris = read_stl(SRC / 'duct_1B14.stl')
    check_surface('rotor_1B14.stl', rotor, rtris)
    check_surface('duct_1B14.stl', duct, dtris)

    envelope = np.hypot(*rotor[:, 1:].T).max()
    if envelope > ENVELOPE_MAX:
        fail(f'rotor radius {envelope * 1e3:.2f} mm > {ENVELOPE_MAX * 1e3:.0f} mm')

    xs, rd = duct_inner_profile(duct)
    if abs(2 * rd.min() - THROAT_D) > TOLERANCE:
        fail(f'duct throat {2e3 * rd.min():.2f} mm, expected {THROAT_D * 1e3:.0f} mm')

    rx = rotor[:, 0]
    if rx.min() < xs[0] or rx.max() > xs[-1]:
        fail(f'rotor x {rx.min() * 1e3:.2f}..{rx.max() * 1e3:.2f} mm extends outside the duct')
    e = np.vstack([rtris[:, [0, 1]], rtris[:, [1, 2]], rtris[:, [2, 0]]])
    sample = np.vstack([rotor, (rotor[e[:, 0]] + rotor[e[:, 1]]) / 2, rotor[rtris].mean(1)])
    gap = np.interp(sample[:, 0], xs, rd) - np.hypot(*sample[:, 1:].T)
    i = int(np.argmin(gap))
    if gap[i] < CLEARANCE_MIN:
        fail(f'rotor-duct clearance {gap[i] * 1e3:.2f} mm at x = {sample[i, 0] * 1e3:.2f} mm')

    x1, x2, radius = mrf_cylinder()
    duct_in_zone = np.interp(np.linspace(x1, x2, 400), xs, rd).min()
    if radius < envelope + MRF_MARGIN:
        fail(f'MRF radius {radius * 1e3:.2f} mm too close to rotor ({envelope * 1e3:.2f} mm)')
    if radius > duct_in_zone - MRF_MARGIN:
        fail(f'MRF radius {radius * 1e3:.2f} mm too close to duct ({duct_in_zone * 1e3:.2f} mm)')
    if rx.min() < x1 + MRF_MARGIN or rx.max() > x2 - MRF_MARGIN:
        fail(f'MRF span {x1 * 1e3:.1f}..{x2 * 1e3:.1f} mm does not cover rotor '
             f'{rx.min() * 1e3:.2f}..{rx.max() * 1e3:.2f} mm')

    print(f'rotor radius {envelope * 1e3:.2f} mm; duct throat {2e3 * rd.min():.2f} mm; '
          f'clearance {gap[i] * 1e3:.2f} mm at x = {sample[i, 0] * 1e3:.2f} mm')
    print(f'MRF r = {radius * 1e3:.1f} mm, x {x1 * 1e3:.1f}..{x2 * 1e3:.1f} mm: '
          f'{(radius - envelope) * 1e3:.2f} mm to rotor, {(duct_in_zone - radius) * 1e3:.2f} mm to duct')

    DST.mkdir(parents=True, exist_ok=True)
    for name in ('rotor_1B14.stl', 'duct_1B14.stl'):
        shutil.copy2(SRC / name, DST / name)
    print('All geometry checks passed; STLs copied to constant/triSurface/')


if __name__ == '__main__':
    main()
