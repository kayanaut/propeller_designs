"""Export individual mm 3MFs, test mesh topology, render actual-geometry previews and the
blade section chart. Geometric layer sections are NOT slicer toolpaths.
"""
import csv
import json
import zipfile
import xml.etree.ElementTree as ET

import cadquery as cq
import matplotlib
import numpy as np
import vtk
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from vtk.util.numpy_support import vtk_to_numpy

import rotor as RT

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

vtk.vtkLogger.SetStderrVerbosity(vtk.vtkLogger.VERBOSITY_WARNING)
ROOT, P = RT.ROOT, RT.P
E = ROOT / 'exports'
PRINT = ['rotor', 'duct_full', 'motor_support', 'hub_fit_coupon']
ASSEMBLY = ['duct_full', 'motor_support', 'rotor', 'REFERENCE_M200_rotating', 'REFERENCE_M200_stationary',
            'REFERENCE_clamp_ring', 'REFERENCE_hub_screws']
COLORS = {'rotor': (.22, .43, .55), 'duct_full': (.76, .79, .80), 'motor_support': (.55, .62, .65),
          'hub_fit_coupon': (.70, .70, .72), 'REFERENCE_M200_rotating': (.30, .31, .30),
          'REFERENCE_M200_stationary': (.22, .23, .23), 'REFERENCE_clamp_ring': (.78, .74, .55),
          'REFERENCE_hub_screws': (.50, .50, .50)}
INK, INK2, GRID, SURFACE = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
CURRENT = P['revision'].split('-')[-1]
SERIES = {CURRENT: '#2a78d6', 'M0': '#eb6834'}   # categorical slots 1 and 2, validated light-mode pair
MOTOR = 'Blue Robotics M200'
FORWARD = 'forward: counter-clockwise seen from the inlet'


def read(name):
    r = vtk.vtkSTLReader()
    r.SetFileName(str(E / (name + '.stl')))
    r.MergingOn()
    r.Update()
    return r.GetOutput()


def arrays(poly):
    return vtk_to_numpy(poly.GetPoints().GetData()), vtk_to_numpy(poly.GetPolys().GetData()).reshape(-1, 4)[:, 1:]


def meshcheck(poly):
    v, f = arrays(poly)
    pairs = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    _, inv, cnt = np.unique(np.sort(pairs, axis=1), axis=0, return_inverse=True, return_counts=True)
    bal = np.bincount(inv.ravel(), weights=np.where(pairs[:, 0] < pairs[:, 1], 1, -1))
    graph = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(v), len(v))).tocsr()
    nc, _ = connected_components(graph, directed=False)
    areas = np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1) / 2
    vol = np.einsum('ij,ij->i', v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]])).sum() / 6
    return {'triangles': int(len(f)), 'vertices': int(len(v)), 'connected_components': int(nc),
            'boundary_edges': int(sum(cnt == 1)), 'nonmanifold_edges': int(sum(cnt > 2)),
            'inconsistent_edge_directions': int(sum(bal != 0)), 'degenerate_triangles': int(sum(areas < 1e-10)),
            'signed_volume_mm3': float(vol), 'watertight': bool(np.all(cnt == 2) and np.all(bal == 0) and nc == 1),
            'bbox_mm': (v.max(0) - v.min(0)).tolist()}


def stl_self_intersections(name):
    """Self-intersecting triangle pairs, counted on the STL with exactly merged vertices (VTK's merge
    reports extra pairs)."""
    import open3d as o3d
    from export_cfd import read_stl
    p, t = read_stl(E / (name + '.stl'))
    mesh = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(p), o3d.utility.Vector3iVector(t))
    return int(len(np.asarray(mesh.get_self_intersecting_triangles())))


