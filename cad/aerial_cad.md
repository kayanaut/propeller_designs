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
- **Frame** — hub front face at `Z = 0`, thrust toward +Z, angular velocity along +Z by the
  right-hand rule, so a blade sweeps from +X toward +Y. Rotation sense and twist sign together decide
  which way the propeller pushes, so they are not independent settings: with ω along +Z the pressure
  face has to end up looking toward −Z. Verify that on the built model instead of assuming it.
- **Units** — millimetres and degrees.
- **Output** — `cad/aerial/<slug>/` holding `model.step`, `model.stl` and the script.
- **Shared checks** — the solid is watertight and manifold, blade count matches, nothing
  self-intersects, blades clear each other through their full travel, both STEP and STL export. See
  Modelling notes for how to actually check each of these.

## Modelling notes

Craft rules that decide whether these models build at all. Cheap to follow, tedious to retrofit.

- **Section wires** — every section in a loft needs the same point count, the same seam (start at the
  trailing edge) and the same winding direction. Get this wrong and the loft quietly twists between
  stations rather than failing.
- **Cylindrical placement** — there is no "wrap onto a cylinder" operation, so do not go looking for
  one. Build the section in 2D, then map each point onto the cylinder of radius `r` before making the
  wire: circumferential distance `x` becomes the angle `x/r`. On small propellers a flat section
  placed tangentially is a fair simplification — if you take it, say so in the script.
- **Fillets last** — fillet after the blades are unioned to the hub, never before, and keep the
  radius below the local thickness. OCCT fillets fail on lofted blade roots more often than they
  succeed; when one does, model the blend as extra loft sections instead of fighting the operation.
- **Handedness** — to build the opposite-hand version, mirror in a plane that *contains* the rotation
  axis (XZ), not in the disc plane. Both flip handedness, but the XZ mirror leaves the hub and its
  mounting face pointing the way they started.
- **Motion and clash checks** — script CAD has no kinematics. Where a brief asks for something to
  sweep, fold or articulate, sample the range at fixed poses, boolean-intersect the parts at each
  pose, and assert the intersection volume is zero. That is the check; a rendered animation is not.
- **Export** — STEP (AP242) is the source of truth. Write the STL from the same solid at a stated
  tessellation tolerance (0.05 mm linear deflection is a reasonable default): a blade exported at the
  default deflection looks faceted and measures wrong.
