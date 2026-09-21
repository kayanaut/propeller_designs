# Hub fit coupon (P2A-M2)

Print `hub_fit_coupon.3mf` before the rotor. Use the same resin, layer height, exposure, orientation relative to the plate, washing and post-cure you intend for the rotor hub. Resin holes usually come out smaller than modelled, so measure rather than assume.

The 82 × 30 × 16 mm block has three columns, marked with one, two and three small dots and placed at x = −25, 0 and +25 mm.

**Front row: a copy of the hub's M200 interface.** It opens at the top face, which stands in for the M200 rotor face:
- a collar counterbore 6.3 mm deep;
- a round bore over the plain part of the shaft;
- a D-bore through the rest of the block, with its flat parallel to the long edge.

| Column | Collar counterbore | Shaft bores (round and D) | M3 clearance hole (back row, Ø6.2 × 3 mm counterbore) |
|---|---|---|---|
| 1 dot | Ø11.1 (collar + 0.1) | Ø5.05, flat 4.025 mm from the far side (+0.05) | Ø3.2 |
| 2 dots | Ø11.2 (+0.2) | Ø5.10, flat 4.05 (+0.10) | Ø3.3 |
| 3 dots | Ø11.3 (+0.3) | Ø5.20, flat 4.10 (+0.20) | Ø3.4 |

The hub uses the column 2 values by default. The sizes follow `motor.collar_diameter`, `motor.shaft_diameter`, `motor.flat_across` and the `coupon` allowances.

**Test on a real M200**, with the motor unpowered:
1. Turn the coupon upside down over the motor so the collar and shaft go into one column. Line the flat up with the D-bore.
2. The coupon should slide down until it sits flat on the rotor face, without force and without visible rocking.
3. Try to turn the coupon on the shaft. With a good D-bore there is only a little rotational play.
4. Pass real M3 screws through the back-row holes; the heads should seat flat.

**Record:**
- resin product and batch, exposure, layer height, orientation, washing and post-cure;
- the measured bores, the measured holes and the measured M200 collar and shaft;
- which column seats flat, and how much play each has;
- any cracking;
- the fit again after soaking the coupon in water for your intended test duration.

Choose the tightest column that seats by hand. Put its allowances into `hub_interface.collar_diameter_allowance` and `hub_interface.pilot_bore_allowance`, and the hole into `hub_interface.screw_clearance_hole`. Then rebuild and rerun the checks. Don't scale the whole rotor to tune the hub fit.

The coupon is a fit sample only. It says nothing about torque capacity, fatigue, balance or long-term water ageing.