def mf(poly, name):
    v, f = arrays(poly)
    v = v - v.min(0)   # individual build-plate placement, not assembly coordinates
    ns = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    ET.register_namespace('', ns)
    tag = lambda s: '{' + ns + '}' + s
    model = ET.Element(tag('model'), {'unit': 'millimeter', 'xml:lang': 'en-US'})
    ET.SubElement(model, tag('metadata'), {'name': 'Title'}).text = f"{name} {P['revision']} — FIT TEST ONLY"
    res = ET.SubElement(model, tag('resources'))
    mesh = ET.SubElement(ET.SubElement(res, tag('object'), {'id': '1', 'type': 'model'}), tag('mesh'))
    verts, tris = ET.SubElement(mesh, tag('vertices')), ET.SubElement(mesh, tag('triangles'))
    for p in v:
        ET.SubElement(verts, tag('vertex'), dict(zip(['x', 'y', 'z'], [f'{x:.7g}' for x in p])))
    for face in f:
        ET.SubElement(tris, tag('triangle'), dict(zip(['v1', 'v2', 'v3'], map(str, face))))
    ET.SubElement(ET.SubElement(model, tag('build')), tag('item'), {'objectid': '1'})
    with zipfile.ZipFile(E / (name + '.3mf'), 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr('3D/3dmodel.model', ET.tostring(model, encoding='utf-8', xml_declaration=True))
    with zipfile.ZipFile(E / (name + '.3mf')) as z:
        assert z.testzip() is None
        rt = ET.fromstring(z.read('3D/3dmodel.model'))
        assert rt.attrib['unit'] == 'millimeter' and len(rt.findall('.//' + tag('triangle'))) == len(f)


def render(name, parts, position, title, section=False, zoom=1.45):
    fig = plt.figure(figsize=(12, 9), facecolor='#f7f9fa')
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#f7f9fa')
    allv, alltri, allcolors = [], [], []
    light = np.array([.3, -.5, -.8]) / np.linalg.norm([.3, -.5, -.8])
    for part, offset in parts:
        if section:
            sh = cq.Shape.importBrep(str(E / (part + '.brep')))
            sh = sh.cut(cq.Workplane('XY', origin=(0, 100, 0)).box(500, 200, 600).val())
            if not sh.Solids():
                continue
            vv, ff = sh.tessellate(.12, .18)
            v, f = np.array([p.toTuple() for p in vv]), np.array(ff)
        else:
            v, f = arrays(read(part))
        v = v + np.array(offset)
        tri = v[f]
        normal = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-12)
        shade = .58 + .42 * np.abs(normal @ light)
        allv.append(v)
        alltri.append(tri)
        allcolors.append(np.clip(np.array(COLORS.get(part, (.65, .65, .66)))[None, :] * shade[:, None], 0, 1))
    ax.add_collection3d(Poly3DCollection(np.concatenate(alltri), facecolors=np.concatenate(allcolors),
                                         edgecolors='none', linewidths=0, rasterized=True))
    v = np.concatenate(allv)
    mid, span = (v.min(0) + v.max(0)) / 2, (v.max(0) - v.min(0)).max() / 2 * 1.02
    for setter, c in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), mid):
        setter(c - span, c + span)
    ax.set_box_aspect((1, 1, 1), zoom=zoom)
    pos = np.array(position, float)
    ax.view_init(elev=np.degrees(np.arctan2(pos[2], np.linalg.norm(pos[:2]))), azim=np.degrees(np.arctan2(pos[1], pos[0])))
    ax.set_proj_type('ortho')
    ax.axis('off')
    fig.suptitle(title, fontsize=19, color='#243640', y=.965)
    fig.text(.5, .025, f"Actual CAD · {P['revision']} provisional fit-test geometry", ha='center', fontsize=11, color='#52646e')
    fig.subplots_adjust(left=0, right=1, bottom=.04, top=.94)
    fig.savefig(ROOT / 'previews' / name, dpi=150)
    plt.close(fig)


def layers():
    poly = read('rotor')
    b = poly.GetBounds()
    zs = np.arange(b[4] + .1, b[5], .2)
    show = set(np.linspace(0, len(zs) - 1, 12, dtype=int))
    results, examples = [], []
    for i, z in enumerate(zs):
        plane = vtk.vtkPlane()
        plane.SetOrigin(0, 0, float(z))
        plane.SetNormal(0, 0, 1)
        cut = vtk.vtkCutter()
        cut.SetInputData(poly)
        cut.SetCutFunction(plane)
        cut.Update()
        lines = cut.GetOutput()
        results.append({'z_mm': float(z), 'segments': lines.GetNumberOfCells()})
        if i in show:
            copy = vtk.vtkPolyData()
            copy.DeepCopy(lines)
            examples.append((z, copy))
    fig, axes = plt.subplots(3, 4, figsize=(13, 10))
    for a, (z, pd) in zip(axes.flat, examples):
        for j in range(pd.GetNumberOfCells()):
            c = pd.GetCell(j)
            pts = np.array([pd.GetPoint(c.GetPointId(k)) for k in range(c.GetNumberOfPoints())])
            a.plot(pts[:, 0], pts[:, 1], color='#28607b', lw=.7)
        a.set_aspect('equal')
        a.set_xlim(-54, 54)
        a.set_ylim(-54, 54)
        a.set_title(f'z = {z:.1f} mm')
        a.axis('off')
    fig.suptitle('Rotor geometric cross-sections at selected 0.20 mm planes\n'
                 'Not a resin slicer preview; supports, islands and thin features still need slicer review', fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, .94])
    fig.savefig(ROOT / 'previews/rotor_layer_sections.png', dpi=140)
    plt.close(fig)
    (ROOT / 'reports/geometric_layers.json').write_text(json.dumps({'plane_spacing_mm': .2, 'is_machine_slicing': False,
                                                                     'layers': results}, indent=2))