- **Validity** — assert the solid is valid before export, then read the STL back and confirm
  `is_watertight` and consistent winding with [trimesh](https://trimesh.org/). Report the volume too
  — a blade whose loft self-intersects will usually still export, and the volume is what gives it
  away.

## Blade loft recipe

Most designs below are a lofted blade. Build it the same way each time and note only the deviations.

1. Pick station radii `r/R` from the hub joint (~0.15) to the tip (1.0), spaced closer outboard.
2. At each station set chord `c(r)`, thickness ratio `t/c`, and twist `β(r) = atan(P / (2πr))` for a
   constant-pitch blade — quoted pitch is the value at `r/R = 0.75`.
3. Scale the section airfoil to `c`, rotate it by `β`, and map it onto the cylinder of radius `r`
   (see Modelling notes — this is a coordinate transform, not a wrap operation).
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

**Build** — solve the design point in [JavaProp](https://www.mh-aerotools.de/airfoils/javaprop.htm),
QPROP, XROTOR or JBLADE for `c(r)` and `β(r)`, write that to CSV, and have the script loft from the
CSV. The CSV is the interface: a new design point is a new table, not a new script. Do not reach for
OpenProp here — it is a marine lifting-line code, and it belongs in the underwater briefs.

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

## eVTOL proprotor

**Model** — a rigid blade with no cyclic that has to work as a rotor in hover and as a propeller in
wing-borne cruise, tilting between the two.

**Parameters** — `D = 1500`, `Z = 5`, two design points rather than one (hover: high thrust, advance
ratio ≈ 0; cruise: high advance ratio at reduced rpm), tip Mach capped around 0.55 because tip speed
sets the noise, and a blend weight that says which point the twist favours.

**Build** — solve both design points, then reconcile them: the script ingests two chord/twist tables
and blends to one geometry at the blend weight. That compromise is the entire design problem here —
a blade optimal in hover is badly pitched in cruise and the other way round, so the blend weight must
stay a live input, not a number baked into the loft.

**Done when** — the one geometry is evaluated at both design points and the run reports thrust and
efficiency at each, tip Mach stays under the cap at hover rpm, and changing the blend weight visibly
moves the twist distribution.

## Folding blade

**Model** — two blades on clevis hinges in the hub, trailing back when unpowered.

**Parameters** — hinge pin Ø 3, hinge offset from the rotation axis 10, root tang thickness 3, fold
range 0–175°, deployed stop face on the hub.

**Build** — blade as fixed-pitch but ending in a tang instead of a root fillet; hub is a clamp with
two jaws and a pin bore per blade. Emit deployed and folded as two configurations of one script.

**Done when** — the blade's centre of mass sits outboard of the hinge pin, so spinning up deploys the
blade and holds it against the stop (get this wrong and the prop never opens); folded blades clear
each other, the motor bell and the arm; deployed stop faces meet flat with their contact area
reported; the pin bore is a clearance fit on the pin.

## Ducted fan

**Model** — rotor, duct, stator and motor pod as one assembly.

**Parameters** — fan Ø 90, rotor `Z = 5`, stator `V = 11`, hub ratio 0.45, tip clearance 0.4 (~0.5%
of Ø), duct inlet lip radius 6, exit nozzle area 85% of swept area.

Vane count is not a matter of picking something coprime. The Tyler–Sofrin rule sets it: `V ≥ 2Z`
cuts off the fundamental blade-passing tone so it never propagates down the duct, and `V ≥ 4Z` holds
that through the second harmonic. With `Z = 5` the floor is 10, hence 11 — see
[NASA's low-noise fan design methods](https://ntrs.nasa.gov/api/citations/20230003262/downloads/20230003262%20REV%20FINAL.pdf).

**Build** — rotor by the loft recipe but high-solidity and thin-sectioned; duct is an annular
airfoil revolved about +Z, running cylindrical across the rotor plane; stator vanes sit downstream
and carry the pod; pod holds the motor bore.

**Done when** — tip clearance is uniform to within 0.05 all round, exit area ratio matches the
parameter, and `V ≥ 2Z` holds.

## Coaxial contra-rotating

**Model** — two rotors on one axis turning opposite ways, plus the mounting stack.

**Parameters** — `D = 254` on both, axial spacing `h = 0.12 D`, upper right-hand and lower
left-hand, with the lower rotor's pitch exposed separately since it works in the upper rotor's wake.

Size the stack against what a coaxial pair actually delivers, not double a single rotor: the lower
rotor's inflow is the upper's downwash, induced power climbs steeply as spacing shrinks, and the
pair lands well short of 2× thrust at equal power.

**Build** — build the upper rotor with the loft recipe; the lower is the same script mirrored in the
XZ plane (see Modelling notes — mirroring in the disc plane also flips handedness, but turns the hub
around with it) and given its own pitch value. Stack them on a common axis at the spacing parameter.

**Done when** — handedness is a genuine mirror rather than a rotation, spacing stays a live
parameter, and the two discs never intersect across the spacing range.

## Tip device (Q-tip)

**Model** — a conventional blade with the outer span curled aft into an inverted winglet.

**Parameters** — base blade from Fixed-pitch, bend starting at `r/R = 0.92`, bend angle 75° aft,
bend radius 8, tip cap.

**Build** — loft the straight blade first, then carry the outer sections around the bend by sweeping
along a curved spanwise path. Bend the geometry; do not cut a bent tip off and glue it on, or chord
and thickness will step at the joint.

**Done when** — chord and thickness run continuous through the bend with no kink, and the run reports
the projected (swept-disc) diameter alongside the developed one — the bent tip shrinks the disc, and
that reduction is the ground-clearance and tip-noise trade being bought.

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

## Serrated edge

**Model** — a fixed-pitch blade with saw-tooth serrations along the trailing edge, optionally the
leading edge too.

**Parameters** — base blade from Fixed-pitch, serration amplitude and wavelength as a ratio of local
chord, applied over `r/R = 0.5` to the tip, saw-tooth or sinusoidal profile, and a flag for
leading-edge serrations.

**Build** — build the base blade, then apply the serration along the edge curve *in the blade's own
surface*, following the twist — not as a cut through a flat plane, which would bite deeper at the
root than at the tip.

**Done when** — serrations appear only in the specified radial band, the solid is still watertight
after the boolean, amplitude and wavelength are parametric, and the plain unserrated blade is
exported alongside it so the pair can be compared on a thrust stand.

## Cyclorotor

**Model** — drum of straight vertical blades with a cyclic pitch linkage.

**Parameters** — orbit radius 75, blade span 150, chord 26 (`c/R ≈ 0.35`), `Z = 4`, symmetric NACA
0015 section, pitch axis at 30% chord, pitch amplitude ±35°, eccentricity `e` as the control input.
Keep `c/R` visible as a derived value: push much past 0.4 and the blade sees enough flow curvature
across its own chord that its effective camber no longer matches the section you drew.

**Build** — constant-section blades extruded to span, pivoting between two end discs. Each blade arm
links to a common eccentric point offset `e` from the rotor axis, so pitch cycles once per
revolution. Expose the eccentric as magnitude and direction — that pair is the thrust vector command.

**Done when** — one revolution produces the expected pitch-versus-azimuth curve (export it as a
table), blades clear the end discs and each other, and `e = 0` gives zero pitch amplitude.
