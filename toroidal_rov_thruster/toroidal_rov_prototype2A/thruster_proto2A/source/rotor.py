"""Loop rotor for P2A: section geometry, numeric gates and the solid (M1 blade, M2 hub for the M200).

Lengths mm, rotation axis +Z. The loop keeps the P2A path, with both roots buried in the hub:
    x = root_x + (apex_x - root_x) sin(pi u),  y = h cos(pi u),
    z = -a/2 cos(pi u) + rise sin(pi u).
Changes from M0 (docs/PARAMETERS.md):
  * constant face pitch P = pitch_to_diameter * D, so every section lies on a true helix.
    M0 turned the section linearly in a path-following frame (P/D 0.55 at the hub,
    7.8 outboard);
  * the chord lies on the helix along the legs and turns normal to the path across the
    apex, weight 1 - (t.e_r)^2, as in the 1B-14 design B generator. The weight only changes
    how the surface is cut into sections, not the helical surface itself;
  * sections keep their true shape: apex_x is solved to fit the envelope instead of
    scaling x and y after lofting;
  * the root flare is part of the loft, and all section splines share one knot vector.
Forward thrust: the rotor turns about -Z (counter-clockwise seen from the inlet at -Z),
and water leaves toward +Z over the motor support. check() verifies the sign.

Run: python source/rotor.py --check-only   (numeric gates, no CAD)
"""
import argparse
import json
import math
import pathlib

import numpy as np
from scipy.spatial import cKDTree

ROOT = pathlib.Path(__file__).resolve().parents[1]
P = json.loads((ROOT / 'source/parameters.json').read_text())
R, HI, M = P['rotor'], P['hub_interface'], P['motor']
EZ = np.array([0.0, 0.0, 1.0])


def pitch():
    return R['pitch_to_diameter'] * R['diameter']


def envelope_target():
    return R['diameter'] / 2 - R['envelope_margin']


def path(u, apex_x):
    """Generator-line points and d/du tangents, (N, 3)."""
    a = np.pi * np.asarray(u, float)
    s, c = np.sin(a), np.cos(a)
    span = apex_x - R['path_root_x']
    pts = np.stack([R['path_root_x'] + span * s, R['half_leg_spacing'] * c,
                    -R['axial_separation'] / 2 * c + R['closure_rise'] * s], -1)
    tan = np.pi * np.stack([span * c, -R['half_leg_spacing'] * s,
                            R['axial_separation'] / 2 * s + R['closure_rise'] * c], -1)
    return pts, tan


def naca_half(x, t_c, chord):
    """NACA 4-digit half thickness (fraction of chord), blunted to the finite trailing edge."""
    y = 5 * t_c * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1036 * x**4)
    return y + R['trailing_edge'] / 2 / chord * x


def profile_x():
    n = R['profile_points_per_side']
    return (1 - np.cos(np.pi * np.linspace(0, 1, n + 1))) / 2


def unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def sections(apex_x):
    """Section rings (stations, points, 3) with their frames and schedules."""
    ud = np.linspace(0, 1, 6001)
    dense, dense_tan = path(ud, apex_x)
    sd = np.r_[0, np.cumsum(np.linalg.norm(np.diff(dense, axis=0), axis=1))]
    curvature = np.linalg.norm(np.gradient(unit(dense_tan), sd, axis=0), axis=1)

    s = np.linspace(0, sd[-1], R['stations'])
    u = np.interp(s, sd, ud)
    ctr, tan = path(u, apex_x)
    t = unit(tan)
    r = np.hypot(ctr[:, 0], ctr[:, 1])
    th = np.arctan2(ctr[:, 1], ctr[:, 0])
    zero = np.zeros_like(r)
    er = np.stack([np.cos(th), np.sin(th), zero], -1)
    et = np.stack([-np.sin(th), np.cos(th), zero], -1)

    beta = np.arctan(pitch() / (2 * np.pi * r))
    lete = np.cos(beta)[:, None] * et + np.sin(beta)[:, None] * EZ   # leading edge -> trailing edge
    along = np.einsum('ij,ij->i', lete, t)
    weight = 1 - np.einsum('ij,ij->i', t, er) ** 2                   # 0 on radial legs, 1 across the apex
    c = unit(lete - (weight * along)[:, None] * t)
    n = unit(np.cross(t, c))

    root = np.exp(-(np.minimum(u, 1 - u) / R['root_blend_u']) ** 2)
    closure = np.exp(-((u - 0.5) / R['closure_blend_u']) ** 2)

    def blend(key):
        leg = R['leg_' + key]
        return leg + (R['root_' + key] - leg) * root + (R['closure_' + key] - leg) * closure

    flare = np.clip((R['hub_radius'] + R['flare_length'] - r) / R['flare_length'], 0, 1) ** 2
    chord = blend('chord') * (1 + R['flare_chord'] * flare)
    t_c = np.maximum(blend('t_c') * (1 + R['flare_thickness'] * flare), R['min_thickness'] / chord)

    # Wrap sections onto their cylinder outside the hub; keep the buried ends flat so
    # the loft's end caps are planar.
    r_end = r.min()
    wrap = np.clip((r - r_end) / (R['hub_radius'] - r_end), 0, 1)
    wrap = wrap * wrap * (3 - 2 * wrap)

    x = profile_x()
    rings, thickness = [], []
    for k in range(len(s)):
        yt = naca_half(x, t_c[k], chord[k])
        px = np.r_[x[::-1], x[1:]]                  # upper TE -> LE, lower LE -> TE
        py = np.r_[yt[::-1], -yt[1:]]
        d = ((px - 0.5) * chord[k])[:, None] * c[k] + (py * chord[k])[:, None] * n[k]
        rr = r[k] + d @ er[k]
        tt = th[k] + (d @ et[k]) / r[k]
        wrapped = np.stack([rr * np.cos(tt), rr * np.sin(tt), ctr[k, 2] + d[:, 2]], -1)
        rings.append(wrap[k] * wrapped + (1 - wrap[k]) * (ctr[k] + d))
        thickness.append(2 * yt.max() * chord[k])
    te = 2 * naca_half(1.0, t_c, chord) * chord
    return dict(apex_x=apex_x, s=s, u=u, ctr=ctr, r=r, theta=th, er=er, et=et, t=t, c=c, n=n,
                beta=beta, chord=chord, t_c=t_c, thickness=np.array(thickness),
                trailing_edge=te, bend_min=1 / curvature.max(), pts=np.array(rings))


def envelope(S):
    return np.hypot(S['pts'][..., 0], S['pts'][..., 1]).max()


def solve_apex():
    """apex_x that puts the section surface at the envelope target."""
    lo, hi = R['apex_x_search']
    if envelope(sections(lo)) > envelope_target() or envelope(sections(hi)) < envelope_target():
        raise SystemExit(f'apex_x_search {R["apex_x_search"]} does not bracket the envelope target')
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if envelope(sections(mid)) <= envelope_target() else (lo, mid)
    return lo


def rotz(p, angle):
    ca, sa = math.cos(angle), math.sin(angle)
    return p @ np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1]]).T


