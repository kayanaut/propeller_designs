# Hardware references — not for printing

- `REFERENCE_M200_rotating` / `REFERENCE_M200_stationary`: Blue Robotics M200 standard (BR-101376), from the vendor STEP hardware/vendor/M200_STANDARD_BR-101376_PUBLIC.STEP, placed in the thruster frame (rotor face at z = 16 mm, cable toward 60°). `vendor/` holds Blue Robotics' original download. `reports/motor_interface.json` compares the STEP with `source/parameters.json`.
- `REFERENCE_clamp_ring`: metal ring Ø27 × 1.5 mm under the screw heads, with 2 screw holes and 2 vent holes aligned with the motor vents. It spreads the clamp load so the resin hub does not crack or creep under the heads.
- `REFERENCE_hub_screws`: 2× M3 × 25 socket head cap screws into the M200 rotor face (5 mm maximum depth; this design engages 4 mm).

## Load path

- **Torque:** M200 shaft D-flat and the 2 face screws (clamp friction plus shank bearing) → resin hub → loops.
- **Forward thrust** (jet toward the support) pulls the rotor away from the motor: the 2 face screws carry it in tension, and the M200 base screws carry it into the rear plate.
- **Reverse thrust** presses the hub onto the rotor face and the base onto the rear plate.
- The collar only locates; the hub seats on the rotor face. `reports/hardware_stack.json` checks screw engagement, shaft tip and collar clearance.

## Fasteners

Do **not** use threadlocker. Blue Robotics warns that most threadlockers attack the polycarbonate in their motors and make it brittle. Tighten snugly and recheck screw tension after the first soak, because resin under a clamp relaxes. The base takes 4× M3 × 8 screws with no more than 6 mm thread engagement.

The M200 is designed to run flooded. The support shroud is a flow-through guard, not a seal; keep the motor vents and cooling slots open.
