#!/usr/bin/env python3
"""Generate every GENERATED and SYNTHETIC geometry table in cad/underwater/.

Two kinds of output, and the distinction is the point of this script:

  GENERATED  computed from a published equation (NACA four-digit). Exact and
             re-derivable by anyone with the same equation.
  SYNTHETIC  created here from the parameters the design's own brief states.
             Defensible parametric design work, but NOT measured data and NOT
             from any published series. Every such file says so in its header.

Nothing here is transcribed from a source; transcribed tables are committed by
hand with their citation. Run from anywhere:  python3 cad/tools/make-geometry.py
Deterministic: re-running rewrites byte-identical files.
"""
import math, os, io

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "underwater")
ROOT = os.path.normpath(ROOT)
GEN = "cad/tools/make-geometry.py"

DECL = ("# FRAME  hub front face Z=0, thrust +Z, omega +Z right-hand. See cad/underwater_cad.md Conventions.\n"
        "# UNITS  mm, degrees. r_R = r/R. c_D = c/D. See cad/CONVENTIONS.md.\n"
        "# PITCH  FACE pitch (pitch line through the PRESSURE side). beta = atan(P/(2*pi*r)).\n"
        "# AXIS   generator line at 50% chord (marine); sections placed and rotated about it.\n"
        "# RAKE   generator-line rake ONLY - skew-induced rake NOT included; add it when placing.\n"
        "# WIRE   seam at TE, constant point count, CCW seen from +Z. See Modelling notes.")

# Measured camber distribution of DTMB 4119 (f/c by r/R), from the real blade committed at
# cad/underwater/fixed-pitch/dtmb4119.csv. Used as the SHAPE reference for synthetic camber,
# the same way its chord distribution is used for synthetic chord.
_DTMB4119_FC = [(0.20,0.01429),(0.30,0.02318),(0.40,0.02303),(0.50,0.02182),
                (0.60,0.02072),(0.70,0.02003),(0.80,0.01967),(0.90,0.01817),
                (0.95,0.01631),(1.00,0.01175)]

def camber(r, hub, scale=1.0):
    """f/c at r/R, following the DTMB 4119 measured distribution, scaled."""
    u=(r-hub)/(1-hub); rr=0.20+0.80*u
    return _interp([a for a,_ in _DTMB4119_FC],[b for _,b in _DTMB4119_FC], rr)*scale

def fillet(r, hub, blend=0.30, r_root=0.020):
    """Root fillet radius / D. Large at the root, tapering to zero at the end of the
    blend region. Marine root fillets are large; the brief calls a sharp corner there a
    modelling defect. Held below local thickness - check-geometry.py asserts it."""
    u=(r-hub)/(1-hub)
    if u>=blend: return 0.0
    return r_root*(1-u/blend)**1.5

def write(slug, name, header, cols, rows):
    path = os.path.join(ROOT, slug, name)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(header.rstrip("\n") + "\n#\n" + DECL + "\n")
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(f"{v:.6f}" if isinstance(v, float) else str(v) for v in r) + "\n")
    print(f"  {slug}/{name}  ({len(rows)} rows)")

# ---------------------------------------------------------------- NACA 4-digit
# Wet-specific rule from cad/underwater_cad.md Conventions:
#   "no knife-edge trailing edges: hold a minimum TE thickness (1 mm at this scale)
#    so the blade is castable and printable."
# D_REF is the scale that rule is quoted at. Everything below honours it.
D_REF = 250.0
TE_MIN_MM = 1.0

def naca4_thickness(x, t, closed=True, te_mm=None, chord_mm=None):
    """NACA four-digit half-thickness. closed=True uses the -0.1036 coefficient so
    y_t(1)=0 exactly; a finite TE is then added deliberately via te_mm rather than
    left as the open-form's arbitrary 0.00168 residue."""
    c4 = -0.1036 if closed else -0.1015
    y = 5*t*(0.2969*math.sqrt(x) - 0.1260*x - 0.3516*x*x + 0.2843*x**3 + c4*x**4)
    if te_mm and chord_mm:                    # blunt linearly toward the TE
        y += (te_mm/2.0/chord_mm)*x
    return y

def naca4_camber(x, m, p):
    if m == 0: return 0.0, 0.0
    if x < p: return m/p**2*(2*p*x - x*x), 2*m/p**2*(p - x)
    return m/(1-p)**2*((1-2*p) + 2*p*x - x*x), 2*m/(1-p)**2*(p - x)

def cosine(n):
    return [(1 - math.cos(math.pi*i/n))/2 for i in range(n+1)]

def naca4(code, n=80, chord_mm=None, te_mm=TE_MIN_MM):
    m = int(code[0])/100; p = int(code[1])/10; t = int(code[2:])/100
    if p == 0: p = 0.1
    out = []
    for x in cosine(n):
        yt = naca4_thickness(x, t, True, te_mm, chord_mm)
        yc, dyc = naca4_camber(x, m, p)
        th = math.atan(dyc)
        out.append((x, yt, yc,
                    x - yt*math.sin(th), yc + yt*math.cos(th),
                    x + yt*math.sin(th), yc - yt*math.cos(th)))
    return out, m, p, t

EQ = ("#   y_t = 5t(0.2969*sqrt(x) - 0.1260x - 0.3516x^2 + 0.2843x^3 - 0.1015x^4)\n"
      "# Abbott & von Doenhoff, 'Theory of Wing Sections' (Dover, 1959), Sec. 6.4.\n"
      "# Closed form (-0.1036), then blunted to a finite TE. x,y are fractions of chord.")

def naca_header(code, role, m, p, t, chord_mm):
    return (f"# NACA {code} - GENERATED BY {GEN}\n#\n"
            f"# Computed from the published NACA four-digit equations, not transcribed:\n{EQ}\n"
            f"# max camber m={m:.4f} at p={p:.2f}, thickness t={t:.4f}\n#\n"
            f"# Role: {role}\n#\n"
            f"# TRAILING EDGE IS BLUNTED, deliberately. The classic open-TE form leaves an\n"
            f"# arbitrary ~0.17% residue - at this chord that is a knife edge, and the underwater\n"
            f"# brief forbids it: 'hold a minimum TE thickness (1 mm at this scale) so the blade is\n"
            f"# castable and printable.' So the closed form (-0.1036) is used and {TE_MIN_MM} mm of TE is\n"
            f"# added linearly over a {chord_mm:.0f} mm chord. Scale the chord and the TE scales with it.\n"
            f"# Exact and re-derivable. Regenerate rather than edit.")

print("GENERATED (published equations):")
for slug, name, code, role, chord_mm in [
    ("voith-schneider", "naca0016.csv", "0016",
     "symmetric hydrofoil for the VSP blade, 16% thick, pitch axis at 30% chord per the brief.", 70.0),
    ("podded-azimuth", "naca0015-strut.csv", "0015",
     "symmetric section for the pod-to-hull strut. Brief specifies a symmetric strut section.", 60.0),
    ("pump-jet", "stator-vane-naca4412.csv", "4412",
     "CAMBERED stator vane. The built model's vanes are 12-triangle flat boxes, which turn no "
     "flow; a stator must be cambered to recover rotor swirl. 4412 is a four-digit stand-in for "
     "the NACA 65-series a stator would normally use - 65-series ordinates are tabulated, not "
     "equation-derived, so they cannot be generated here.", 30.0),
]:
    pts, m, p, t = naca4(code, chord_mm=chord_mm)
    write(slug, name, naca_header(code, role, m, p, t, chord_mm),
          ["x_c","y_t","y_camber","x_upper","y_upper","x_lower","y_lower"],
          [(a,b,c,d,e,f,g) for a,b,c,d,e,f,g in pts])

