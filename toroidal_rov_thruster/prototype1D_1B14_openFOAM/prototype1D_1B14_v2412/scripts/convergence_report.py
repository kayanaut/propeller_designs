#!/usr/bin/env python3
"""Summarise a simpleFoam run and judge whether it has converged.

Usage: python3 scripts/convergence_report.py [--case DIR] [--window 500] [--batches 6]
                                             [--depth 1.0] [--write BASELINE.md]

Signs (CFD frame, rotation axis +x, jet designed toward +x):
  Fx      signed axial force of the water on rotor, duct and assembly. A +x jet
          pushes the assembly toward -x, so assembly Fx should be negative.
  Mx      signed moment of the water on the rotor about +x. It must oppose the
          rotation, so shaft power P = -omega * Mx must be positive.

Verdicts (exit code in brackets):
  CONVERGED (0)             strict: mean assembly Fx, rotor Mx and rotor flow over
                            the last window differ by < 0.5% from the window before,
                            peak-to-peak over the last window is < 1% of the mean, and
                            every residual has dropped 3 decades or gone flat.
  STATISTICALLY STEADY (1)  the solution oscillates about a fixed mean: over the last
                            `batches` windows, the 95% confidence half-width of each
                            mean is < 2% and the last two windows' mean is within 1%
                            of it, and every residual is flat.
  NOT CONVERGED (2)         neither.
Reported values are averages over the last `batches` windows with their 95% interval.
"""
from pathlib import Path
import argparse
import hashlib
import math
import re
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PP = ROOT / 'postProcessing'
RHO = 1025.0            # kg/m3
P_ATM = 101325.0        # Pa
P_VAPOUR = 2340.0       # Pa, seawater at 20 C
G = 9.81

MEAN_CHANGE_PCT, PEAK_TO_PEAK_PCT = 0.5, 1.0
RESIDUAL_DROP_DECADES, RESIDUAL_FLAT_DECADES = 3.0, 0.1
CI_PCT, DRIFT_PCT = 2.0, 1.0
T95 = {2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262}


def dat_files(name, filename):
    """All restart segments of a function object's output, oldest first."""
    folder = PP / name
    if not folder.exists():
        return []
    starts = sorted(folder.glob('*'), key=lambda p: float(p.name))
    return [f / filename for f in starts if (f / filename).exists()]


def read_table(name, filename):
    """(header, times, rows); later restart segments override earlier times."""
    header, rows = None, {}
    for path in dat_files(name, filename):
        for line in path.read_text().splitlines():
            if line.startswith('#'):
                if line[1:].strip().startswith('Time'):
                    header = line[1:].split()
                continue
            if line.strip():
                cells = re.sub(r'[()]', ' ', line).split()
                rows[float(cells[0])] = cells
    if not rows:
        return None
    times = sorted(rows)
    return header, times, [rows[t] for t in times]


def column(table, name):
    header, times, rows = table
    i = header.index(name)
    return np.array(times), np.array([float(r[i]) for r in rows])


def windows(t, v, width):
    last = v[t > t[-1] - width]
    prev = v[(t > t[-1] - 2 * width) & (t <= t[-1] - width)]
    return last, prev


def strict(t, v, width):
    last, prev = windows(t, v, width)
    mean = last.mean()
    if len(prev) == 0 or mean == 0:
        return dict(change=math.inf, p2p=math.inf, ok=False)
    change = abs(mean - prev.mean()) / abs(mean) * 100
    p2p = np.ptp(last) / abs(mean) * 100
    return dict(change=change, p2p=p2p, ok=change < MEAN_CHANGE_PCT and p2p < PEAK_TO_PEAK_PCT)


