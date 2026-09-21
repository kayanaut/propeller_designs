# Print preparation — resin (SLA/MSLA), conditional, not machine approved

The printer, resin and slicer are unconfirmed. No sliced project or exposure file exists, and the 3MFs hold geometry only.

## Approximate resin volume (solid parts, before supports)

| Part | Volume | Size (mm) |
|---|---|---|
| rotor | 27 cm³ | 82 × 92 × 30 |
| duct_full | 119 cm³ | 134 × 134 × 44 |
| motor_support | 45 cm³ | 134 × 134 × 59 |
| hub_fit_coupon | 36 cm³ | 82 × 30 × 16 |

Exact values are in `reports/build_report.json` and `reports/mesh_report.json`.

## Orientation candidates

Resin prints are pulled off the vat film layer by layer. Avoid large flat cross-sections parallel to the plate (high peel force) and cups that open toward the plate (suction). Tilting parts 20–45° is normal.

| Part | Candidate to inspect | Concerns |
|---|---|---|
| Rotor | Axis tilted about 30–45°, rear (motor) face away from the plate | Keep supports off the rear seating face, the collar counterbore, the D-bore and the trailing edges. Support the hub front rim and near the loop roots, and check every loop apex for islands. |
| Duct | Standing on edge or tilted about 20–30° | A flange-down ring has a large peel area; on a plate narrower than 134 mm it has to stand on edge. Keep supports off the inner throat surface. |
| Motor support | Tilted, with the shroud's open front **not** facing the plate | The shroud is a cup, so the cooling slots, cable hole and drain hole must vent during printing. Keep supports off the shroud bore (the M200 base slides in there) and off the rear plate's motor seat. |
| Coupon | The same tilt as the rotor hub axis | Only then do the measured bores transfer to the rotor. |

These are starting points to inspect in the slicer, not approved orientations. Each 3MF keeps +Z and only moves the part onto the plate; apply rotations in the slicer.

## Feature sizes to check

- **Loops:** 0.5 mm trailing edges; the thinnest section is at least 1.0 mm.
- **Hub:**
  - collar counterbore Ø11.2 × 6.3 mm;
  - Ø5.1 mm round bore and D-bore (flat 4.05 mm);
  - two Ø4.5 mm vent passages and two Ø3.3 mm screw holes;
  - clamp-ring recess Ø27.5 mm.
  - Resin shrinkage and over-cure make holes smaller: calibrate with the coupon.
- **Shroud bore:** Ø40.6 mm, a slide fit on the M200 base (Ø40 ±0.2). If it prints tight, adjust `support.base_slide_clearance` rather than sanding unevenly: this bore centres the rotor in the duct.
- **Duct:** 2 mm tip gap in the throat. Warped duct prints close this gap, so measure roundness after post-cure.
- **Support:** 2.5 mm shroud wall, 4 mm foil struts, 4 mm flange ring, 5 mm rear plate, Ø7 mm cable hole.

## Material notes

Use a tough, ABS-like or engineering resin. Wash and post-cure to the maker's instructions, because under-cured parts are weak and dimensionally unstable. Standard resins are brittle, absorb water and creep under sustained load. Treat these parts as fit-test and short wet-test parts, not for long submerged running.

## Mandatory slicer review

After choosing the real printer and resin, check:
- the mm scale and plate fit;
- islands and unsupported overhangs layer by layer, at the loop apexes, roots, trailing edges, strut tips, bolt bosses and cable boss;
- suction cups and trapped volumes;
- that every support can be removed without touching trailing edges, the hub rear face or the shroud bore.

Keep the slicer project in `slicer/`. `previews/rotor_layer_sections.png` shows geometric cross-sections only; it is not a slicer preview.
