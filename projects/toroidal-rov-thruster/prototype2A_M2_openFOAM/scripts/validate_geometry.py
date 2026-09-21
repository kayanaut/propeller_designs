#!/usr/bin/env python3
"""Mandatory geometry checks before meshing. Exits non-zero on the first failed check.

Reads geometry/rotor_p2a.stl and geometry/stator_p2a.stl (metres, rotation axis +x), written
by the prototype's source/export_cfd.py, and the MRF cylinder in system/topoSetDict, then
copies both STLs to constant/triSurface/.

The stator is the duct fused with the motor support and pod, so the duct's inner profile is
read only from stator points outside DUCT_R_MIN and ahead of the duct's rear face.
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
ROTOR, STATOR = 'rotor_p2a.stl', 'stator_p2a.stl'

ENVELOPE_MAX = 0.0500      # m, rotor radius (100 mm diameter)
THROAT_D = 0.104           # m, duct throat diameter
CLEARANCE_MIN = 0.0020     # m, rotor-to-duct radial gap over a full revolution
MRF_MARGIN = 0.0005        # m, MRF cylinder to rotor and to every stationary surface
TOLERANCE = 0.0005         # m
DUCT_R_MIN = 0.030         # m, stator points inside this radius belong to the motor pod
DUCT_X_MAX = 0.0215        # m, the struts start at the duct rear face, x = 0.022 m
EPS = 1e-7                 # m, float32 STL rounding


def fail(msg):
    sys.exit(f'GEOMETRY CHECK FAILED: {msg}')


def read_stl(path):
    if not path.exists():
        fail(f'missing {path}: run the prototype source/export_cfd.py first')
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
    if span.max() > 0.3 or span.max() < 0.01:
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


def duct_inner_profile(pts, tris, bin_m=0.00025, per_edge=21):
    """Lowest duct radius in axial bins. Points are sampled along every triangle edge, because
    the straight throat has vertices only at its two ends; a vertex-only profile would read the
    outer surface in between."""
    v = pts[tris]
    t = np.linspace(0.0, 1.0, per_edge)[None, :, None]
    s = np.vstack([(v[:, a, None, :] + (v[:, b, None, :] - v[:, a, None, :]) * t).reshape(-1, 3)
                   for a, b in ((0, 1), (1, 2), (2, 0))])
    r = np.hypot(s[:, 1], s[:, 2])
    keep = (r > DUCT_R_MIN) & (s[:, 0] < DUCT_X_MAX)
    x, r = s[keep, 0], r[keep]
    idx = np.floor((x - x.min()) / bin_m).astype(int)
    order = np.argsort(idx, kind='stable')
    idx, x, r = idx[order], x[order], r[order]
    starts = np.flatnonzero(np.r_[True, np.diff(idx) != 0])
    return x.min() + (idx[starts] + 0.5) * bin_m, np.minimum.reduceat(r, starts)


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
    rotor, rtris = read_stl(SRC / ROTOR)
    stator, stris = read_stl(SRC / STATOR)
    check_surface(ROTOR, rotor, rtris)
    check_surface(STATOR, stator, stris)

    envelope = np.hypot(*rotor[:, 1:].T).max()
    if envelope > ENVELOPE_MAX:
        fail(f'rotor radius {envelope * 1e3:.2f} mm > {ENVELOPE_MAX * 1e3:.0f} mm')

    xs, rd = duct_inner_profile(stator, stris)
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
    if rx.min() < x1 + MRF_MARGIN - EPS or rx.max() > x2 - MRF_MARGIN + EPS:
        fail(f'MRF span {x1 * 1e3:.1f}..{x2 * 1e3:.1f} mm does not cover rotor '
             f'{rx.min() * 1e3:.2f}..{rx.max() * 1e3:.2f} mm with {MRF_MARGIN * 1e3:.1f} mm margin')
    sr = np.hypot(*stator[:, 1:].T)
    inside = (sr < radius + MRF_MARGIN - EPS) & (stator[:, 0] > x1 - MRF_MARGIN + EPS) & (stator[:, 0] < x2 + MRF_MARGIN - EPS)
    if inside.any():
        j = np.flatnonzero(inside)[0]
        fail(f'stationary surface within {MRF_MARGIN * 1e3:.1f} mm of the MRF zone at x = {stator[j, 0] * 1e3:.2f} mm, '
             f'r = {sr[j] * 1e3:.2f} mm')
    pod_front = stator[sr < DUCT_R_MIN][:, 0].min()

    print(f'rotor radius {envelope * 1e3:.2f} mm, x {rx.min() * 1e3:.2f}..{rx.max() * 1e3:.2f} mm; '
          f'duct throat {2e3 * rd.min():.2f} mm; clearance {gap[i] * 1e3:.2f} mm at x = {sample[i, 0] * 1e3:.2f} mm')
    print(f'MRF r = {radius * 1e3:.1f} mm, x {x1 * 1e3:.1f}..{x2 * 1e3:.1f} mm: {(radius - envelope) * 1e3:.2f} mm to rotor, '
          f'{(duct_in_zone - radius) * 1e3:.2f} mm to duct, {(pod_front - x2) * 1e3:.2f} mm to the motor pod')

    DST.mkdir(parents=True, exist_ok=True)
    for name in (ROTOR, STATOR):
        shutil.copy2(SRC / name, DST / name)
    print('All geometry checks passed; STLs copied to constant/triSurface/')


if __name__ == '__main__':
    main()
