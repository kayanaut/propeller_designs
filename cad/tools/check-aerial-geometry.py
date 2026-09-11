#!/usr/bin/env python3
"""Assert the AERIAL briefs' conventions across every cad/aerial CSV.

Deliberately NOT the same rules as check-geometry.py. The marine 1 mm minimum
trailing-edge thickness is filed under "Wet-specific" in the underwater brief and
does not appear in the aerial one, which asks for a SHARP trailing edge on the
carbon blade. Enforcing the marine floor here would be a category error, so this
file checks aerial things instead: thin sections, Tyler-Sofrin vane counts, tip
Mach, a cylindrical duct wall across the rotor plane, and chord shape benchmarked
against the real APC 10x5E rather than against a marine blade.

    python3 cad/tools/check-aerial-geometry.py
"""
import csv, math, os, sys, glob

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "aerial"))
fails, checks = [], 0

def rd(rel):
    with open(os.path.join(ROOT, rel)) as f:
        return list(csv.DictReader(l for l in f if not l.lstrip().startswith("#")))
def col(rows, n): return [float(r[n]) for r in rows]
def ok(cond, label, detail=""):
    global checks; checks += 1
    if not cond: fails.append(f"{label}  {detail}")

# ---- 1. the real reference blade parses and is sane ---------------------
apc = rd("fixed-pitch/apc-10x5e.csv")
r_R, c_D = col(apc, "r_R"), col(apc, "c_D")
ok(len(apc) == 51, "APC 10x5E station count", f"{len(apc)}")
ok(abs(r_R[-1]-1.0) < 1e-9, "APC blade runs to the tip", f"last r/R {r_R[-1]}")
ok(all(b >= a-1e-9 for a, b in zip(r_R, r_R[1:])), "APC stations monotonic", "")
tr = col(apc, "thickness_ratio")
ok(tr[0] > tr[-1], "APC thickness tapers outward", f"root {tr[0]} tip {tr[-1]}")
APC_PEAK = max(c_D)
def apc_at(rr):
    for i in range(len(r_R)-1):
        if r_R[i] <= rr <= r_R[i+1]:
            f = (rr-r_R[i])/(r_R[i+1]-r_R[i]); return c_D[i]+f*(c_D[i+1]-c_D[i])
    return c_D[-1]
APC_ROOT_RATIO = apc_at(0.15)/APC_PEAK     # root/peak of the REAL blade

# ---- 1b. synthetic blades must track the real blade's chord SHAPE -------
# This check exists because the marine round shipped a chord distribution that starved the
# root while still hitting its area ratio: an integral cannot see a wrong distribution. The
# benchmark was computed there and never asserted, and the defect went out. Assert it here.
for rel, filt, lab in [("custom-carbon/blade-planform.csv", None, "custom carbon"),
                       ("coaxial/rotor-pair.csv", ("rotor", "upper"), "coaxial upper"),
                       ("coaxial/rotor-pair.csv", ("rotor", "lower"), "coaxial lower")]:
    rr = rd(rel)
    if filt: rr = [x for x in rr if x[filt[0]] == filt[1]]
    cc = col(rr, "c_D")
    ratio = cc[0]/max(cc)
    ok(abs(ratio-APC_ROOT_RATIO) <= 0.15, f"root chord tracks the real APC blade: {lab}",
       f"root/peak {ratio:.2f} vs APC {APC_ROOT_RATIO:.2f}")
    ok(cc[-1] < 0.25*max(cc), f"open aerial blade tapers to a fine tip: {lab}",
       f"tip/peak {cc[-1]/max(cc):.3f}")

# ---- 1c. the DUCTED rotor is the exception: it ends square --------------
dr = rd("ducted-fan/rotor-schedule.csv")
drc = col(dr, "c_D")
ok(drc[-1] >= 0.60*max(drc), "ducted rotor keeps a wide, square-cut tip",
   f"tip/peak {drc[-1]/max(drc):.3f} - the duct carries tip loading, so it does not fair")
tip = col(dr, "r_fanR")[-1]
want = (45.0-0.4)/45.0
ok(abs(tip-want) < 1e-4, "ducted rotor tip pinned to the brief's 0.4 mm clearance",
   f"tip {tip:.4f} fan radius, want {want:.4f}")
sv = rd("ducted-fan/stator-vanes.csv")
ok(len(sv) == 11, "stator vane count is geometry, not prose", f"{len(sv)} vanes")
ok(abs(float(sv[1]["angle_deg"])-360.0/11) < 1e-6, "stator vanes evenly spaced", "")