# ------------------------------------------------------- SYNTHETIC: wedge sections
def wedge(te_thick, n=40):
    """Supercavitating/ventilating wedge: flat pressure face, straight suction ramp
    from a sharp LE to maximum thickness AT the trailing edge."""
    return [(x, 0.0, te_thick*x) for x in [i/n for i in range(n+1)]]

SC_TE = 0.04           # brief: TE thickness 4% of chord
SC_SPEED = 45.0        # knots - see header
sc_angle = math.degrees(math.atan(SC_TE))
write("supercavitating", "wedge-sections.csv",
f"""# Supercavitating wedge section - SYNTHETIC, GENERATED BY {GEN}
#
# NOT Newton-Rader data. NOT from any published supercavitating series. Newton & Rader
# (Trans. RINA 103, 1961) is the real source and is paywalled; this is a parametric stand-in
# built from the numbers the brief itself states, so a model can be built and checked.
#
# Determined by the brief: sharp leading edge, straight suction-side ramp, maximum thickness
# at the TRAILING edge, TE thickness = {SC_TE:.0%} of chord. Pressure face is flat (y=0).
# Consequence, not an input: a straight ramp to {SC_TE:.0%} at the TE gives a leading-edge
# included angle of atan({SC_TE}) = {sc_angle:.4f} deg. If a different LE angle is wanted the
# ramp must become convex - change it here, do not fudge the table.
#
# DESIGN SPEED = {SC_SPEED:.0f} knots. The brief calls recording this mandatory - "the geometry
# is poor below it, so a model without that number is not usable" - and it was recorded
# nowhere. It is an ASSUMPTION made here to make the design well-posed, not a measurement.
# Change it and the section family should change with it.
#
# Section is constant in form across radius; scale by local chord.
# x_c from 0 (sharp LE) to 1 (TE). y_pressure is the flat face; y_suction the ramp.""",
      ["x_c","y_pressure","y_suction"], wedge(SC_TE))

# --------------------------------------------- SYNTHETIC: SPP cleaver planform
# --- shared blade-fit helpers, defined before their first use ---------------
def _area(xs, cs, Z):
    return 2*Z/math.pi*sum((cs[i]+cs[i+1])/2*(xs[i+1]-xs[i]) for i in range(len(cs)-1))

FIT_MAX = 0.95        # fraction of the local circumference Z blades may occupy
def enforce_fit(xs, cs, betas, Z, EAR, fit_max=FIT_MAX):
    """Cap chord so Z blades physically FIT round the disc, holding Ae/Ao.

    Blades occupy Z * c * cos(beta) of the 2*pi*r circumference at each radius. Let that
    exceed 1.0 and adjacent blades interfere - which is not a tolerance issue, it is two
    solids in the same place, and a boolean union of them collapses to zero volume.

    Ae/Ao cannot see this. It is an EXPANDED area ratio: it integrates chord without ever
    asking whether the chord fits round the hub. Three designs in this repo overlapped at
    the root while sitting exactly on their area-ratio target.

    Applies to OPEN propellers only. A ducted cascade (pump-jet rotor, EDF rotor) runs
    solidity above 1.0 on purpose - staggered blades in a duct do not intersect - so it
    is exempt, and its clearance is settled by a solid-intersection test instead.

    Same machinery as enforce_tc: pin the stations that violate the cap, then scale the
    rest by a single exact factor, and iterate because scaling can push a free station over.
    """
    cs = list(cs)
    def cap(i):
        # c/D <= fit_max * pi * (r/R) / (Z * cos(beta))
        return fit_max*math.pi*xs[i]/(Z*max(math.cos(math.radians(betas[i])), 1e-6))
    for _ in range(200):
        fixed = {i: cap(i) for i in range(len(cs)) if cs[i] > cap(i)}
        for i, v in fixed.items(): cs[i] = v
        if abs(_area(xs, cs, Z) - EAR) < 1e-12: break
        free = [i for i in range(len(cs)) if i not in fixed]
        if not free: break
        pinned = [cs[i] if i in fixed else 0.0 for i in range(len(cs))]
        loose  = [0.0 if i in fixed else cs[i] for i in range(len(cs))]
        A_pin, A_free = _area(xs, pinned, Z), _area(xs, loose, Z)
        if A_free <= 1e-12: break
        f = (EAR - A_pin)/A_free
        if f <= 0: break
        for i in free: cs[i] *= f
    return cs, _area(xs, cs, Z)

SPP_PD = 1.4      # brief: P/D 1.4, used only to check the blades fit round the disc
SPP = dict(Z=5, EAR=0.75, D=250.0, hub=0.20, rake_deg=12.0, cup_deg=2.0, te_thick=0.03)
def cleaver_planform(n=17):
    """Cleaver: swept LE, near-radial TE, chord still wide at a square-cut tip.
    Chord shape is a schedule; it is then scaled so the expanded-area ratio hits
    the brief's EAR exactly, which makes the table checkable rather than drawn."""
    hub, Z, EAR = SPP["hub"], SPP["Z"], SPP["EAR"]
    xs = [hub + (1-hub)*i/(n-1) for i in range(n)]
    # shape: grows outboard, stays wide at the tip (cleaver), never zero -> square tip
    shape = [0.45 + 0.95*((r-hub)/(1-hub))**0.75 - 0.28*((r-hub)/(1-hub))**4 for r in xs]
    # Ae/Ao = (2Z/pi) * integral of (c/D) d(r/R)  -> scale to hit EAR
    integ = sum((shape[i]+shape[i+1])/2*(xs[i+1]-xs[i]) for i in range(n-1))
    k = EAR*math.pi/(2*Z*integ)
    rows = []
    for i, r in enumerate(xs):
        c_D = k*shape[i]
        # LE swept back, TE near-radial: skew angle grows outboard, TE held ~constant
        skew = 32.0*((r-hub)/(1-hub))**1.6
        rake = math.tan(math.radians(SPP["rake_deg"]))*r
        cup = SPP["cup_deg"] if r >= hub + (1-hub)*2/3 else 0.0
        rows.append((r, c_D, skew, rake, SPP["te_thick"], cup, fillet(r, hub)))
    ach = 2*SPP["Z"]/math.pi*sum((rows[i][1]+rows[i+1][1])/2*(xs[i+1]-xs[i]) for i in range(n-1))
    return rows, ach
spp_rows, spp_ear = cleaver_planform()
# SPP blades are steeply pitched cleavers; check they fit before anything else uses them.
_sx = [r[0] for r in spp_rows]
_sb = [math.degrees(math.atan(SPP_PD/(math.pi*max(r,1e-6)))) for r in _sx]
_sc, spp_ear = enforce_fit(_sx, [r[1] for r in spp_rows], _sb, SPP["Z"], SPP["EAR"])
spp_rows = [(r[0], _sc[i]) + tuple(r[2:]) for i, r in enumerate(spp_rows)]
write("surface-piercing", "cleaver-planform.csv",
f"""# Surface-piercing CLEAVER planform - SYNTHETIC, GENERATED BY {GEN}
#
# NOT Rolla, NOT Mercury Bravo, NOT Newton-Rader. Production cleaver geometry is commercial
# and unpublished; this is a parametric stand-in from the brief's own parameters.
#
# WHY IT EXISTS: the built model's tip tapers to ~9 mm chord and keeps falling, where a
# cleaver ends SQUARE. This table is what a rebuild should follow - note c_D is still large
# at r_R = 1.0 and does not go to zero. That is the defining cleaver feature.
#
# From the brief: Z = {SPP['Z']}, target Ae/Ao = {SPP['EAR']}, D = {SPP['D']:.0f} mm,
#   hub ratio {SPP['hub']}, aft rake {SPP['rake_deg']} deg, TE thickness {SPP['te_thick']:.0%}
#   of chord, {SPP['cup_deg']} deg cup over the outer third (cup_deg is 0 inboard of r_R 0.467).
# The chord schedule is scaled so the expanded-area ratio hits the target:
#   achieved Ae/Ao = {spp_ear:.4f} against {SPP['EAR']} requested.
# skew_deg sweeps the LEADING edge back while the trailing edge stays near-radial.
# rake_z_D is aft rake as a fraction of D. Sections are wedges - see wedge-sections.csv.""",
      ["r_R","c_D","skew_deg","rake_z_D","te_thick_c","cup_deg","fillet_r_D"], spp_rows)
