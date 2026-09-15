"""Reference hardware: Blue Robotics M200 motor, clamp ring and hub screws. Not for printing.

The motor comes from the vendor STEP aligned by motor_step.py. If that file is missing, a
parametric M200 built from parameters.json is used instead (can, collar, D-flat shaft, face
holes and vents, base with inserts, cable stub). No helical threads or production fits.
"""
import math

import cadquery as cq

import motor_step as MS
import rotor as RT

ROOT, P = RT.ROOT, RT.P
R, M, HI = P['rotor'], P['motor'], P['hub_interface']
E, H = ROOT / 'exports', ROOT / 'hardware'
H.mkdir(exist_ok=True)
cyl, at_azimuth, azimuths = RT.cyl, RT.at_azimuth, RT.azimuths


def parametric_m200():
    z = RT.interface_z()
    zc = z['face']
    can = cyl(M['can_diameter'] / 2, zc, M['can_length']).fuse(cyl(M['collar_diameter'] / 2, z['collar_top'], M['collar_height']))
    shaft = cyl(M['shaft_diameter'] / 2, z['tip'], M['shaft_length'] + 0.01)
    flat = M['flat_across'] - M['shaft_diameter'] / 2
    cut = cq.Solid.makeBox(10, 10, M['flat_length'], cq.Vector(flat, -5, z['tip'])).rotate((0, 0, 0), (0, 0, 1), M['cable_azimuth_deg'])
    can = can.fuse(shaft.cut(cut))
    for deg in azimuths(0, M['can_face_screw_count']):
        can = can.cut(at_azimuth(cyl(1.25, zc - 0.01, M['can_face_plate_thickness'] + 0.02), deg, M['can_face_screw_pcd'] / 2))
    for deg in azimuths(M['vent_offset_deg'], M['vent_count']):
        can = can.cut(at_azimuth(cyl(M['vent_diameter'] / 2, zc - 0.01, M['can_face_plate_thickness'] + 0.02), deg, M['vent_pcd'] / 2))
    zb = zc + M['can_length'] + M['can_to_base_gap']
    rear = zb + M['base_length']
    base = cyl(M['base_diameter'] / 2, zb, M['base_length'])
    for deg in azimuths(M['base_screw_offset_deg'], M['base_screw_count']):
        base = base.cut(at_azimuth(cyl(1.25, rear - M['base_thread_depth'], M['base_thread_depth'] + 0.01), deg, M['base_screw_pcd'] / 2))
    cable = cq.Solid.makeCylinder(M['cable_diameter'] / 2, MS.CABLE_KEEP_RADIUS - M['base_diameter'] / 2 + 1,
                                  cq.Vector(M['base_diameter'] / 2 - 1, 0, rear - M['cable_height_above_base_rear']),
                                  cq.Vector(1, 0, 0)).rotate((0, 0, 0), (0, 0, 1), M['cable_azimuth_deg'])
    return {'rotating': can.clean(), 'stationary': cq.Compound.makeCompound([base.clean(), cable])}


def clamp_and_screws():
    z = RT.interface_z()
    floor, t = z['floor'], HI['clamp_ring_thickness']
    clamp = cyl(HI['clamp_ring_od'] / 2, floor - t, t).cut(cyl(HI['clamp_ring_id'] / 2, floor - t - 1, t + 2))
    screws = []
    for deg in azimuths(0, M['can_face_screw_count']):
        clamp = clamp.cut(at_azimuth(cyl(HI['screw_clearance_hole'] / 2, floor - t - 1, t + 2), deg, M['can_face_screw_pcd'] / 2))
        head = cyl(HI['screw_head_diameter'] / 2, floor - t - HI['screw_head_height'], HI['screw_head_height'])
        screws.append(at_azimuth(head.fuse(cyl(1.25, floor - t, HI['screw_length'])), deg, M['can_face_screw_pcd'] / 2))
    for deg in azimuths(M['vent_offset_deg'], M['vent_count']):
        clamp = clamp.cut(at_azimuth(cyl(HI['vent_passage_diameter'] / 2, floor - t - 1, t + 2), deg, M['vent_pcd'] / 2))
    return clamp.clean(), cq.Compound.makeCompound(screws)


def main():
    motor = MS.load_aligned()
    source = 'vendor STEP ' + M['vendor_step']
    if motor is None:
        motor, source = parametric_m200(), 'parametric model (vendor STEP unavailable)'
    clamp, screws = clamp_and_screws()
    refs = {'REFERENCE_M200_rotating': motor['rotating'], 'REFERENCE_M200_stationary': motor['stationary'],
            'REFERENCE_clamp_ring': clamp, 'REFERENCE_hub_screws': screws}
    for name, s in refs.items():
        assert s.isValid(), name
        cq.exporters.export(s, str(H / (name + '.step')))
        s.exportBrep(str(H / (name + '.brep')))
        # Display meshes for the previews only; never print these.
        cq.exporters.export(s, str(E / (name + '.stl')), tolerance=0.04, angularTolerance=0.12)
        s.exportBrep(str(E / (name + '.brep')))
    printed = [cq.Shape.importBrep(str(E / (n + '.brep'))) for n in ('rotor', 'duct_full', 'motor_support')]
    cq.exporters.export(cq.Compound.makeCompound(printed + list(refs.values())),
                        str(E / 'assembly_with_reference_hardware.step'))
    n = M['can_face_screw_count']
    (H / 'README.md').write_text(f'''# Hardware references — not for printing

- `REFERENCE_M200_rotating` / `REFERENCE_M200_stationary`: {M['model']}, from the {source}, placed in the thruster frame (rotor face at z = {R['hub_rear_z']:g} mm, cable toward {M['cable_azimuth_deg']:g}°). `vendor/` holds Blue Robotics' original download. `reports/motor_interface.json` compares the STEP with `source/parameters.json`.
- `REFERENCE_clamp_ring`: metal ring Ø{HI['clamp_ring_od']:g} × {HI['clamp_ring_thickness']:g} mm under the screw heads, with {n} screw holes and {M['vent_count']} vent holes aligned with the motor vents. It spreads the clamp load so the resin hub does not crack or creep under the heads.
- `REFERENCE_hub_screws`: {n}× M3 × {HI['screw_length']:g} socket head cap screws into the M200 rotor face ({M['can_thread_depth']:g} mm maximum depth; this design engages {HI['target_engagement']:g} mm).

## Load path

- **Torque:** M200 shaft D-flat and the {n} face screws (clamp friction plus shank bearing) → resin hub → loops.
- **Forward thrust** (jet toward the support) pulls the rotor away from the motor: the {n} face screws carry it in tension, and the M200 base screws carry it into the rear plate.
- **Reverse thrust** presses the hub onto the rotor face and the base onto the rear plate.
- The collar only locates; the hub seats on the rotor face. `reports/hardware_stack.json` checks screw engagement, shaft tip and collar clearance.

## Fasteners

Do **not** use threadlocker. Blue Robotics warns that most threadlockers attack the polycarbonate in their motors and make it brittle. Tighten snugly and recheck screw tension after the first soak, because resin under a clamp relaxes. The base takes 4× M3 × {M['base_screw_length']:g} screws with no more than {M['base_thread_depth']:g} mm thread engagement.

The M200 is designed to run flooded. The support shroud is a flow-through guard, not a seal; keep the motor vents and cooling slots open.
''')
    print('Hardware references exported from', source)


if __name__ == '__main__':
    main()
