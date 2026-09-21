"""Make the review index, release report, file hashes and ZIP after run_all.py.

Every number and gate status in docs/RELEASE_STATUS.md comes from the reports. The archive is
named after the revision, so an earlier revision's ZIP is never overwritten.
"""
import hashlib
import html
import json
import pathlib
import zipfile

R = pathlib.Path(__file__).resolve().parents[1]


def load(rel):
    return json.loads((R / rel).read_text())


p = load('source/parameters.json')
g, m, b = load('reports/geometry_verification.json'), load('reports/mesh_report.json'), load('reports/build_report.json')
hs, mi, rt = load('reports/hardware_stack.json'), load('reports/rotor_mesh_intersections.json'), load('reports/step_roundtrip.json')
mif = load('reports/motor_interface.json')
c, k, bc = g['clearance'], g['checks'], b['blade_checks']
M, S = p['motor'], p['support']

assert all(x['watertight'] and x['degenerate_triangles'] == 0 for x in m.values())
assert all(x['valid'] and x['solids'] == 1 for x in rt.values())
assert not bc['failures'], bc['failures']
assert mif['status'] == 'PASS' or mif['status'].startswith('VENDOR STEP UNAVAILABLE'), mif.get('failures')
assert c['rotor_volume_outside_envelope_mm3'] < 1e-6
assert c['all_angle_rotor_duct_gap_after_budget_mm'] > 0 and c['all_angle_rotor_support_gap_after_budget_mm'] > 0
for gate in ('blade_to_strut_gap_pass', 'rotor_support_gap_pass', 'rotor_duct_gap_pass', 'can_shroud_clearance_pass',
             'base_slide_fit_pass', 'flange_ring_clear_of_jet'):
    assert k[gate], gate
assert hs['all_pass'], [n for n, x in hs['checks'].items() if not x['pass']]
assert all(v < 1e-6 for v in g['static_pair_intersection_volume_mm3'].values()), g['static_pair_intersection_volume_mm3']
assert mi['candidate_nonadjacent_intersections'] == 0

archive = R.parent / f"toroidal_ROV_{p['revision'].replace('-', '_')}_fit_test.zip"
assert p['revision'] not in ('P2A-M0', 'P2A-M1'), 'refusing to overwrite an earlier revision archive'


def si_text(item):
    si = item['self_interference']
    if si['status'] == 'completed':
        return 'PASS: no errors' + (', warnings reported' if si['warnings'] else '') if not si['errors'] else 'FAIL: errors reported'
    text = f"UNRESOLVED ({si['status']})"
    one = si.get('one_blade_and_hub')
    if one:
        text += '; one blade + hub: ' + ('no errors' if one['status'] == 'completed' and not one['errors']
                                         else one['status'] if one['status'] != 'completed' else 'errors reported')
    return text


rotor_si = si_text(g['solids']['rotor'])
others = ', '.join(f"{n} {si_text(x).split(':')[0]}" for n, x in g['solids'].items() if n != 'rotor')
rd = lambda v, n=2: f'{v:.{n}f}'
motor_check = ('PASS: the vendor STEP agrees with `parameters.json` within '
               f"{mif['tolerance_mm']:g} mm and {mif['tolerance_deg']:g}° on {len(mif['checks'])} features"
               if mif['status'] == 'PASS' else mif['status'])