write("surface-piercing", "wedge-sections.csv",
f"""# Surface-piercing wedge section - SYNTHETIC, GENERATED BY {GEN}
#
# NOT from any published series. Same construction as the supercavitating wedge but a
# DIFFERENT design: this blade ventilates through the free surface at {SPP['te_thick']:.0%} TE
# thickness, rather than running submerged inside its own vapour cavity. Do not interchange
# the two files just because the shapes look alike - the briefs are explicit about this.
#
# Flat pressure face, straight ramp from a sharp LE to max thickness at the TE.
# LE included angle = atan({SPP['te_thick']}) = {math.degrees(math.atan(SPP['te_thick'])):.4f} deg.
# The 2 deg cup over the outer third is applied to the TRAILING EDGE by the planform table,
# not baked into this section.""",
      ["x_c","y_pressure","y_suction"], wedge(SPP["te_thick"]))

# ------------------------------------------- SYNTHETIC: Kappel tip rake (quintic)
def kappel(r0=0.85, rake_deg=15.0, tip_h=0.075, tip_deg=55.0, n=31):
    """Quintic blend: position, slope and curvature continuous at r0, and a
    specified height, tangent and zero curvature at the tip. Six conditions,
    six coefficients - a quintic is the lowest order that satisfies them."""
    y0, s0, c0 = 0.0, math.tan(math.radians(rake_deg))*(1-r0), 0.0
    y1, s1, c1 = tip_h, math.tan(math.radians(tip_deg))*(1-r0), 0.0
    # Hermite quintic on u in [0,1]
    def H(u):
        return ( y0*(1-10*u**3+15*u**4-6*u**5) + s0*(u-6*u**3+8*u**4-3*u**5)
                 + c0/2*(u**2-3*u**3+3*u**4-u**5) + y1*(10*u**3-15*u**4+6*u**5)
                 + s1*(-4*u**3+7*u**4-3*u**5) + c1/2*(u**3-2*u**4+u**5) )
    rows=[]
    for i in range(n+1):
        u=i/n; r=r0+(1-r0)*u
        rows.append((r, u, H(u), math.tan(math.radians(rake_deg))*r))
    return rows
write("tip-loaded", "kappel-tip-rake.csv",
f"""# Kappel tip-rake curve - SYNTHETIC, GENERATED BY {GEN}
#
# NOT MAN's Kappel geometry and NOT Sistemar's CLT. Both are proprietary and no tip-rake law
# is published; searching 2026-09-10 produced nothing tabulated. This is a curve constructed
# to satisfy the brief's stated requirement, which is the honest alternative to guessing.
#
# METHOD: quintic Hermite blend on r_R in [0.85, 1.0]. Six boundary conditions -
#   at r_R=0.85: height 0, slope matching the 15 deg linear rake, curvature 0
#   at r_R=1.00: height 0.075*R toward the SUCTION side, tangent 55 deg, curvature 0
# A quintic is the lowest polynomial order that can meet all six, which is exactly what the
# brief's 'curvature-continuous with no crease at the transition' demands. Curvature is
# continuous BY CONSTRUCTION here - that Done-when is satisfied by the method, not by luck.
#
# tip_rake_R is the rake height as a fraction of R, the number the brief asks be reported.
# rake_linear_R is the underlying 15 deg linear rake for comparison inboard of the blend.
# For the CLT variant this file does NOT apply: CLT is a discrete end plate on the PRESSURE
# side, a different construction. Getting the side backwards turns one design into the other.""",
      ["r_R","u","tip_rake_R","rake_linear_R"], kappel())

# ------------------------------------------------ SYNTHETIC: toroidal loop path
TOR_HUB, TOR_WIDTH, TOR_TIP = 0.20, 42.0, 1.0
def loop_path(n=120, hub=TOR_HUB, width_deg=TOR_WIDTH, tip=TOR_TIP):
    """Closed loop: out along the leading branch, around the tip, back along the
    trailing branch. Tangent-continuous by construction (single smooth harmonic
    parametrisation, no piecewise joins to crease)."""
    rows=[]
    for i in range(n+1):
        s=i/n; a=2*math.pi*s
        r = hub + (tip-hub)*(0.5-0.5*math.cos(a))          # out and back, zero slope at both roots
        th = width_deg*math.sin(a)                          # circumferential excursion
        z = 0.10*(1-math.cos(2*a))/2                        # slight axial arch over the top
        rows.append((s, r, th, z))
    return rows
write("toroidal", "loop-path.csv",
f"""# Marine toroidal (loop) blade path - SYNTHETIC, GENERATED BY {GEN}
#
# NOT Sharrow geometry. Sharrow's loop is patented; the claims describe it but tabulate
# nothing, so no real path is obtainable. This is a parametric closed loop from the brief.
#
# METHOD: single smooth harmonic parametrisation in s over [0,1], closed and periodic, so the
# path is TANGENT-CONTINUOUS by construction - the brief's first Done-when - with no piecewise
# joins that could crease. r returns to the hub with zero radial slope at both root ends.
#   r_R    radius, hub {TOR_HUB} out to the tip and back
#   theta  circumferential offset, max half-width {TOR_WIDTH} deg
#   z_D    axial arch over the top of the loop, as a fraction of D
#
# 3 loops per the brief: replicate this path at 120 deg intervals about the axis.
# NOT CHECKED HERE: that the return branch clears the leading branch. That is a solid-model
# question - sweep the section along the path, then test for self-intersection. A tangent-
# continuous centreline does not by itself guarantee a non-self-intersecting solid.""",
      ["s","r_R","theta_deg","z_D"], loop_path())

# --------------------------------- SYNTHETIC: decelerating duct for the pump-jet
DUCT_L_MM   = 250.0      # shroud length 1.0 D per the brief
THROAT_R_MM = 125.0      # duct ordinates below are fractions of the THROAT RADIUS,
                         # not of duct length - the TE floor must use this scale
def decel_duct(n=41, throat=1.0, exit_r=1.10, inlet_r=1.06, t=0.16):
    """Decelerating (pump-jet) duct: inner wall DIVERGES downstream so flow slows
    through and behind the rotor. Outer wall = inner + a NACA four-digit thickness,
    with a FINITE leading-edge radius and a TE floored at the wet minimum - a duct
    with a knife-edge LE is neither castable nor tolerant of off-design inflow."""
    rows=[]
    le_r = TE_MIN_MM/THROAT_R_MM        # LE radius, in throat-radius units
    for i in range(n):
        x=i/(n-1)
        if x < 0.35:
            u=x/0.35; ri = inlet_r + (throat-inlet_r)*(3*u*u-2*u**3)
        else:
            u=(x-0.35)/0.65; ri = throat + (exit_r-throat)*(3*u*u-2*u**3)
        th = naca4_thickness(max(x,1e-9), t, True, TE_MIN_MM, THROAT_R_MM)
        th = max(th, le_r)                  # rounded nose: never below the wet minimum
        rows.append((x, ri, ri + th))
    return rows
