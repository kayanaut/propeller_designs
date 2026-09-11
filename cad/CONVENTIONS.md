# Geometry Conventions

Definitions the build briefs leave implicit. **Only what is missing** — frame, units, section seam,
point count, winding, cylindrical placement, fillets-last and handedness are already defined in
[underwater_cad.md](underwater_cad.md) § Conventions and § Modelling notes, and are not restated here.

Every geometry CSV carries these as a declaration block in its header, so a script author reading one
table never has to come back here to interpret it.

## Pitch datum — FACE pitch

`P` is the **face pitch**: the pitch of the pitch line through the **pressure side** of the section.
`β(r) = atan(P / (2πr))` rotates the section about that line, not about its chord line.

Not a preference — it is what the repo's real data already uses:

- The Ka-series offsets in [underwater/ducted-kort/ka-sections.csv](underwater/ducted-kort/ka-sections.csv)
  are stated by their source as "referenced to the pitch line through the **pressure side** of the blade".
- APC's `pitch_quoted_in` in [aerial/fixed-pitch/apc-10x5e.csv](aerial/fixed-pitch/apc-10x5e.csv) is
  defined "with a flat bottom surface" — face pitch for a flat-bottomed section such as Clark-Y.

APC publish three pitch columns per station because the definitions genuinely disagree. Use
`pitch_quoted_in`. Using `pitch_le_te_in` instead changes blade angle by degrees, which is a different
propeller.

## Generator line — mid-chord marine, leading edge aerial

The generator line is the radial line the sections are placed and rotated about. It differs by domain
because the source data differs, so **every file declares its own**:

| Domain | Generator line | Why |
|---|---|---|
| Marine | 50% chord (mid-chord) | standard marine blade-reference-line practice |
| Aerial | leading edge | APC define sweep and rake "with (mold) LE parting line" |

Move the generator line and the whole blade moves. It is not a detail.

## Rake — generator-line rake only

`rake_z_D` is **generator-line rake**: the axial offset of the generator line itself. It does **not**
include skew-induced rake.

Total rake = generator rake + skew-induced rake, where the skew-induced part is what the section
picks up axially by being displaced along the pitch helix. A build script must add it when placing
sections. On a highly skewed blade the two are comparable in size — at DTMB 4384's 108° tip skew,
treating `rake_z_D` as total rake misplaces the tip axially by more than the rake itself.

## Skew — circumferential angle of the generator point

`skew_deg` is the angular displacement of the section's generator point from the straight radial
reference, positive opposite to the direction of rotation (blades sweep back). Measured in the disc
plane as an angle, not as an arc length along the pitch helix.

## Camber — `f_c` is maximum camber over local chord

`f_c` = maximum camber / local chord, of the mean line. Combined with `t_c` (or `t_D`) it completes
the section: **pitch sets the angle the section meets the flow, camber sets the lift it makes at that
angle.** A table with chord, thickness and pitch but no camber does not define a section.

Wedge designs — `supercavitating` and `surface-piercing` — carry **no** `f_c` on purpose. A
supercavitating wedge has a flat pressure face and a straight suction ramp; it has no mean-line
camber, and adding one would make it a different section family.

## Root fillet — `fillet_r_D`

Fillet radius over the blade-to-hub blend, as a fraction of `D`, zero outboard of the blend region.
It sits in the planform tables beside `t_D` so the brief's rule — *"keep the radius below the local
thickness"* — is checkable in one line rather than across two files.

`cad/underwater_cad.md` § Modelling notes says OCCT fillets fail on lofted blade roots more often than
they succeed, and to model the blend as extra loft sections instead. This column is that schedule.

## Hub

`hub.csv` per design: truncated cone, keyed taper bore. `rim-driven` has **none** and must not acquire
one — it is hubless by definition, with the blades cantilevered inward from the motor ring. `pump-jet`
(ogive nose and tail cone), `voith-schneider` (rotor casing) and `podded-azimuth` (pod body) use other
forms and likewise take no taper-bore hub.
