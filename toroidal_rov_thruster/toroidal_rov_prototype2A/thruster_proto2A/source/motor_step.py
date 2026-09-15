"""Blue Robotics M200 vendor STEP: align it to the thruster frame and check it against parameters.json.

Vendor frame (BR-101376): motor axis +X, shaft tip at +X, cable leaving the base along -Z.
The rotor face plane (x = 49.6108 in the download) is measured from the file, not typed in, so
contact faces land exactly on the thruster's parametric faces. Thruster frame: axis +Z with the shaft pointing -Z (toward
the rotor), rotor face at rotor.hub_rear_z, cable exit at motor.cable_azimuth_deg.

The mapping (x, y, z)_vendor -> (-z, -y, -(x - face)) is a proper rotation, followed by a
rotation of cable_azimuth_deg about Z and a shift to hub_rear_z. Every measurement below is
taken on the aligned solids and compared with the motor parameters; a difference over TOL_MM
or TOL_DEG stops the build. Azimuths are measured from the cable exit.

Run: python source/motor_step.py
"""
import json
import math
import sys

import cadquery as cq
import numpy as np
from OCP.gp import gp_Trsf

import rotor as RT

ROOT, P = RT.ROOT, RT.P
R, M = P['rotor'], P['motor']
CABLE_KEEP_RADIUS = 45.0     # the vendor cable is 1 m long; keep the part near the thruster
TOL_MM, TOL_DEG = 0.1, 0.5


def vendor_face_x(solids):
    """x of the rotor face plane in the vendor frame: largest +X plane of the solid reaching the shaft tip."""
    rot = max(solids, key=lambda s: s.BoundingBox().xmax)
    face = max((f for f in rot.Faces() if f.geomType() == 'PLANE' and f.normalAt(f.Center()).x > 0.999),
               key=lambda f: f.Area())
    return face.Center().x


def transform(face_x):
    phi = math.radians(M['cable_azimuth_deg'])
    c, s = math.cos(phi), math.sin(phi)
    base = np.array([[0, 0, -1], [0, -1, 0], [-1, 0, 0]], float)
    rot = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]) @ base
    shift = np.array([0.0, 0.0, R['hub_rear_z']]) - rot @ np.array([face_x, 0.0, 0.0])
    t = gp_Trsf()
    t.SetValues(*rot[0], shift[0], *rot[1], shift[1], *rot[2], shift[2])
    return t


def load_aligned():
    """Aligned vendor motor as {'rotating': Compound, 'stationary': Compound}, or None if unavailable."""
    path = ROOT / M['vendor_step']
    if not path.exists():
        return None
    try:
        solids = cq.Compound.makeCompound(cq.importers.importStep(str(path)).vals()).Solids()
    except Exception:
        return None
    loc = cq.Location(transform(vendor_face_x(solids)))
    moved = [s.moved(loc) for s in solids]
    rotating = min(moved, key=lambda s: s.BoundingBox().zmin)          # can + shaft reach furthest toward -Z
    stationary = []
    for s in moved:
        if s is rotating:
            continue
        b = s.BoundingBox()
        if max(abs(b.xmin), abs(b.xmax), abs(b.ymin), abs(b.ymax)) > 100:    # the 1 m cable
            s = s.intersect(RT.cyl(CABLE_KEEP_RADIUS, b.zmin - 1, b.zlen + 2))
        stationary.append(s)
    return {'rotating': cq.Compound.makeCompound([rotating]), 'stationary': cq.Compound.makeCompound(stationary)}


def azimuth_from_cable(x, y):
    return (math.degrees(math.atan2(y, x)) - M['cable_azimuth_deg']) % 360


def planes(shape, sign):
    """Planar faces whose normal is +Z (sign=1) or -Z (sign=-1)."""
    return [f for f in shape.Faces() if f.geomType() == 'PLANE' and sign * f.normalAt(f.Center()).z > 0.999]


def cylinder_centres(shape, radius, tol=0.02):
    """Centres (x, y, zmin, zmax) of clustered cylindrical faces of one radius with axis along Z."""
    pts = []
    for f in shape.Faces():
        if f.geomType() != 'CYLINDER':
            continue
        cy = f._geomAdaptor().Cylinder()
        if abs(cy.Radius() - radius) > tol or abs(abs(cy.Axis().Direction().Z()) - 1) > 1e-6:
            continue
        b = f.BoundingBox()
        pts.append(((b.xmin + b.xmax) / 2, (b.ymin + b.ymax) / 2, b.zmin, b.zmax))
    clusters = []
    for p in pts:
        for cl in clusters:
            if math.hypot(p[0] - cl[0][0], p[1] - cl[0][1]) < 3.0:
                cl.append(p)
                break
        else:
            clusters.append([p])
    return [(np.mean([q[0] for q in cl]), np.mean([q[1] for q in cl]), min(q[2] for q in cl), max(q[3] for q in cl))
            for cl in clusters]