write("pump-jet", "duct-decelerating.csv",
f"""# Decelerating pump-jet duct wall - SYNTHETIC, GENERATED BY {GEN}
#
# NOT 19A and must never be swapped for it. Real 19A ordinates live one folder away in
# ../ducted-kort/duct-19a.csv - 19A is an ACCELERATING duct and is the wrong family here.
# This shroud must DECELERATE the flow: that is what raises static pressure at the rotor and
# suppresses cavitation, which is the entire point of a submarine pump-jet.
# No open decelerating-duct ordinate table was found (searched 2026-09-10).
#
# METHOD: inner wall contracts smoothly to a throat at the rotor plane (x/L = 0.35), then
# DIVERGES to the exit - the defining difference from 19A, whose inner wall is cylindrical
# and never diverges. Smoothstep blends give continuous slope at the throat. Outer wall is
# the inner wall plus a NACA four-digit thickness distribution ({t:.0%}).
# Radii are multiples of the throat radius; scale by the rotor tip radius plus tip gap.
#
# The built model's rotor tip currently overruns the shroud by 9.5 mm. Rebuild the rotor to
# the throat radius here before trusting anything downstream of it.""",
      ["x_L","r_inner_throat","r_outer_throat"], decel_duct())


# =====================================================================
# Blade planforms. Each chord schedule is SCALED to hit the brief's own
# expanded-area ratio, so every table below is checkable against a number
# the brief states rather than being drawn by eye.
# =====================================================================
def scale_to_ear(xs, shape, Z, EAR):
    """Ae/Ao = (2Z/pi) * integral (c/D) d(r/R). Return the scale factor
    that makes the schedule hit EAR exactly, and the achieved value."""
    integ = sum((shape[i]+shape[i+1])/2*(xs[i+1]-xs[i]) for i in range(len(xs)-1))
    k = EAR*math.pi/(2*Z*integ)
    cs = [k*v for v in shape]
    ach = 2*Z/math.pi*sum((cs[i]+cs[i+1])/2*(xs[i+1]-xs[i]) for i in range(len(xs)-1))
    return cs, ach

TC_MAX, TC_FROM = 0.15, 0.70

def enforce_tc(xs, cs, ts, Z, EAR, tc_max=TC_MAX, r_from=TC_FROM):
    """Floor OUTBOARD chord so t/c stays loftable, holding Ae/Ao exactly.

    Two correct rules collide at the tip: the wet-specific 1 mm TE minimum floors
    THICKNESS, while a faired planform following DTMB 4119 takes CHORD to nearly zero
    at r/R = 1.0. Together they gave a tip section as thick as it was long.

    Only stations outboard of r/R = {0} are constrained: a marine blade ROOT genuinely
    runs t/c near 0.20 - DTMB 4119's own root is 0.2055 - so limiting t/c there would
    be wrong. Area is a linear functional of the chord array, so once the floored
    stations are pinned the remaining ones are scaled by a single exact factor to
    recover the area ratio; iterate because scaling can push a free station under its
    own floor.
    """.format(r_from)
    cs = list(cs)
    for _ in range(200):
        fixed = {i: ts[i]/tc_max for i, x in enumerate(xs)
                 if x >= r_from and cs[i] < ts[i]/tc_max}
        for i, v in fixed.items(): cs[i] = v
        if abs(_area(xs, cs, Z) - EAR) < 1e-12: break
        free = [i for i in range(len(cs)) if i not in fixed]
        if not free: break
        pinned = [cs[i] if i in fixed else 0.0 for i in range(len(cs))]
        loose  = [0.0 if i in fixed else cs[i] for i in range(len(cs))]
        A_pin, A_free = _area(xs, pinned, Z), _area(xs, loose, Z)
        if A_free <= 1e-12: break
        f = (EAR - A_pin)/A_free
        if f <= 0: break
        for i in free: cs[i] *= f
    return cs, _area(xs, cs, Z)

def stations(hub, n=17, tip=1.0):
    return [hub + (tip-hub)*i/(n-1) for i in range(n)]

# Real measured chord distribution, read from the one piece of genuine blade
# geometry in this repo: cad/underwater/fixed-pitch/dtmb4119.csv (DTMB 4119).
# Using a measured shape rather than an invented bump is what keeps the synthetic
# blades plausible at the root, where a marine blade must be WIDE - it carries the
# whole bending moment and has to blend into the hub.
_DTMB4119_CD = [(0.20,0.3200),(0.30,0.3625),(0.40,0.4048),(0.50,0.4392),
                (0.60,0.4610),(0.70,0.4622),(0.80,0.4347),(0.90,0.3613),
                (0.95,0.2775),(1.00,0.0000)]

def _interp(xs, ys, x):
    if x <= xs[0]: return ys[0]
    if x >= xs[-1]: return ys[-1]
    for i in range(len(xs)-1):
        if xs[i] <= x <= xs[i+1]:
            f=(x-xs[i])/(xs[i+1]-xs[i]); return ys[i]+f*(ys[i+1]-ys[i])
    return ys[-1]

def blade_shape(xs, hub, tip_style="faired", tip_frac=0.55):
    """Normalised chord shape following DTMB 4119's measured distribution.

    tip_style 'faired'   - closes toward the tip like an open propeller.
    tip_style 'wide_tip' - holds chord at the tip, for a DUCTED rotor or a cleaver,
                           which end square rather than fairing to a point.
    The returned shape is unnormalised; scale_to_ear() sets the absolute level.
    """
    rx=[a for a,_ in _DTMB4119_CD]; ry=[b for _,b in _DTMB4119_CD]
    peak=max(ry)
    out=[]
    for r in xs:
        u=(r-hub)/(1-hub)                       # 0 at the blade root, 1 at the tip
        rr=0.20+0.80*u                          # map onto DTMB's own r/R range
        v=_interp(rx,ry,rr)/peak
        if tip_style=="wide_tip":
            # replace the last 15% fairing with a held chord: a ducted rotor tip is square
            v = max(v, tip_frac)
        out.append(max(v,0.02))
    return out

def pitch_from_PD(r, PD):           # constant-pitch blade
    return math.degrees(math.atan(PD/(math.pi*max(r,1e-6))))

def thickness(r, hub, t_root, t_tip, te_min_D=None):
    """Linear taper, floored so the section's TE clears the wet-specific minimum.
    A max thickness below the floor guarantees a TE below it too."""
    u=(r-hub)/(1-hub)
    t = t_root + (t_tip-t_root)*u
    if te_min_D is None: te_min_D = TE_MIN_MM/D_REF
    return max(t, te_min_D*1.5)      # max thickness >= 1.5x the TE floor

# ------------------------------------------------------- fixed-pitch (FPP)
FPP=dict(D=250.0, Z=4, PD=1.0, EAR=0.55, hub=0.167, rake=15.0, t_root=0.045, t_tip=0.0035)
xs=stations(FPP["hub"]); cs,ach=scale_to_ear(xs, blade_shape(xs,FPP["hub"]), FPP["Z"], FPP["EAR"])
ts=[thickness(r,FPP["hub"],FPP["t_root"],FPP["t_tip"]) for r in xs]
cs,ach=enforce_tc(xs,cs,ts,FPP["Z"],FPP["EAR"])
rows=[(r, cs[i], FPP["PD"], pitch_from_PD(r,FPP["PD"]),
       thickness(r,FPP["hub"],FPP["t_root"],FPP["t_tip"]),
       camber(r,FPP["hub"]),
       math.tan(math.radians(FPP["rake"]))*r, 10.0*((r-FPP["hub"])/(1-FPP["hub"]))**1.5,
       fillet(r,FPP["hub"]))
      for i,r in enumerate(xs)]
