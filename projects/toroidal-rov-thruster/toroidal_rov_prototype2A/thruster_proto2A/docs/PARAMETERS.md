# Parametric construction (P2A-M2)

All settings are in `source/parameters.json` (mm).
- `source/rotor.py` builds the rotor.
- `source/build.py` builds the other printed parts.
- `source/motor_step.py` aligns and checks the vendor M200.
- `source/hardware.py` exports the reference hardware.

After any change, run `python source/rotor.py --check-only`, then `python source/run_all.py`. A successful build is not approval: read the reports.

## Rotor (`rotor`)

Unchanged from M1.

**Loop path.** Each loop follows the P2A generator line, with parameter u from 0 to 1:

x = root_x + (apex_x − root_x)·sin(πu), y = half_leg_spacing·cos(πu), z = −axial_separation/2·cos(πu) + closure_rise·sin(πu)

Both ends are buried in the hub. `apex_x` is solved by bisection within `apex_x_search`, so the section surface reaches `diameter/2 − envelope_margin`. The sections are never rescaled.

**Pitch.** Face pitch P = `pitch_to_diameter` × `diameter` is constant, so the pitch angle at radius r is atan(P / 2πr). Along the legs the chord lies on that helix; across the apex it turns normal to the path, with weight 1 − (t·e_r)².

**Sections.** NACA 4-digit symmetric sections, blunted to `trailing_edge`.
- Chord and t/c blend from `root_*` through `leg_*` to `closure_*`.
- A root flare (`flare_length`, `flare_thickness`, `flare_chord`) is built into the loft.
- `min_thickness` is enforced.
- All section splines share one knot vector.

**Rotation.** Forward thrust needs the rotor to turn about −Z: counter-clockwise seen from the inlet. `rotor.check()` confirms the sign.

**Hub.** A cylinder of `hub_radius` from `hub_front_z` (chamfer `hub_front_chamfer`) to `hub_rear_z`. The M200 can has the same radius (18 mm), so the M1 skirt is skipped automatically.

**Gates** (the build refuses to run if any fail):
- envelope;
- no folded stations;
- root ends and footprint inside the hub;
- leg gap ≥ `min_leg_gap` and loop-to-loop gap ≥ `min_blade_gap`;
- thinnest section ≥ `min_thickness`;
- trailing edge ≥ `process.trailing_edge_min`.

## Motor (`motor`): Blue Robotics M200

All values come from Blue Robotics drawing BR-101694-001 and the motor guide, and are confirmed against the vendor STEP by `motor_step.py` (0.1 mm / 0.5° tolerance). Azimuths are measured from the cable exit.

| Parameter | Meaning |
|---|---|
| `can_diameter`, `can_length`, `can_face_plate_thickness` | Spinning can Ø36 × 29; the face plate is 4 mm thick |
| `can_face_screw_count`, `can_face_screw_pcd`, `can_thread_depth` | 2× M3 in the rotor face on Ø19.05, at 0° and 180°; Blue Robotics' maximum screw depth is 5 mm |
| `vent_count`, `vent_diameter`, `vent_pcd`, `vent_offset_deg` | 2× Ø4 vents on Ø21, at 45° and 225°. The motor is flooded; keep them open |
| `collar_diameter`, `collar_height` | Ø11 × 6 collar on the rotor face |
| `shaft_diameter`, `shaft_length`, `flat_across`, `flat_length` | Ø5 × 12 beyond the collar; the last 6 mm has a flat 4.00 mm across, facing the cable azimuth |
| `can_to_base_gap`, `base_diameter`, `base_diameter_tolerance`, `base_length` | 1.1 mm gap; stationary base Ø40 ±0.2 × 25.5 |
| `base_screw_count`, `base_screw_pcd`, `base_screw_offset_deg`, `base_thread_depth`, `base_screw_length` | 4× M3 inserts on a 21.2 mm square (circle Ø29.98) at 45° from the cable; no more than 6 mm engagement; M3 × 8 screws |
| `cable_diameter`, `cable_height_above_base_rear`, `cable_azimuth_deg` | Ø6.35 cable leaving the base side 6.82 mm above its rear face. `cable_azimuth_deg` (60°) sets how the motor is clocked in the thruster: between two struts |
| `kv_rpm_per_v`, `voltage_range_v`, `max_power_16v_w`, `max_current_16v_a` | Electrical data, for reference |

