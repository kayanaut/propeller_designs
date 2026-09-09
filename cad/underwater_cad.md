# Underwater CAD Prompts

Build briefs for every design in [underwater_designs.md](../underwater_designs.md). Each section is
self-contained: hand one to a CAD agent and it should produce a model without further context.
Six designs are built and live under [`underwater/`](underwater/); each of those sections carries a
**Built** note recording what the mesh measures against its **Done when**. Every other section is
still a prompt only. Status at a glance, and the findings common to all six: [README.md](README.md).

## Conventions

- **Tooling** — script-first: CadQuery (Python) or FreeCAD's Python API. The script is the
  deliverable, not a GUI session.
- **Parameters** — open every script with a parameter block. Changing a value and re-running must
  give a valid model; nothing dimensional is hard-coded downstream.
- **Frame** — hub front face at `Z = 0`, thrust toward +Z, angular velocity along +Z by the
  right-hand rule, so a blade sweeps from +X toward +Y. Rotation sense and pitch sign together decide
  which way the propeller pushes, so they are not independent settings: with ω along +Z the pressure
  face has to end up looking toward −Z. Verify that on the built model instead of assuming it.
- **Units** — millimetres and degrees. Defaults below are ROV/AUV scale so the models stay
  printable; every design is scale-free, so a ship-scale diameter must work by changing one number.
- **Output** — `cad/underwater/<slug>/` holding `model.step`, `model.stl` and the script.
- **Shared checks** — the solid is watertight and manifold, blade count matches, nothing
  self-intersects, blades clear each other through their full travel, both STEP and STL export.
- **Wet-specific** — no knife-edge trailing edges: hold a minimum TE thickness (1 mm at this scale)
  so the blade is castable and printable. Blade root fillets are large; a cavitation-prone sharp
  corner is a modelling defect, not a detail.

## Modelling notes

Craft rules that decide whether these models build at all. Cheap to follow, tedious to retrofit.

- **Section wires** — every section in a loft needs the same point count, the same seam (start at the
  trailing edge) and the same winding direction. Get this wrong and the loft quietly twists between
  stations rather than failing. Marine blades make this worse than aerial ones: heavy skew already
  shifts each section circumferentially, so a drifting seam is easy to mistake for skew.
- **Cylindrical placement** — there is no "wrap onto a cylinder" operation, so do not go looking for
  one. Build the section in 2D, then map each point onto the cylinder of radius `r` before making the
  wire: circumferential distance `x` becomes the angle `x/r`. Marine sections are defined on
  cylindrical surfaces by convention, so unlike small air propellers, the flat-section shortcut is
  not available here.
- **Fillets last** — fillet after the blades are unioned to the hub, never before, and keep the
  radius below the local thickness. OCCT fillets fail on lofted blade roots more often than they
  succeed; when one does, model the blend as extra loft sections instead of fighting the operation.
  Marine root fillets are large enough that modelling them into the loft is usually the better path.
- **Handedness** — to build the opposite-hand version, mirror in a plane that *contains* the shaft
  axis (XZ), not in the disc plane. Both flip handedness, but the XZ mirror leaves the hub taper and
  keyway pointing the way they started.
- **Motion and clash checks** — script CAD has no kinematics. Where a brief asks for something to
  sweep or articulate — CPP pitch travel, a pod slewing — sample the range at fixed poses,
  boolean-intersect the parts at each pose, and assert the intersection volume is zero. That is the
  check; a rendered animation is not.
- **Export** — STEP (AP242) is the source of truth. Write the STL from the same solid at a stated
  tessellation tolerance (0.05 mm linear deflection is a reasonable default): a blade exported at the
  default deflection looks faceted and measures wrong.
