#!/usr/bin/env python3
"""Assert the underwater briefs' own conventions across every geometry CSV.

This exists because the previous round's verification checked integrals and target
values and passed everything, while the distributions underneath were wrong. An
area ratio is an integral: starve the root, inflate mid-span, and Ae/Ao still lands
on target. These checks look at SHAPE and at the briefs' stated rules instead.

    python3 cad/tools/check-geometry.py       # exits non-zero on any failure
"""
import csv, math, os, sys, glob

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "underwater"))
D_REF, TE_MIN_MM = 250.0, 1.0
# CSVs are written at 6 decimal places, so a value generated as exactly 1.000 mm reads
# back as 0.99996. Tolerate a micron - far below anything a foundry or printer resolves.
TOL_MM = 1e-3
fails, checks = [], 0

def rd(rel):
    with open(os.path.join(ROOT, rel)) as f:
        return list(csv.DictReader(l for l in f if not l.lstrip().startswith("#")))

def ok(cond, label, detail=""):
    global checks
    checks += 1
    if not cond: fails.append(f"{label}  {detail}")
    return cond

def col(rows, name): return [float(r[name]) for r in rows]

def ear(xs, cs, Z):
    return 2*Z/math.pi*sum((cs[i]+cs[i+1])/2*(xs[i+1]-xs[i]) for i in range(len(xs)-1))

# ---- 1. trailing edges: the brief's wet-specific 1 mm rule ---------------
# "no knife-edge trailing edges: hold a minimum TE thickness (1 mm at this scale)"
for rel, chord_mm, label in [("voith-schneider/naca0016.csv", 70.0, "VSP NACA0016"),
                             ("podded-azimuth/naca0015-strut.csv", 60.0, "strut NACA0015"),
                             ("pump-jet/stator-vane-naca4412.csv", 30.0, "stator NACA4412")]:
    r = rd(rel); te = 2*col(r, "y_t")[-1]*chord_mm
    ok(te >= TE_MIN_MM-TOL_MM, f"TE >= {TE_MIN_MM} mm: {label}", f"got {te:.3f} mm on a {chord_mm:.0f} mm chord")

d = rd("pump-jet/duct-decelerating.csv")
ri, ro = col(d, "r_inner_throat"), col(d, "r_outer_throat")
for idx, edge in ((0, "LE"), (-1, "TE")):
    t = (ro[idx]-ri[idx])*125.0
    ok(t >= TE_MIN_MM-TOL_MM, f"TE >= {TE_MIN_MM} mm: decelerating duct {edge}", f"got {t:.3f} mm")

for rel, lab in [("fixed-pitch/blade-planform.csv", "FPP"), ("skewed/skew-sweep.csv", "skewed"),
                 ("rim-driven/blade-schedule.csv", "rim-driven"),
                 ("pump-jet/rotor-schedule.csv", "pump-jet"),
                 ("supercavitating/blade-planform.csv", "supercav")]:
    t = min(col(rd(rel), "t_D"))*D_REF
    ok(t >= TE_MIN_MM-TOL_MM, f"min section thickness >= {TE_MIN_MM} mm: {lab}", f"got {t:.3f} mm at D={D_REF:.0f}")

# ---- 2. chord SHAPE, benchmarked against the real blade -----------------
real = rd("fixed-pitch/dtmb4119.csv")
rc = col(real, "c_D"); REAL_RATIO = rc[0]/max(rc)          # DTMB 4119 root/peak
ok(0.6 < REAL_RATIO < 0.8, "reference blade sane", f"DTMB4119 root/peak {REAL_RATIO:.2f}")

FAIRED   = [("fixed-pitch/blade-planform.csv", None, "FPP"),
            ("skewed/skew-sweep.csv", ("propeller", "DTMB 4381"), "skewed"),
            ("contra-rotating/crp-discs.csv", ("disc", "forward"), "CRP fwd"),
            ("supercavitating/blade-planform.csv", None, "supercav")]
WIDE_TIP = [("pump-jet/rotor-schedule.csv", None, "pump-jet rotor"),
            ("surface-piercing/cleaver-planform.csv", None, "SPP cleaver")]
# rim-driven is measured separately: it has no hub root. Its structural root is the
# RING at r/R = 1.0, so the widest section belongs at the end a hubbed blade calls the tip.

def planform(rel, filt):
    r = rd(rel)
    if filt: r = [x for x in r if x[filt[0]] == filt[1]]
    return col(r, "r_R"), col(r, "c_D")

for rel, filt, lab in FAIRED + WIDE_TIP:
    xs, cs = planform(rel, filt)
    ratio = cs[0]/max(cs)
    ok(abs(ratio-REAL_RATIO) <= 0.30, f"root chord realistic: {lab}",
       f"root/peak {ratio:.2f} vs DTMB4119 {REAL_RATIO:.2f}")

for rel, filt, lab in WIDE_TIP:
    xs, cs = planform(rel, filt)
    ok(cs[-1]/max(cs) >= 0.50, f"tip stays wide (ducted/cleaver ends square): {lab}",
       f"tip/peak {cs[-1]/max(cs):.2f}")

xs, cs = planform("rim-driven/blade-schedule.csv", None)
ok(cs[-1] == max(cs), "rim-driven widest at the ring (its structural root)",
   f"ring {cs[-1]:.4f} vs peak {max(cs):.4f}")