## Hub interface (`hub_interface`)

- **Front recess:** holds the metal clamp ring (`clamp_ring_od` 27 × `clamp_ring_thickness`, radial clearance `recess_radial_clearance`). The recess floor is placed so the M3 × `screw_length` screws engage `target_engagement` (4 mm) into the M200 rotor face.
- **Collar counterbore:** from the hub rear face, Ø(collar + `collar_diameter_allowance`), `collar_depth_allowance` deeper than the collar. The hub therefore seats on the rotor face, never on the collar.
- **Round bore:** Ø(shaft + `pilot_bore_allowance`) over the plain part of the shaft.
- **D-bore** over the flat, starting `flat_lead_in` past the flat's start. Its flat sits half the bore allowance beyond the shaft's flat, so the printed flat drives the shaft. `shaft_d_drive: false` turns it into a round bore.
- **Vent passages:** `vent_passage_diameter` holes through the hub, lined up with the M200 vents. Matching holes are cut in the clamp ring.
- **Hub wall:** `min_hub_wall` is the smallest allowed wall between the clamp recess and the hub surface.

`reports/hardware_stack.json` checks all of these, plus the contact faces.

## Duct (`duct`)

Unchanged from M1.
- Throat radius = rotor radius + `nominal_radial_clearance` (2 mm).
- Straight throat over ±`throat_half_length`, bellmouths (`bell_radius_rise`) to round lips (`lip_radius`) at ±`half_length`.
- Convex outer surface.
- Faired rear flange with `bolt_count` holes on `bolt_circle_radius` and nut spot faces.

## Motor support (`support`)

One printed part.
- **Flange ring** (`ring_thickness`) starting at the duct lip.
- **Foil struts** (`strut_chord` × `strut_thickness`) to bolt bosses.
- **Flooded shroud:**
  - Bore radius = max(can radius + `shroud_can_radial_clearance`, (base Ø + tolerance)/2 + `base_slide_clearance`) = 20.3 mm. The largest base slides in, and the bore centres it.
  - Wall `shroud_wall`; round front lip `shroud_front_axial_clearance` behind the rotor face.
  - `cooling_slot_count` slots, offset `cooling_slot_offset_deg` from the struts, spanning the can from `cooling_slot_front_offset` to `cooling_slot_rear_offset`.
- **Cable hole:** radial, `cable_hole_diameter`, at the M200 cable height and azimuth, through a strain-relief boss (`strain_relief_od` × `strain_relief_length`).
- **Rear plate** (`rear_plate_thickness`): counterbored base screw holes (`base_screw_hole`, `base_screw_counterbore_*`) and a central drain hole (`drain_hole_diameter`).

`verify.py` gates the all-angle rotor-to-support gap (`min_rotor_to_stationary_gap`), the blade-to-strut gap (`min_blade_to_strut_gap`), can clearance and the base slide fit.

## Coupon, CFD, budget, process

- `coupon`: the hub fit coupon. Each column copies the hub interface with its own `collar_allowances` and `shaft_allowances`; the second row has M3 holes (`hole_diameters`). See `COUPON.md`.
- `cfd`: `split_z` is where the rotating CFD body ends, inside the 2 mm gap to the shroud lip. `stl_*` set the CFD surface tessellation (`export_cfd.py`).
- `clearance_budget`: illustrative resin print, runout and alignment errors, subtracted from the proven gaps. Replace them with measured values.
- `process`: resin assumptions, otherwise empty until the printer and resin are confirmed.
- `hardware`: nominal washer and nut thicknesses for the duct bolt stack.