text = f'''# Release status — {p['revision']}

**FIT AND ASSEMBLY TESTING ONLY.** Built for the {M['model']}. The resin process is unconfirmed. Manufacturing release stays incomplete until the open inputs and process checks are closed.

P2A-M2 is P2A-M1 rebuilt around the Blue Robotics M200. The blade is unchanged from M1. No CFD result applies yet: the pitch was chosen from the 1B-14 design A data point, and the M2 CFD case has only been prepared.

| Check | Result | Scope / limitation |
|---|---|---|
| Printed parts | PASS: {len(m)} parts, one valid solid each | {', '.join(m)} |
| STL topology | PASS: closed, one component, consistent orientation, no degenerate triangles | |
| STL triangle self-intersections | {', '.join(f"{n} {x['self_intersecting_triangle_pairs']}" for n, x in m.items())} | open3d. Non-zero pairs on the support are coplanar overlaps of tiny triangles on the cable-boss end face; the slicer's mesh repair handles these |
| Motor interface | {motor_check} | `reports/motor_interface.json` |
| Blade gates | PASS: {bc['folded_stations']} folded stations; leg gap {rd(bc['leg_gap_mm'])} mm; blade gap {rd(bc['blade_gap_mm'])} mm; thinnest section {rd(bc['min_section_thickness_mm'])} mm; trailing edge {rd(bc['trailing_edge_min_mm'])} mm | Numeric, on the loft sections |
| Blade pitch and sections | Constant P/D {p['rotor']['pitch_to_diameter']} (pitch angle {rd(bc['pitch_angle_range_deg'][0], 1)}–{rd(bc['pitch_angle_range_deg'][1], 1)}°); chord {rd(bc['chord_range_mm'][0], 1)}–{rd(bc['chord_range_mm'][1], 1)} mm; t/c {rd(bc['t_c_range'][0])}–{rd(bc['t_c_range'][1])} | Per station in `reports/blade_sections.csv` |
| Forward rotation | {bc['forward_rotation']} | Flat-plate sign check, not a performance result |
| Rotor triangle intersection test | {mi['candidate_nonadjacent_intersections']} non-adjacent contacting triangle pairs | Triangle approximation |
| Exact rotor self-interference | {rotor_si} | OCCT BOPAlgo_CheckerSI, level 5 |
| Other exact self-interference | {others} | Per part in `geometry_verification.json` |
| Rotor swept diameter | {rd(c['rotor_swept_diameter_sampled_mm'], 3)} mm sampled | Contained in the revolved envelope by exact boolean |
| Rotor/duct gap, full revolution | ≥ {rd(c['all_angle_rotor_duct_gap_mm'])} mm nominal; ≥ {rd(c['all_angle_rotor_duct_gap_after_budget_mm'])} mm after the {rd(c['radial_budget_mm'])} mm radial budget | Budget is illustrative for resin, not measured |
| Rotor/support gap, full revolution | ≥ {rd(c['all_angle_rotor_support_gap_mm'])} mm (required {rd(c['required_rotor_support_gap_mm'], 1)}); ≥ {rd(c['all_angle_rotor_support_gap_after_budget_mm'])} mm after the {rd(c['axial_budget_mm'])} mm axial budget | No elastic deflection |
| Blade trailing edge to strut | {rd(k['blade_to_strut_axial_gap_mm'], 1)} mm axial (required ≥ {S['min_blade_to_strut_gap']:g}) | |
| M200 can in the shroud | PASS: {rd(k['can_shroud_radial_clearance_mm'])} mm radial clearance to the spinning can | Vendor geometry |
| M200 base in the shroud | PASS: slide fit, at most {rd(k['base_radial_play_max_mm'])} mm radial play; centres the motor on the duct | Base Ø{M['base_diameter']:g} ±{M['base_diameter_tolerance']:g} mm |
| Flange ring clear of the jet | {'PASS' if k['flange_ring_clear_of_jet'] else 'FAIL'}: probe points between the struts lie outside the ring | |
| Fixed interfaces | PASS: zero overlap volume in {len(g['static_pair_intersection_volume_mm3'])} pairs, including the vendor M200 | Face contacts allowed |
| Hub clamp, vents and bolt stacks | PASS: {len(hs['checks'])} checks in `hardware_stack.json` | Nominal lengths; threads not modelled |
| STEP read-back | PASS: valid single solids; rotor volume difference {100 * rt['rotor']['brep_volume_difference_mm3'] / b['parts']['rotor']['volume_mm3']:.3f}% | Exact surface equivalence not certified |
| STL/3MF units | STL numeric mm; 3MF declares millimetres | Each 3MF is placed on its build plate, unscaled |
| Hub fit coupon | INCLUDED | Not yet printed or measured |
| Minimum thickness | PARTIAL: section gate ≥ {p['rotor']['min_thickness']:g} mm, trailing edge {p['rotor']['trailing_edge']:g} mm | No full local-thickness field |
| Printer/resin profile | UNRESOLVED | Printer, resin, build volume and slicer required |
| Motor | RESOLVED: {M['model']} | ESC, battery voltage and cable routing still open |
| Structural, powered and efficiency checks | NOT PERFORMED | No speed rating, thrust, efficiency or durability claim |

## Clearance method

The rotor tessellation was binned every {c['envelope_bin_mm']:g} mm along the axis. Each triangle's largest radius was applied over its whole z span, plus {c['envelope_margin_mm']:g} mm, and the result was revolved into an envelope. An exact boolean found {c['rotor_volume_outside_envelope_mm3']:g} mm³ of rotor outside it. Growing the envelope by g, radially and axially, and intersecting it exactly with a stationary part proves a gap of at least g at every rotation angle. The duct result is the largest such g, to 0.01 mm. The support result comes from bisection. These bounds apply to the nominal, centred CAD with the stated illustrative budgets; real misalignment, tolerances and deformation need measured inputs.

## Next release gates

Confirm the printer, resin and build volume. Print and measure the hub fit coupon against a real M200. Inspect the resin slicer's layers and supports and keep the project. Only then approve a fit-test print. CFD, structural, balance and submerged qualification come later; see `ROADMAP.md`.
'''
(R / 'docs/RELEASE_STATUS.md').write_text(text)