def thrust_sign(S):
    """Sign of the axial flat-plate force on a mid-leg section with the rotor turning about -Z."""
    signs = []
    for k in (len(S['s']) // 4, 3 * len(S['s']) // 4):
        v = np.cos(S['beta'][k]) * S['et'][k] + np.sin(S['beta'][k]) * EZ
        m = np.cross(S['er'][k], v)                       # chord-line normal within the cylinder
        w = unit(-np.cross(-EZ, S['ctr'][k]))             # water relative to the moving blade
        signs.append(int(np.sign((w @ m) * (m @ EZ))))
    return signs


def check(S):
    """Numeric gates on the section rings before any CAD work."""
    pts = S['pts']
    rad = np.hypot(pts[..., 0], pts[..., 1])
    res = dict(apex_x_mm=S['apex_x'], envelope_mm=rad.max(), bend_radius_min_mm=S['bend_min'],
               z_range_mm=[pts[..., 2].min(), pts[..., 2].max()])

    # Fold test: every profile point must advance along the path between stations.
    step = np.einsum('kmj,kj->km', pts[1:] - pts[:-1], (S['t'][1:] + S['t'][:-1]) / 2)
    res['folded_stations'] = int((step <= 0).any(axis=1).sum())
    res['min_station_advance_mm'] = step.min()

    ends = np.r_[pts[0], pts[-1]]
    res['root_end_r_max_mm'] = np.hypot(ends[:, 0], ends[:, 1]).max()
    near_hub = pts[rad < R['hub_radius'] + 0.5]
    res['root_footprint_z_mm'] = [near_hub[:, 2].min(), near_hub[:, 2].max()]

    mid = S['s'][-1] / 2
    lead = pts[S['s'] < mid - R['leg_gap_apex_exclusion']].reshape(-1, 3)
    aft = pts[S['s'] > mid + R['leg_gap_apex_exclusion']].reshape(-1, 3)
    lead, aft = [p[np.hypot(p[:, 0], p[:, 1]) > R['hub_radius']] for p in (lead, aft)]
    res['leg_gap_mm'] = cKDTree(aft).query(lead)[0].min()
    cloud = pts.reshape(-1, 3)
    cloud = cloud[np.hypot(cloud[:, 0], cloud[:, 1]) > R['hub_radius']]
    res['blade_gap_mm'] = cKDTree(rotz(cloud, 2 * math.pi / R['blades'])).query(cloud)[0].min()

    res['min_section_thickness_mm'] = S['thickness'].min()
    res['trailing_edge_min_mm'] = S['trailing_edge'].min()
    res['t_c_range'] = [S['t_c'].min(), S['t_c'].max()]
    res['chord_range_mm'] = [S['chord'].min(), S['chord'].max()]
    res['pitch_mm'] = pitch()
    res['pitch_angle_range_deg'] = [math.degrees(S['beta'].min()), math.degrees(S['beta'].max())]
    res['thrust_sign_rotating_about_minus_z'] = thrust_sign(S)
    res['forward_rotation'] = ('about -Z: counter-clockwise seen from the inlet (-Z); jet toward +Z'
                              if all(v < 0 for v in res['thrust_sign_rotating_about_minus_z'])
                              else 'CHECK: thrust sign not uniform')

    fails = []
    if res['envelope_mm'] > R['diameter'] / 2 - 0.05:
        fails.append(f'envelope {res["envelope_mm"]:.3f} mm')
    if res['folded_stations']:
        fails.append(f'{res["folded_stations"]} folded stations')
    if res['root_end_r_max_mm'] > R['hub_radius'] - 0.5:
        fails.append(f'root ends reach r {res["root_end_r_max_mm"]:.2f} mm')
    zlo = R['hub_front_z'] + R['hub_front_chamfer'] + 0.5
    if res['root_footprint_z_mm'][0] < zlo or res['root_footprint_z_mm'][1] > R['hub_rear_z'] - 0.5:
        fails.append(f'root footprint z {res["root_footprint_z_mm"]} outside the hub')
    if res['leg_gap_mm'] < R['min_leg_gap']:
        fails.append(f'leg gap {res["leg_gap_mm"]:.2f} mm')
    if res['blade_gap_mm'] < R['min_blade_gap']:
        fails.append(f'blade gap {res["blade_gap_mm"]:.2f} mm')
    if res['min_section_thickness_mm'] < R['min_thickness'] - 1e-6:
        fails.append(f'section thickness {res["min_section_thickness_mm"]:.2f} mm')
    if res['trailing_edge_min_mm'] < P['process']['trailing_edge_min'] - 1e-6:
        fails.append(f'trailing edge {res["trailing_edge_min_mm"]:.2f} mm')
    if res['forward_rotation'].startswith('CHECK'):
        fails.append('thrust sign differs between legs')
    res['failures'] = fails
    return res


def section_rows(S):
    header = ['station', 's_mm', 'u', 'x_mm', 'y_mm', 'z_mm', 'r_mm', 'theta_deg', 'pitch_angle_deg',
              'P_over_D', 'chord_mm', 'section_thickness_mm', 't_c']
    rows = [[k, S['s'][k], S['u'][k], *S['ctr'][k], S['r'][k], math.degrees(S['theta'][k]),
             math.degrees(S['beta'][k]), R['pitch_to_diameter'], S['chord'][k], S['thickness'][k],
             S['t_c'][k]] for k in range(len(S['s']))]
    return header, rows


# ------------------------------------------------------------------ CAD
def cyl(r, z0, h):
    import cadquery as cq
    return cq.Solid.makeCylinder(r, h, cq.Vector(0, 0, z0))


def clamp_floor_z():
    """Recess floor: the screw engages target_engagement mm into the can face."""
    return R['hub_rear_z'] + HI['clamp_ring_thickness'] - (HI['screw_length'] - HI['target_engagement'])


def interface_z():
    """Axial stations of the M200 rotor-face interface (the shaft points toward -Z)."""
    face = R['hub_rear_z']
    collar_top = face - M['collar_height']
    tip = collar_top - M['shaft_length']
    flat_start = tip + M['flat_length']
    return dict(face=face, collar_top=collar_top, tip=tip, flat_start=flat_start, floor=clamp_floor_z(),
                counterbore_bottom=collar_top - HI['collar_depth_allowance'],
                d_bore_top=flat_start - HI['flat_lead_in'])


def azimuths(offset_deg, count):
    """Motor feature azimuths, measured from the cable exit."""
    return [M['cable_azimuth_deg'] + offset_deg + 360 * i / count for i in range(count)]


def at_azimuth(shape, deg, radius):
    a = math.radians(deg)
    return shape.translate((radius * math.cos(a), radius * math.sin(a), 0))


def d_bore(z0, z1, allowance, azimuth_deg):
    """Bore for the M200 D-flat shaft between z0 and z1. The flat faces azimuth_deg; the bore's
    flat sits allowance/2 beyond the shaft's, so the printed flat drives the shaft."""
    import cadquery as cq
    bore = cyl((M['shaft_diameter'] + allowance) / 2, z0, z1 - z0)
    if not HI['shaft_d_drive']:
        return bore
    flat = M['flat_across'] - M['shaft_diameter'] / 2 + allowance / 2     # distance of the flat from the axis
    keep = cq.Solid.makeBox(20, 20, z1 - z0 + 2, cq.Vector(flat, -10, z0 - 1))
    return bore.cut(keep.rotate((0, 0, 0), (0, 0, 1), azimuth_deg))


def blade_solid(S):
    return loft(S['pts'], R['leg_t_c'], R['leg_chord'])


def loft(rings, ref_t_c, ref_chord):
    """Closed solid lofted through section rings (stations, points, 3), each ordered upper trailing
    edge -> leading edge -> lower trailing edge. Every section spline uses the parametrisation of
    one reference NACA section, so all splines share a knot vector (small STEP files), and the
    surface has knots along the loft, which keeps tessellation triangles short."""
    import cadquery as cq
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
    from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
    from OCP.GeomAPI import GeomAPI_Interpolate
    from OCP.ShapeFix import ShapeFix_Shape
    from OCP.TColStd import TColStd_HArray1OfReal
    from OCP.TColgp import TColgp_HArray1OfPnt
    from OCP.gp import gp_Pnt

    x = profile_x()
    yt = naca_half(x, ref_t_c, ref_chord)
    ref = np.c_[np.r_[x[::-1], x[1:]], np.r_[yt[::-1], -yt[1:]]]
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(ref, axis=0), axis=1))]
    params = TColStd_HArray1OfReal(1, len(arc))
    for i, v in enumerate(arc / arc[-1]):
        params.SetValue(i + 1, float(v))

    def wire(ring):
        arr = TColgp_HArray1OfPnt(1, len(ring))
        for i, p in enumerate(ring):
            arr.SetValue(i + 1, gp_Pnt(*map(float, p)))
        spline = GeomAPI_Interpolate(arr, params, False, 1e-7)
        spline.Perform()
        edge = BRepBuilderAPI_MakeEdge(spline.Curve()).Edge()
        te = BRepBuilderAPI_MakeEdge(gp_Pnt(*map(float, ring[-1])), gp_Pnt(*map(float, ring[0]))).Edge()
        return BRepBuilderAPI_MakeWire(edge, te).Wire()

    builder = BRepOffsetAPI_ThruSections(True, False, 1e-6)
    builder.CheckCompatibility(False)
    for ring in rings:
        builder.AddWire(wire(ring))
    builder.Build()
    if not builder.IsDone():
        raise SystemExit('loft failed')
    fix = ShapeFix_Shape(builder.Shape())
    fix.Perform()
    solid = cq.Shape.cast(fix.Shape())
    if not solid.isValid() or len(solid.Solids()) != 1:
        raise SystemExit('loft is not one valid solid')
    return solid.Solids()[0]


