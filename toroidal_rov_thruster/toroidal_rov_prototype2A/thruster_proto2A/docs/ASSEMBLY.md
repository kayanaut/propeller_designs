# Fit-test assembly guide (P2A-M2, Blue Robotics M200)

Start with unpowered hand testing.

1. **Coupon first.** Print `hub_fit_coupon` in the rotor's resin, orientation, exposure and post-cure. Test each column on the real M200 rotor: the collar, the shaft and its flat. Test the M3 holes with the real screws. Transfer the chosen values to `collar_diameter_allowance`, `pilot_bore_allowance` and `screw_clearance_hole`, rebuild and recheck. See `COUPON.md`.
2. **Prepare the parts.** Remove supports and post-cure as the resin maker specifies.
   - Clear the collar counterbore, D-bore, both vent passages, the screw holes and the cable hole.
   - Inspect the loop closures, root flares and 0.5 mm trailing edges; don't sand the edges away.
   - The hub rear face must be flat: it seats on the M200 rotor face.
3. **Cable through the shroud.** From inside the shroud, push the free end of the M200 cable out through the radial cable hole and strain-relief boss.
4. **Motor into the support.**
   - Slide the M200 into the shroud from the front, base first, turning it so the cable lines up with the hole. The Ø40 base is a slide fit in the bore; don't force it.
   - Seat the base on the rear plate and fit 4× M3 × 8 socket head screws from the rear through the counterbores.
   - Turn the M200 rotor by hand: it must not touch the shroud (2.3 mm nominal gap).
5. **Rotor onto the motor.**
   - Line the hub's D-bore up with the shaft flat. The flat faces the cable side.
   - Slide the rotor on until the hub rear face sits flat on the M200 rotor face, with the collar inside its counterbore.
   - Put the metal clamp ring in the front recess with its two vent holes over the hub's vent passages.
   - Fit 2× M3 × 25 socket head screws into the M200 rotor face and tighten evenly until snug.
   - **No threadlocker:** Blue Robotics warns that most threadlockers attack the polycarbonate in their motors.
   - Resin under a clamp relaxes, so recheck the screws after the first soak.
6. **Duct.** Slide the duct over the rotor from the front until its rear flange meets the support's flange ring. Fit 3× M3 × 25 bolts from the rear through the strut bosses, with a washer under each head, and washers and nuts in the flange spot faces.
7. **Hand check.** Turn the rotor through several full revolutions with the assembly in different orientations.
   - Measure the tip gap (2 mm nominal), the axial gap to the shroud lip (2 mm) and the runout.
   - Nothing may touch the duct, struts, shroud, screws or cable.
   - Look through the vent passages: you should see the M200's vents.
8. **Direction.** For forward thrust the rotor must turn **counter-clockwise seen from the inlet** (the open front of the duct). If it spins the wrong way, swap any two of the three motor wires at the ESC. Water then leaves past the motor support.
9. **Service order.** Remove the duct (3 bolts), then the rotor (2 screws from the front), then the motor (4 screws from the rear).

## Load path

- **Torque:** M200 shaft flat → hub D-bore, plus the 2 clamped face screws → hub → loops.
- **Forward thrust (jet toward the support):** pulls the rotor away from the motor.
  - The 2 face screws carry it in tension into the M200 rotor.
  - The motor bearings carry it to the base, and the 4 base screws carry it into the rear plate, the struts, the duct flange and the ROV mount.
  - Thrust of about 35–40 N gives about 20 N per screw.
- **Reverse thrust:** presses the hub onto the rotor face and the base onto the rear plate.
- The collar only locates. The Blue Robotics T200 uses the same motor at up to 51 N forward and 40 N reverse at 16 V.

## Screw access

| Joint | Tool approach | Remaining check |
|---|---|---|
| Rotor to M200, 2× M3 × 25 | Axially through the duct inlet, or before fitting the duct | Head clearance in the recess |
| Duct to support, 3× M3 × 25 | Heads from the rear at the strut bosses; nuts at the front of the flange | ROV mount access to the nuts |
| M200 base to plate, 4× M3 × 8 | From the rear | Engagement ≤ 6 mm (5 mm as designed) |

No swept tool-access simulation has been done. Check access on the first print.
