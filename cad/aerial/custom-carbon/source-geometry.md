# Source geometry — Custom carbon blade

Brief: [aerial_cad.md](../../aerial_cad.md) › *Custom carbon blade*
Model: not built.

## Required

- **Chord/twist CSV solved at the design point** — `SYNTHETIC`
  → [blade-planform.csv](blade-planform.csv). Same column shape a solved JavaProp/QPROP/
  XROTOR/JBLADE table would have, so a real solve drops in without touching downstream code —
  which is what the brief means by "the CSV is the interface". Design point is recorded in
  the header as an assumption, not a solve.
  Feeds: the entire planform — the brief calls this CSV *"the interface"*.
  Source: Solve thrust, rpm, forward speed and air density in JavaProp (https://www.mh-aerotools.de/airfoils/javaprop.htm), QPROP, XROTOR or JBLADE and export. Not OpenProp — that is a marine code and belongs in the underwater briefs.
  Without it: *"the script regenerates the blade from any well-formed chord/twist CSV without edits"* has nothing to regenerate from, and the design point is not recorded anywhere.

- **Thin section coordinates, `t/c` 12% root to 7% tip** — `SYNTHETIC`
  The `t_c` column of [blade-planform.csv](blade-planform.csv) carries the schedule; scale
  [../fixed-pitch/clark-y.csv](../fixed-pitch/clark-y.csv) to it. Trailing edge stays **sharp** —
  the 1 mm floor elsewhere in this repo is a wet-specific marine rule and does not apply.
  Feeds: sections thinner than moulded plastic, with a sharp trailing edge.
  Source: UIUC airfoil coordinates — https://m-selig.ae.illinois.edu/ads/coord_database.html
  Without it: the thin-section premise of a carbon blade is asserted rather than built.

## Inherits

Nothing.