def statistics(t, v, width, batches):
    """Batch-means average over the last `batches` windows, 95% half-width, drift."""
    span = v[t > t[-1] - batches * width]
    n = min(batches, len(span) // max(1, int(width / np.median(np.diff(t)))))
    if n < 3:
        return dict(mean=span.mean(), ci=math.inf, ci_pct=math.inf, drift=math.inf, ok=False, n=n)
    groups = np.array_split(span[len(span) % n:], n)
    means = np.array([g.mean() for g in groups])
    mean = span.mean()
    ci = T95.get(n, 2.262) * means.std(ddof=1) / math.sqrt(n)
    drift = abs(v[t > t[-1] - 2 * width].mean() - mean) / abs(mean) * 100
    ci_pct = ci / abs(mean) * 100
    return dict(mean=mean, ci=ci, ci_pct=ci_pct, drift=drift, n=n,
                ok=ci_pct < CI_PCT and drift < DRIFT_PCT)


def omega():
    text = re.sub(r'//.*', '', (ROOT / 'constant' / 'MRFProperties').read_text())
    return float(re.search(r'omega\s+([-+0-9.eE]+)', text).group(1))


def residuals(width):
    table = read_table('residuals', 'solverInfo.dat')
    out = []
    if table is None:
        return out
    for name in [h for h in table[0] if h.endswith('_initial')]:
        t, v = column(table, name)
        v = np.maximum(v, 1e-30)
        drop = math.log10(v[:20].max() / v[t > t[-1] - 100].mean())
        last, prev = windows(t, v, width)
        flat = abs(math.log10(last.mean()) - math.log10(prev.mean())) if len(prev) else math.inf
        out.append(dict(field=name[:-8], final=v[-1], drop=drop, flat=flat,
                        strict=drop >= RESIDUAL_DROP_DECADES or flat <= RESIDUAL_FLAT_DECADES,
                        flat_ok=flat <= RESIDUAL_FLAT_DECADES))
    return out


def mesh_stats():
    log = ROOT / 'log.checkMesh'
    if not log.exists():
        return {}
    text = log.read_text()
    grab = lambda pat: (re.search(pat, text) or [None, 'n/a'])[1]
    return dict(cells=grab(r'cells:\s+(\d+)'), non_ortho=grab(r'non-orthogonality Max: ([0-9.]+)'),
                skewness=grab(r'Max skewness = ([0-9.]+)'), ok='Mesh OK.' in text)


def main():
    global ROOT, PP
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--case', help='case or archived results folder (default: this case)')
    ap.add_argument('--window', type=float, default=500, help='iterations per window')
    ap.add_argument('--batches', type=int, default=6, help='windows averaged for reported values')
    ap.add_argument('--depth', type=float, default=1.0, help='thruster depth for cavitation margin, m')
    ap.add_argument('--write', help='also write a markdown summary to this file')
    args = ap.parse_args()
    if args.case:
        ROOT = Path(args.case).resolve()
        PP = ROOT / 'postProcessing'
    w, nb = args.window, args.batches

    rf, rm, df = (read_table('rotorForces', 'force.dat'), read_table('rotorForces', 'moment.dat'),
                  read_table('ductForces', 'force.dat'))
    if rf is None or df is None or rm is None:
        sys.exit(f'no force output in {PP}')
    t, fx_rotor = column(rf, 'total_x')
    _, fx_duct = column(df, 'total_x')
    _, mx_rotor = column(rm, 'total_x')
    n = min(len(fx_rotor), len(fx_duct), len(mx_rotor))
    t, fx_rotor, fx_duct, mx_rotor = t[:n], fx_rotor[:n], fx_duct[:n], mx_rotor[:n]
    fx_total = fx_rotor + fx_duct
    om = omega()
    power = -om * mx_rotor                    # positive when the torque opposes rotation

    # name, times, values, is a convergence metric
    series = [('Assembly Fx (N)', t, fx_total, True),
              ('Rotor Fx (N)', t, fx_rotor, False),
              ('Duct Fx (N)', t, fx_duct, False),
              ('Rotor Mx (N m)', t, mx_rotor, True),
              ('Shaft power -omega*Mx (W)', t, power, False),
              ('Thrust/power -Fx/P (N/W)', t, -fx_total / np.where(power != 0, power, np.nan), False)]
    flow = read_table('ductFlow', 'surfaceFieldValue.dat')
    if flow is not None:
        ft, q = column(flow, flow[0][1])
        series.append(('Flow through rotor (L/s)', ft, q * 1e3, True))
    walls = {}
    for part in ('rotor', 'duct'):
        table = read_table(f'{part}Pressure', 'surfaceFieldValue.dat')
        if table is not None:
            pt, p = column(table, table[0][1])
            walls[part] = (pt, p * RHO / 1e3)
            series.append((f'Min wall pressure, {part} (kPa)', pt, p * RHO / 1e3, False))

    res = residuals(w)
    rows = []
    for name, st, sv, metric in series:
        s = statistics(st, sv, w, nb)
        s.update(name=name, metric=metric, strict=strict(st, sv, w) if metric else None)
        rows.append(s)
    mean_of = {r['name']: r['mean'] for r in rows}
    metrics = [r for r in rows if r['metric']]
    converged = all(r['strict']['ok'] for r in metrics) and bool(res) and all(r['strict'] for r in res)
    steady = all(r['ok'] for r in metrics) and bool(res) and all(r['flat_ok'] for r in res)
    verdict, code = (('CONVERGED', 0) if converged else
                     ('STATISTICALLY STEADY - oscillates about a stable mean', 1) if steady else
                     ('NOT CONVERGED', 2))

    span = min(nb * w, t[-1])
    lines = [f'Iterations: {t[-1]:.0f}; omega {om:+.3f} rad/s about +x; averages over the last '
             f'{span:.0f} iterations ({rows[0]["n"]} batches of {w:.0f})', '',
             f'  {"Quantity":<34}{"Mean":>11}{"95% +/-":>10}{"(%)":>7}{"drift %":>9}'
             f'{"window change %":>17}{"peak-to-peak %":>16}']
    for r in rows:
        sr = r['strict']
        lines.append(f'  {r["name"]:<34}{r["mean"]:>+11.4g}{r["ci"]:>10.3g}{r["ci_pct"]:>7.2f}'
                     f'{r["drift"]:>9.2f}' + (f'{sr["change"]:>17.2f}{sr["p2p"]:>16.2f}' if sr else ''))
    lines.append('')

    fx, p_shaft = mean_of['Assembly Fx (N)'], mean_of['Shaft power -omega*Mx (W)']
    lines.append(f'  Assembly force {fx:+.3f} N: thrust {abs(fx):.3f} N toward {"-x" if fx < 0 else "+x"}')
    lines.append(f'  Shaft power {p_shaft:+.1f} W: ' + ('rotor torque opposes rotation - rotor drives the water'
                 if p_shaft > 0 else 'NOT POSITIVE - the water drives the rotor; check the sign of omega'))
    if flow is not None:
        q = mean_of['Flow through rotor (L/s)']
        consistent = (q > 0) == (fx < 0)
        lines.append(f'  Jet {"+x (bellmouth intake, as designed)" if q > 0 else "-x (REVERSED)"}; '
                     f'force direction {"consistent" if consistent else "INCONSISTENT"} with the jet')
    lines += [f'  residual {r["field"]:<7} final {r["final"]:.2e}  dropped {r["drop"]:.1f} decades  '
              f'change over last window {r["flat"]:.2f} decades' for r in res]

    for part, (pt, p) in walls.items():
        mean = p[pt > pt[-1] - span].mean()
        worst = p[pt > pt[-1] - span].min()
        depth = max(0.0, (P_VAPOUR - P_ATM - mean * 1e3) / (RHO * G))
        p_abs = P_ATM / 1e3 + RHO * G * args.depth / 1e3 + mean
        lines.append(f'  Cavitation, {part}: mean min wall pressure {mean:+.1f} kPa gauge (worst {worst:+.1f}); '
                     f'absolute at {args.depth} m depth {p_abs:.1f} kPa vs vapour {P_VAPOUR / 1e3:.2f} kPa'
                     + (f'; needs > {depth:.1f} m depth' if depth > args.depth else '; clear'))
    yfiles = dat_files('yPlus', 'yPlus.dat')      # one row per patch per write time
    if yfiles:
        yrows = [l.split() for l in yfiles[-1].read_text().splitlines()
                 if l.strip() and not l.startswith('#')]
        for r in [r for r in yrows if r[0] == yrows[-1][0]]:
            lines.append(f'  y+ {r[1]:<6} min {float(r[2]):.2f}  max {float(r[3]):.1f}  mean {float(r[4]):.1f}')
    lines += ['', f'VERDICT: {verdict}']
    print('\n'.join(lines))

    if args.write:
        mesh = mesh_stats()
        stl = next((p for p in (ROOT / 'constant' / 'triSurface' / 'rotor_1B14.stl',
                                ROOT / 'geometry' / 'rotor_1B14.stl') if p.exists()), None)
        digest = hashlib.sha256(stl.read_bytes()).hexdigest() if stl else 'n/a'
        md = ['# Prototype 1B-14 L0 baseline', '',
              'Steady MRF, k-omega SST, bollard (still water), seawater, 3000 rpm. '
              'Generated by `scripts/convergence_report.py`.', '',
              '## Mesh and geometry', '',
              f'- Cells {mesh.get("cells")}; max non-orthogonality {mesh.get("non_ortho")}; '
              f'max skewness {mesh.get("skewness")}; checkMesh {"Mesh OK" if mesh.get("ok") else "FAILED"}',
              f'- Rotor STL sha256 `{digest}`; see geometry/GEOMETRY_REPORT.md', '',
              '## Result', '', '```', *lines, '```', '']
        Path(args.write).write_text('\n'.join(md))
    sys.exit(code)


if __name__ == '__main__':
    main()
