#!/usr/bin/env python3
"""Build the prototype 1B-14 rotor from its design parameters, plus the CFD duct.

Why a rebuild: the recovered prototype1B_rotor.stl is not a valid solid. Its loop
legs converge into a folded tip (path bend radius 0.04 mm under a 20 mm chord,
1604 self-intersecting triangle pairs), the roots twist ~70 deg within 2 mm and sit
0.11 mm off the hub, every shell is wound inside out, and the envelope reaches
111 mm. Details in geometry/GEOMETRY_REPORT.md.

Blade construction, design B - SYNTHETIC, parametric design from
prototype1B_design.json, shaped like a front-opening toroidal rotor:
  * Constant face pitch P = 2*pi*r_outer*tan(helical_deg) * loading_scale.
  * Each loop is a leading leg and a second leg joined by a round apex. The second
    leg is a rigid copy of the leading leg, offset LOOP_OPEN at LOOP_ANGLE on the
    cylinder at R_REF (mostly circumferential), so the loop opens in the front view.
  * The chord lies on the pitch helix along the legs and turns normal to the path
    around the apex (weight 1 - (t.e_r)^2), so the apex never bends across the chord.
  * The apex generator radius is solved so the rotor just fits the 100 mm envelope;
    chord, skew and rake schedules run from r_root to that apex radius.
  * The loop apex sits outer_z aft of the leading root (loop axial rise).
  * NACA 00xx sections, closed form blunted to a finite TE (as in
    cad/tools/make-geometry.py; 1 mm TE at D 250 scaled to this D).
  * Roots start inside the hub wall and flare over the last 3 mm as a modelled
    fillet (cad/underwater_cad.md Modelling notes: blend as loft sections).
  * closure_bias is not used.

Printed part (STEP): ring hub with spokes and a splined bore - SYNTHETIC
dimensions, confirm against the shaft before printing. CFD STL: closed hub.
Design A (stacked legs) and its L0 baseline: results/designA_stacked_loops_L0/.

Frames: the design frame is mm, axis +z, omega +z, jet +z (bellmouth at -z).
CFD STLs are metres with axis +x: (x, y, z)_OF = 0.001*(z, y, -x).

Run: python3 scripts/make_geometry.py [--check-only]
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import tempfile

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent.parent / 'toroidal_rov_prototype1B'
OUT = ROOT / 'geometry'
CASE = '1B-14'

# ------------------------------------------------------------------ parameters
design = json.loads((SRC / 'prototype1B_design.json').read_text())
G = design['geometry']
with open(SRC / 'CFD_DOE_27.csv') as f:
    DOE = {row['case']: row for row in csv.DictReader(f)}[CASE]

BLADES = int(G['blades'])
HUB_R, HUB_LEN = G['hub_d'] / 2, G['hub_len']
R_ROOT, R_OUTER = G['r_root'], G['r_outer']
SKEW_DEG, HELICAL_DEG = G['skew_deg'], G['helical_deg']
CHORD_MIN, CHORD_MAX = G['chord_min'], G['chord_max']
FOIL_T, ROOT_LOAD = G['foil_t'], G['root_load']
LOOP_RISE = float(DOE['outer_z_mm'])
LOADING = float(DOE['loading_scale'])
THROAT_ID = float(DOE['throat_id_mm'])

# Choices made here (the design file does not define them)
PITCH = 2 * math.pi * R_OUTER * math.tan(math.radians(HELICAL_DEG)) * LOADING
LOOP_OPEN = 24.0            # mm, offset of the second leg at R_REF
LOOP_ANGLE = 35.0           # deg, offset direction on the cylinder: from +theta toward +z (aft)
R_REF = 20.0                # mm, radius where the offset is defined
R_START = 11.5              # mm, generator line starts inside the hub wall
FLARE_TOP = HUB_R + 3.0     # mm, root flare (modelled fillet) begins here
FLARE_T, FLARE_C = 0.5, 0.15  # extra thickness and chord fraction at the hub surface
TE_MM = 1.0 * 100.0 / 250.0   # finite trailing edge, mm
N_SECTIONS, N_SIDE = 121, 40

HUB_RING_R = 11.0           # mm, inner radius of the printed hub ring; blade roots end in its wall
BUSHING_R = 8.0             # mm, outer radius of the printed bushing
SPOKES, SPOKE_W = 3, 3.0    # printed spokes between ring and bushing; width mm
SPLINE_TEETH = 12
SPLINE_MAJOR_D, SPLINE_MINOR_D = 12.0, 10.5   # mm, internal spline in the bushing

ENVELOPE_MAX = 50.0         # mm, rotor radius limit (100 mm diameter)
ENVELOPE_TARGET = 49.9      # mm, solved apex leaves this margin for tessellation
CLEARANCE_MIN = 2.0         # mm, design radial gap to the duct
STL_DEFLECTION = (0.02, 0.3)  # linear mm, angular rad

APEX_R = R_OUTER            # mm, apex generator radius; main() solves it to fit ENVELOPE_TARGET

TO_OF = 0.001 * np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], float)


def pitch_angle(r):
    return np.arctan(PITCH / (2 * np.pi * r))


def derived():
    """Second-leg offset (rad, mm), generator rake at the apex, and round-apex geometry."""
    a = math.radians(LOOP_ANGLE)
    dth, dz = LOOP_OPEN * math.cos(a) / R_REF, LOOP_OPEN * math.sin(a)
    apex_a = 0.5 * math.hypot(APEX_R * dth, dz)
    return dict(dth=dth, dz=dz, rake=LOOP_RISE - 0.5 * dz, apex_a=apex_a, r_turn=APEX_R - apex_a)


# ------------------------------------------------------------------- STL I/O
def read_stl(path):
    """Unique points (N,3) and triangles (M,3) of a binary or ASCII STL."""
    b = Path(path).read_bytes()
    n = int(np.frombuffer(b, np.uint32, 1, 80)[0]) if len(b) >= 84 else -1
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
    Path(path).write_bytes(name.encode().ljust(80, b' ') +
                           np.uint32(len(tris)).tobytes() + rec.tobytes())


def surface_stats(pts, tris):
    """Closed/manifold, orientation consistency, signed volume, connected parts."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    _, directed = np.unique(e, axis=0, return_counts=True)
    _, undirected = np.unique(np.sort(e, axis=1), axis=0, return_counts=True)
    v = pts[tris]
    vol = np.einsum('ij,ij->i', v[:, 0], np.cross(v[:, 1], v[:, 2])).sum() / 6
    a = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(pts),) * 2)
    parts = connected_components(a, directed=False)[0]
    return dict(closed=bool((undirected == 2).all()), consistent=bool((directed == 1).all()),
                volume=vol, parts=parts, triangles=len(tris))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --------------------------------------------------------------- blade layout