def m0_distribution():
    """M0 leading-leg sections from M0's own generator formulas and recorded radial scale."""
    found = [d / 'toroidal_ROV_P2A_M0_fit_test.zip' for d in (ROOT.parent, ROOT.parent.parent)]
    found = [a for a in found if a.exists()]
    if not found:
        return None
    with zipfile.ZipFile(found[0]) as z:
        R0 = json.loads(z.read('thruster_proto2A/source/parameters.json'))['rotor']
        sc = json.loads(z.read('thruster_proto2A/reports/build_report.json'))['blade_radial_scale']
    S, ez = np.array([sc, sc, 1.0]), np.array([0.0, 0.0, 1.0])
    out = {k: [] for k in ('r_mm', 'P_over_D', 'pitch_angle_deg', 'chord_mm', 't_c')}
    for u in np.linspace(0, 0.5, 201):
        a = np.pi * u
        span = R0['path_apex_x'] - R0['path_root_x']
        ctr = np.array([R0['path_root_x'] + span * np.sin(a), R0['half_leg_spacing'] * np.cos(a),
                        -R0['axial_separation'] / 2 * np.cos(a) + R0['closure_rise'] * np.sin(a)])
        tan = np.array([span * np.cos(a), -R0['half_leg_spacing'] * np.sin(a),
                        R0['axial_separation'] / 2 * np.sin(a) + R0['closure_rise'] * np.cos(a)])
        root, clo = np.exp(-(min(u, 1 - u) / .20) ** 2), np.exp(-((u - .5) / .14) ** 2)
        blend = lambda key: R0['leg_' + key] + (R0['root_' + key] - R0['leg_' + key]) * root + (R0['closure_' + key] - R0['leg_' + key]) * clo
        beta = np.deg2rad(R0['root_pitch_deg'] + (180 - 2 * R0['root_pitch_deg']) * u)
        t = tan / np.linalg.norm(tan)
        b = np.cross(ez, t)
        b /= np.linalg.norm(b)
        k = np.cross(t, b)
        c = np.cos(beta) * b + np.sin(beta) * k / np.linalg.norm(k)
        n = np.cross(t, c)
        p, t, c, n = ctr * S, tan * S, c * S, n * S
        r = np.hypot(p[0], p[1])
        er, et = np.array([p[0], p[1], 0]) / r, np.array([-p[1], p[0], 0]) / r
        if r <= R0['hub_radius'] or abs(t @ er) < 0.2 * np.linalg.norm(t):
            continue
        v = c - (c @ er) / (t @ er) * t
        phi = abs(np.degrees(np.arctan2(v @ ez, v @ et)))
        phi = min(phi, 180 - phi)
        chord, thick = blend('chord') * np.linalg.norm(c), blend('thickness') * np.linalg.norm(n)
        for key, val in zip(out, (r, 2 * np.pi * r * np.tan(np.radians(phi)) / R0['diameter'], phi, chord, thick / chord)):
            out[key].append(val)
    return {k: np.array(v) for k, v in out.items()}


