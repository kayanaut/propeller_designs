"""CadQuery generator for P2A-M2. Lengths mm, rotation axis +Z, water enters at -Z.

Printed parts: rotor (source/rotor.py), duct_full, motor_support (flange ring, foil struts,
flooded shroud for the Blue Robotics M200 and rear plate in one part) and hub_fit_coupon.
Not reconstructed from previous geometry or a generated image.
Run from any directory: python source/build.py
"""
import csv
import json
import math
import time

import cadquery as cq
import numpy as np

import rotor as RT

ROOT, P = RT.ROOT, RT.P
R, D, S, M, C, HI = P['rotor'], P['duct'], P['support'], P['motor'], P['coupon'], P['hub_interface']
OUT = ROOT / 'exports'
OUT.mkdir(exist_ok=True)
cyl, at_azimuth, azimuths = RT.cyl, RT.at_azimuth, RT.azimuths


def volume(shape, eps=1e-6):
    """Volume by adaptive integration. The default Shape.Volume() under-counts thin spline faces
    (a lofted strut by 14%)."""
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape.wrapped, props, eps, True)
    return props.Mass()


def save(shape, name):
    assert shape.isValid(), name + ' invalid'
    assert len(shape.Solids()) == 1, name + ' is not one solid'
    cq.exporters.export(shape, str(OUT / (name + '.step')))
    cq.exporters.export(shape, str(OUT / (name + '.stl')), tolerance=0.02, angularTolerance=0.1)
    shape.exportBrep(str(OUT / (name + '.brep')))
    print(name, 'valid, volume', round(volume(shape), 1), flush=True)


def duct_radii():
    """Throat, bell exit, lip radius, lip outer and outer mid-surface radii."""
    rt = R['diameter'] / 2 + D['nominal_radial_clearance']
    rb = rt + D['bell_radius_rise']
    rho = D['lip_radius']
    return rt, rb, rho, rb + 2 * rho, rt + D['outer_mid_rise']


def bolt_xy(i, count, radius, offset_deg=0.0):
    a = math.radians(offset_deg) + 2 * math.pi * i / count
    return radius * math.cos(a), radius * math.sin(a)


def duct(cfd=False):
    """Symmetric duct: straight throat over the rotor, bellmouths and round lips at both ends,
    convex outer surface, faired rear flange with nut spot faces (no holes when cfd=True)."""
    rt, rb, rho, rlo, rom = duct_radii()
    L, zt = D['half_length'], D['throat_half_length']
    kb, ko = (L - rho - zt) / 2, (L - rho) / 2
    body = (cq.Workplane('XZ').moveTo(rt, -zt).lineTo(rt, zt)
            .bezier([(rt, zt + kb), (rb, L - rho - kb), (rb, L - rho)], includeCurrent=True)
            .threePointArc((rb + rho, L), (rlo, L - rho))
            .bezier([(rlo, L - rho - ko), (rom, ko), (rom, 0)], includeCurrent=True)
            .bezier([(rom, -ko), (rlo, -(L - rho) + ko), (rlo, -(L - rho))], includeCurrent=True)
            .threePointArc((rb + rho, -L), (rb, -(L - rho)))
            .bezier([(rb, -(L - rho) + kb), (rt, -zt - kb), (rt, -zt)], includeCurrent=True)
            .close().revolve().val())
    zface = L - D['flange_thickness']
    flange = (cq.Workplane('XZ').polyline([(rom - 0.5, D['fairing_start_z']), (D['flange_radius'], zface),
                                           (D['flange_radius'], L), (rb + rho, L), (rb + rho, L - 1)])
              .close().revolve().val())
    body = body.fuse(flange)
    if not cfd:
        for i in range(D['bolt_count']):
            x, y = bolt_xy(i, D['bolt_count'], D['bolt_circle_radius'])
            body = body.cut(cyl(D['bolt_hole'] / 2, D['fairing_start_z'] - 2, L - D['fairing_start_z'] + 3).translate((x, y, 0)))
            body = body.cut(cyl(D['nut_spotface_radius'], D['fairing_start_z'] - 2, zface - D['fairing_start_z'] + 2)
                            .translate((x, y, 0)))
    return body.clean()


def support_z():
    """Axial stations of the stationary support, derived from the M200 dimensions."""
    can_front = R['hub_rear_z']
    can_rear = can_front + M['can_length']
    plate_front = can_rear + M['can_to_base_gap'] + M['base_length']
    return dict(can_front=can_front, can_rear=can_rear, lip=can_front + S['shroud_front_axial_clearance'],
                base_front=can_rear + M['can_to_base_gap'], plate_front=plate_front,
                plate_rear=plate_front + S['rear_plate_thickness'],
                cable=plate_front - M['cable_height_above_base_rear'])