def radial_blend(r):
    return np.clip((r - R_ROOT) / (APEX_R - R_ROOT), 0.0, 1.0)


def loop_rf(n=6000):
    """Dense (r, f) along one loop: f = 0 on the leading leg, 1 on the second leg."""
    d = derived()
    leg = np.linspace(R_START, d['r_turn'], n, endpoint=False)
    phi = np.linspace(0, np.pi, n, endpoint=False)
    r = np.r_[leg, d['r_turn'] + d['apex_a'] * np.sin(phi), np.linspace(d['r_turn'], R_START, n)]
    f = np.r_[np.zeros(n), (1 - np.cos(phi)) / 2, np.ones(n)]
    return r, f


def place(r, f, z0):
    """Generator line (r, theta, z) from radius and second-leg fraction."""
    d, b = derived(), radial_blend(r)
    theta = -np.radians(SKEW_DEG) * b**2 + f * d['dth']
    z = z0 + d['rake'] * b**2 + f * d['dz']
    return r, theta, z


def xyz(r, th, z):
    return np.stack([r * np.cos(th), r * np.sin(th), z], -1)


def naca_half(x, t_c, chord):
    y = 5 * t_c * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x**2
                   + 0.2843 * x**3 - 0.1036 * x**4)
    return y + TE_MM / 2 / chord * x


def build_sections(z0):
    """Section rings (N, M, 3) in mm, seam at the upper TE, plus schedules."""
    r_d, f_d = loop_rf()
    dense = xyz(*place(r_d, f_d, z0))
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(dense, axis=0), axis=1))]
    tan = np.gradient(dense, s, axis=0)
    tan /= np.linalg.norm(tan, axis=1, keepdims=True)
    bend = 1 / np.maximum(np.linalg.norm(np.gradient(tan, s, axis=0), axis=1), 1e-12)

    sk = np.linspace(0, s[-1], N_SECTIONS)
    r, th, z = place(np.interp(sk, s, r_d), np.interp(sk, s, f_d), z0)
    t = np.stack([np.interp(sk, s, tan[:, i]) for i in range(3)], -1)
    t /= np.linalg.norm(t, axis=1, keepdims=True)

    zero = np.zeros_like(r)
    er = np.stack([np.cos(th), np.sin(th), zero], -1)
    et = np.stack([-np.sin(th), np.cos(th), zero], -1)
    beta = pitch_angle(r)
    lete = -np.cos(beta)[:, None] * et + np.sin(beta)[:, None] * np.array([0, 0, 1.0])  # LE->TE
    along = np.einsum('ij,ij->i', lete, t)
    weight = 1 - np.einsum('ij,ij->i', t, er) ** 2       # 0 on radial legs, 1 across the apex
    c = lete - (weight * along)[:, None] * t
    c /= np.linalg.norm(c, axis=1, keepdims=True)
    n = np.cross(t, c)
    n /= np.linalg.norm(n, axis=1, keepdims=True)

    b = radial_blend(r)
    flare = np.clip((FLARE_TOP - r) / (FLARE_TOP - HUB_R), 0, 1) ** 2
    chord = (CHORD_MIN + (CHORD_MAX - CHORD_MIN) * np.sin(np.pi * b / 2)) * (1 + FLARE_C * flare)
    t_c = FOIL_T * (1 + (1 / ROOT_LOAD - 1) * (1 - b) ** 2) * (1 + FLARE_T * flare)

    # Sections are wrapped onto their cylinder outside the hub, but flat where the
    # root is buried, so the loft's end caps are planar.
    wrap = np.clip((r - R_START) / (HUB_R - R_START), 0, 1)
    wrap = wrap * wrap * (3 - 2 * wrap)

    x = (1 - np.cos(np.pi * np.linspace(0, 1, N_SIDE + 1))) / 2
    rings = []
    for k in range(N_SECTIONS):
        yt = naca_half(x, t_c[k], chord[k])
        px = np.r_[x[::-1], x[1:]]                      # upper TE->LE, lower LE->TE
        py = np.r_[yt[::-1], -yt[1:]]
        d = ((px - 0.5) * chord[k])[:, None] * c[k] + (py * chord[k])[:, None] * n[k]
        wrapped = xyz(r[k] + d @ er[k], th[k] + (d @ et[k]) / r[k], z[k] + d[:, 2])
        flat = xyz(r[k], th[k], z[k]) + d
        rings.append(wrap[k] * wrapped + (1 - wrap[k]) * flat)
    thickness = 2 * np.array([naca_half(x, t_c[k], chord[k]).max() * chord[k]
                              for k in range(N_SECTIONS)])
    return dict(s=sk, r=r, theta=th, z=z, t=t, c=c, chord=chord, t_c=t_c, thickness=thickness,
                beta=beta, bend_min=bend.min(), along_max=np.abs(along).max(), pts=np.array(rings))