write("fixed-pitch","blade-planform.csv",
f"""# Fixed-pitch (FPP) blade planform - SYNTHETIC, GENERATED BY {GEN}
#
# NOT Wageningen B-series. The brief asks for B4-55 offsets; those tables are copyrighted and
# could not be obtained. This is a parametric blade at the brief's OWN parameters, so a model
# can be built and checked - but it is not the B-series and must not be reported as such.
# A real, measured alternative sits alongside in dtmb4119.csv (DTMB 4119, Z=3, no skew).
#
# From the brief: D = {FPP['D']:.0f} mm, Z = {FPP['Z']}, P/D = {FPP['PD']}, Ae/Ao = {FPP['EAR']},
#   hub ratio {FPP['hub']}, rake {FPP['rake']} deg.
# Chord schedule scaled to hit the area ratio: achieved Ae/Ao = {ach:.4f} against {FPP['EAR']}.
# Constant-pitch blade: pitch_deg = atan(P/D / (pi * r/R)), quoted P/D held at every station.
# Modest skew included so the baseline is not degenerate; skewed/ is where skew is the variable.""",
["r_R","c_D","P_D","pitch_deg","t_D","f_c","rake_z_D","skew_deg","fillet_r_D"], rows)

# ------------------------------------------------- supercavitating planform
SC=dict(Z=3, PD=1.6, EAR=0.55, hub=0.20, t_root=0.040, t_tip=0.012)
xs=stations(SC["hub"]); shape=[0.55+0.85*((r-SC["hub"])/(1-SC["hub"]))**0.8
                               -0.30*((r-SC["hub"])/(1-SC["hub"]))**5 for r in xs]
cs,ach=scale_to_ear(xs,shape,SC["Z"],SC["EAR"])
rows=[(r,cs[i],SC["PD"],pitch_from_PD(r,SC["PD"]),
       thickness(r,SC["hub"],SC["t_root"],SC["t_tip"]),0.04,
       18.0*((r-SC["hub"])/(1-SC["hub"]))**1.4, fillet(r,SC["hub"]))
      for i,r in enumerate(xs)]
write("supercavitating","blade-planform.csv",
f"""# Supercavitating blade planform - SYNTHETIC, GENERATED BY {GEN}
#
# NOT Newton-Rader data. Newton & Rader (Trans. RINA 103, 1961) is the real series and is
# paywalled. This is a parametric planform at the brief's own parameters, to pair with the
# wedge sections in wedge-sections.csv.
#
# From the brief: Z = {SC['Z']}, P/D = {SC['PD']}, Ae/Ao = {SC['EAR']}, hub ratio {SC['hub']}.
# Achieved Ae/Ao = {ach:.4f} against {SC['EAR']} requested.
# te_thick_c is held at 4% of chord at every station - the defining supercavitating feature,
# maximum thickness AT the trailing edge. Design speed 45 knots, recorded in wedge-sections.csv.
# The tip does not close to zero chord: a supercavitating blade carries load to the tip.""",
["r_R","c_D","P_D","pitch_deg","t_D","te_thick_c","skew_deg","fillet_r_D"], rows)

# ------------------------------------------------------- skewed: 4-model sweep
SK=dict(Z=5, PD=1.0, EAR=0.725, hub=0.20, t_root=0.045, t_tip=0.0035)
SK_SKEWS=[("DTMB 4381",0.0),("DTMB 4382",36.0),("DTMB 4383",72.0),("DTMB 4384",108.0)]
xs=stations(SK["hub"]); cs,ach=scale_to_ear(xs, blade_shape(xs,SK["hub"]), SK["Z"], SK["EAR"])
ts=[thickness(r,SK["hub"],SK["t_root"],SK["t_tip"]) for r in xs]
cs,ach=enforce_tc(xs,cs,ts,SK["Z"],SK["EAR"])
rows=[]
for name,tipskew in SK_SKEWS:
    for i,r in enumerate(xs):
        u=(r-SK["hub"])/(1-SK["hub"])
        rows.append((name, tipskew, r, cs[i], SK["PD"], pitch_from_PD(r,SK["PD"]),
                     thickness(r,SK["hub"],SK["t_root"],SK["t_tip"]), camber(r,SK["hub"]),
                     tipskew*(u**1.6), fillet(r,SK["hub"])))
write("skewed","skew-sweep.csv",
f"""# Four-propeller skew sweep - SYNTHETIC distributions, REAL skew values.
# GENERATED BY {GEN}
#
# NOT the DTMB 4381-4384 offsets. Those are in NSRDC 3339 (DTIC AD0732511), which was still
# serving a maintenance page when retried on 2026-09-10. The SKEW ANGLES here are the real
# series values; the chord, pitch and thickness distributions are parametric stand-ins.
#
# The brief invents a 0/15/30/45 deg sweep. The real Boswell series is 0/36/72/108 deg, so the
# real values are used. Above 25 deg is a "highly skewed" blade, so three of these four are.
#
# Common to all four: Z = {SK['Z']}, P/D = {SK['PD']}, Ae/Ao = {SK['EAR']} (achieved {ach:.4f}),
#   hub ratio {SK['hub']}. Skew is the ONLY column that differs between propellers - that is the
#   whole point of the series, and verification checks it.
# skew_deg follows a spline: zero at the root, tip value at r/R = 1.0, balanced about the
#   generator line so spindle torque stays low.""",
["propeller","tip_skew_deg","r_R","c_D","P_D","pitch_deg","t_D","f_c","skew_deg","fillet_r_D"], rows)

# --------------------------------------------------- contra-rotating (CRP)
CRP=dict(Df=250.0, Zf=4, Za=5, aft_scale=0.90, PD_f=1.0, EAR=0.55, hub=0.20, gap_D=0.25)
def actuator_disc(PD_f, CT=0.60):
    """First-order: axial induction a from disc loading, a = 0.5(sqrt(1+CT)-1).
    Aft disc sees Va(1+a) axially and Omega*r + swirl tangentially."""
    a = 0.5*(math.sqrt(1+CT)-1)
    return a
a_ind = actuator_disc(CRP["PD_f"])
xs=stations(CRP["hub"])
ts_c=[thickness(r,CRP["hub"],0.045,0.0035) for r in xs]
cs_f,ach_f=scale_to_ear(xs, blade_shape(xs,CRP["hub"]), CRP["Zf"], CRP["EAR"])
cs_f,ach_f=enforce_tc(xs,cs_f,ts_c,CRP["Zf"],CRP["EAR"])
cs_a,ach_a=scale_to_ear(xs, blade_shape(xs,CRP["hub"]), CRP["Za"], CRP["EAR"])
cs_a,ach_a=enforce_tc(xs,cs_a,ts_c,CRP["Za"],CRP["EAR"])
rows=[]
for i,r in enumerate(xs):
    rows.append(("forward", CRP["Zf"], 1.0, r, cs_f[i], ts_c[i], camber(r,CRP["hub"]),
                 CRP["PD_f"], CRP["PD_f"], pitch_from_PD(r,CRP["PD_f"]),
                 fillet(r,CRP["hub"]), "right"))
for i,r in enumerate(xs):
    # aft disc: higher axial inflow -> more pitch; opposite rotation meets the swirl head-on,
    # which raises relative tangential speed and claws some of that back.
    # absolute pitch the actuator-disc model calls for, referenced to the FORWARD diameter
    P_abs = CRP["PD_f"]*(1+a_ind)/(1+0.35*a_ind)
    # ...expressed on the aft disc's OWN (smaller) diameter, which is what P/D means
    PD_a = P_abs/CRP["aft_scale"]
    rows.append(("aft", CRP["Za"], CRP["aft_scale"], r, cs_a[i], ts_c[i], camber(r,CRP["hub"]),
                 PD_a, P_abs, pitch_from_PD(r,PD_a), fillet(r,CRP["hub"]), "left"))
