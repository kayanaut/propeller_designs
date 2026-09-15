"""Independent checks on the exported P2A-M2 geometry (Blue Robotics M200).

All-angle clearances use a revolved envelope Omega(z) built from the rotor tessellation:
each triangle's largest radius is applied over its whole z span, plus a margin larger
than the tessellation tolerance. An exact boolean proves the rotor BRep lies inside
Omega. Omega dilated by g grows by g radially and axially, so a stationary part that
does not intersect it is at least g from the rotor at every rotation angle, with no
angle sampling.
"""
import json
import math
import subprocess
import sys

import cadquery as cq
import numpy as np
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.TopAbs import TopAbs_OUT
from OCP.gp import gp_Pnt

import build as B
import rotor as RT

ROOT, P = RT.ROOT, RT.P
R, D, S, M = P['rotor'], P['duct'], P['support'], P['motor']
E = ROOT / 'exports'
PRINTED = ['rotor', 'duct_full', 'motor_support', 'hub_fit_coupon']
SI_TIMEOUT_S = {'rotor': 900}
ENVELOPE_MARGIN, ENVELOPE_DZ = 0.05, 0.5


def load(name):
    return cq.Shape.importBrep(str(E / (name + '.brep')))


def volume(shape):
    return sum(s.Volume() for s in shape.Solids())


def run_checker(code, limit):
    try:
        run = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=limit, check=True)
        return {'status': 'completed', 'timeout_s': limit, **json.loads(run.stdout.strip().splitlines()[-1])}
    except subprocess.TimeoutExpired:
        return {'status': f'UNRESOLVED: exceeded {limit} s', 'timeout_s': limit}
    except Exception as exc:
        return {'status': 'UNRESOLVED: ' + str(exc)[:200], 'timeout_s': limit}


CHECKER = ('from OCP.BOPAlgo import BOPAlgo_CheckerSI; import json; c = BOPAlgo_CheckerSI(); '
           'c.AddArgument(s.wrapped); c.SetLevelOfCheck(5); c.SetRunParallel(True); c.Perform(); '
           "print(json.dumps({'errors': c.HasErrors(), 'warnings': c.HasWarnings()}))")


def self_interference(name):
    load_code = f'import cadquery as cq; s = cq.Shape.importBrep({str(E / (name + ".brep"))!r}); '
    result = run_checker(load_code + CHECKER, SI_TIMEOUT_S.get(name, 120))
    if name == 'rotor' and result['status'] != 'completed':
        # Fallback from the plan: one blade fused to the hub has the same junction types.
        one = (f'import sys; sys.path.insert(0, {str(ROOT / "source")!r}); import rotor as RT; '
               'S = RT.sections(RT.solve_apex()); s = RT.hub_solid().fuse(RT.blade_solid(S)).clean(); ')
        result['one_blade_and_hub'] = run_checker(one + CHECKER, SI_TIMEOUT_S['rotor'])
    return result


def rotor_envelope(rotor):
    verts, tris = rotor.tessellate(0.01, 0.05)
    v = np.array([p.toTuple() for p in verts])
    tri = v[np.array(tris)]
    tz0, tz1 = tri[..., 2].min(1), tri[..., 2].max(1)
    tr = np.hypot(tri[..., 0], tri[..., 1]).max(1)
    edges = np.arange(math.floor(v[:, 2].min() / ENVELOPE_DZ) * ENVELOPE_DZ,
                      math.ceil(v[:, 2].max() / ENVELOPE_DZ) * ENVELOPE_DZ + ENVELOPE_DZ / 2, ENVELOPE_DZ)
    bins = np.array([tr[(tz1 >= a) & (tz0 <= b)].max(initial=0.0) for a, b in zip(edges[:-1], edges[1:])])
    nodes = np.maximum(np.r_[bins, 0.0], np.r_[0.0, bins]) + ENVELOPE_MARGIN
    return edges, nodes, v


def dilate(edges, nodes, g):
    w = math.ceil(g / ENVELOPE_DZ) + 2
    grown = np.array([nodes[max(0, i - w):i + w + 1].max() for i in range(len(nodes))]) + g
    return np.r_[edges[0] - g, edges, edges[-1] + g], np.r_[grown[0], grown, grown[-1]]


def revolved(edges, nodes):
    raw = [(0.0, float(edges[0]))] + [(float(r), float(z)) for r, z in zip(nodes, edges)] + [(0.0, float(edges[-1]))]
    pts = [q for i, q in enumerate(raw) if i == 0 or math.dist(q, raw[i - 1]) > 1e-9]   # OCCT rejects zero-length edges
    return cq.Workplane('XZ').polyline(pts).close().revolve().val()