def rotz(p, angle):
    ca, sa = math.cos(angle), math.sin(angle)
    return p @ np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1]]).T


def check_sections(S):
    """Numerical checks on the section rings before any CAD work."""
    pts = S['pts']
    rad = np.hypot(pts[..., 0], pts[..., 1])
    res = dict(envelope=rad.max(), bend_min=S['bend_min'], z_range=(pts[..., 2].min(),
                                                                     pts[..., 2].max()))

    # Fold test: every profile point must advance along the path between stations.
    step = np.einsum('kmj,kj->km', pts[1:] - pts[:-1], (S['t'][1:] + S['t'][:-1]) / 2)
    res['folds'] = int((step <= 0).any(axis=1).sum())
    res['min_step'] = step.min()

    ends = np.r_[pts[0], pts[-1]]
    res['root_r_max'] = np.hypot(ends[:, 0], ends[:, 1]).max()
    near_hub = rad < HUB_R + 0.5
    res['hub_margin'] = HUB_LEN / 2 - np.abs(pts[near_hub][:, 2]).max()

    # Leg-to-leg gap: the two legs outside the hub, excluding 20 mm of path at the apex.
    mid = S['s'][-1] / 2
    lead = pts[S['s'] < mid - 20].reshape(-1, 3)
    aft = pts[S['s'] > mid + 20].reshape(-1, 3)
    lead, aft = [p[np.hypot(p[:, 0], p[:, 1]) > HUB_R] for p in (lead, aft)]
    res['leg_gap'] = cKDTree(aft).query(lead)[0].min()

    cloud = pts.reshape(-1, 3)
    cloud = cloud[np.hypot(cloud[:, 0], cloud[:, 1]) > HUB_R]
    res['blade_gap'] = cKDTree(rotz(cloud, 2 * math.pi / BLADES)).query(cloud)[0].min()
    res['r_min'] = rad.min()
    return res


def centre_z0():
    """Axial placement that centres the rotor on z = 0."""
    p = build_sections(0.0)['pts'][..., 2]
    return -(p.min() + p.max()) / 2


def solve_apex():
    """Largest apex generator radius (up to design r_outer) that fits ENVELOPE_TARGET."""
    global APEX_R

    def envelope(apex_r):
        global APEX_R
        APEX_R = apex_r
        p = build_sections(0.0)['pts']
        return np.hypot(p[..., 0], p[..., 1]).max()

    if envelope(R_OUTER) <= ENVELOPE_TARGET:
        return R_OUTER
    lo, hi = R_ROOT + 15.0, R_OUTER
    for _ in range(25):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if envelope(mid) <= ENVELOPE_TARGET else (lo, mid)
    APEX_R = lo
    return lo


def section_failures(chk):
    fails = []
    if chk['envelope'] > ENVELOPE_MAX - 0.1:
        fails.append(f'envelope {chk["envelope"]:.2f} mm')
    if chk['folds']:
        fails.append(f'{chk["folds"]} folded stations')
    if chk['root_r_max'] > HUB_R - 0.5:
        fails.append(f'root ends reach r {chk["root_r_max"]:.2f} mm')
    if chk['r_min'] < HUB_RING_R + 0.5:
        fails.append(f'blade root reaches the printed hub pocket (r {chk["r_min"]:.2f} mm)')
    if derived()['r_turn'] < FLARE_TOP + 2:
        fails.append(f'apex turn starts at r {derived()["r_turn"]:.2f} mm, inside the root flare')
    if chk['hub_margin'] < 0.5:
        fails.append(f'root footprint {-chk["hub_margin"]:.2f} mm past the hub end')
    if chk['leg_gap'] < 2.0 or chk['blade_gap'] < 2.0:
        fails.append(f'gaps leg {chk["leg_gap"]:.2f} / blade {chk["blade_gap"]:.2f} mm < 2')
    if max(abs(v) for v in chk['z_range']) > 17.0:
        fails.append(f'axial extent {chk["z_range"]} beyond +/-17 mm')
    return fails