ok(0.30 <= cs[0]/max(cs) <= 0.70, "rim-driven free end narrower than the ring",
   f"free/ring {cs[0]/max(cs):.2f}")

# ---- 3. thickness tapers the right way ---------------------------------
for rel, lab in [("fixed-pitch/blade-planform.csv", "FPP"),
                 ("supercavitating/blade-planform.csv", "supercav"),
                 ("pump-jet/rotor-schedule.csv", "pump-jet")]:
    t = col(rd(rel), "t_D")
    ok(t[0] > t[-1], f"thickness tapers outward: {lab}", f"root {t[0]:.4f} tip {t[-1]:.4f}")
t = col(rd("rim-driven/blade-schedule.csv"), "t_D")
ok(t[-1] > t[0], "thickness tapers INWARD (structural root is the ring): rim-driven",
   f"free end {t[0]:.4f} ring {t[-1]:.4f}")

# ---- 3b. tip sections must be loftable, not thicker than they are long --
# The 1 mm TE floor and a faired planform pull in opposite directions at the tip.
for rel, filt, lab in [("fixed-pitch/blade-planform.csv", None, "FPP"),
                       ("skewed/skew-sweep.csv", ("propeller", "DTMB 4381"), "skewed"),
                       ("supercavitating/blade-planform.csv", None, "supercav"),
                       ("pump-jet/rotor-schedule.csv", None, "pump-jet"),
                       ("rim-driven/blade-schedule.csv", None, "rim-driven"),
                       ("contra-rotating/crp-discs.csv", ("disc", "forward"), "CRP fwd"),
                       ("contra-rotating/crp-discs.csv", ("disc", "aft"), "CRP aft")]:
    r = rd(rel)
    if filt: r = [x for x in r if x[filt[0]] == filt[1]]
    # only outboard of r/R 0.70: marine ROOTS legitimately run t/c ~0.20
    tc = max(float(x["t_D"])/float(x["c_D"]) for x in r if float(x["r_R"]) >= 0.70)
    ok(tc <= 0.15+1e-3, f"outboard t/c loftable: {lab}", f"got t/c {tc:.3f}")

# ---- 4. area ratios still hit their briefs ------------------------------
for rel, filt, Z, tgt, lab in [("fixed-pitch/blade-planform.csv", None, 4, 0.55, "FPP"),
                               ("supercavitating/blade-planform.csv", None, 3, 0.55, "supercav"),
                               ("pump-jet/rotor-schedule.csv", None, 7, 1.05, "pump-jet"),
                               ("rim-driven/blade-schedule.csv", None, 5, 0.70, "rim-driven"),
                               ("skewed/skew-sweep.csv", ("propeller", "DTMB 4381"), 5, 0.725, "skewed"),
                               ("surface-piercing/cleaver-planform.csv", None, 5, 0.75, "SPP")]:
    xs, cs = planform(rel, filt)
    ok(abs(ear(xs, cs, Z)-tgt) < 1e-3, f"Ae/Ao hits brief: {lab}", f"{ear(xs,cs,Z):.4f} vs {tgt}")

# ---- 5. CRP: the aft disc must be pitched UP, in absolute terms ---------
c = rd("contra-rotating/crp-discs.csv")
f0 = [x for x in c if x["disc"] == "forward"][0]
a0 = [x for x in c if x["disc"] == "aft"][0]
fa, aa = float(f0["pitch_abs_D"]), float(a0["pitch_abs_D"])
ok(aa > fa, "CRP aft absolute pitch exceeds forward (accelerated inflow)",
   f"aft {aa:.4f} D vs forward {fa:.4f} D")
ok(abs(float(a0["P_D_own"])*float(a0["d_scale"]) - aa) < 1e-6,
   "CRP P_D_own and pitch_abs_D agree", "")
ok(math.gcd(int(f0["Z"]), int(a0["Z"])) == 1, "CRP blade counts coprime", "")

# ---- 6. skew sweep differs ONLY in skew --------------------------------
rows = rd("skewed/skew-sweep.csv")
props = {}
for r in rows: props.setdefault(r["propeller"], []).append(r)
diff = set()
base = props["DTMB 4381"]
for rs in props.values():
    for a, b in zip(base, rs):
        for k in a:
            if k in ("propeller", "tip_skew_deg", "skew_deg"): continue
            if a[k] != b[k]: diff.add(k)
ok(not diff, "skew sweep varies only in skew", f"also differs in {sorted(diff)}")

# ---- 7. every SYNTHETIC file declares what it is not --------------------
for f in glob.glob(os.path.join(ROOT, "*", "*.csv")):
    head = "".join(l for l in open(f) if l.startswith("#"))
    if "SYNTHETIC" in head:
        ok("NOT " in head, f"SYNTHETIC declares what it is not: {os.path.basename(f)}", "")
    ok("Source:" in head or "GENERATED BY" in head,
       f"provenance present: {os.path.basename(f)}", "")

print(f"checked {checks} assertions across {len(glob.glob(os.path.join(ROOT,'*','*.csv')))} CSVs")
if fails:
    print(f"\n{len(fails)} FAILED:")
    for f in fails: print("  x " + f)
    sys.exit(1)
print("all pass")