def coaxial_radii(shape):
    """(radius, zmin, zmax) of cylinders coaxial with Z."""
    rows = []
    for f in shape.Faces():
        if f.geomType() == 'CYLINDER':
            cy = f._geomAdaptor().Cylinder()
            loc = cy.Location()
            if abs(abs(cy.Axis().Direction().Z()) - 1) < 1e-6 and math.hypot(loc.X(), loc.Y()) < 1e-3:
                b = f.BoundingBox()
                rows.append((cy.Radius(), b.zmin, b.zmax))
    return rows


def measure(motor):
    rot, sta = motor['rotating'], motor['stationary']
    m = {}
    rr = coaxial_radii(rot)
    m['can_diameter'] = 2 * max(c[0] for c in rr)
    face = max(planes(rot, -1), key=lambda f: f.Area())
    m['rotor_face_z'] = face.Center().z
    can_rear = max((f for f in planes(rot, 1) if f.Area() > 200), key=lambda f: f.Center().z)
    m['can_length'] = can_rear.Center().z - m['rotor_face_z']
    m['collar_diameter'] = 2 * min((c[0] for c in rr if abs(c[0] - 5.5) < 0.3), key=lambda r: abs(r - 5.5))
    collar_top = min((f for f in planes(rot, -1) if 20 < f.Area() < 100),
                     key=lambda f: abs(f.Center().z - (m['rotor_face_z'] - 6)))
    m['collar_height'] = m['rotor_face_z'] - collar_top.Center().z
    m['shaft_length'] = collar_top.Center().z - rot.BoundingBox().zmin
    m['shaft_diameter'] = 2 * min((c[0] for c in rr if abs(c[0] - 2.5) < 0.3), key=lambda r: abs(r - 2.5))
    flats = [f for f in rot.Faces() if f.geomType() == 'PLANE' and abs(f.normalAt(f.Center()).z) < 1e-6
             and f.BoundingBox().zmax < collar_top.Center().z
             and max(abs(f.BoundingBox().xmin), abs(f.BoundingBox().xmax), abs(f.BoundingBox().ymin), abs(f.BoundingBox().ymax)) < 3]
    flat = max(flats, key=lambda f: f.Area())
    n, c = flat.normalAt(flat.Center()), flat.Center()
    m['flat_across'] = m['shaft_diameter'] / 2 + abs(n.x * c.x + n.y * c.y)
    m['flat_length'] = flat.BoundingBox().zlen
    m['flat_azimuth_from_cable_deg'] = azimuth_from_cable(n.x, n.y)
    holes = [h for h in cylinder_centres(rot, 1.25) if h[3] < m['rotor_face_z'] + 6]
    m['can_face_screw_count'] = len(holes)
    m['can_face_screw_pcd'] = 2 * float(np.mean([math.hypot(h[0], h[1]) for h in holes]))
    m['can_face_screw_azimuths_from_cable_deg'] = sorted(azimuth_from_cable(h[0], h[1]) for h in holes)
    vents = cylinder_centres(rot, M['vent_diameter'] / 2)
    m['vent_count'] = len(vents)
    m['vent_pcd'] = 2 * float(np.mean([math.hypot(v[0], v[1]) for v in vents]))
    m['vent_azimuths_from_cable_deg'] = sorted(azimuth_from_cable(v[0], v[1]) for v in vents)
    m['can_face_plate_thickness'] = float(np.mean([v[3] - v[2] for v in vents]))

    solids = sta.Solids()
    base = [s for s in solids if abs(s.BoundingBox().xlen - M['base_diameter']) < 0.5]
    m['base_diameter'] = max(s.BoundingBox().xlen for s in base)
    base_front = min(s.BoundingBox().zmin for s in base)
    base_rear = max(s.BoundingBox().zmax for s in base)
    m['base_length'] = base_rear - base_front
    m['can_to_base_gap'] = base_front - (m['rotor_face_z'] + m['can_length'])
    inserts = [s.BoundingBox() for s in solids if abs(s.BoundingBox().xlen - 5.0) < 0.05
               and abs(s.BoundingBox().ylen - 5.0) < 0.05 and s.BoundingBox().zmax > base_rear - 0.5]
    m['base_screw_count'] = len(inserts)
    centres = [((b.xmin + b.xmax) / 2, (b.ymin + b.ymax) / 2) for b in inserts]
    m['base_screw_pcd'] = 2 * float(np.mean([math.hypot(*q) for q in centres]))
    m['base_screw_azimuths_from_cable_deg'] = sorted(azimuth_from_cable(*q) for q in centres)
    m['base_thread_depth'] = float(np.mean([b.zlen for b in inserts]))
    # The base also holds a cable-sized hole, so pick the cable among the non-base solids.
    cable = max((s for s in solids if all(s is not b for b in base)
                 and any(abs(f._geomAdaptor().Cylinder().Radius() - M['cable_diameter'] / 2) < 0.05
                         for f in s.Faces() if f.geomType() == 'CYLINDER')), key=lambda s: s.Volume())
    cb, cc = cable.BoundingBox(), cable.Center()
    m['cable_diameter'] = cb.zlen
    m['cable_height_above_base_rear'] = base_rear - (cb.zmin + cb.zmax) / 2
    m['cable_azimuth_from_cable_deg'] = azimuth_from_cable(cc.x, cc.y)
    m['protrudes_behind_base_rear_mm'] = max(0.0, max(s.BoundingBox().zmax for s in solids) - base_rear)
    return m