# ------------------------------------------------------------------ CAD (OCP)
def cad_rotor(S):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
    from OCP.BRepBuilderAPI import (BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace,
                                    BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeWire,
                                    BRepBuilderAPI_Transform)
    from OCP.BRepCheck import BRepCheck_Analyzer
    from OCP.BRepGProp import BRepGProp
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakePrism
    from OCP.GProp import GProp_GProps
    from OCP.GeomAPI import GeomAPI_Interpolate
    from OCP.Interface import Interface_Static
    from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer
    from OCP.ShapeFix import ShapeFix_Shape
    from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
    from OCP.StlAPI import StlAPI_Writer
    from OCP.TColStd import TColStd_HArray1OfReal
    from OCP.TColgp import TColgp_HArray1OfPnt
    from OCP.TopAbs import TopAbs_SOLID
    from OCP.TopExp import TopExp_Explorer
    from OCP.gp import gp_Ax1, gp_Ax2, gp_Dir, gp_Pnt, gp_Trsf, gp_Vec

    def volume(shape):
        g = GProp_GProps()
        BRepGProp.VolumeProperties_s(shape, g)
        return g.Mass()

    def area(shape):
        g = GProp_GProps()
        BRepGProp.SurfaceProperties_s(shape, g)
        return g.Mass()

    def fixed(shape, what):
        fix = ShapeFix_Shape(shape)
        fix.Perform()
        shape = fix.Shape()
        if not BRepCheck_Analyzer(shape).IsValid():
            raise SystemExit(f'{what}: solid is not valid')
        return shape

    def boolean(op, a, b, what):
        result = op(a, b)
        if not result.IsDone():       # a failed boolean returns a null shape that crashes OCCT later
            raise SystemExit(f'{what}: boolean operation failed')
        return result.Shape()

    def rotated(shape, angle):
        tr = gp_Trsf()
        tr.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), angle)
        return BRepBuilderAPI_Transform(shape, tr, True).Shape()

    def cylinder(radius, z0, length):
        return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0, 0, z0), gp_Dir(0, 0, 1)),
                                        radius, length).Shape()

    def solids(shape):
        ex, n = TopExp_Explorer(shape, TopAbs_SOLID), 0
        while ex.More():
            n += 1
            ex.Next()
        return n

    # One parametrisation for every section, so all section splines share a knot
    # vector. With per-section knots the loft merges them all and the STEP file
    # grows to millions of control points.
    x = (1 - np.cos(np.pi * np.linspace(0, 1, N_SIDE + 1))) / 2
    yt = naca_half(x, FOIL_T, CHORD_MAX)
    ref = np.c_[np.r_[x[::-1], x[1:]], np.r_[yt[::-1], -yt[1:]]]
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(ref, axis=0), axis=1))]
    params = TColStd_HArray1OfReal(1, len(arc))
    for i, u in enumerate(arc / arc[-1]):
        params.SetValue(i + 1, float(u))

    def wire(ring):
        arr = TColgp_HArray1OfPnt(1, len(ring))
        for i, p in enumerate(ring):
            arr.SetValue(i + 1, gp_Pnt(*map(float, p)))
        spline = GeomAPI_Interpolate(arr, params, False, 1e-7)
        spline.Perform()
        edge = BRepBuilderAPI_MakeEdge(spline.Curve()).Edge()
        te = BRepBuilderAPI_MakeEdge(gp_Pnt(*map(float, ring[-1])),
                                     gp_Pnt(*map(float, ring[0]))).Edge()
        return BRepBuilderAPI_MakeWire(edge, te).Wire()

    def spline_bore():
        """Internal spline: gaps at the major radius, teeth down to the minor radius."""
        big, small = SPLINE_MAJOR_D / 2, SPLINE_MINOR_D / 2
        pitch = 2 * math.pi / SPLINE_TEETH
        poly = BRepBuilderAPI_MakePolygon()
        for i in range(SPLINE_TEETH):
            for frac, rad in ((0.0, big), (0.2, big), (0.4, big), (0.5, small), (0.7, small), (0.9, small)):
                a = (i + frac) * pitch
                poly.Add(gp_Pnt(rad * math.cos(a), rad * math.sin(a), -HUB_LEN))
        poly.Close()
        face = BRepBuilderAPI_MakeFace(poly.Wire(), True).Face()
        return BRepPrimAPI_MakePrism(face, gp_Vec(0, 0, 2 * HUB_LEN)).Shape()

    loft = BRepOffsetAPI_ThruSections(True, False, 1e-6)
    loft.CheckCompatibility(False)
    for ring in S['pts']:
        loft.AddWire(wire(ring))
    loft.Build()
    if not loft.IsDone():
        raise SystemExit('blade loft failed')
    blade = fixed(loft.Shape(), 'blade')
    blades = [blade] + [rotated(blade, 2 * math.pi * i / BLADES) for i in range(1, BLADES)]

    clash = max(volume(boolean(BRepAlgoAPI_Common, blades[i], blades[j], 'blade clash test'))
                for i in range(BLADES) for j in range(i + 1, BLADES))

    # The hub stays one cylindrical face. Its tessellation has long flat sliver
    # triangles between the blade intersection curves, but they lie on the cylinder
    # and snap without distortion. Splitting the hub along its axis instead makes
    # OpenFOAM surfaceCheck report self-intersections at the split seams.
    rotor = cylinder(HUB_R, -HUB_LEN / 2, HUB_LEN)
    for i, b in enumerate(blades):
        rotor = boolean(BRepAlgoAPI_Fuse, rotor, b, f'fuse blade {i}')
    unify = ShapeUpgrade_UnifySameDomain(rotor, True, True, False)
    unify.Build()
    rotor = fixed(unify.Shape(), 'rotor')
    if solids(rotor) != 1:
        raise SystemExit(f'rotor has {solids(rotor)} solids, expected 1')

    # Printed part: ring hub, spokes to a bushing, splined bore.
    pocket = boolean(BRepAlgoAPI_Cut, cylinder(HUB_RING_R, -HUB_LEN, 2 * HUB_LEN),
                     cylinder(BUSHING_R, -HUB_LEN, 2 * HUB_LEN), 'hub pocket')
    for i in range(SPOKES):
        spoke = BRepPrimAPI_MakeBox(gp_Pnt(0, -SPOKE_W / 2, -HUB_LEN),
                                    HUB_RING_R + 1, SPOKE_W, 2 * HUB_LEN).Shape()
        pocket = boolean(BRepAlgoAPI_Cut, pocket, rotated(spoke, 2 * math.pi * (i + 0.5) / SPOKES),
                         f'spoke {i}')
    printed = boolean(BRepAlgoAPI_Cut, rotor, pocket, 'hub pocket cut')
    printed = fixed(boolean(BRepAlgoAPI_Cut, printed, spline_bore(), 'splined bore'), 'printed rotor')
    Interface_Static.SetCVal_s('write.step.schema', 'AP242DIS')
    Interface_Static.SetCVal_s('write.step.unit', 'MM')
    step = STEPControl_Writer()
    step.Transfer(printed, STEPControl_AsIs)
    step.Write(str(OUT / 'rotor_1B14.step'))

    # CFD STL: closed hub (the shaft fills it), from the same solid.
    BRepMesh_IncrementalMesh(rotor, STL_DEFLECTION[0], False, STL_DEFLECTION[1], True)
    with tempfile.TemporaryDirectory() as tmp:
        StlAPI_Writer().Write(rotor, str(Path(tmp) / 'rotor.stl'))
        pts, tris = read_stl(Path(tmp) / 'rotor.stl')

    return dict(blade_volume=volume(blade), blade_area=area(blade), rotor_volume=volume(rotor),
                printed_volume=volume(printed), clash=clash, solids=solids(rotor),
                pts=pts, tris=tris)


