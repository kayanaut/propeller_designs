# P2A-M2: 300-iteration direction check (L0)

Run 2026-09-15 with `./Allsolve 300` on the L0 mesh (`P2A_M2_mesh_L0.md`). Setup:
- steady MRF, k-omega SST, seawater, bollard (still water);
- 3000 rpm forward: `omega -314.159` about +x;
- 6 cores.

**Purpose:** confirm the thruster works the right way round before a long run. **The values are not converged and must not be used as results.**

## Direction checks (all passed)

| Check | Expected | Result |
|---|---|---|
| Assembly force | Negative x (thrust toward −x) | −31.9 N mean over the run; −30.0 to −32.5 N over the last 50 iterations |
| Shaft power −ω·Mx | Positive: the rotor drives the water | +155 W (last 50 iterations) |
| Jet | +x, water entering the front bellmouth | +15.5 L/s through the rotor, consistent with the force |

## How the values were moving (provisional)

| Iterations | Thrust (rotor + stator) | Torque | Shaft power | Flow | Rotor min wall pressure |
|---|---:|---:|---:|---:|---:|
| 151–200 | 25.9 N (20.8 + 5.1) | 0.487 N·m | 153 W | 13.5 L/s | −196 kPa |
| 201–250 | 27.0 N (20.9 + 6.2) | 0.501 N·m | 157 W | 14.5 L/s | −210 kPa |
| 251–300 | 31.5 N (24.0 + 7.5) | 0.493 N·m | 155 W | 15.5 L/s | −197 kPa |

- **Trend:** thrust and flow were still rising at iteration 300. Torque was already nearly steady at about 0.49–0.50 N·m.
- **For orientation only:** the converged 1B-14 design A run gave 27.0 N, 0.451 N·m, 142 W and 16.0 L/s. It used a different rotor, domain and mesh.
- **Residuals:** p dropped 4.6 decades; U 1.9–2.2; k 2.5; omega 1.5. The turbulence solver printed "bounding k" warnings up to iteration 292. That is common while the flow develops; check it has stopped in the long run.
- **Time:** 4.43 s per iteration on 6 cores, so 5000 iterations take about 6.2 hours.

## Things to watch in the full run

- **Cavitation:** the lowest rotor wall pressure was about −200 kPa gauge. At 1 m depth that is far below vapour pressure; the convergence report says it clears below about 12 m. Design A's converged value was −141 kPa. This L0 value is unconverged and uses wall functions, so it only shows where to look.
- **Motor torque:** the rotor absorbs about 0.5 N·m at 3000 rpm. Check this against the M200's real capacity once converged. Blue Robotics' simulated 0.5 N·m "stall torque" does not match the T200's measured 390 W at 3600 rpm, so it is not a firm limit.

## Next step (needs a go-ahead)

Run the full forward solve: `./Allsolve` (5000 iterations, about 6.2 h). Then run `python3 scripts/convergence_report.py --write results/P2A_M2_L0_forward.md`.
