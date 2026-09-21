#!/usr/bin/env python3
"""Render geometry/preview.png from the files written by scripts/make_geometry.py.

Panels: printed rotor (STEP) seen from upstream, printed rotor isometric, CFD rotor
seen from the side, and the rotor's swept outline against the duct and MRF zone.
"""
from pathlib import Path
import sys
import tempfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / 'geometry'
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_geometry import duct_inner_profile, mrf_cylinder, read_stl  # noqa: E402

TEAL = np.array([0.10, 0.62, 0.62])


def step_triangles(path, deflection=0.03):
    """Tessellate a STEP file; returns points (mm) and triangles."""
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.STEPControl import STEPControl_Reader
    from OCP.StlAPI import StlAPI_Writer
    reader = STEPControl_Reader()
    reader.ReadFile(str(path))
    reader.TransferRoots()
    shape = reader.OneShape()
    BRepMesh_IncrementalMesh(shape, deflection, False, 0.3, True)
    with tempfile.TemporaryDirectory() as tmp:
        StlAPI_Writer().Write(shape, f'{tmp}/printed.stl')
        return read_stl(Path(f'{tmp}/printed.stl'))


def draw(ax, pts, tris, view, up, title, colour=TEAL):
    """Orthographic painter's-algorithm render looking along `view`."""
    view = np.asarray(view, float) / np.linalg.norm(view)
    right = np.cross(view, up)
    right /= np.linalg.norm(right)
    upv = np.cross(right, view)
    v = pts[tris]
    normal = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
    normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-30)
    light = -view + 0.6 * upv - 0.4 * right
    light /= np.linalg.norm(light)
    shade = 0.30 + 0.70 * np.abs(normal @ light)
    depth = (v.mean(1) @ view)
    order = np.argsort(depth)[::-1]
    poly = np.stack([v[order] @ right, v[order] @ upv], -1)
    ax.add_collection(PolyCollection(poly, facecolors=np.clip(np.outer(shade[order], colour), 0, 1),
                                     edgecolors='none'))
    ax.set_xlim(poly[..., 0].min() - 2, poly[..., 0].max() + 2)
    ax.set_ylim(poly[..., 1].min() - 2, poly[..., 1].max() + 2)
    ax.set_aspect('equal')
    ax.set_title(title)
    ax.axis('off')


def main():
    printed, ptris = step_triangles(GEO / 'rotor_1B14.step')         # mm, design frame (axis +z)
    rotor, rtris = read_stl(GEO / 'rotor_1B14.stl')                  # m, CFD frame (axis +x)
    duct, _ = read_stl(GEO / 'duct_1B14.stl')

    fig = plt.figure(figsize=(18, 5.2), facecolor='0.86')
    axes = [fig.add_subplot(1, 4, i + 1) for i in range(4)]
    draw(axes[0], printed, ptris, view=(0, 0, 1), up=(0, 1, 0),
         title='Printed rotor seen from upstream (bellmouth side)')
    draw(axes[1], printed, ptris, view=(-0.55, 0.45, 0.70), up=(0, 0, 1), title='Printed rotor, isometric')
    draw(axes[2], rotor * 1e3, rtris, view=(0, 1, 0), up=(0, 0, 1),
         title='CFD rotor from the side (jet toward +x, right)')

    ax = axes[3]
    e = np.vstack([rtris[:, [0, 1]], rtris[:, [1, 2]], rtris[:, [2, 0]]])
    sweep = np.vstack([rotor, (rotor[e[:, 0]] + rotor[e[:, 1]]) / 2]) * 1e3
    ax.scatter(sweep[:, 0], np.hypot(sweep[:, 1], sweep[:, 2]), s=0.2, c='tab:cyan', label='rotor, swept')
    xs, rd = duct_inner_profile(duct)
    ax.plot(xs * 1e3, rd * 1e3, '-o', c='tab:orange', ms=3, label='duct inner wall')
    x1, x2, radius = mrf_cylinder()
    ax.plot([x1 * 1e3, x1 * 1e3, x2 * 1e3, x2 * 1e3], [0, radius * 1e3, radius * 1e3, 0], 'k--', lw=1,
            label='MRF zone')
    ax.axhline(50, c='tab:red', ls=':', lw=1, label='100 mm envelope')
    ax.set_xlabel('x (mm)')
    ax.set_ylabel('radius (mm)')
    ax.set_title('Meridional view: rotor sweep vs duct')
    ax.set_aspect('equal')
    ax.set_ylim(0, 62)
    ax.legend(loc='lower left', fontsize=7)
    ax.set_facecolor('white')

    plt.tight_layout()
    out = GEO / 'preview.png'
    plt.savefig(out, dpi=90, facecolor=fig.get_facecolor())
    print(f'wrote {out.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