def shroud_radii():
    """Shroud bore and outer radius: the bore clears the rotating can and is a slide fit on the base."""
    si = max(M['can_diameter'] / 2 + S['shroud_can_radial_clearance'],
             (M['base_diameter'] + M['base_diameter_tolerance']) / 2 + S['base_slide_clearance'])
    return si, si + S['shroud_wall']


def strut(angle_deg, r_start, r_end):
    """Symmetric foil strut: chord along +Z from just behind the duct rear face, thickness tangential.
    Lofted through strut_stations identical sections (rotor.loft). A plain extrusion tessellated into
    full-span triangles about 0.01 mm wide, which OpenFOAM's surfaceCheck reports as self-intersecting.
    The leading edge sits strut_leading_edge_offset behind the ring's front plane, which keeps the
    ring fuse clean."""
    chord, L = S['strut_chord'], D['half_length'] + S['strut_leading_edge_offset']
    t_c = S['strut_thickness'] / chord
    x = RT.profile_x()
    yt = RT.naca_half(x, t_c, chord) * chord
    px, py = np.r_[x[::-1], x[1:]], np.r_[yt[::-1], -yt[1:]]      # upper TE -> LE -> lower TE
    rings = np.array([np.c_[np.full_like(px, r), py, L + px * chord]
                      for r in np.linspace(r_start, r_end, S['strut_stations'])])
    return RT.loft(rings, t_c, chord).rotate((0, 0, 0), (0, 0, 1), angle_deg)


def radial_cylinder(radius, r0, r1, z, azimuth_deg):
    return cq.Solid.makeCylinder(radius, r1 - r0, cq.Vector(r0, 0, z), cq.Vector(1, 0, 0)).rotate(
        (0, 0, 0), (0, 0, 1), azimuth_deg)


def motor_support(cfd=False):
    """Flange ring, foil struts and the M200 shroud with rear plate. cfd=True fills the shroud into a
    solid pod and leaves out holes, slots and the cable boss (first CFD model)."""
    rt, rb, rho, rlo, rom = duct_radii()
    L = D['half_length']
    z = support_z()
    si, so = shroud_radii()
    lip = S['shroud_wall'] / 2
    if cfd:
        cx, cz = so - lip, z['lip'] + lip
        body = (cq.Workplane('XZ').moveTo(0, z['lip']).lineTo(cx, z['lip'])
                .threePointArc((cx + lip * math.sqrt(0.5), cz - lip * math.sqrt(0.5)), (so, cz))
                .lineTo(so, z['plate_rear']).lineTo(0, z['plate_rear']).close().revolve().val())
    else:
        rd = S['drain_hole_diameter'] / 2
        body = (cq.Workplane('XZ').moveTo(si, z['lip'] + lip).threePointArc((si + lip, z['lip']), (so, z['lip'] + lip))
                .lineTo(so, z['plate_rear']).lineTo(rd, z['plate_rear']).lineTo(rd, z['plate_front'])
                .lineTo(si, z['plate_front']).close().revolve().val())
    # The flange ring starts at the duct lip apex, so nothing steps into the jet.
    body = body.fuse(cyl(D['flange_radius'], L, S['ring_thickness']).cut(cyl(rb + rho, L - 1, S['ring_thickness'] + 2)))
    for i in range(D['bolt_count']):
        x, y = bolt_xy(i, D['bolt_count'], D['bolt_circle_radius'])
        body = body.fuse(cyl(S['bolt_boss_radius'], L, S['bolt_boss_length']).translate((x, y, 0)))
        body = body.fuse(strut(360 * i / D['bolt_count'], so - 0.5, D['bolt_circle_radius']))
    if cfd:
        return body.clean()

    cable_az = M['cable_azimuth_deg']
    boss_end = so + S['strain_relief_length']
    # Start the boss where its whole flat end is buried in the shroud wall; starting at so - 0.5
    # left the end face poking out beside the boss and made sliver faces.
    boss_start = math.sqrt(so ** 2 - (S['strain_relief_od'] / 2) ** 2) - 0.5
    assert boss_start > si, 'strain-relief boss wider than the shroud wall allows'
    body = body.fuse(radial_cylinder(S['strain_relief_od'] / 2, boss_start, boss_end, z['cable'], cable_az))
    for i in range(D['bolt_count']):
        x, y = bolt_xy(i, D['bolt_count'], D['bolt_circle_radius'])
        body = body.cut(cyl(D['bolt_hole'] / 2, L - 1, S['bolt_boss_length'] + 2).translate((x, y, 0)))
    body = body.cut(radial_cylinder(S['cable_hole_diameter'] / 2, si - 1, boss_end + 1, z['cable'], cable_az))
    cb = S['base_screw_counterbore_depth']
    for deg in azimuths(M['base_screw_offset_deg'], M['base_screw_count']):
        body = body.cut(at_azimuth(cyl(S['base_screw_hole'] / 2, z['plate_front'] - 1, S['rear_plate_thickness'] + 2),
                                   deg, M['base_screw_pcd'] / 2))
        body = body.cut(at_azimuth(cyl(S['base_screw_counterbore_diameter'] / 2, z['plate_rear'] - cb, cb + 1),
                                   deg, M['base_screw_pcd'] / 2))
    z0, z1 = z['can_front'] + S['cooling_slot_front_offset'], z['can_rear'] - S['cooling_slot_rear_offset']
    for i in range(S['cooling_slot_count']):
        slot = (cq.Workplane('XY', origin=((si + so) / 2, 0, z0))
                .box(S['shroud_wall'] + 2, S['cooling_slot_width'], z1 - z0, centered=(True, True, False)).val())
        body = body.cut(slot.rotate((0, 0, 0), (0, 0, 1), S['cooling_slot_offset_deg'] + 360 * i / S['cooling_slot_count']))
    return body.clean()


