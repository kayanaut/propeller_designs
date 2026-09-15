# Required inputs before manufacturing release (P2A-M2)

| Input | Current status |
|---|---|
| Motor | **Resolved:** Blue Robotics M200 standard, vendor STEP cross-checked |
| Reversible ESC for the M200 (24 A at 16 V full throttle) | Not selected |
| Battery voltage (the M200 runs on 7–20 V) | Not selected. The rotor's actual rpm and power at a given voltage come from CFD or a test rig |
| Cable routing from the strain-relief boss to the ROV frame, penetrator and strain relief | Not designed |
| ROV mounting points on the thruster | Not designed; the 3 flange bolts only join the duct and support |
| Resin printer model and usable X/Y/Z build volume | Unknown |
| Resin product (tough or ABS-like recommended), exposure and post-cure | Unknown |
| Slicer and version | Unknown |
| Water environment, depth, duty cycle and test duration | Unknown |

The duct and the motor support are about 134 mm across and the rotor about 91 mm. Many MSLA plates are narrower than 134 mm in one direction, so check each part against your plate in the orientation you choose. Bounding boxes are in `reports/mesh_report.json`.

The clearance budget in `parameters.json` is illustrative, not your printer's accuracy. Measure the coupon, the M200's shaft runout and axial play, and the assembly alignment, then replace the budget values and rerun `verify.py`.