def self_intersections(pts, tris):
    import open3d as o3d
    mesh = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(pts),
                                     o3d.utility.Vector3iVector(tris))
    return len(np.asarray(mesh.get_self_intersecting_triangles()))


def triangle_quality(pts, tris, S):
    """OpenFOAM triangle quality (1 equilateral, 0 degenerate), summarised by region."""
    v = pts[tris]
    a = np.linalg.norm(v[:, 1] - v[:, 2], axis=1)
    b = np.linalg.norm(v[:, 0] - v[:, 2], axis=1)
    c = np.linalg.norm(v[:, 0] - v[:, 1], axis=1)
    tri_area = 0.5 * np.linalg.norm(np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0]), axis=1)
    circum = a * b * c / np.maximum(4 * tri_area, 1e-300)
    q = tri_area / np.maximum(circum**2 * 3 * math.sqrt(3) / 4, 1e-300)
    cen = v.mean(1)
    r = np.hypot(cen[:, 0], cen[:, 1])
    te = np.vstack([rotz(np.r_[S['pts'][:, 0], S['pts'][:, -1]], 2 * math.pi * i / BLADES)
                    for i in range(BLADES)])
    region = np.full(len(q), 'blade', dtype=object)
    region[cKDTree(te).query(cen)[0] < 0.8] = 'trailing edge'
    region[(np.abs(r - HUB_R) < 0.05) & (np.abs(cen[:, 2]) < HUB_LEN / 2 - 0.05)] = 'hub cylinder'
    region[np.abs(np.abs(cen[:, 2]) - HUB_LEN / 2) < 0.05] = 'hub end caps'
    rows = []
    for name in ('blade', 'trailing edge', 'hub cylinder', 'hub end caps'):
        m = region == name
        if m.any():
            rows.append((name, int(m.sum()), q[m].min(), int((q[m] < 1e-3).sum()),
                         int((q[m] < 0.05).sum())))
    return rows


# ----------------------------------------------------------------- duct
def duct_profile(pts):
    """Inner radius at each duct ring station, sorted by z (mm, design frame)."""
    z = np.round(pts[:, 2], 3)
    stations = np.unique(z)
    inner = np.array([np.hypot(*pts[z == s][:, :2].T).min() for s in stations])
    return stations, inner