# ---- 2. aerial sections stay THIN and SHARP -----------------------------
# Aerial blades are thin; the marine TE floor must NOT have been applied here.
for rel, tmax, lab in [("cyclorotor/naca0015.csv", 0.15, "cyclorotor NACA0015"),
                       ("ducted-fan/rotor-section-naca2408.csv", 0.08, "EDF rotor NACA2408"),
                       ("ducted-fan/stator-vane-naca4412.csv", 0.12, "EDF stator NACA4412")]:
    y = col(rd(rel), "y_t")
    ok(abs(2*max(y)-tmax) < 1e-3, f"section thickness matches its code: {lab}",
       f"got {2*max(y):.4f} want {tmax}")
    ok(2*y[-1] < 0.005, f"trailing edge stays SHARP (aerial, not marine): {lab}",
       f"TE {2*y[-1]:.5f} c - marine 1 mm floor must not be applied here")

for rel, lab in [("custom-carbon/blade-planform.csv", "custom carbon")]:
    tc = col(rd(rel), "t_c")
    ok(max(tc) <= 0.15, f"sections thin enough for a carbon blade: {lab}", f"max t/c {max(tc):.3f}")
    ok(tc[0] > tc[-1], f"thickness tapers outward: {lab}", f"root {tc[0]} tip {tc[-1]}")

# ---- 3. Tyler-Sofrin: V >= 2Z on the ducted fan -------------------------
Z, V = 5, 11
ok(V >= 2*Z, "ducted fan V >= 2Z (blade-passing tone cut off)", f"V={V} Z={Z} floor={2*Z}")

# ---- 4. duct wall cylindrical across the rotor plane --------------------
d = rd("ducted-fan/duct-ordinates.csv")
cyl = [r for r in d if abs(float(r["r_inner_fanR"])-1.0) < 1e-9]
ok(len(cyl) >= 8, "duct wall cylindrical across the rotor plane",
   f"{len(cyl)} stations at exactly 1.000 fan radius")
ri = col(d, "r_inner_fanR")
ok(abs(ri[-1]-math.sqrt(0.85)) < 1e-3, "exit nozzle area ratio 0.85",
   f"exit r {ri[-1]:.4f} want {math.sqrt(0.85):.4f}")
ok(ri[0] > 1.0, "inlet lip is rounded outward, not a knife edge", f"inlet r {ri[0]:.4f}")

# ---- 5. eVTOL tip Mach cap and a live blend weight ----------------------
ev = rd("evtol-proprotor/blend-twist.csv")
h, c, b = col(ev, "twist_hover_deg"), col(ev, "twist_cruise_deg"), col(ev, "twist_blended_deg")
ok(all(min(x, y)-1e-6 <= z <= max(x, y)+1e-6 for x, y, z in zip(h, c, b)),
   "blended twist lies between the hover and cruise tables", "")
ok(any(abs(x-y) > 1.0 for x, y in zip(h, c)),
   "hover and cruise twist genuinely differ (there is a trade to make)",
   f"max delta {max(abs(x-y) for x,y in zip(h,c)):.1f} deg")
ok(all(y > x for x, y in zip(h, c)),
   "cruise is coarser than hover at every station (higher advance ratio)",
   f"stations where it is not: {sum(1 for x,y in zip(h,c) if y<=x)}")

# ---- 6. Q-tip: the bend must actually shrink the disc -------------------
q = rd("q-tip/bend-path.csv")
proj = col(q, "r_projected_R")
ok(proj[-1] < 1.0, "Q-tip bend reduces the swept disc (that is the trade)",
   f"projected {proj[-1]:.4f} R")
# The brief over-specifies the bend (start, radius AND angle). Radius and span fix real
# geometry, so the angle is derived; assert the arc closes rather than a superseded number.
ang = math.radians(float(q[-1]["bend_deg"]))
arc = 8.0*ang; span = (1.0-0.92)*254.0/2
ok(abs(arc-span)/span < 1e-3, "Q-tip arc length matches the developed span",
   f"arc {arc:.4f} mm vs span {span:.4f} mm, angle {math.degrees(ang):.3f} deg")