write("contra-rotating","crp-discs.csv",
f"""# Contra-rotating pair, forward and aft discs - SYNTHETIC, GENERATED BY {GEN}
#
# NOT the Wageningen contra-rotating series (van Manen / Oosterveld, 1968) and NOT a
# lifting-line solution.
#
# CAVEAT - READ THIS BEFORE BUILDING. The aft disc's pitch is the whole design problem of a
# CRP: it runs inside the forward disc's slipstream, so its inflow is neither free-stream nor
# knowable from a table. The value here comes from a FIRST-ORDER ACTUATOR-DISC estimate:
#   axial induction  a = 0.5(sqrt(1+CT) - 1) = {a_ind:.4f}  at an assumed thrust loading CT = 0.60
#   aft pitch ratio  P/D_aft = P/D_fwd * (1+a) / (1 + 0.35a) = {CRP['PD_f']*(1+a_ind)/(1+0.35*a_ind):.4f}
# The (1 + 0.35a) term is the swirl the aft disc recovers by turning the opposite way, which
# partially offsets the raised axial inflow. Both CT and the 0.35 are ASSUMPTIONS.
#
# Replace this with an OpenProp (https://www.epps.com/openprop) lifting-line run before
# anything is built for real. Swirl recovery is the entire reason a CRP exists; a table cannot
# supply it, and treating these numbers as designed rather than estimated would hide that.
#
# From the brief: forward D = {CRP['Df']:.0f} mm Z = {CRP['Zf']}; aft D = {CRP['aft_scale']} x forward,
#   Z = {CRP['Za']} (coprime with {CRP['Zf']}), axial gap {CRP['gap_D']} D, opposite handedness.
# Achieved Ae/Ao: forward {ach_f:.4f}, aft {ach_a:.4f}.
# d_scale multiplies the forward diameter. hand is the rotation sense - a genuine XZ mirror.""",
["disc","Z","d_scale","r_R","c_D","t_D","f_c","P_D_own","pitch_abs_D","pitch_deg","fillet_r_D","hand"], rows)

# ------------------------------------------------------------- pump-jet rotor
PJ=dict(Z=7, throat_r=1.0, tip_gap_frac=0.004, hub=0.40, PD=1.1, EAR=1.05,
        t_root=0.050, t_tip=0.008, tip_skew=45.0)
xs=stations(PJ["hub"])
cs,ach=scale_to_ear(xs, blade_shape(xs,PJ["hub"],tip_style="wide_tip",tip_frac=0.85),
                    PJ["Z"], PJ["EAR"])
tip_r = PJ["throat_r"] - PJ["tip_gap_frac"]
# NO enforce_fit here, deliberately. A pump-jet rotor is a DUCTED CASCADE and the brief
# asks for high solidity: Z*chord/circumference above 1.0 is the design intent, exactly as
# in a compressor stage, because the blades are axially staggered and do not intersect.
# Applying the open-propeller fit cap here would be a category error. The real test is a
# solid-intersection check between adjacent blades, which belongs in the build script.
rows=[(r, r*tip_r, cs[i], PJ["PD"], pitch_from_PD(r,PJ["PD"]),
       thickness(r,PJ["hub"],PJ["t_root"],PJ["t_tip"]), camber(r,PJ["hub"]),
       PJ["tip_skew"]*((r-PJ["hub"])/(1-PJ["hub"]))**1.5, fillet(r,PJ["hub"]))
      for i,r in enumerate(xs)]
write("pump-jet","rotor-schedule.csv",
f"""# Pump-jet rotor schedule, Z = {PJ['Z']} - SYNTHETIC, GENERATED BY {GEN}
#
# NOT from any published series. No open rotor geometry exists for a submarine pump-jet, for
# obvious reasons. This is parametric, from the brief's numbers, and the real design route is
# an OpenProp lifting-line run.
#
# FIXES THE BUILT MODEL'S WORST DEFECT. The built rotor tip radius is 134.54 against a shroud
# inner radius of 125 - it passes THROUGH the duct wall by 9.5 mm. Here the tip is pinned to
#   r_tip = throat_radius - tip_gap = {PJ['throat_r']} - {PJ['tip_gap_frac']} = {tip_r} (fractions of throat radius)
# giving the brief's 0.5 mm gap at a 250 mm throat, ~0.2% of diameter. r_throat_frac is the
# station radius as a fraction of the THROAT radius - multiply by the throat from
# duct-decelerating.csv, never by the blade's own tip.
#
# High solidity (Ae/Ao = {PJ['EAR']}, achieved {ach:.4f}) and high skew ({PJ['tip_skew']} deg at the tip),
# both per the brief - a quiet propulsor needs area to unload the blade and skew to spread
# blade-passing over azimuth. Chord stays wide at the tip: a ducted rotor ends square, not faired.
# Hub ratio {PJ['hub']} reflects the ogive/tail-cone hub the stator vanes carry.""",
["r_R","r_throat_frac","c_D","P_D","pitch_deg","t_D","f_c","skew_deg","fillet_r_D"], rows)

# --------------------------------------------------------- rim-driven blade
RD=dict(Z=5, ring_r=1.0, free_r=0.31, PD=0.9, EAR=0.70, t_ring=0.040, t_free=0.012)
xs=[RD["free_r"]+(RD["ring_r"]-RD["free_r"])*i/16 for i in range(17)]
# Chord grows outward to the ring: the cantilever root is at the tip radius, so that
# is where both chord and thickness must be greatest. Inverted from a hubbed blade.
shape=[0.45+0.55*((r-RD["free_r"])/(RD["ring_r"]-RD["free_r"]))**0.85 for r in xs]
cs,ach=scale_to_ear(xs,shape,RD["Z"],RD["EAR"])
# Fillet is at the RING (r/R = 1.0), not at a hub - there is no hub. The blade is
# cantilevered inward, so the structural joint needing a blend is at the outer end.
def rd_fillet(r):
    u=(RD["ring_r"]-r)/(RD["ring_r"]-RD["free_r"])       # 0 at the ring, 1 at the free end
    return 0.0 if u>=0.30 else 0.018*(1-u/0.30)**1.5
rows=[(r,cs[i],RD["PD"],pitch_from_PD(r,RD["PD"]),
       RD["t_free"]+(RD["t_ring"]-RD["t_free"])*((r-RD["free_r"])/(RD["ring_r"]-RD["free_r"])),
       camber(r,RD["free_r"]), 0.0, rd_fillet(r)) for i,r in enumerate(xs)]
write("rim-driven","blade-schedule.csv",
f"""# Rim-driven (hubless) blade schedule - SYNTHETIC, GENERATED BY {GEN}
#
# NOT from any published series. Rim-drive blade geometry is commercial (SCHOTTEL, Copenhagen
# Subsea). Parametric, from the brief.
#
# THE STRUCTURE IS INVERTED and the thickness column reflects it. Every other propeller here
# is thickest at the hub; this blade is cantilevered INWARD from the motor ring, so its
# structural root is at r/R = {RD['ring_r']} and its FREE end is at r/R = {RD['free_r']}. Thickness therefore
# runs {RD['t_ring']} at the ring down to {RD['t_free']} at the free inner end - the opposite of a hubbed blade.
# Getting this backwards produces a blade that is thinnest exactly where the bending moment is
# highest.
#
# Z = {RD['Z']}, P/D = {RD['PD']}, Ae/Ao = {RD['EAR']} (achieved {ach:.4f}). No rake: there is no hub to rake from.
# Sections: use the generated NACA form in ../voith-schneider/naca0016.csv scaled to t_D, or a
# cambered four-digit section if loading demands it.""",
["r_R","c_D","P_D","pitch_deg","t_D","f_c","rake_z_D","fillet_r_D"], rows)

# ------------------------------------------------------ rim-driven magnet band
MAG=dict(poles=16, ring_od=123.5, gap=1.5, band_axial=23.5, pocket_depth=5.0, bridge=1.2)
pitch_deg=360.0/MAG["poles"]
arc=math.radians(pitch_deg)*MAG["ring_od"]
rows=[(i, i*pitch_deg, MAG["ring_od"], MAG["ring_od"]-MAG["pocket_depth"],
       arc-MAG["bridge"], MAG["band_axial"], MAG["pocket_depth"]) for i in range(MAG["poles"])]