def swept_clearance(pts, tris, zs, rd):
    """Min over the rotor surface of duct inner radius minus rotor radius (360 deg sweep)."""
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    sample = np.vstack([pts, (pts[e[:, 0]] + pts[e[:, 1]]) / 2, pts[tris].mean(1)])
    inside = (sample[:, 2] >= zs[0]) & (sample[:, 2] <= zs[-1])
    gap = np.interp(sample[inside, 2], zs, rd) - np.hypot(*sample[inside, :2].T)
    i = int(np.argmin(gap))
    return gap[i], sample[inside][i], int((~inside).sum())


# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check-only', action='store_true', help='numerical checks, no CAD')
    args = ap.parse_args()

    solve_apex()
    z0 = centre_z0()
    S = build_sections(z0)
    chk = check_sections(S)
    d = derived()
    print(f'{CASE}: P = {PITCH:.2f} mm (P/D {PITCH / 100:.3f}); loop opens {np.degrees(d["dth"]):.1f} deg, '
          f'+{d["dz"]:.2f} mm aft; apex r {APEX_R:.2f} mm (design r_outer {R_OUTER}), '
          f'turn radius {d["apex_a"]:.2f} mm; rake {d["rake"]:.2f} mm; z0 {z0:.2f}')
    print(f'  envelope r {chk["envelope"]:.2f} mm, z {chk["z_range"][0]:.2f}..{chk["z_range"][1]:.2f} mm, '
          f'min bend radius {chk["bend_min"]:.2f} mm, max |chord.tangent| {S["along_max"]:.2f}')
    print(f'  folds {chk["folds"]} (min station advance {chk["min_step"]:.3f} mm); '
          f'root ends r <= {chk["root_r_max"]:.2f}, r_min {chk["r_min"]:.2f}; hub margin {chk["hub_margin"]:.2f} mm')
    print(f'  leg gap {chk["leg_gap"]:.2f} mm, blade gap {chk["blade_gap"]:.2f} mm; '
          f'chord {S["chord"].min():.2f}..{S["chord"].max():.2f}, '
          f'thickness {S["thickness"].min():.2f}..{S["thickness"].max():.2f} mm')
    fails = section_failures(chk)
    if fails:
        raise SystemExit('section checks failed: ' + '; '.join(fails))
    if args.check_only:
        return

    OUT.mkdir(exist_ok=True)
    cad = cad_rotor(S)
    if cad['clash'] > 1e-6:
        raise SystemExit(f'blades intersect each other: {cad["clash"]:.3g} mm3')
    rotor = surface_stats(cad['pts'], cad['tris'])
    if not (rotor['closed'] and rotor['consistent'] and rotor['parts'] == 1):
        raise SystemExit(f'rotor STL is not one closed, consistently wound shell: {rotor}')
    if rotor['volume'] < 0:
        cad['tris'] = cad['tris'][:, ::-1]
        rotor['volume'] = -rotor['volume']
    crossings = self_intersections(cad['pts'], cad['tris'])
    if crossings:
        raise SystemExit(f'rotor STL has {crossings} self-intersecting triangle pairs')
    envelope = np.hypot(*cad['pts'][:, :2].T).max()
    if envelope > ENVELOPE_MAX:
        raise SystemExit(f'rotor STL envelope {envelope:.3f} mm > {ENVELOPE_MAX}')

    dpts, dtris = read_stl(SRC / 'prototype1B_duct.stl')
    duct = surface_stats(dpts, dtris)
    if not (duct['closed'] and duct['consistent'] and duct['parts'] == 1):
        raise SystemExit(f'duct STL is not one closed, consistently wound shell: {duct}')
    if duct['volume'] < 0:
        dtris = dtris[:, ::-1]
    zs, rd = duct_profile(dpts)
    if abs(2 * rd.min() - THROAT_ID) > 0.5:
        raise SystemExit(f'duct throat {2 * rd.min():.2f} mm does not match {CASE} ({THROAT_ID} mm)')
    clearance, where, outside = swept_clearance(cad['pts'], cad['tris'], zs, rd)
    if clearance < CLEARANCE_MIN:
        raise SystemExit(f'duct clearance {clearance:.2f} mm < {CLEARANCE_MIN} mm')

    quality = triangle_quality(cad['pts'], cad['tris'], S)
    write_stl(OUT / 'rotor_1B14.stl', cad['pts'] @ TO_OF.T, cad['tris'], f'rotor {CASE} m +x')
    write_stl(OUT / 'duct_1B14.stl', dpts @ TO_OF.T, dtris, f'duct {CASE} m +x')
    write_sections(S)
    write_report(S, chk, cad, rotor, envelope, duct, zs, rd, clearance, where, outside, quality)
    print(f'  rotor: 1 solid, {rotor["triangles"]} triangles, envelope {envelope:.2f} mm, '
          f'volume {rotor["volume"]:.0f} mm3; duct clearance {clearance:.2f} mm')
    for name, count, qmin, n3, n05 in quality:
        print(f'  triangles {name:<14} {count:6d}  min q {qmin:.2e}  q<1e-3 {n3:4d}  q<0.05 {n05:5d}')
    print(f'  wrote {OUT.relative_to(ROOT)}/: rotor_1B14.stl, rotor_1B14.step, duct_1B14.stl, '
          'rotor_1B14_sections.csv, GEOMETRY_REPORT.md')