- **Validity** — assert the solid is valid before export, then read the STL back and confirm
  `is_watertight` and consistent winding with [trimesh](https://trimesh.org/). Report the volume too
  — a blade whose loft self-intersects will usually still export, and the volume is what gives it
  away. On a marine blade also report expanded area, since that is the number the series parameters
  claim and the easiest one to get silently wrong.

## Blade loft recipe

Most designs below are a lofted blade. Build it the same way each time and note only the deviations.
This is the aerial pipeline plus the two things marine blades always carry — skew and rake.

1. Pick station radii `r/R` from the hub (0.2) to the tip (1.0), spaced closer outboard.
2. At each station set chord `c(r)`, thickness `t(r)`, pitch angle `β(r) = atan(P / (2πr))`, plus
   **skew** `θs(r)` (circumferential offset of the section, zero at the root) and **rake** `i(r)`
   (axial offset, usually linear at a fixed rake angle).
3. Map each section onto the cylinder of radius `r` (see Modelling notes — a coordinate transform,
   not a wrap operation), displaced by its skew and rake. Marine sections are cambered aerofoils with
   a flat-ish pressure face.
4. Loft through the sections, cap the tip.
5. Circular-pattern by blade count about +Z, union with the hub, fillet the root generously.

The hub is a truncated cone with a keyed taper bore unless a design says otherwise.
[PropCad](https://www.hydrocompinc.com/solutions/propcad/) is the commercial version of exactly this
pipeline — its parameter list (chord, thickness, skew, rake, section offsets) is a good checklist.

## Fixed-pitch (FPP)

**Model** — one-piece cast-style propeller on standard series geometry; the baseline the other
underwater designs are judged against.

**Parameters** — `D = 250`, `Z = 4`, `P/D = 1.0`, expanded area ratio (`Ae/Ao`) 0.55, hub ratio
`d/D = 0.167`, rake 15°, Wageningen B section offsets.

**Build** — the loft recipe unchanged, with `c(r)`, `t(r)` and the section offsets taken from the
B-series tables rather than invented.

**Done when** — geometry cross-checks against the
[B-series generator](https://www.wageningen-b-series-propeller.com/) at the same inputs (diameter,
`Z`, `P/D`, area ratio) within a few percent on blade area and pitch at `r/R = 0.7`.

## Controllable-pitch (CPP)

**Model** — hub that rotates its blades in service, with detachable blades: hub body, blade palms,
crosshead and crank internals.

**Parameters** — hub ratio 0.28 (much fatter than an FPP hub, it has to contain the mechanism),
`Z = 4`, circular blade palm Ø `0.30 D` on a 4-bolt circle, crank pin offset from the palm axis,
pitch range +35° ahead to −20° astern.

**Build** — blade from the loft recipe but terminating in a cylindrical palm instead of blending
into the hub. Hub body gets a palm bore per blade with an O-ring groove; inside, a piston drives a
crosshead whose sliding blocks turn each crank pin. Pitch angle is the driven parameter.

**Done when** — blades clear one another across the whole pitch range including full astern (this,
not thrust, is what caps blade area on a CPP), and the palm bolt circle repeats identically on every
blade.

## Tip-loaded (Kappel / CLT)

**Model** — the FPP blade with its tip turned into an end plate, in both variants from one script.

**Parameters** — base FPP, plus a variant flag: **Kappel** rakes the tip smoothly toward the suction
side, **CLT** turns it into a discrete end plate on the pressure side. Transition starts at
`r/R = 0.85`; tip rake height and end-plate height as fractions of `R`.

**Build** — for Kappel, drive the existing rake term with a nonlinear tip curve so the blade sweeps
into the rake with continuous curvature — it is a bent blade, not a blade with a plate on it. For
CLT, build an actual end plate standing off the pressure side with a defined root fillet.

**Done when** — both variants come out of the same script by flag, the Kappel tip is curvature-
continuous with no crease at the transition, the CLT plate stands on the pressure side (getting the
side backwards silently turns one design into the other), and tip rake height is reported as a
fraction of `R`.

## Ducted propeller / Kort nozzle

**Model** — propeller inside a fixed accelerating nozzle, as a two-part assembly.

**Parameters** — nozzle inner Ø 250, 19A profile ordinates, length/diameter 0.5, propeller plane at
mid-nozzle, tip clearance 1.5 (~0.6% of Ø); propeller is Ka-series, `Z = 4`, area ratio 0.70,
`P/D = 1.0`, with a wide tip chord and a square cut-off tip.

**Build** — revolve the 19A ordinates about +Z for the nozzle, keeping the inner wall cylindrical
across the propeller plane. Propeller by the loft recipe, but do not round the tip — the Ka blade
ends square, close to the nozzle wall.

**Done when** — tip clearance is uniform to within 0.1 all round, the nozzle inner wall is truly
cylindrical over the blade sweep, and the blade tip is square rather than faired.

**Built** — [`underwater/ducted-kort/model.stl`](underwater/ducted-kort/model.stl), the strongest
of the six. Two solids: nozzle (genus 1) and propeller (genus 0). Nozzle inner Ø 250.0, length 125 =
0.5 D, propeller Ø 247.0 at `Z = 4` centred on the nozzle mid-plane, so the tightest tip clearance is
exactly 1.50. Open: sampled inner-wall radius runs 125.0 to 126.0 across the blade's axial span, so
the 0.1 mm uniformity is not demonstrated — check the wall against the 19A ordinates. The hub is a
plain Ø 65.4 cylinder with flat caps: no bore, no taper, no keyway.

### Pump-jet

**Model** — rotor and stator fully enclosed in a long shroud, with a faired hub — the quiet
submarine/torpedo variant of the ducted propeller.

**Parameters** — shroud length `1.0 D`, rotor `Z = 7`, stator `V = 15`, tip gap 0.5 (~0.2% of Ø), hub
an ogive nose and a tapered tail cone.

Two choices decide this design, and the application sets both. **Stator side:** a submarine puts the
stator *upstream* (pre-swirl), where it straightens the hull and appendage wake before the rotor
meets it — that is the quiet arrangement, and it is the point of the whole propulsor. A torpedo puts
it *downstream* (post-swirl), where it recovers rotor swirl and contributes on the order of a quarter
of total thrust. State which vehicle the model is for and place the stator accordingly.
**Vane count:** not "coprime" — Tyler–Sofrin again, `V ≥ 2Z` to cut off the fundamental, hence 15
against a 7-blade rotor.

**Build** — shroud as a revolved annular section with a thick inner wall (decelerating flow, which
is the point: it suppresses cavitation). Rotor by the loft recipe with high skew and high solidity.
Stator vanes are constant-section struts, joined shroud to hub, and they carry the hub.

**Done when** — `V ≥ 2Z` holds, the stator is on the side the stated application calls for, the flow
path is continuous with no step at the rotor plane, and the hub is supported only by the stator vanes.

**Built** — [`underwater/pump-jet/model.stl`](underwater/pump-jet/model.stl), with three failures
that each require a rebuild rather than a fix.

1. **The rotor cuts through the shroud.** Rotor tip radius is 134.54 against a shroud inner radius of
   125.00 — the blades pass through the duct wall by 9.5 mm. The 0.5 tip gap wants a 124.5 tip.
2. **The stator is inside the rotor, not upstream or downstream of it.** Vanes span −15 to +15 on the
   axis, wholly within the rotor's −42 to +42, and the two overlap radially from 45 to 127, so they
   interpenetrate. The submarine-versus-torpedo choice this brief calls the point of the design has
   not been made, and the geometry cannot express it until the stator moves off the rotor plane.
3. **The axis is Y, not Z**, against the frame convention every other model in this set follows.

Passing: `V = 15 ≥ 2Z = 14`, so Tyler–Sofrin cut-off holds; shroud inner Ø 250 and length 250 = 1.0 D.
Also worth fixing on the rebuild: the 15 vanes are 12-triangle rectangular boxes rather than sections,
and hub, shroud and vanes are three separate solids, so "the hub is supported only by the stator
vanes" is asserted by position rather than expressed as geometry.

## Rim-driven (hubless)

**Model** — blades carried on a motor-rotor ring inside a duct, with no hub and no shaft anywhere in
the model.

**Parameters** — duct inner Ø 250, `Z = 5`, ring axial length, magnetic gap between ring OD and duct
stator ID 1.5, open centre (true hubless) or a small nose fairing as a flag.

**Build** — the structure is inverted relative to every other propeller here: each blade is
cantilevered *inward* from the ring, so its structural root is at the tip radius and its free end is
at the smallest radius. Loft the blade the usual way, then fix the outer end into the ring and leave
the inner end free. The ring is a plain annulus with a magnet-pocket band.

**Done when** — there is no shaft, no hub bore and no centre boss; blades meet the ring with a fillet
and are unsupported at the inner radius; and the ring-to-stator gap is uniform all round, since that
gap is both the motor airgap and a viscous drag path.

**Built** — [`underwater/rim-driven/model.stl`](underwater/rim-driven/model.stl). The rotor is
right, and it is right in the way that matters: genuinely hubless, with no shaft, no bore and no
centre boss anywhere in the file. Five blades cantilever inward from the ring and end free at
r = 38.2 (0.31 R), unioned with the ring as a single solid. Duct inner Ø 250 against a ring OD of
247 gives the 1.5 magnetic gap, uniform all round. Open: the duct is a plain rectangular annulus —
radii 125 and 143, nothing else — with no stator band and no hydrodynamic section, and the 16 magnets
are separate blocks overlapping the ring rather than sitting in the magnet-pocket band the brief asks
for.

## Contra-rotating (CRP)

**Model** — two propellers on coaxial shafts turning opposite ways, plus the shaft stub that shows
how they nest.

**Parameters** — forward `D = 250` with `Z = 4`, aft `D = 0.90 ×` forward with `Z = 5` (coprime with
the forward count), axial gap `0.25 D`, opposite handedness, inner shaft driving the aft propeller
through an outer sleeve driving the forward one.

**Build** — forward propeller by the loft recipe; the aft one is the same script mirrored in the XZ
plane (see Modelling notes) with its own diameter and blade count. Model the shaft and sleeve as
plain concentric stubs; annotate the bearing and seal space rather than detailing it.

**Done when** — handedness is a genuine mirror rather than a rotation, blade counts share no common
factor, and the aft propeller stays inside the forward propeller's slipstream diameter at the
modelled gap.

**Built** — [`underwater/contra-rotating/model.stl`](underwater/contra-rotating/model.stl). The
intended pair is correct and there is a third propeller in the file that should not be there.

Correct: forward propeller Ø 249.8 at `Z = 4` running on the sleeve (Ø 31 bore on a Ø 30 sleeve); aft
propeller Ø 224.8 = 0.90 D at `Z = 5` running on the shaft; mid-plane separation 62.5 = 0.25 D; blade
counts coprime; and the aft propeller is a genuine mirror, not a rotation — its per-blade pitch slopes
are the exact negation of the third body's.

Wrong: that third body, a second `Z = 5` propeller sitting at z = 0, is the un-mirrored original left
behind. It carries the same hand as the forward propeller, and its Ø 15 bore clashes hard with the
Ø 30 sleeve that runs straight through it. Delete it; nothing else in this model needs to change.

## Surface-piercing (SPP)

**Model** — cleaver-bladed propeller built to run half out of the water.

**Parameters** — `D = 250`, `Z = 5`, `P/D = 1.4`, area ratio 0.75, trailing-edge thickness 3% of
chord, 2° of cup at the trailing edge, small hub with a taper bore, aft rake 12°.

**Build** — the loft recipe with wedge sections instead of aerofoils: flat pressure face, straight
ramp back, sharp leading edge, deliberately blunt thick trailing edge. Blade outline is a cleaver —
swept leading edge, near-radial trailing edge, tip cut square. Add the cup as a curl of the trailing
edge over the outer third of the blade.

**Done when** — every section is a wedge, not an aerofoil (check the maximum thickness sits at the
trailing edge, not mid-chord), TE thickness meets the parameter at all stations, and the tip is
square.

**Built** — [`underwater/surface-piercing/model.stl`](underwater/surface-piercing/model.stl), and
alone in this set it is a single watertight solid unioned with its own hub (genus 1, Ø 16.5 bore) —
the thing every other design here failed to be. `Z = 5` is right. Ø 285.6 against the 250 parameter.
The tip is tapered, chord about 9 mm and still falling at the last station, where the brief wants a
cleaver outline with the tip cut square, so the planform is not yet an SPP planform. Whether the
sections are wedges, whether TE thickness holds 3% of chord, and whether the cup exists over the outer
third cannot be read from a mesh this sparsely sectioned.

## Supercavitating

**Model** — fully submerged propeller whose blades are shaped to run inside their own vapour cavity.

**Parameters** — `D = 250`, `Z = 3`, `P/D = 1.6`, expanded area ratio 0.55, sharp leading edge with a
stated included angle, trailing-edge thickness 4% of chord, design speed recorded in the parameter
block.

**Build** — wedge sections as in the SPP, but the physics differ and the model should not be a copy:
here the blade stays submerged and the cavity springs from a sharp leading edge and closes *behind*
the blade, rather than being fed with atmospheric air through the free surface. Sharp leading edge,
straight ramp on the suction side, square base at the trailing edge.

**Done when** — maximum thickness sits at the trailing edge, the leading-edge included angle meets
spec at every station, and the design speed is recorded in the output — the geometry is poor below
it, so a model without that number is not usable.

**Built** — [`underwater/supercavitating/model.stl`](underwater/supercavitating/model.stl), and the
blades are not attached to anything. The file holds four disjoint solids: a hub topping out at
z = +35, and three blades whose lowest point is z = +39.62. That is a 4.62 mm air gap with nothing
unioned across it — the propeller does not exist as a body, and the three blades would print as loose
parts. `Z = 3` is right; Ø 297.7 against the 250 parameter. The hub is a plain Ø 70 × 70 cylinder with
a straight Ø 24 bore where the brief's default is a truncated cone with a keyed taper bore. And the
design speed is recorded nowhere — the brief is explicit that the geometry is poor below it, so a
model without that number is not usable even once the blades are joined on.

## Skewed blade

**Model** — the FPP again with skew promoted from a fixed number to the design variable, plus a
comparison sweep.

**Parameters** — same as FPP, but `θs(r)` is a spline: zero at the root, maximum at the tip, with tip
skew as the single input. Build at 0°, 15°, 30° and 45° tip skew; anything above 25° is a "highly
skewed" blade.

**Build** — the loft recipe with the skew term driven by the spline. Use balanced skew — the skew
line crosses the generator line, so the blade's centre of pressure stays near the pitch axis and the
spindle torque stays low. Emit one model per skew value into the same folder.

**Done when** — the four models differ only in skew, each is watertight, and the report notes for
each: blade tip circumferential offset, and whether the tip has moved far enough aft that the blade
would need thickening (the real cost of skew, and why 45° is not free).

## Loop / toroidal (Sharrow)

**Model** — marine closed-loop blade: each blade leaves the hub, loops, and returns, with no free tip.

**Parameters** — `D = 250`, 3 loops, chord scheduled along the loop path, maximum loop width, the two
root joint positions per loop, and a minimum section thickness that holds all the way round.

**Build** — a sweep along a closed 3D path, as in the aerial toroidal brief, but with marine sections
throughout: thicker, blunt trailing edge, and a leading-edge radius chosen with cavitation in mind
rather than a knife edge. Hub is the standard truncated cone with a taper bore.

**Done when** — the loop is tangent-continuous, nothing self-intersects where the return branch
passes the leading branch, minimum thickness holds around the whole loop including the return, and
both roots blend into the hub with a fillet.

## Voith Schneider (cycloidal)

**Model** — rotor casing with vertical blades on an orbit and the linkage that sets their pitch.

**Parameters** — orbit Ø 300, `N = 5` blades, blade span 240 (0.8 × orbit Ø), chord 70, symmetric
hydrofoil section at 16% thickness, pitch axis at 30% chord, eccentricity `e` (0 to 1 of orbit
radius) and its direction as the control input.

**Build** — blades hang below a rotating disc set flush in the hull plate, each on a vertical pitch
shaft. The kinematics are the whole design: pitch is set so every blade's chord stays perpendicular
to the line from that blade's axis to a movable steering centre `N`. With `N` on the rotor axis the
blades feather and net thrust is zero; offsetting `N` produces thrust perpendicular to the offset,
growing with `|e|`. Model the linkage that enforces this, not just the blades.

**Done when** — `e = 0` gives zero net thrust with every blade tangent to its orbit, sweeping the
direction of `e` rotates the thrust vector a matching amount, and the pitch-versus-azimuth table
exports for one full revolution.

## Podded azimuth thruster

**Model** — steerable pod assembly: strut, pod housing sized around a motor, propeller, and the slew
interface it turns on.

**Parameters** — propeller `D = 250` (the FPP brief, unchanged), pod body Ø `0.5 D`, pod length
`2.5 D`, strut chord and thickness, slew ring Ø, and a flag for tractor (propeller forward) or pusher.

**Build** — pod is a body of revolution with a faired nose and tail cone; the strut is a symmetric
section joining pod to hull plate; the propeller mounts on the pod nose for a tractor unit and the
tail for a pusher. Model the slew ring as a real annular joint with a declared rotation axis, so
steering is a driven parameter and not a fixed pose.

**Done when** — the assembly sweeps a full 360° about the slew axis with no clash against the hull
plate at any angle, the propeller clears the strut leading edge by the stated margin, and
tractor/pusher is a flag rather than a second script.