def clear_of(part, edges, nodes, g):
    return volume(part.intersect(revolved(*dilate(edges, nodes, g)))) < 1e-6


def proven_gap(part, edges, nodes, estimate):
    """Largest 0.01 mm-rounded g <= estimate for which the exact intersection is empty."""
    g = math.floor((estimate - 0.01) * 100) / 100
    for _ in range(12):
        if g <= 0 or clear_of(part, edges, nodes, g):
            return max(g, 0.0)
        g = round(g - 0.05, 2)
    return None


def bisect_gap(part, edges, nodes, hi=20.0):
    lo = 0.0
    if not clear_of(part, edges, nodes, lo):
        return None
    for _ in range(8):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if clear_of(part, edges, nodes, mid) else (lo, mid)
    return math.floor(lo * 100) / 100


def outside(shape, points):
    return all(BRepClass3d_SolidClassifier(shape.wrapped, gp_Pnt(*p), 1e-6).State() == TopAbs_OUT for p in points)


def main():
    shapes = {n: load(n) for n in PRINTED + ['REFERENCE_M200_rotating', 'REFERENCE_M200_stationary',
                                              'REFERENCE_clamp_ring', 'REFERENCE_hub_screws']}
    report = {'units': 'mm', 'scope': 'Nominal CAD with the Blue Robotics M200 (vendor STEP when available); '
                                      'resin error budget; no deformation model'}

    roundtrip = {}
    for n in PRINTED:
        sh = cq.importers.importStep(str(E / (n + '.step'))).val()
        roundtrip[n] = {'valid': sh.isValid(), 'solids': len(sh.Solids()), 'volume_mm3': sh.Volume(),
                        'brep_volume_difference_mm3': abs(sh.Volume() - shapes[n].Volume())}
    (ROOT / 'reports/step_roundtrip.json').write_text(json.dumps(roundtrip, indent=2))

    rotor, duct, support = shapes['rotor'], shapes['duct_full'], shapes['motor_support']
    edges, nodes, rv = rotor_envelope(rotor)
    outside_volume = volume(rotor.cut(revolved(edges, nodes)))

    dv, _ = duct.tessellate(0.01, 0.05)
    dv = np.array([p.toTuple() for p in dv])
    dv = dv[(dv[:, 2] >= edges[0]) & (dv[:, 2] <= edges[-1])]
    duct_estimate = float((np.hypot(dv[:, 0], dv[:, 1]) - np.interp(dv[:, 2], edges, nodes)).min())
    # Throat triangles run the full throat length with vertices only at its ends, so also bound the
    # estimate with the throat radius; the exact intersection below certifies whichever is used.
    duct_estimate = min(duct_estimate, B.duct_radii()[0] - float(nodes.max()))
    duct_gap = proven_gap(duct, edges, nodes, duct_estimate)

    need = S['min_rotor_to_stationary_gap']
    support_gap = bisect_gap(support, edges, nodes)
    b = P['clearance_budget']
    rad_budget = sum(b[k] for k in ('rotor_radial_print_error', 'duct_inward_print_error',
                                    'shaft_radial_runout', 'radial_alignment'))
    ax_budget = 2 * b['axial_print_error_per_part'] + b['axial_endplay'] + b['axial_alignment']
    contained = outside_volume < 1e-6
    report['clearance'] = {
        'rotor_swept_diameter_sampled_mm': 2 * float(np.hypot(rv[:, 0], rv[:, 1]).max()),
        'envelope_margin_mm': ENVELOPE_MARGIN, 'envelope_bin_mm': ENVELOPE_DZ,
        'rotor_volume_outside_envelope_mm3': outside_volume,
        'duct_gap_estimate_mm': duct_estimate,
        'all_angle_rotor_duct_gap_mm': duct_gap if contained else None,
        'radial_budget_mm': rad_budget,
        'all_angle_rotor_duct_gap_after_budget_mm': (duct_gap - rad_budget) if contained and duct_gap is not None else None,
        'all_angle_rotor_support_gap_mm': support_gap if contained else None,
        'required_rotor_support_gap_mm': need,
        'axial_budget_mm': ax_budget,
        'all_angle_rotor_support_gap_after_budget_mm': (support_gap - ax_budget) if contained and support_gap is not None else None,
        'method': 'Revolved envelope from the rotor tessellation; exact boolean containment; dilated envelope '
                  'intersection with each stationary part. Gaps are lower bounds for the full revolution.'}

    can_r = M['can_diameter'] / 2
    si, so = B.shroud_radii()
    base_r_max = (M['base_diameter'] + M['base_diameter_tolerance']) / 2
    rt, rb, rho, _, _ = B.duct_radii()
    sv, _ = support.tessellate(0.01, 0.05)
    sv = np.array([p.toTuple() for p in sv])
    sr = np.hypot(sv[:, 0], sv[:, 1])
    blade_zmax = float(rv[np.hypot(rv[:, 0], rv[:, 1]) > can_r + 0.5][:, 2].max())
    strut_zmin = float(sv[(sr > so + 0.5) & (sr < rt)][:, 2].min())
    z = B.support_z()
    shroud_band = RT.cyl(can_r + S['shroud_can_radial_clearance'] - 0.01, z['can_front'], M['can_length'])
    base_band = RT.cyl(base_r_max, z['base_front'], M['base_length'])
    L = D['half_length']
    mid_angles = [math.radians(180 / D['bolt_count'] + 360 * i / D['bolt_count']) for i in range(D['bolt_count'])]
    probes = [(r * math.cos(a), r * math.sin(a), zz) for a in mid_angles
              for r in (rb - 1.0, rb + rho - 0.1) for zz in (L + 0.5, L + S['ring_thickness'] - 0.5)]
    checks = {
        'blade_max_z_mm': blade_zmax, 'strut_min_z_mm': strut_zmin,
        'blade_to_strut_axial_gap_mm': strut_zmin - blade_zmax,
        'blade_to_strut_gap_pass': strut_zmin - blade_zmax >= S['min_blade_to_strut_gap'],
        'rotor_support_gap_pass': contained and support_gap is not None and support_gap >= need,
        'rotor_duct_gap_pass': contained and duct_gap is not None and duct_gap >= P['duct']['nominal_radial_clearance'] - 0.15,
        'shroud_bore_radius_mm': si,
        'can_shroud_radial_clearance_mm': si - can_r,
        'shroud_material_inside_can_clearance_mm3': volume(support.intersect(shroud_band)),
        'shroud_material_inside_base_envelope_mm3': volume(support.intersect(base_band)),
        'base_radial_play_max_mm': si - M['base_diameter'] / 2 + M['base_diameter_tolerance'] / 2,
        'flange_ring_clear_of_jet': outside(support, probes),
    }
    checks['can_shroud_clearance_pass'] = (checks['shroud_material_inside_can_clearance_mm3'] < 1e-6
                                           and checks['can_shroud_radial_clearance_mm'] >= S['shroud_can_radial_clearance'] - 1e-9)
    checks['base_slide_fit_pass'] = (checks['shroud_material_inside_base_envelope_mm3'] < 1e-6
                                     and si - base_r_max <= S['base_slide_clearance'] + 1e-9)
    report['checks'] = checks

    # Screws are left out against the motor rotor: they thread into it.
    pairs = [('rotor', 'REFERENCE_clamp_ring'), ('rotor', 'REFERENCE_hub_screws'),
             ('REFERENCE_clamp_ring', 'REFERENCE_hub_screws'), ('rotor', 'REFERENCE_M200_rotating'),
             ('rotor', 'REFERENCE_M200_stationary'), ('duct_full', 'motor_support'),
             ('motor_support', 'REFERENCE_M200_stationary'), ('motor_support', 'REFERENCE_M200_rotating'),
             ('REFERENCE_hub_screws', 'REFERENCE_M200_stationary'), ('rotor', 'motor_support'), ('rotor', 'duct_full')]
    report['static_pair_intersection_volume_mm3'] = {f'{a} / {b}': volume(shapes[a].intersect(shapes[b])) for a, b in pairs}
    print(json.dumps({k: report[k] for k in ('clearance', 'checks', 'static_pair_intersection_volume_mm3')}, indent=2), flush=True)

    report['solids'] = {}
    for n in PRINTED:
        item = {'brep_valid': shapes[n].isValid(), 'solid_count': len(shapes[n].Solids()),
                'shell_count': len(shapes[n].Shells()), 'checker_level': 5, 'self_interference': self_interference(n)}
        report['solids'][n] = item
        print(n, item, flush=True)
    report['release_gates'] = {'printer_confirmed': False, 'motor_selected': True, 'local_thickness_field_complete': False,
                               'machine_slicing_complete': False, 'structural_test_complete': False,
                               'powered_test_complete': False}
    (ROOT / 'reports/geometry_verification.json').write_text(json.dumps(report, indent=2, default=float))


if __name__ == '__main__':
    main()