def write_sections(S):
    with open(OUT / 'rotor_1B14_sections.csv', 'w', newline='') as f:
        w = csv.writer(f)
        f.write('# Prototype 1B-14 loop sections (design B) - SYNTHETIC, GENERATED BY scripts/make_geometry.py\n'
                '# Design frame: mm, axis +z, omega +z, jet +z. Generator line at 50% chord.\n'
                '# s = path length from the leading root; beta = face pitch angle.\n')
        w.writerow(['k', 's_mm', 'r_mm', 'theta_deg', 'z_mm', 'beta_deg', 'chord_mm',
                    'thickness_mm', 't_c'])
        for k in range(len(S['s'])):
            w.writerow([k] + [f'{v:.4f}' for v in (
                S['s'][k], S['r'][k], np.degrees(S['theta'][k]), S['z'][k],
                np.degrees(S['beta'][k]), S['chord'][k], S['thickness'][k], S['t_c'][k])])


def write_report(S, chk, cad, rotor, envelope, duct, zs, rd, clearance, where, outside, quality):
    d = derived()
    beta_ref = math.degrees(pitch_angle(R_REF))
    to_chord = abs((180 - beta_ref) - LOOP_ANGLE) % 180
    to_chord = min(to_chord, 180 - to_chord)
    zlo, zhi = np.min(cad['pts'][:, 2]), np.max(cad['pts'][:, 2])
    duct_min_in_zone = np.interp(np.linspace(zlo - 2, zhi + 2, 200), zs, rd).min()
    sources = [SRC / n for n in ('prototype1B_design.json', 'CFD_DOE_27.csv',
                                 'prototype1B_duct.stl', 'prototype1B_rotor.stl')]
    lines = [
        f'# Prototype {CASE} rotor geometry (design B: front-opening loops)',
        '',
        'Generated by `scripts/make_geometry.py`. Re-running it rewrites every file in this folder.',
        '',
        '## History',
        '',
        'The recovered `prototype1B_rotor.stl` could not be repaired into a valid blade:',
        '',
        '- the loop legs converge into a folded tip: path bend radius 0.04 mm under a 20 mm chord, '
        'legs closer than one chord beyond r = 40 mm, 1604 self-intersecting triangle pairs;',
        '- the roots twist about 70 deg within 2 mm and the end caps sit 0.11 mm off the hub;',
        '- all four shells were wound inside out and the envelope reached 111 mm;',
        '- adjacent blades overlapped each other at r = 14-25 mm.',
        '',
        'Design A (legs stacked axially) replaced it and ran an L0 baseline, archived in '
        '`results/designA_stacked_loops_L0/`. Design B, below, opens each loop in the front view '
        'like the reference toroidal rotor. Both are SYNTHETIC designs built from the same '
        'design parameters, not the recovered shape.',
        '',
        '## Parameters',
        '',
        '| Parameter | Value | Source |',
        '|---|---:|---|',
        f'| Blades | {BLADES} | design json |',
        f'| Hub diameter x length | {2 * HUB_R:.1f} x {HUB_LEN:.1f} mm | design json |',
        f'| Root radius (generator line) | {R_ROOT} mm | design json |',
        f'| Apex radius (generator line) | {APEX_R:.2f} mm, solved to fit the 100 mm envelope '
        f'(design r_outer {R_OUTER} mm) | this script |',
        f'| Chord root / apex | {CHORD_MIN} / {CHORD_MAX} mm | design json |',
        f'| Section | NACA 00xx, t/c {FOIL_T} outboard, {FOIL_T / ROOT_LOAD:.2f} at root | '
        'design json (foil_t, root_load) |',
        f'| Skew at apex | {SKEW_DEG} deg, back from rotation | design json |',
        f'| Loop axial rise (apex aft of leading root) | {LOOP_RISE} mm | DOE {CASE} |',
        f'| Loading / pitch scale | {LOADING} | DOE {CASE} |',
        f'| Face pitch | {PITCH:.2f} mm (P/D {PITCH / 100:.3f}), constant | '
        f'2 pi r_outer tan({HELICAL_DEG} deg) x loading |',
        f'| Second-leg offset | {LOOP_OPEN} mm at r = {R_REF} mm, {LOOP_ANGLE} deg from +theta toward '
        f'+z ({to_chord:.0f} deg from the chord line): +{np.degrees(d["dth"]):.1f} deg, '
        f'+{d["dz"]:.2f} mm | this script |',
        f'| Front-view loop opening | {np.degrees(d["dth"]):.1f} deg | this script |',
        f'| Apex turn radius / turn starts at | {d["apex_a"]:.2f} mm / r = {d["r_turn"]:.2f} mm | this script |',
        f'| Chord orientation | on the pitch helix along the legs, normal to the path across the apex '
        f'(max chord-tangent cosine {S["along_max"]:.2f}) | this script |',
        f'| Trailing edge thickness | {TE_MM:.2f} mm | repo rule 1 mm at D 250, scaled |',
        f'| Root flare over last {FLARE_TOP - HUB_R:.1f} mm | +{FLARE_T:.0%} thickness, '
        f'+{FLARE_C:.0%} chord | modelled fillet |',
        '| closure_bias | not used | |',
        '',
        '## Printed hub (STEP only, SYNTHETIC - confirm against the shaft)',
        '',
        f'- Ring: outer diameter {2 * HUB_R:.0f} mm, inner diameter {2 * HUB_RING_R:.0f} mm; '
        f'blade roots end inside this wall (blade r_min {chk["r_min"]:.2f} mm).',
        f'- {SPOKES} spokes, {SPOKE_W:.0f} mm wide, to a bushing of outer diameter {2 * BUSHING_R:.0f} mm.',
        f'- Internal spline: {SPLINE_TEETH} teeth, major diameter {SPLINE_MAJOR_D} mm, '
        f'minor diameter {SPLINE_MINOR_D} mm.',
        '- The CFD STL keeps a closed hub: the shaft and insert fill it, and open spoke passages '
        'would need their own mesh study.',
        '',
        '## Checks',
        '',
        '| Check | Result | Limit |',
        '|---|---:|---|',
        f'| Envelope radius (STL) | {envelope:.2f} mm | <= {ENVELOPE_MAX} mm |',
        f'| Folded stations | {chk["folds"]} | 0 |',
        f'| Minimum path bend radius | {chk["bend_min"]:.2f} mm | > half thickness |',
        f'| Root ends inside hub | r <= {chk["root_r_max"]:.2f} mm | <= {HUB_R - 0.5} mm |',
        f'| Blade clear of printed hub pocket | r_min {chk["r_min"]:.2f} mm | >= {HUB_RING_R + 0.5} mm |',
        f'| Root footprint margin to hub ends | {chk["hub_margin"]:.2f} mm | >= 0.5 mm |',
        f'| Leg-to-leg gap | {chk["leg_gap"]:.2f} mm | >= 2 mm |',
        f'| Blade-to-blade gap | {chk["blade_gap"]:.2f} mm | >= 2 mm |',
        f'| Blade clash volume | {cad["clash"]:.2g} mm3 | 0 |',
        f'| Solids after fuse | {cad["solids"]} | 1 |',
        f'| STL closed / consistent / parts | {rotor["closed"]} / {rotor["consistent"]} / '
        f'{rotor["parts"]} | True / True / 1 |',
        '| STL self-intersections | 0 | 0 |',
        f'| Swept clearance to duct | {clearance:.2f} mm at z = {where[2]:.2f} mm, '
        f'r = {np.hypot(*where[:2]):.2f} mm | >= {CLEARANCE_MIN} mm |',
        f'| Rotor surface samples outside duct length | {outside} | reported only |',
        '',
        '## STL triangle quality (OpenFOAM definition)',
        '',
        'The worst triangles are flat slivers on the hub cylinder and end caps. Splitting the hub '
        'along its axis removes them but makes OpenFOAM surfaceCheck report self-intersections at '
        'the split seams, so the hub is left whole. On design A the snapped mesh stayed within '
        '0.018 mm of these hub surfaces (results/designA_stacked_loops_L0/CHECKS.md).',
        '',
        '| Region | Triangles | Min quality | q < 1e-3 | q < 0.05 |',
        '|---|---:|---:|---:|---:|',
    ] + [f'| {n} | {c} | {qmin:.2e} | {n3} | {n05} |' for n, c, qmin, n3, n05 in quality] + [
        '',
        '## Quantities',
        '',
        f'- Chord {S["chord"].min():.2f}-{S["chord"].max():.2f} mm; thickness '
        f'{S["thickness"].min():.2f}-{S["thickness"].max():.2f} mm; t/c '
        f'{S["t_c"].min():.3f}-{S["t_c"].max():.3f} (flare included).',
        f'- Blade volume {cad["blade_volume"]:.0f} mm3; blade wetted area {cad["blade_area"]:.0f} mm2.',
        f'- CFD rotor volume {cad["rotor_volume"]:.0f} mm3 (closed hub); printed rotor volume '
        f'{cad["printed_volume"]:.0f} mm3.',
        f'- Rotor axial extent z = {zlo:.2f}..{zhi:.2f} mm. Duct inner radius over that span '
        f'+/- 2 mm: min {duct_min_in_zone:.2f} mm.',
        f'- Duct: throat {2 * rd.min():.2f} mm; source STL wound '
        f'{"inside out (flipped)" if duct["volume"] < 0 else "outward"}.',
        '',
        '## Frames and files',
        '',
        'Design frame: mm, rotation axis +z, omega +z, jet +z (water enters the bellmouth at -z).',
        '',
        '| File | Frame | Use |',
        '|---|---|---|',
        '| `rotor_1B14.step` | design frame, mm, ring hub with spokes and spline | manufacturing / CAD |',
        '| `rotor_1B14.stl` | metres, axis +x: (x, y, z) = 0.001 (z, y, -x) | CFD, closed hub |',
        '| `duct_1B14.stl` | metres, axis +x | CFD |',
        '| `rotor_1B14_sections.csv` | design frame, mm | section table |',
        '| `preview.png` | | renders, from `scripts/render_geometry.py` |',
        '',
        '## Sources (SHA-256)',
        '',
    ] + [f'- `{p.name}` {sha256(p)}' for p in sources]
    (OUT / 'GEOMETRY_REPORT.md').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