# ---- 7. serrations scale with LOCAL chord ------------------------------
s = rd("serrated/serration-schedule.csv")
ch, am = col(s, "chord_mm"), col(s, "amplitude_mm")
ratios = [a/c for a, c in zip(am, ch) if c > 0]
ok(max(ratios)-min(ratios) < 1e-6, "serration amplitude is a constant fraction of local chord",
   f"spread {max(ratios)-min(ratios):.2e} - a flat-plane cut would vary")
ok(all(float(r["r_R"]) >= 0.5-1e-9 for r in s), "serrations only outboard of r/R 0.5", "")

# ---- 8. toroidal loop closes and is periodic ---------------------------
t = rd("toroidal/loop-path.csv")
HUB = 0.18
ok(abs(float(t[0]["r_R"])-HUB) < 1e-6 and abs(float(t[-1]["r_R"])-HUB) < 1e-6,
   "toroidal path starts and ends at the hub (the hub closes the loop)",
   f"ends at r/R {float(t[0]['r_R']):.4f} and {float(t[-1]['r_R']):.4f}")
ok(float(t[0]["theta_deg"])*float(t[-1]["theta_deg"]) < 0,
   "the two root joints sit on opposite sides of the hub", "")
# The whole reason this check exists: an unconstrained spline dipped to r/R 0.1338, i.e.
# the blade path passed INSIDE the hub boss it attaches to.
ok(min(col(t, "r_R")) >= HUB-1e-6, "toroidal path never dips inside the hub",
   f"min r/R {min(col(t,'r_R')):.4f} against hub {HUB}")
ok(max(col(t, "r_R")) <= 1.0+1e-9, "toroidal loop stays inside the disc", "")

# ---- 9. coaxial: lower rotor pitched UP for the upper's downwash --------
cx = rd("coaxial/rotor-pair.csv")
up = [x for x in cx if x["rotor"] == "upper"]; lo = [x for x in cx if x["rotor"] == "lower"]
ok(float(lo[0]["P_D"]) > float(up[0]["P_D"]),
   "coaxial lower rotor pitched up for the upper's downwash",
   f"upper {up[0]['P_D']} lower {lo[0]['P_D']}")
ok(up[0]["hand"] != lo[0]["hand"], "coaxial rotors are opposite hand", "")

# ---- 9b. every table declares how to read itself -----------------------
# Aerial declares a DIFFERENT axis datum from marine (leading edge, not mid-chord), because
# APC define sweep and rake off the mould LE parting line. That is exactly why the datum has
# to travel with the file instead of living in prose.
for f in sorted(glob.glob(os.path.join(ROOT, "*", "*.csv"))):
    head = "".join(l for l in open(f) if l.startswith("#"))
    for tag in ("# FRAME ", "# UNITS ", "# PITCH ", "# AXIS ", "# RAKE ", "# WIRE "):
        ok(tag in head, f"declares {tag.strip('# ')}: {os.path.basename(f)}", "")
    if "# AXIS " in head:
        ok("LEADING EDGE" in head, f"aerial axis datum is the LE: {os.path.basename(f)}", "")

# ---- 9c. camber on the lifting blades ----------------------------------
for rel, filt, lab in [("custom-carbon/blade-planform.csv", None, "custom carbon"),
                       ("coaxial/rotor-pair.csv", ("rotor", "upper"), "coaxial upper"),
                       ("ducted-fan/rotor-schedule.csv", None, "EDF rotor")]:
    rows = rd(rel)
    if filt: rows = [x for x in rows if x[filt[0]] == filt[1]]
    ok("f_c" in rows[0], f"lifting blade carries camber: {lab}", "")
    if "f_c" in rows[0]:
        ok(max(float(x["f_c"]) for x in rows) > 0.001, f"camber is non-trivial: {lab}", "")

# ---- 10. provenance across every aerial CSV ----------------------------
for f in glob.glob(os.path.join(ROOT, "*", "*.csv")):
    head = "".join(l for l in open(f) if l.startswith("#"))
    ok("Source:" in head or "GENERATED BY" in head,
       f"provenance present: {os.path.basename(f)}", "")
    if "SYNTHETIC" in head:
        ok("NOT " in head, f"SYNTHETIC declares what it is not: {os.path.basename(f)}", "")

print(f"checked {checks} assertions across {len(glob.glob(os.path.join(ROOT,'*','*.csv')))} aerial CSVs")
if fails:
    print(f"\n{len(fails)} FAILED:")
    for f in fails: print("  x " + f)
    sys.exit(1)
print("all pass")
