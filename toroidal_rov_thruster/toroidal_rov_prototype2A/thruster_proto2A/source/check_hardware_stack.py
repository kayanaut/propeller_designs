"""Clamp and bolt stacks for P2A-M2 on the Blue Robotics M200: nominal lengths and contacts, threads not modelled.

M0's front nut clamped onto the shaft step instead of the rotor. These checks make the
equivalent mistakes visible: the hub must seat on the M200 rotor face (not on the collar or
the shaft tip), every screw must engage its thread within Blue Robotics' depth limits, and the
hub must keep the motor's vents open.
"""
import json
import math

import cadquery as cq

import build as B
import rotor as RT

ROOT, P = RT.ROOT, RT.P
R, M, HI, S, D, HW = P['rotor'], P['motor'], P['hub_interface'], P['support'], P['duct'], P['hardware']
E = ROOT / 'exports'


def within(value, lo, hi=None):
    return {'value': round(value, 3), 'min': lo, 'max': hi,
            'pass': bool(value >= lo - 1e-9 and (hi is None or value <= hi + 1e-9))}


def polar(deg, radius):
    return radius * math.cos(math.radians(deg)), radius * math.sin(math.radians(deg))


def main():
    z = RT.interface_z()
    floor, t = z['floor'], HI['clamp_ring_thickness']
    zf, zr = R['hub_front_z'], R['hub_rear_z']
    grip = zr - floor + t
    _, _, _, _, rom = B.duct_radii()
    zface = D['half_length'] - D['flange_thickness']
    r0 = rom - 0.5
    fairing_z = D['fairing_start_z'] + (D['bolt_circle_radius'] - r0) / (D['flange_radius'] - r0) * (zface - D['fairing_start_z'])
    duct_grip = D['flange_thickness'] + S['bolt_boss_length']
    duct_tail = D['bolt_length'] - duct_grip - 2 * HW['washer_thickness'] - HW['nut_thickness']
    screw_pts = [polar(a, M['can_face_screw_pcd'] / 2) for a in RT.azimuths(0, M['can_face_screw_count'])]
    vent_pts = [polar(a, M['vent_pcd'] / 2) for a in RT.azimuths(M['vent_offset_deg'], M['vent_count'])]
    vent_wall = min(math.dist(s, v) for s in screw_pts for v in vent_pts) - (HI['screw_clearance_hole'] + HI['vent_passage_diameter']) / 2

    checks = {
        'hub screw engagement in M200 rotor face (mm)': within(HI['screw_length'] - grip, HI['min_engagement'], M['can_thread_depth'] - 0.5),
        'screw head recessed below hub front face (mm)': within(floor - t - HI['screw_head_height'] - zf, 0.5),
        'shaft tip ahead of clamp floor (mm)': within(z['tip'] - floor, 0.5),
        'collar counterbore deeper than collar, hub seats on rotor face (mm)': within(z['face'] - z['counterbore_bottom'] - M['collar_height'], 0.1),
        'collar counterbore diametral clearance (mm)': within(HI['collar_diameter_allowance'], 0.05, 0.5),
        'pilot bore diametral allowance (mm)': within(HI['pilot_bore_allowance'], 0.02, 0.3),
        'screw head inside clamp ring outer edge (mm)': within(HI['clamp_ring_od'] / 2 - M['can_face_screw_pcd'] / 2 - HI['screw_head_diameter'] / 2, 0.0),
        'hub wall around clamp recess (mm)': within(R['hub_radius'] - HI['clamp_ring_od'] / 2 - HI['recess_radial_clearance'], HI['min_hub_wall']),
        'clamp ring radial clearance in recess (mm)': within(HI['recess_radial_clearance'], 0.1),
        'vent passage area / M200 vent area (ratio)': within((HI['vent_passage_diameter'] / M['vent_diameter']) ** 2, 1.0),
        'wall between vent passage and screw hole (mm)': within(vent_wall, 1.0),
        'base screw engagement in M200 inserts (mm)': within(M['base_screw_length'] - (S['rear_plate_thickness'] - S['base_screw_counterbore_depth']),
                                                            HI['min_engagement'], M['base_thread_depth'] - 0.5),
        'cable hole radial clearance around cable (mm)': within((S['cable_hole_diameter'] - M['cable_diameter']) / 2, 0.2),
        'duct bolt thread past nut (mm)': within(duct_tail, 0.5),
        'duct nut stack inside flange spot face (mm)': within(zface - fairing_z - (HW['washer_thickness'] + HW['nut_thickness'] + duct_tail), 0.0),
    }
    if HI['shaft_d_drive']:
        checks['D-flat engagement length (mm)'] = within(z['d_bore_top'] - z['tip'], 4.0)

    iface = ROOT / 'reports/motor_interface.json'
    status = json.loads(iface.read_text())['status'] if iface.exists() else 'not run'
    checks['M200 vendor STEP agrees with parameters'] = {'value': status, 'pass': status == 'PASS' or status.startswith('VENDOR STEP UNAVAILABLE')}

    names = ['rotor', 'motor_support', 'REFERENCE_M200_rotating', 'REFERENCE_M200_stationary', 'REFERENCE_clamp_ring']
    s = {n: cq.Shape.importBrep(str(E / (n + '.brep'))) for n in names}
    rotor_face = max((f for f in s['REFERENCE_M200_rotating'].Faces()
                      if f.geomType() == 'PLANE' and f.normalAt(f.Center()).z < -0.999), key=lambda f: f.Area())
    base_rear = max(x.BoundingBox().zmax for x in s['REFERENCE_M200_stationary'].Solids()
                    if abs(x.BoundingBox().xlen - M['base_diameter']) < 0.5)
    contacts = {
        'hub rear face on M200 rotor face (gap mm)': rotor_face.Center().z - s['rotor'].BoundingBox().zmax,
        'M200 base rear face on support rear plate (gap mm)': B.support_z()['plate_front'] - base_rear,
        'clamp ring on recess floor (gap mm)': floor - s['REFERENCE_clamp_ring'].BoundingBox().zmax,
    }
    for key, gap in contacts.items():
        checks[key] = within(abs(gap), 0.0, 0.02)
    out = {'scope': f"Nominal reference stack for the {M['model']}; contacts allowed, threads omitted",
           'grip_mm': {'hub_screw': grip, 'duct_bolt': duct_grip}, 'checks': checks,
           'all_pass': all(c['pass'] for c in checks.values())}
    (ROOT / 'reports/hardware_stack.json').write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
