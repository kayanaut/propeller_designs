#!/usr/bin/env python3
"""Render geometry/preview.png: where the rotor, stator, rotating zone and refinement regions sit.

Left: side (meridional) view near the thruster, radius against axial position, so the tip gap,
the rotating-zone margins and the 1 mm split gap to the motor pod are visible.
Right: the whole domain to scale, with the wake refinement region.
"""
from pathlib import Path
import re
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_geometry import ROTOR, STATOR, mrf_cylinder, read_stl  # noqa: E402

INK, INK2, GRID, SURFACE = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
ROTOR_C, STATOR_C = '#2a78d6', '#8a8984'


def cylinders(name):
    text = re.sub(r'//.*', '', (ROOT / 'system' / 'snappyHexMeshDict.template').read_text())
    block = re.search(rf'{name}\s*\{{(.*?)\}}', text, re.S).group(1)
    p1 = float(re.search(r'point1\s*\(\s*([-0-9.eE+]+)', block).group(1))
    p2 = float(re.search(r'point2\s*\(\s*([-0-9.eE+]+)', block).group(1))
    radius = float(re.search(r'radius\s+([-0-9.eE+]+)', block).group(1))
    return p1, p2, radius


def edge_points(pts, tris, per_edge=12, limit=400000):
    """Points along every triangle edge (long straight faces have vertices only at their ends)."""
    v = pts[tris]
    t = np.linspace(0.0, 1.0, per_edge)[None, :, None]
    s = np.vstack([(v[:, a, None, :] + (v[:, b, None, :] - v[:, a, None, :]) * t).reshape(-1, 3)
                   for a, b in ((0, 1), (1, 2), (2, 0))])
    return s[np.random.default_rng(0).choice(len(s), min(limit, len(s)), replace=False)]


def outline(ax, x1, x2, r, style, label):
    ax.add_patch(Rectangle((x1 * 1e3, 0), (x2 - x1) * 1e3, r * 1e3, fill=False, ec=INK2, lw=1.2, ls=style, label=label))


def main():
    rotor = edge_points(*read_stl(ROOT / 'geometry' / ROTOR))
    stator = edge_points(*read_stl(ROOT / 'geometry' / STATOR))
    x1, x2, rz = mrf_cylinder()
    fig, (a, b) = plt.subplots(1, 2, figsize=(14, 5.6), facecolor=SURFACE, gridspec_kw={'width_ratios': [1.5, 1]})
    for ax in (a, b):
        ax.set_facecolor(SURFACE)
        ax.grid(True, color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
        for side in ('left', 'bottom'):
            ax.spines[side].set_color(GRID)
        ax.tick_params(colors=INK2, labelsize=9)
    for pts, colour, label in ((stator, STATOR_C, 'stator (duct, struts, pod)'), (rotor, ROTOR_C, 'rotor (rotating body)')):
        a.scatter(pts[:, 0] * 1e3, np.hypot(pts[:, 1], pts[:, 2]) * 1e3, s=0.4, c=colour, lw=0, label=label, rasterized=True)
    outline(a, x1, x2, rz, '-', 'rotating (MRF) zone')
    p1, p2, rr = cylinders('rotorRegion')
    outline(a, p1, p2, rr, '--', 'rotor refinement region')
    a.set_xlim(-30, 85)
    a.set_ylim(0, 72)
    a.set_aspect('equal')
    a.set_xlabel('x (mm, jet toward +x)', color=INK2)
    a.set_ylabel('radius (mm)', color=INK2)
    a.set_title('Side view near the thruster, swept around the axis', loc='left', color=INK, fontsize=11)
    a.legend(loc='upper right', frameon=False, fontsize=8, markerscale=12, labelcolor=INK)

    b.add_patch(Rectangle((-500, 0), 1500, 500, fill=False, ec=INK, lw=1.2))
    w1, w2, wr = cylinders('wakeRegion')
    outline(b, w1, w2, wr, ':', 'wake refinement region')
    b.scatter(stator[:, 0] * 1e3, np.hypot(stator[:, 1], stator[:, 2]) * 1e3, s=0.4, c=STATOR_C, lw=0, rasterized=True)
    b.scatter(rotor[:, 0] * 1e3, np.hypot(rotor[:, 1], rotor[:, 2]) * 1e3, s=0.4, c=ROTOR_C, lw=0, rasterized=True)
    b.set_xlim(-520, 1020)
    b.set_ylim(0, 520)
    b.set_aspect('equal')
    b.set_xlabel('x (mm)', color=INK2)
    b.set_title('Whole domain to scale (half, radius up)', loc='left', color=INK, fontsize=11)
    b.legend(loc='upper right', frameon=False, fontsize=8, labelcolor=INK)
    fig.suptitle('P2A-M2 CFD geometry', x=0.02, ha='left', color=INK, fontsize=14)
    fig.tight_layout(rect=[0, 0.03, 1, 0.96])
    fig.savefig(ROOT / 'geometry' / 'preview.png', dpi=140, facecolor=SURFACE)
    print('wrote geometry/preview.png')


if __name__ == '__main__':
    main()