def coupon():
    """Resin calibration for the M200 hub interface. Each column copies the hub's collar counterbore,
    round bore and D-bore (open at the top face, which stands in for the can face) with one set of
    allowances; the second row holds M3 clearance holes with counterbores."""
    sx, sy, sz = C['size']
    blk = cq.Workplane('XY').box(sx, sy, sz, centered=(True, True, False)).edges('|Z').fillet(2).val()
    bore_y, hole_y = -4.0, 8.0
    counterbore_bottom = sz - M['collar_height'] - HI['collar_depth_allowance']
    d_top = sz - M['collar_height'] - (M['shaft_length'] - M['flat_length']) - HI['flat_lead_in']
    for i, (ca, sa, hole) in enumerate(zip(C['collar_allowances'], C['shaft_allowances'], C['hole_diameters'])):
        x = (i - 1) * C['spacing']
        feat = cyl((M['collar_diameter'] + ca) / 2, counterbore_bottom, sz - counterbore_bottom + 1)
        feat = feat.fuse(cyl((M['shaft_diameter'] + sa) / 2, d_top - 0.01, counterbore_bottom - d_top + 0.02))
        feat = feat.fuse(RT.d_bore(-1, d_top, sa, 90.0))
        blk = blk.cut(feat.translate((x, bore_y, 0)))
        blk = blk.cut(cyl(hole / 2, -1, sz + 2).translate((x, hole_y, 0)))
        blk = blk.cut(cyl(C['counterbore_diameter'] / 2, sz - C['counterbore_depth'], C['counterbore_depth'] + 1)
                      .translate((x, hole_y, 0)))
        for mark in range(i + 1):
            blk = blk.cut(cyl(0.65, sz - 0.8, 1).translate((x + (mark - i / 2) * 2.5, -sy / 2 + 2.5, 0)))
    return blk.clean()


def main():
    t0 = time.time()
    sec = RT.sections(RT.solve_apex())
    chk = RT.check(sec)
    if chk['failures']:
        raise SystemExit('section checks failed: ' + '; '.join(chk['failures']))
    header, rows = RT.section_rows(sec)
    with (ROOT / 'reports/blade_sections.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows([[f'{v:.5g}' if isinstance(v, float) else v for v in row] for row in rows])

    rotor, blade = RT.rotor_solid(sec)
    save(rotor, 'rotor')
    shapes = {'rotor': rotor, 'duct_full': duct(), 'motor_support': motor_support(), 'hub_fit_coupon': coupon()}
    for name in ('duct_full', 'motor_support', 'hub_fit_coupon'):
        save(shapes[name], name)
    cq.exporters.export(cq.Compound.makeCompound([shapes[n] for n in ('rotor', 'duct_full', 'motor_support')]),
                        str(OUT / 'assembly.step'))
    info = {'revision': P['revision'], 'motor': M['model'], 'blade_checks': chk, 'blade_volume_mm3': volume(blade),
            'support_stations_mm': support_z(), 'shroud_radii_mm': dict(zip(['bore', 'outer'], shroud_radii())),
            'hub_interface_stations_mm': RT.interface_z(),
            'duct_radii_mm': dict(zip(['throat', 'bell_exit', 'lip_radius', 'lip_outer', 'outer_mid'], duct_radii())),
            'generation_seconds': time.time() - t0,
            'parts': {k: {'valid_brep': v.isValid(), 'solids': len(v.Solids()), 'volume_mm3': volume(v),
                          'bbox_mm': [v.BoundingBox().xlen, v.BoundingBox().ylen, v.BoundingBox().zlen],
                          'z_range_mm': [v.BoundingBox().zmin, v.BoundingBox().zmax]} for k, v in shapes.items()}}
    text = json.dumps(info, indent=2, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    (ROOT / 'reports/build_report.json').write_text(text)
    print(text, flush=True)


if __name__ == '__main__':
    main()
