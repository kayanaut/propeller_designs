# Aerial CAD Prompts

Build briefs for every design in [aerial_designs.md](../aerial_designs.md). Each section is
self-contained: hand one to a CAD agent and it should produce a model without further context.
Nothing here has been built yet — these are the prompts.

## Conventions

- **Tooling** — script-first: CadQuery (Python) or FreeCAD's Python API. OpenSCAD is fine where a
  part is pure primitives, as [bladegen](https://github.com/tallakt/bladegen) already does. The
  script is the deliverable, not a GUI session.
- **Parameters** — open every script with a parameter block. Changing a value and re-running must
  give a valid model; nothing dimensional is hard-coded downstream.
- **Frame** — rotation axis is +Z, thrust toward +Z, hub face on the origin. Right-hand rotation
  unless a design says otherwise.
- **Units** — millimetres and degrees.
- **Output** — `cad/aerial/<slug>/` holding `model.step`, `model.stl` and the script.
- **Shared checks** — the solid is watertight and manifold, blade count matches, nothing
  self-intersects, blades clear each other through their full travel, both STEP and STL export.

## Blade loft recipe

Most designs below are a lofted blade. Build it the same way each time and note only the deviations.

1. Pick station radii `r/R` from the hub joint (~0.15) to the tip (1.0), spaced closer outboard.
2. At each station set chord `c(r)`, thickness ratio `t/c`, and twist `β(r) = atan(P / (2πr))` for a
   constant-pitch blade — quoted pitch is the value at `r/R = 0.75`.
3. Scale the section airfoil to `c`, rotate it by `β`, wrap it onto the cylinder of radius `r`.
4. Loft through the sections and cap the tip.
5. Circular-pattern by blade count about +Z, union with the hub, fillet the root joint (1–2 mm).

Take real chord and twist distributions from the
[UIUC database](https://m-selig.ae.illinois.edu/props/propDB.html) rather than inventing a planform;
APC publish blade offsets directly as
[`.peo` files](https://www.apcprop.com/technical-information/file-downloads/).

## Fixed-pitch (low-Re)

**Model** — one-piece two-blade propeller; the baseline the other aerial designs are judged against.

**Parameters** — `D = 254` (10 in), `P = 127` (5 in), `Z = 2`, hub Ø 12, bore Ø 5, root at
`r/R = 0.15`, Clark-Y or Eppler E63 sections, `t/c` 14% at the root tapering to 9% at the tip, chord
peaking near `r/R = 0.6`.

**Build** — the loft recipe unchanged, with `c(r)` and `β(r)` lifted from a UIUC entry of the same
nominal size.

**Done when** — pitch measured back off the model at `r/R = 0.75` is within 2% of `P`, and the bore
is concentric with the rotation axis.

## Custom carbon blade

**Model** — a blade whose planform comes from a design point rather than a catalogue size, with a
cylindrical root shank for clamping.

**Parameters** — design point first (thrust, rpm, forward speed, air density), then `Z`, `D`, shank
Ø 8 and shank length 15. Sections thinner than moulded plastic: `t/c` 12% root to 7% tip, sharp
trailing edge.

**Build** — solve the design point in [JavaProp](https://www.mh-aerotools.de/airfoils/javaprop.htm)
or [OpenProp](https://www.epps.com/openprop) for `c(r)` and `β(r)`, write that to CSV, and have the
script loft from the CSV. The CSV is the interface: a new design point is a new table, not a new
script.

**Done when** — the script regenerates the blade from any well-formed chord/twist CSV without edits,
and the shank is a true cylinder over its clamped length.

### Collective pitch

**Model** — hub that changes blade pitch in flight: blade grips on bearings, pitch horns, links, and
a collar sliding on the shaft.

**Parameters** — shank Ø 8, two bearing bores per grip, pitch horn offset 6, collar travel ±4,
pitch range ±25° about the `r/R = 0.75` setting.

**Build** — reuse the custom carbon blade with its shank. Yoke carries pitch-axis bores normal to
+Z; each grip gets a horn; links run from horn to collar; collar position drives pitch.

**Done when** — sweeping `collar_z` covers the full pitch range with no link-to-hub interference at
either stop, and blades stay clear of one another at maximum pitch.

## Folding blade

**Model** — two blades on clevis hinges in the hub, trailing back when unpowered.

**Parameters** — hinge pin Ø 3, hinge offset from the rotation axis 10, root tang thickness 3, fold
range 0–175°, deployed stop face on the hub.

**Build** — blade as fixed-pitch but ending in a tang instead of a root fillet; hub is a clamp with
two jaws and a pin bore per blade. Emit deployed and folded as two configurations of one script.

**Done when** — folded blades clear each other, the motor bell and the arm; deployed stop faces meet
flat with their contact area reported; the pin bore is a clearance fit on the pin.

## Ducted fan

**Model** — rotor, duct, stator and motor pod as one assembly.

**Parameters** — fan Ø 90, rotor `Z = 5`, stator `V = 7` (coprime with `Z`, which spreads the tonal
noise), hub ratio 0.45, tip clearance 0.4 (~0.5% of Ø), duct inlet lip radius 6, exit nozzle area
85% of swept area.

**Build** — rotor by the loft recipe but high-solidity and thin-sectioned; duct is an annular
airfoil revolved about +Z, running cylindrical across the rotor plane; stator vanes sit downstream
and carry the pod; pod holds the motor bore.

**Done when** — tip clearance is uniform to within 0.05 all round, exit area ratio matches the
parameter, and rotor and stator counts share no common factor.

## Coaxial contra-rotating

**Model** — two rotors on one axis turning opposite ways, plus the mounting stack.

**Parameters** — `D = 254` on both, axial spacing `h = 0.12 D`, upper right-hand and lower
left-hand, with the lower rotor's pitch exposed separately since it works in the upper rotor's wake.

**Build** — build the upper rotor with the loft recipe; the lower is the same script mirrored about
the XY plane with its own pitch value. Stack them on a common axis at the spacing parameter.

**Done when** — handedness is a genuine mirror rather than a rotation, spacing stays a live
parameter, and the two discs never intersect across the spacing range.

## Toroidal

**Model** — closed-loop blade with no free tip.

**Parameters** — `D = 254`, two or three loops, chord scheduled along the loop path, maximum loop
width, and the two root joint positions per loop.

**Build** — a sweep, not a radial loft. Define the closed 3D path (out along the leading branch,
over the top, back along the trailing branch, into the hub), then sweep the airfoil along it with
chord and twist scheduled by path parameter, holding the section frame so it cannot flip. Start from
the [toroidal generator](https://github.com/RaulBejarano/Ultimate-Toroidal-Propeller-Generator)
rather than a blank file.

**Done when** — the loop is tangent-continuous, nothing self-intersects where the return branch
passes the leading branch, and both root ends blend into the hub with a fillet.

## Cyclorotor

**Model** — drum of straight vertical blades with a cyclic pitch linkage.

**Parameters** — orbit radius 75, blade span 150, chord 40, `Z = 4`, symmetric NACA 0015 section,
pitch axis at 30% chord, pitch amplitude ±35°, eccentricity `e` as the control input.

**Build** — constant-section blades extruded to span, pivoting between two end discs. Each blade arm
links to a common eccentric point offset `e` from the rotor axis, so pitch cycles once per
revolution. Expose the eccentric as magnitude and direction — that pair is the thrust vector command.

**Done when** — one revolution produces the expected pitch-versus-azimuth curve (export it as a
table), blades clear the end discs and each other, and `e = 0` gives zero pitch amplitude.
