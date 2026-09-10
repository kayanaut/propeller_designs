# Source geometry — Custom carbon blade

Brief: [aerial_cad.md](../../aerial_cad.md) › *Custom carbon blade*
Model: not built.

## Required

- **Chord/twist CSV solved at the design point** — `NOT SOURCED`
  Feeds: the entire planform — the brief calls this CSV *"the interface"*.
  Source: Solve thrust, rpm, forward speed and air density in JavaProp (https://www.mh-aerotools.de/airfoils/javaprop.htm), QPROP, XROTOR or JBLADE and export. Not OpenProp — that is a marine code and belongs in the underwater briefs.
  Without it: *"the script regenerates the blade from any well-formed chord/twist CSV without edits"* has nothing to regenerate from, and the design point is not recorded anywhere.

- **Thin section coordinates, `t/c` 12% root to 7% tip** — `NOT SOURCED`
  Feeds: sections thinner than moulded plastic, with a sharp trailing edge.
  Source: UIUC airfoil coordinates — https://m-selig.ae.illinois.edu/ads/coord_database.html
  Without it: the thin-section premise of a carbon blade is asserted rather than built.

## Inherits

Nothing.