def compare(m):
    lengths = ['can_diameter', 'can_length', 'collar_diameter', 'collar_height', 'shaft_diameter', 'shaft_length',
               'flat_across', 'flat_length', 'can_face_screw_pcd', 'vent_pcd', 'can_face_plate_thickness',
               'base_diameter', 'base_length', 'can_to_base_gap', 'base_screw_pcd', 'base_thread_depth',
               'cable_diameter', 'cable_height_above_base_rear']
    rows = {k: {'step': round(m[k], 3), 'parameter': M[k], 'difference': round(m[k] - M[k], 3),
                'pass': abs(m[k] - M[k]) <= TOL_MM} for k in lengths}
    rows['rotor_face_z'] = {'step': round(m['rotor_face_z'], 3), 'parameter': R['hub_rear_z'],
                            'pass': abs(m['rotor_face_z'] - R['hub_rear_z']) <= TOL_MM}
    for k in ('can_face_screw_count', 'vent_count', 'base_screw_count'):
        rows[k] = {'step': m[k], 'parameter': M[k], 'pass': m[k] == M[k]}
    angles = {
        'flat_azimuth_from_cable_deg': [0.0],
        'can_face_screw_azimuths_from_cable_deg': [360 * i / M['can_face_screw_count'] for i in range(M['can_face_screw_count'])],
        'vent_azimuths_from_cable_deg': [M['vent_offset_deg'] + 360 * i / M['vent_count'] for i in range(M['vent_count'])],
        'base_screw_azimuths_from_cable_deg': [M['base_screw_offset_deg'] + 360 * i / M['base_screw_count'] for i in range(M['base_screw_count'])],
        'cable_azimuth_from_cable_deg': [0.0],
    }
    for k, want in angles.items():
        got = sorted(m[k]) if isinstance(m[k], list) else [m[k]]
        want = sorted(w % 360 for w in want)
        circ = lambda a, b: abs((a - b + 180) % 360 - 180)
        diffs = [min(circ(g, w) for g in got) for w in want] if len(got) == len(want) else [999.0]
        rows[k] = {'step': [round(g, 2) for g in got], 'parameter': want, 'max_difference_deg': round(max(diffs), 3),
                   'pass': max(diffs) <= TOL_DEG}
    rows['nothing_behind_base_rear'] = {'step': round(m['protrudes_behind_base_rear_mm'], 3),
                                        'pass': m['protrudes_behind_base_rear_mm'] < 1e-6}
    return rows, [k for k, v in rows.items() if not v['pass']]


def main():
    motor = load_aligned()
    report = {'vendor_step': M['vendor_step'], 'tolerance_mm': TOL_MM, 'tolerance_deg': TOL_DEG}
    if motor is None:
        report['status'] = 'VENDOR STEP UNAVAILABLE: parametric M200 model used; interface not cross-checked'
        (ROOT / 'reports/motor_interface.json').write_text(json.dumps(report, indent=2))
        print(report['status'])
        return
    rows, fails = compare(measure(motor))
    report.update(status='PASS' if not fails else 'FAIL', failures=fails, checks=rows)
    (ROOT / 'reports/motor_interface.json').write_text(json.dumps(report, indent=2, default=float))
    print(json.dumps(report, indent=2, default=float))
    if fails:
        sys.exit('M200 STEP and parameters.json disagree: ' + ', '.join(fails))


if __name__ == '__main__':
    main()