def hub_solid():
    import cadquery as cq
    r, zf, zr, c, zs = (R[k] for k in ('hub_radius', 'hub_front_z', 'hub_rear_z', 'hub_front_chamfer',
                                       'skirt_start_z'))
    rs = M['can_diameter'] / 2
    prof = cq.Workplane('XZ').moveTo(0, zf).lineTo(r - c, zf).lineTo(r, zf + c).lineTo(r, zs)
    if abs(rs - r) > 1e-6:                    # skirt only when the can is larger than the hub
        k = (zr - 1 - zs) / 2
        prof = prof.bezier([(r, zs + k), (rs, zr - 1 - k), (rs, zr - 1)], includeCurrent=True)
    prof = prof.lineTo(rs, zr).lineTo(0, zr).close()
    return prof.revolve().val()


def rotor_solid(S, cfd=False):
    """Printed rotor: hub, three fused loops and the M200 interface (clamp-ring recess, collar
    counterbore, round and D bores, face screw holes, vent passages aligned with the motor vents).
    cfd=True returns the closed rotating body for the CFD model instead: no interface cuts, and
    the hub extended to cfd.split_z."""
    blade = blade_solid(S)
    rotor = hub_solid()
    for i in range(R['blades']):
        rotor = rotor.fuse(blade.rotate((0, 0, 0), (0, 0, 1), 360 * i / R['blades']))
    zf, zr = R['hub_front_z'], R['hub_rear_z']
    if cfd:
        split = P['cfd']['split_z']
        rotor = rotor.fuse(cyl(M['can_diameter'] / 2, zr - 0.5, split - zr + 0.5)).clean()
    else:
        z = interface_z()
        rotor = rotor.clean()
        rotor = rotor.cut(cyl(HI['clamp_ring_od'] / 2 + HI['recess_radial_clearance'], zf - 1, z['floor'] - zf + 1))
        rotor = rotor.cut(cyl((M['collar_diameter'] + HI['collar_diameter_allowance']) / 2, z['counterbore_bottom'],
                              zr - z['counterbore_bottom'] + 1))
        rotor = rotor.cut(cyl((M['shaft_diameter'] + HI['pilot_bore_allowance']) / 2, z['d_bore_top'] - 0.01,
                              z['counterbore_bottom'] - z['d_bore_top'] + 0.02))
        rotor = rotor.cut(d_bore(z['floor'] - 1, z['d_bore_top'], HI['pilot_bore_allowance'], M['cable_azimuth_deg']))
        for deg in azimuths(0, M['can_face_screw_count']):
            rotor = rotor.cut(at_azimuth(cyl(HI['screw_clearance_hole'] / 2, z['floor'] - 1, zr - z['floor'] + 2),
                                         deg, M['can_face_screw_pcd'] / 2))
        for deg in azimuths(M['vent_offset_deg'], M['vent_count']):
            rotor = rotor.cut(at_azimuth(cyl(HI['vent_passage_diameter'] / 2, z['floor'] - 1, zr - z['floor'] + 2),
                                         deg, M['vent_pcd'] / 2))
        rotor = rotor.clean()
    if not rotor.isValid() or len(rotor.Solids()) != 1:
        raise SystemExit('rotor is not one valid solid')
    return rotor, blade


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check-only', action='store_true', help='numeric gates, no CAD')
    ap.parse_args()
    S = sections(solve_apex())
    chk = check(S)
    for key, val in chk.items():
        if key != 'failures':
            print(f'  {key}: {np.round(val, 3).tolist() if isinstance(val, (list, np.ndarray)) else (round(val, 3) if isinstance(val, float) else val)}')
    if chk['failures']:
        raise SystemExit('section checks failed: ' + '; '.join(chk['failures']))
    print('section checks passed')


if __name__ == '__main__':
    main()