write("rim-driven","magnet-band.csv",
f"""# Rim-driven magnet pocket band - SYNTHETIC, GENERATED BY {GEN}
#
# NOT a motor design. Pole count, magnet grade and flux are electromagnetic decisions this
# repo does not make; {MAG['poles']} poles is taken from the built model, which has 16 magnet blocks.
#
# WHAT THIS FIXES: in the built model the 16 magnets are separate solids OVERLAPPING the ring,
# not pockets cut into it. This table defines actual pockets - a recess of depth {MAG['pocket_depth']} mm in the
# ring OD, with a {MAG['bridge']} mm bridge of material left between neighbours so the ring stays a ring.
#
# Ring OD {MAG['ring_od']} mm, magnetic gap {MAG['gap']} mm to the duct stator bore at {MAG['ring_od']+MAG['gap']} mm.
# That gap is both the motor airgap and a viscous drag path - it is the number to hold.
# Pocket pitch {pitch_deg:.2f} deg; arc length at the OD {arc:.3f} mm; width is arc minus the bridge.
# All lengths mm, angles degrees.""",
["pocket","angle_deg","r_outer_mm","r_inner_mm","width_mm","axial_len_mm","depth_mm"], rows)

# --------------------------------------------------------- podded pod body
POD=dict(D=250.0, body_D=0.5, length=2.5, nose=0.30, tail=0.45)
def pod_profile(n=61):
    rows=[]; Rb=POD["body_D"]/2
    for i in range(n):
        x=i/(n-1)
        if x < POD["nose"]:                       # ellipsoidal nose
            u=x/POD["nose"]; r=Rb*math.sqrt(max(0.0,1-(1-u)**2))
        elif x > 1-POD["tail"]:                   # conic tail, faired
            u=(x-(1-POD["tail"]))/POD["tail"]; r=Rb*(1-u**1.6)*0.98+Rb*0.02
        else: r=Rb                                 # parallel mid-body
        rows.append((x, x*POD["length"], r, r*2))
    return rows
write("podded-azimuth","pod-body.csv",
f"""# Podded azimuth thruster pod body profile - SYNTHETIC, GENERATED BY {GEN}
#
# NOT ABB Azipod geometry, which is proprietary. Parametric axisymmetric fairing from the
# brief's numbers.
#
# From the brief: pod body diameter {POD['body_D']} D = {POD['body_D']*POD['D']:.0f} mm on a {POD['D']:.0f} mm propeller,
#   pod length {POD['length']} D = {POD['length']*POD['D']:.0f} mm, faired nose and tail cone.
# Shape: ellipsoidal nose over the first {POD['nose']:.0%} of length, parallel mid-body, then a faired
# conic tail over the last {POD['tail']:.0%}. The tail is longer than the nose because separation on the
# after body is what costs a pod its efficiency, and it must clear the propeller for a pusher.
#
# x_frac is fraction of pod length; x_mm and radius_mm are at the stated scale. Revolve about
# the pod axis. Strut section is in naca0015-strut.csv.""",
["x_frac","x_mm","radius_mm","diameter_mm"], pod_profile())

# ------------------------------------------- toroidal section schedule
TOR=dict(min_t_D=0.012, root_t_D=0.038, peak_t_D=0.022, chord_root=0.16, chord_mid=0.26)
def loop_sections(n=61):
    rows=[]
    for i in range(n):
        s=i/(n-1); a=2*math.pi*s
        span=(0.5-0.5*math.cos(a))                  # 0 at roots, 1 over the top
        c=TOR["chord_root"]+(TOR["chord_mid"]-TOR["chord_root"])*math.sin(math.pi*span)**0.7
        t=TOR["root_t_D"]+(TOR["peak_t_D"]-TOR["root_t_D"])*span
        rows.append((s, span, c, max(t,TOR["min_t_D"]), t/c))
    return rows
sec=loop_sections()
write("toroidal","section-schedule.csv",
f"""# Marine toroidal blade section schedule along the loop - SYNTHETIC, GENERATED BY {GEN}
#
# NOT Sharrow geometry, which is patented and tabulates nothing. Parametric, from the brief.
#
# Scheduled by the SAME path parameter s as loop-path.csv, so the two files index together:
# row i here is the section to sweep at row i there. Both are closed and periodic in s.
#
# The brief's binding constraint is a minimum thickness that holds ALL THE WAY ROUND, including
# the return branch - a loop has no free tip to thin toward, and the return branch carries load
# just as the leading branch does. Floor is t/D = {TOR['min_t_D']}; achieved minimum {min(r[3] for r in sec):.4f}.
# Thickness runs {TOR['root_t_D']} at the roots to {TOR['peak_t_D']} over the top; chord {TOR['chord_root']} to {TOR['chord_mid']}.
#
# Marine sections throughout: blunt trailing edge, leading-edge radius chosen for cavitation,
# never a knife edge. t_c is reported so the section can be scaled from any aerofoil.""",
["s","span_frac","c_D","t_D","t_c"], sec)

# --------------------------------------------- CPP O-ring groove dimensions
ORING=dict(squeeze=0.20, width_ratio=1.30, corner=0.10)
def oring_table():
    rows=[]
    for cord in (1.78, 2.62, 3.53, 5.33, 6.99):     # common AS568 cord diameters, mm
        depth = cord*(1-ORING["squeeze"])
        rows.append((cord, ORING["squeeze"], depth, cord*ORING["width_ratio"],
                     cord*ORING["corner"], depth/cord))
    return rows
write("controllable-pitch","oring-grooves.csv",
f"""# CPP palm-bore O-ring groove dimensions - SYNTHETIC, GENERATED BY {GEN}
#
# NOT transcribed from ISO 3601-2 or the Parker O-Ring Handbook (ORD-5700). Those are the
# authoritative sources and are not freely available; consult them before cutting metal.
#
# WHAT THIS IS: the standard design RATIOS applied to common cord diameters, which is the
# method those standards encode - not a copy of their tables.
#   groove depth = cord x (1 - squeeze), squeeze = {ORING['squeeze']:.0%}  (static seals run 15-25%)
#   groove width = cord x {ORING['width_ratio']}   (room for the ring to roll and for thermal expansion)
#   corner radius = cord x {ORING['corner']}
# Cord diameters listed are the common AS568 sizes in mm.
#
# WHY IT MATTERS HERE: the CPP hub has a palm bore per blade and the blades rotate in service,
# so this is a DYNAMIC rotary application, not static. Rotary seals want lower squeeze and
# tighter surface finish than the ratios above - treat this table as the starting point for a
# static check and size the running seal properly.
#
# All lengths mm.""",
["cord_dia_mm","squeeze_frac","groove_depth_mm","groove_width_mm","corner_r_mm","depth_ratio"],
oring_table())

# ------------------------------------------- ducted-kort Ka blade planform ---
# Thickness and max-thickness position are READ FROM THE REAL Ka DATA already committed
# in ducted-kort/ka-thickness.csv, not invented. Only the chord distribution is synthetic,
# because the Ka chord law c(r) = K(r)*D*EAR/Z needs a K(r) table that is NOT IN SOURCE.
KA = dict(D=250.0, Z=4, EAR=0.70, PD=1.0, hub=0.265, tip_gap=1.5, nozzle_id=250.0)
def _read_ka_thickness():
    import csv as _csv
    path = os.path.join(ROOT, "ducted-kort", "ka-thickness.csv")
    rows = list(_csv.DictReader(l for l in open(path) if not l.lstrip().startswith("#")))
    out = []
    for r in rows:
        if r["tmax_D"]:                      # r/R = 0.2 is empty: flagged SUSPECT in source
            out.append((float(r["r_R"]), float(r["tmax_D"]), float(r["Xtmax_cr"])))
    return out
