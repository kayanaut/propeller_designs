# P2A-M2 forward L0 run: notes

- **Run:** `./Allsolve 5000` on the L0 mesh (`../P2A_M2_mesh_L0.md`), 6 cores, 4.1 s per iteration.
- **Stopped at iteration 4467** on 2026-09-15, by choice, after about 5 h 10 min. `stopAt writeNow` wrote the fields, and `reconstructPar` put them in the case's `4467/` folder.
- **This folder:** `REPORT.md` (from `scripts/convergence_report.py`), `history.png`, `postProcessing/` (force, flow, pressure and residual histories), `log.checkMesh`, the mesh spec and the physics settings. The fields themselves (`4467/`, `processor*/`) stay in the case and are not in git.

## Result (averages over iterations 1461–4460)

| Quantity | P2A-M2 | 1B-14 design A (L0 baseline) |
|---|---:|---:|
| Thrust, total | **29.1 ± 0.6 N** | 27.0 ± 0.5 N |
| — rotor / duct and support | 17.9 / 11.3 N | 18.4 / 8.6 N |
| Rotor torque | 0.413 ± 0.010 N·m | 0.451 N·m |
| Shaft power | 130 ± 3 W | 142 W |
| Thrust / power | 0.225 N/W | 0.191 N/W |
| Flow through rotor | 18.1 L/s | 16.0 L/s |
| Lowest rotor wall pressure | −180 kPa (clears cavitation below about 8 m) | −141 kPa (below about 4.2 m) |
| y+ rotor mean / max | 30 / 159 | 35 / 157 |

The ± values give the uncertainty of each average, not the size of the swings.

## How to read it

- **Convergence:** the verdict is NOT CONVERGED, and 5000 iterations would likely have given the same verdict.
  - Thrust and flow average out well: ±2% and ±0.6%, with drift under 0.4%.
  - Torque still drifts 2.3% between windows, above the 1% limit.
  - The steady-MRF solution swings about its mean (thrust peak-to-peak 38%), as design A's did.
  - Residuals have been flat for thousands of iterations, and "bounding k" warnings stopped after iteration 3815.
  - Treat the table as statistically steady mean values with a few per cent uncertainty on torque.
- **Against design A:** P2A-M2 gives about 8% more thrust for 8% less shaft power, and about 18% better thrust per watt. The duct and support carry more of the thrust (39% vs 32%). The cases differ, so this is not a clean comparison:
  - rotor (true helix at P/D 0.75, not P/D 0.58);
  - duct (104 mm throat, symmetric foil);
  - a motor pod and struts in the jet;
  - a larger domain (5 D / 10 D / 5 D, compared with design A's 2 D / 4 D / 2 D, where the jet left through the sides);
  - a refined wake.
- **Target:** 35 N is not reached at 3000 rpm.
  - The torque (0.41 N·m) and power (130 W) leave headroom on the M200, which is rated 390 W electrical at 16 V.
  - A higher speed is the likely route to 35 N. As a rough scaling, thrust goes with rpm² and power with rpm³, so about 3300 rpm and 170–180 W at the shaft. Confirm with a run at that speed.
- **Cavitation:** the lowest rotor pressure (−180 kPa gauge, worst −250) sits at the loop apex. At 3000 rpm and shallow depth this predicts vapour bubbles; running faster makes it worse. L0 wall functions only indicate where the suction peak is, but it is the main design risk to act on: lighter loading at the apex, or a higher `closure_t_c` or chord there.

## Not done

- Reverse run (`omega +314.159`).
- Mesh independence (L1), prism layers, and a check of how closely the snapped rotor follows the STL.
- Field pictures (ParaView is not installed); `4467/` holds the fields for later.