def blade_distribution():
    with (ROOT / 'reports/blade_sections.csv').open() as f:
        rows = list(csv.DictReader(f))
    cur = {k: np.array([float(r[k]) for r in rows]) for k in ('u', 'r_mm', 'P_over_D', 'pitch_angle_deg', 'chord_mm', 't_c')}
    keep = (cur['u'] <= 0.5) & (cur['r_mm'] > P['rotor']['hub_radius'])
    series = [(CURRENT, {k: v[keep] for k, v in cur.items()})]
    m0 = m0_distribution()
    if m0 is not None:
        series.append(('M0', m0))
    panels = [('P_over_D', 'Pitch / diameter (log scale)'), ('pitch_angle_deg', 'Pitch angle (deg)'),
              ('chord_mm', 'Chord (mm)'), ('t_c', 'Thickness / chord')]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.6), facecolor=SURFACE)
    for ax, (key, title) in zip(axes.flat, panels):
        ax.set_facecolor(SURFACE)
        for name, d in series:
            ax.plot(d['r_mm'], d[key], color=SERIES.get(name, '#2a78d6'), lw=2, solid_capstyle='round', solid_joinstyle='round')
            ax.annotate(name, (d['r_mm'][-1], d[key][-1]), xytext=(7, 0), textcoords='offset points',
                        color=INK2, fontsize=10, va='center')
        if key == 'P_over_D':
            ax.set_yscale('log')
            ax.set_yticks([0.5, 1, 2, 5, 10], ['0.5', '1', '2', '5', '10'])
            ax.set_ylim(0.3, 12)
            ax.axhline(0.584, color=INK2, lw=1)
            ax.text(21, 0.555, '1B-14 design A (CFD, 27 N): 0.58', color=INK2, fontsize=9, va='top')
        ax.set_title(title, loc='left', color=INK, fontsize=12)
        ax.grid(True, color=GRID, lw=0.8, ls='-')
        ax.set_axisbelow(True)
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
        for side in ('left', 'bottom'):
            ax.spines[side].set_color(GRID)
        ax.tick_params(colors=INK2, labelsize=9)
        ax.set_xlim(right=max(d['r_mm'].max() for _, d in series) + 4)
    for ax in axes[1]:
        ax.set_xlabel('Radius (mm)', color=INK2)
    handles = [Line2D([], [], color=SERIES.get(n, '#2a78d6'), lw=2) for n, _ in series]
    fig.legend(handles, [f'P2A-{n}' for n, _ in series], loc='upper right', frameon=False, labelcolor=INK, ncol=2,
               bbox_to_anchor=(0.98, 0.985))
    fig.suptitle('Blade sections along the leading leg', x=0.06, ha='left', y=0.975, color=INK, fontsize=15)
    note = (f'M0 from its own generator formulas with its recorded ×1.080 radial scale; {CURRENT} from '
            'reports/blade_sections.csv.' if m0 is not None else f'{CURRENT} from reports/blade_sections.csv.')
    fig.text(0.06, 0.015, note + ' Geometry only, not a performance result.', color=INK2, fontsize=9)
    fig.tight_layout(rect=[0.02, 0.03, 1, 0.95])
    fig.savefig(ROOT / 'previews/blade_distribution.png', dpi=150, facecolor=SURFACE)
    plt.close(fig)


def main():
    report = {}
    for name in PRINT:
        poly = read(name)
        report[name] = meshcheck(poly)
        report[name]['self_intersecting_triangle_pairs'] = stl_self_intersections(name)
        mf(poly, name)
        print(name, report[name], flush=True)
    (ROOT / 'reports/mesh_report.json').write_text(json.dumps(report, indent=2))
    blade_distribution()
    parts = [(x, (0, 0, 0)) for x in ASSEMBLY]
    render('assembly.png', parts, (160, -240, -290), f'Assembly with the {MOTOR}')
    render('axial.png', parts, (0, 0, -300), f'Axial view from the inlet ({FORWARD})')
    render('rotor.png', [('rotor', (0, 0, 0))], (130, -170, -270), f'One-piece loop rotor, P/D {P["rotor"]["pitch_to_diameter"]} ({FORWARD})')
    render('exploded.png', [('duct_full', (0, 0, -95)), ('REFERENCE_hub_screws', (0, 0, -75)), ('REFERENCE_clamp_ring', (0, 0, -60)),
                            ('rotor', (0, 0, -30)), ('REFERENCE_M200_rotating', (0, 0, 15)), ('REFERENCE_M200_stationary', (0, 0, 30)),
                            ('motor_support', (0, 0, 75))], (270, -450, -300), f'Exploded parts with the {MOTOR}', zoom=1.2)
    render('section.png', parts, (160, 300, 40), f'Half-section with the {MOTOR} (jet toward +Z)', section=True)
    layers()


if __name__ == '__main__':
    main()
