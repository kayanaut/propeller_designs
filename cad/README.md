# CAD Models

Briefs: [aerial_cad.md](aerial_cad.md) · [underwater_cad.md](underwater_cad.md).
Models: [underwater/](underwater/), one folder per design.

**Built:** 6 of 13 underwater, 0 of 11 aerial. All six are watertight and manifold.

- **[ducted-kort](underwater/ducted-kort/model.stl)** — *closest to spec.* Nozzle ID 250, Ø247
  `Z=4`, clearance 1.50. Confirm the wall is cylindrical across the sweep.
- **[surface-piercing](underwater/surface-piercing/model.stl)** — *fix the planform.* The only
  single unioned solid in the set. Tip is tapered, not a square-cut cleaver. Ø285.6 vs 250.
- **[rim-driven](underwater/rim-driven/model.stl)** — *fix the duct.* Rotor correct and truly
  hubless. Duct is a bare annulus; magnets overlap the ring instead of sitting in pockets.
- **[contra-rotating](underwater/contra-rotating/model.stl)** — *delete one body.* Pair is correct
  and the mirror is genuine. A stray third propeller sits at `z=0` and clashes with the sleeve.
- **[pump-jet](underwater/pump-jet/model.stl)** — **rebuild.** Rotor cuts through the shroud by
  9.5 mm; stator sits inside the rotor, not up- or downstream; built on Y.
- **[supercavitating](underwater/supercavitating/model.stl)** — **rebuild.** Blades are detached —
  a 4.62 mm gap, nothing unioned. Ø297.7 vs 250.

Not built — underwater: FPP · CPP · Tip-loaded · Skewed · Toroidal · Voith Schneider ·
Podded azimuth.

Not built — aerial: Fixed-pitch · Custom carbon · Collective pitch · eVTOL proprotor · Folding ·
Ducted fan · Coaxial · Q-tip · Toroidal · Serrated · Cyclorotor.