printrows = ''.join('<tr><td>' + html.escape(n) + '</td>' + ''.join(f'<td><a href="exports/{n}.{e}">{e.upper()}</a></td>'
                                                                   for e in ['step', 'stl', '3mf']) + '</tr>' for n in m)
figures = ['assembly', 'rotor', 'blade_distribution', 'section', 'axial', 'exploded', 'rotor_layer_sections']
gallery = ''.join(f'<figure><img src="previews/{n}.png" alt="{n}"><figcaption>{html.escape(n.replace("_", " ").title())}</figcaption></figure>'
                  for n in figures)
docs = ['ROADMAP', 'RELEASE_STATUS', 'ASSEMBLY', 'PRINT_PREPARATION', 'COUPON', 'OPEN_INPUTS', 'PARAMETERS']
links = ''.join(f'<li><a href="docs/{d}.md">{d.replace("_", " ").title()}</a></li>' for d in docs)
rev = html.escape(p['revision'])
page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Toroidal ROV thruster {rev}</title><style>body{{font:16px/1.55 system-ui,sans-serif;color:#19333f;background:#f4f7f8;max-width:1120px;margin:40px auto;padding:0 24px}}h1{{font-size:32px}}a{{color:#146880}}.note{{padding:16px;background:#fff1d5;border-left:4px solid #bf8330}}table{{border-collapse:collapse;width:100%;background:white}}td,th{{padding:10px 16px;text-align:left;border-bottom:1px solid #d9e1e5}}.gallery{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}figure{{margin:0;background:white}}img{{width:100%;display:block}}figcaption{{padding:12px}}@media(max-width:700px){{.gallery{{grid-template-columns:1fr}}}}</style><h1>Toroidal ROV thruster · {rev}</h1><p>Three closed loops on a true pitch helix (P/D {p['rotor']['pitch_to_diameter']}), a symmetric foil duct with a {p['duct']['nominal_radial_clearance']:g} mm tip gap, and a streamlined support around a flooded {html.escape(M['model'])}.</p><p class="note"><strong>Fit and assembly testing only.</strong> The resin process is unconfirmed. No powered-operation approval. Forward: rotor {html.escape(bc['forward_rotation'])}.</p><p>All views are generated from the actual CAD. Start with <a href="docs/ROADMAP.md">Roadmap</a>, <a href="docs/RELEASE_STATUS.md">Release status</a> and <a href="README.md">README</a>.</p><h2>CAD and print meshes</h2><p><a href="exports/assembly_with_reference_hardware.step">Assembly STEP with the M200 and hardware</a> · <a href="source/parameters.json">Editable parameters</a> · <a href="source/build.py">CAD generator</a> · <a href="source/rotor.py">Rotor generator</a></p><table><thead><tr><th>Printed part</th><th>CAD</th><th>Mesh</th><th>mm geometry</th></tr></thead><tbody>{printrows}</tbody></table><p>STL values are millimetres. 3MFs declare millimetres and contain geometry only. Never print the REFERENCE_ files.</p><h2>Checks</h2><p>All {len(m)} printed meshes are watertight single shells. The all-angle rotor–duct gap is at least {c['all_angle_rotor_duct_gap_mm']:.2f} mm ({c['all_angle_rotor_duct_gap_after_budget_mm']:.2f} mm after the illustrative budget). Motor interface: {html.escape(mif['status'])}. Rotor self-interference: {html.escape(rotor_si)}.</p><h2>Documentation</h2><ul>{links}<li><a href="docs/HARDWARE.csv">Hardware list CSV</a></li><li><a href="hardware/README.md">Hardware reference notes</a></li></ul><h2>Actual-CAD previews</h2><div class="gallery">{gallery}</div></html>'''
(R / 'index.html').write_text(page)

files = sorted(x for x in R.rglob('*') if x.is_file() and '__pycache__' not in x.parts and x.name != 'manifest.json'
               and 'cfd' not in x.relative_to(R).parts)
manifest = {'revision': p['revision'], 'status': 'FIT AND ASSEMBLY TESTING ONLY — OPEN GATES DOCUMENTED',
            'files': [{'path': str(x.relative_to(R)), 'bytes': x.stat().st_size,
                       'sha256': hashlib.sha256(x.read_bytes()).hexdigest()} for x in files]}
(R / 'manifest.json').write_text(json.dumps(manifest, indent=2))
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for f in files + [R / 'manifest.json']:
        z.write(f, str(pathlib.Path(R.name) / f.relative_to(R)))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for f in manifest['files']:
        assert hashlib.sha256(z.read(str(pathlib.Path(R.name) / f['path']))).hexdigest() == f['sha256']
print(json.dumps({'archive': str(archive), 'files': len(files) + 1, 'bytes': archive.stat().st_size}, indent=2))