KA_T = _read_ka_thickness()
ka_tip_r = (KA["nozzle_id"]/2 - KA["tip_gap"]) / (KA["D"]/2)     # 123.5 / 125.0
xs = stations(KA["hub"], n=15)
cs, ka_ach = scale_to_ear(xs, blade_shape(xs, KA["hub"], tip_style="wide_tip", tip_frac=0.80),
                          KA["Z"], KA["EAR"])
ka_betas = [pitch_from_PD(r, KA["PD"]) for r in xs]
cs, ka_ach = enforce_fit(xs, cs, ka_betas, KA["Z"], KA["EAR"])
rows = []
for i, r in enumerate(xs):
    t  = _interp([a for a,_,_ in KA_T], [b for _,b,_ in KA_T], r)
    xt = _interp([a for a,_,_ in KA_T], [c for _,_,c in KA_T], r)
    rows.append((r, r*ka_tip_r*KA["D"]/2, cs[i], KA["PD"], pitch_from_PD(r, KA["PD"]),
                 t, xt, 0.0, 0.0))
write("ducted-kort", "blade-planform.csv",
f"""# Ka 4-70 blade planform for the Kort nozzle - chord SYNTHETIC, thickness REAL.
# GENERATED BY {GEN}
#
# NOT a complete Ka-series blade. The Ka chord law is c(r) = K(r) * D * EAR / Z, and the K(r)
# table is NOT IN SOURCE - the 2009 paper that carries the rest of the Ka data misnumbers its
# own cross-reference to it. So:
#   t_D and Xtmax_cr are READ from the real ka-thickness.csv in this folder.
#   c_D is SYNTHETIC - a wide-tip distribution scaled to hit the brief's Ae/Ao.
# Fetch Oosterveld (1970) to replace the chord column with the real K(r).
#
# From the brief: D = {KA['D']:.0f} mm, Z = {KA['Z']}, Ae/Ao = {KA['EAR']}, P/D = {KA['PD']},
#   nozzle inner Ø {KA['nozzle_id']:.0f}, tip clearance {KA['tip_gap']} mm.
#   Achieved Ae/Ao = {ka_ach:.4f}.
#
# THE TIP IS SQUARE AND PINNED. r_tip_mm = r_R * {ka_tip_r*KA['D']/2:.4f}, so the outermost station
# lands at exactly {ka_tip_r*KA['D']/2:.1f} mm - nozzle bore {KA['nozzle_id']/2:.1f} minus the {KA['tip_gap']} mm gap. Chord is HELD
# near the tip (tip/peak {cs[-1]/max(cs):.2f}); a Ka blade ends square close to the wall and must not be
# faired to a point. Rake is zero: the Ka series has no rake, per ka-thickness.csv.
# Xtmax_cr is the chordwise position of maximum thickness, needed to place the Ka section.""",
["r_R","r_tip_mm","c_D","P_D","pitch_deg","t_D","Xtmax_cr","skew_deg","rake_z_D"], rows)

# ============================================================ hubs =========
# A truncated cone with a keyed taper bore - the brief's default hub - dimensioned
# from standard ratios. rim-driven gets NOTHING here on purpose: it is hubless, and
# check-geometry.py asserts the file's ABSENCE so nobody "completes" it later.
HUB_TAPER   = 1/12.0      # bore taper on diameter; marine shaft tapers run ~1:10 to 1:15
HUB_CONE    = 1/15.0      # outer cone taper, fore to aft
HUB_LEN_D   = 0.30        # hub length / D
HUB_BORE_F  = 0.55        # mean bore diameter / hub fore diameter

def hub_rows(D, hub_ratio, note=""):
    dh   = hub_ratio*D                       # hub diameter at the propeller reference plane
    L    = HUB_LEN_D*D
    dfwd = dh + HUB_CONE*L/2
    daft = dh - HUB_CONE*L/2
    bore = HUB_BORE_F*dh                     # mean bore diameter
    bfwd = bore + HUB_TAPER*L/2
    baft = bore - HUB_TAPER*L/2
    # keyway proportioned off the bore, in the manner of DIN 6885 / BS 46 parallel keys
    kw   = round(0.25*bore, 2)
    kd   = round(0.5*kw, 2)
    # NOTE: no commas in the note field - these are CSV values, not prose.
    return [("hub_diameter_at_prop_plane", round(dh,3), "mm", note),
            ("hub_length", round(L,3), "mm", "0.30 D"),
            ("hub_dia_forward", round(dfwd,3), "mm", f"outer cone taper {HUB_CONE:.4f} on dia"),
            ("hub_dia_aft", round(daft,3), "mm", "truncated cone - larger forward"),
            ("bore_dia_mean", round(bore,3), "mm", f"{HUB_BORE_F} x hub diameter"),
            ("bore_dia_forward", round(bfwd,3), "mm", f"taper {HUB_TAPER:.4f} on dia (1:12)"),
            ("bore_dia_aft", round(baft,3), "mm", "taper bore - larger forward"),
            ("keyway_width", kw, "mm", "0.25 x bore - parallel key per DIN 6885 practice"),
            ("keyway_depth", kd, "mm", "0.5 x keyway width - in the hub"),
            # wall taken at the FORWARD end where the bore is largest: thinnest section.
            ("wall_min", round((dfwd-bfwd)/2,3), "mm", "hub wall per side at the fwd end")]

HUB_HEADER = """# {name} hub - SYNTHETIC, GENERATED BY {gen}
#
# NOT a manufacturer's hub. Dimensioned from standard RATIOS, which is the method, not a
# transcription: marine shaft tapers run about 1:10 to 1:15 (1:12 used here) and parallel
# keys are proportioned off the bore in the manner of DIN 6885 / BS 46. Confirm against the
# actual shaft and key standard before cutting metal.
#
# The brief's default hub is "a truncated cone with a keyed taper bore"; it gives no
# dimensions, so these are derived from the design's own hub ratio. Larger diameter forward,
# bore tapering the same way, so the propeller seats and locks under thrust.
#
# Hub ratio {hr} of D = {D} mm. {extra}"""

for slug, D, hr, name, extra in [
    ("fixed-pitch",        250.0, 0.167, "Fixed-pitch (FPP)", ""),
    ("skewed",             250.0, 0.200, "Skewed blade", "Same hub across all four skew models."),
    ("tip-loaded",         250.0, 0.167, "Tip-loaded (Kappel / CLT)", "Base FPP hub, unchanged."),
    ("supercavitating",    250.0, 0.200, "Supercavitating",
     "The built model has a plain cylinder with a straight bore - this is what it should be."),
    ("surface-piercing",   250.0, 0.200, "Surface-piercing (SPP)",
     "Brief calls for a small hub with a taper bore."),
    ("toroidal",           250.0, 0.200, "Loop / toroidal", "Both loop roots land on this hub."),
    ("ducted-kort",        250.0, 0.265, "Ducted propeller / Kort nozzle",
     "Hub ratio measured off the built model (65.4 mm on 247 mm). Ka series is nominally D/6."),
    ("controllable-pitch", 250.0, 0.300, "Controllable-pitch (CPP)",
     "Fat hub: it has to contain the pitch mechanism. Palm bores and O-ring grooves are separate."),
    ("contra-rotating",    250.0, 0.200, "Contra-rotating (CRP) forward disc",
     "Aft disc runs on the inner shaft through this hub's sleeve; see crp-discs.csv."),
]:
    write(slug, "hub.csv",
          HUB_HEADER.format(name=name, gen=GEN, hr=hr, D=D, extra=extra),
          ["parameter","value","unit","note"], hub_rows(D, hr, f"hub ratio {hr}"))

print("\nAll geometry regenerated.")
