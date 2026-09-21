# Formulas

The working equations, and the datum each one assumes. This repository uses these
quantities in the briefs, the tables and the CFD reports; this is where they are defined.

Where a formula is already implemented in the repository, the code is named. If the two
ever disagree, the code is what produced the numbers.

## Symbols and units

SI throughout. The geometry tables are in **mm** because that is what a CAD kernel and a
printer want; every formula below wants **metres**, so divide by 1000 first. This is the
single most common arithmetic mistake in propeller work.

| | | |
|---|---|---|
| `D` | diameter | m (tables: mm) |
| `R` | tip radius, `D/2` | m |
| `r` | radius of a blade station | m |
| `r/R` | non-dimensional radius | — |
| `c` | chord at a station | m |
| `P` | pitch — **face pitch**, see below | m |
| `Z` | number of blades | — |
| `n` | rotation rate — **revolutions per second, not rpm** | rev/s |
| `V` | speed of advance (inflow, not boat speed) | m/s |
| `T`, `Q` | thrust, shaft torque | N, N·m |
| `ρ` | density — 1025 kg/m³ seawater (the value in the CFD case), 1000 fresh, 1.225 air | kg/m³ |
| `ν` | kinematic viscosity — ≈1.05×10⁻⁶ m²/s seawater, 1.5×10⁻⁵ air | m²/s |
| `p_v` | vapour pressure of water — ≈2.3 kPa at 20 °C | Pa |

**`n` in rev/s is the trap.** Every coefficient below is defined on rev/s. Feeding it rpm
puts `Kt` out by 3600.

## Geometry ratios

The tables are published as ratios of diameter, which is exactly what lets you build the
same design at any size.

| Quantity | Formula | Notes |
|---|---|---|
| Pitch ratio | `P/D` | The number that defines how coarse a propeller is. Meaningless without its datum. |
| Non-dimensional radius | `r/R` | Blade stations run from the hub ratio out to 1.0. |
| Chord ratio | `c/D` | |
| Hub ratio | `d_hub/D` | 0.265 for this repo's ducted Kort, 0.28 for its CPP, 0.2 for DTMB 4119. |
| Expanded area ratio | `Ae/Ao = (2Z/π) ∫ (c/D) d(r/R)` | Also written BAR. Implemented as `ear()` in [cad/tools/check-geometry.py](cad/tools/check-geometry.py). |

`Ae/Ao` is an **integral**, which is why this repository's checkers do not rely on it: you
can starve the root, inflate the mid-span, and still hit the target area ratio with a blade
that is wrong. Check the distribution, not its integral.

## Pitch angle

```
β(r) = atan( P / (2πr) )
```

`β` is the angle the section is set at, and it falls off along the blade because the same
axial advance is spread over a longer circumference.

**The datum matters more than the formula.** `P` here is **face pitch** — the pitch line
through the *pressure* side of the section — which is what the Ka tables and APC's quoted
pitch use. Applying the same angle to the *chord* line instead gives a different propeller,
by degrees, on any cambered section. See [cad/CONVENTIONS.md](cad/CONVENTIONS.md).

Substituting `P = (P/D)·D` and `r = (r/R)·(D/2)`:

```
β = atan( (P/D) / (π · r/R) )
```

**`D` cancels.** At a constant `P/D`, the blade angle at a given `r/R` is the same at every
diameter — which is why a table of ratios can be built at any size, and why
`build_ducted_kort.py --diameter` only has to scale lengths.

## Operating point

| Quantity | Formula | Notes |
|---|---|---|
| Advance ratio | `J = V / (n·D)` | How far the propeller advances per turn, relative to its diameter. |
| Bollard condition | `J = 0` | Static: no inflow. The condition an ROV thruster or a tug at full pull actually works in, and the one where a duct helps most. |
| Advance angle | `atan( J / (π · r/R) )` | Compare with `β` above: the difference is roughly the angle of attack. |

DTMB 4119 in this repository is specified at its design `J = 0.833`
([dtmb4119.csv](cad/underwater/fixed-pitch/dtmb4119.csv)).

## Thrust, torque and efficiency

```
Kt = T / (ρ n² D⁴)
Kq = Q / (ρ n² D⁵)
η₀ = (J / 2π) · (Kt / Kq)
```

These three against `J` are what an **open-water curve** plots, and what the
[ITTC procedure](https://www.ittc.info/media/9621/75-02-03-021.pdf) standardises. Curves
almost always plot `10·Kq`, so that it shares an axis with `Kt` — read the axis label
before reading a value.

`η₀` is *open-water* efficiency: the propeller alone, in uniform inflow. It says nothing
about the hull in front of it.

At the bollard condition `J = 0`, so `η₀ = 0` by definition. **A static thruster has no
open-water efficiency**, and quoting one is a category error. Use thrust per watt instead:

```
T / P_shaft        where  P_shaft = 2π n Q
```

This repository's toroidal thruster reports 29.1 N at 130 W shaft, i.e. 0.225 N/W — an
unvalidated CFD number, but the right *kind* of number for a static thruster.

## Speeds

| Quantity | Formula | Notes |
|---|---|---|
| Tip speed | `π n D` | |
| Resultant speed at a station | `W = √( V² + (2π n r)² )` | At bollard, `V = 0`, so `W = 2π n r`. |
| Blade Reynolds number | `Re = c·W / ν`, taken at `r/R = 0.75` | 0.75R is the conventional reference station. |
| Tip Mach number | `π n D / a`, `a ≈ 343 m/s` in air | The aerial briefs cap this near 0.55 ([cad/aerial_cad.md](cad/aerial_cad.md)). |

Reynolds number is why **geometry scales but performance does not**. Halve the diameter at
the same rpm and you halve the tip speed and quarter the Reynolds number; the sections are
then working in a different regime, and a section that was efficient may stall.

## Cavitation

```
σ = (p₀ − p_v) / (½ ρ V²)
```

`p₀` is the local absolute pressure — atmospheric plus `ρgh` at depth `h`. For propellers
the reference speed is often taken as `nD` rather than `V`, giving `σ_n = (p₀ − p_v)/(½ρn²D²)`;
state which one you mean.

Cavitation begins where the **local** pressure on the blade falls to `p_v`. In a CFD result
reported as gauge pressure, that threshold is roughly `p_v − p_atm ≈ −99 kPa` at the
surface, and it moves down by about 10 kPa per metre of depth. So a minimum wall pressure
of −180 kPa gauge implies vapour unless you are deeper than about 8 m — which is exactly
how the toroidal thruster's cavitation margin was read.

Thin, uncambered sections at high angle of attack produce the sharpest suction peaks. That
is a geometry decision, not an operating one.

## Rules of thumb worth knowing

- **Bigger and slower beats smaller and faster.** For a given thrust, efficiency rises with
  diameter. Gear down before you speed up.
- **Thrust goes roughly as `n²`, power as `n³`.** Ten percent more rpm is about 21% more
  thrust and 33% more power.
- **Tip clearance is a fraction of diameter, not a fixed gap.** 1.5 mm is 0.6% of a 250 mm
  propeller and 1.5% of a 100 mm one. In a duct, that gap is a leak.
- **A duct pays at low `J` and costs at high `J`.** Tugs, trawlers and ROV thrusters gain;
  a fast open boat loses.
