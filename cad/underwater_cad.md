# Underwater CAD Prompts

Build briefs for every design in [underwater_designs.md](../underwater_designs.md). Each section is
self-contained: hand one to a CAD agent and it should produce a model without further context.
Nothing here has been built yet — these are the prompts.

## Conventions

- **Tooling** — script-first: CadQuery (Python) or FreeCAD's Python API. The script is the
  deliverable, not a GUI session.
- **Parameters** — open every script with a parameter block. Changing a value and re-running must
  give a valid model; nothing dimensional is hard-coded downstream.
- **Frame** — shaft axis is +Z, thrust toward +Z, hub face on the origin. Right-hand rotation unless
  a design says otherwise.
- **Units** — millimetres and degrees. Defaults below are ROV/AUV scale so the models stay
  printable; every design is scale-free, so a ship-scale diameter must work by changing one number.
- **Output** — `cad/underwater/<slug>/` holding `model.step`, `model.stl` and the script.
- **Shared checks** — the solid is watertight and manifold, blade count matches, nothing
  self-intersects, blades clear each other through their full travel, both STEP and STL export.
- **Wet-specific** — no knife-edge trailing edges: hold a minimum TE thickness (1 mm at this scale)
  so the blade is castable and printable. Blade root fillets are large; a cavitation-prone sharp
  corner is a modelling defect, not a detail.

## Blade loft recipe

Most designs below are a lofted blade. Build it the same way each time and note only the deviations.
This is the aerial pipeline plus the two things marine blades always carry — skew and rake.

1. Pick station radii `r/R` from the hub (0.2) to the tip (1.0), spaced closer outboard.
2. At each station set chord `c(r)`, thickness `t(r)`, pitch angle `β(r) = atan(P / (2πr))`, plus
   **skew** `θs(r)` (circumferential offset of the section, zero at the root) and **rake** `i(r)`
   (axial offset, usually linear at a fixed rake angle).
3. Lay each section on the cylinder of radius `r` — wrapped, not flat — displaced by its skew and
   rake. Marine sections are cambered aerofoils with a flat-ish pressure face.
4. Loft through the sections, cap the tip.
5. Circular-pattern by blade count about +Z, union with the hub, fillet the root generously.

The hub is a truncated cone with a keyed taper bore unless a design says otherwise.
[PropCad](https://www.hydrocompinc.com/solutions/propcad/) is the commercial version of exactly this
pipeline — its parameter list (chord, thickness, skew, rake, section offsets) is a good checklist.

## Fixed-pitch (FPP)

**Model** — one-piece cast-style propeller on standard series geometry; the baseline the other
underwater designs are judged against.

**Parameters** — `D = 250`, `Z = 4`, `P/D = 1.0`, blade area ratio 0.55, hub ratio `d/D = 0.167`,
rake 15°, Wageningen B section offsets.

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

### Pump-jet

**Model** — rotor and stator fully enclosed in a long shroud, with a faired hub — the quiet
submarine/torpedo variant of the ducted propeller.

**Parameters** — shroud length `1.0 D`, rotor `Z = 7`, stator `V = 9` (no common factor with `Z`,
which is what keeps the blade-passing tones from reinforcing), stator downstream of the rotor
(post-swirl), tip gap 0.5 (~0.2% of Ø), hub an ogive nose and a tapered tail cone.

**Build** — shroud as a revolved annular section with a thick inner wall (decelerating flow, which
is the point: it suppresses cavitation). Rotor by the loft recipe with high skew and high solidity.
Stator vanes are constant-section struts, joined shroud to hub, and they carry the hub.

**Done when** — rotor and stator counts share no common factor, the flow path is continuous with no
step at the rotor plane, and the hub is supported only by the stator vanes.

## Contra-rotating (CRP)

**Model** — two propellers on coaxial shafts turning opposite ways, plus the shaft stub that shows
how they nest.

**Parameters** — forward `D = 250` with `Z = 4`, aft `D = 0.90 ×` forward with `Z = 5` (coprime with
the forward count), axial gap `0.25 D`, opposite handedness, inner shaft driving the aft propeller
through an outer sleeve driving the forward one.

**Build** — forward propeller by the loft recipe; the aft one is the same script mirrored about the
XY plane with its own diameter and blade count. Model the shaft and sleeve as plain concentric
stubs; annotate the bearing and seal space rather than detailing it.

**Done when** — handedness is a genuine mirror rather than a rotation, blade counts share no common
factor, and the aft propeller stays inside the forward propeller's slipstream diameter at the
modelled gap.

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
