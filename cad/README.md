# CAD Models

Briefs: [aerial_cad.md](aerial_cad.md) · [underwater_cad.md](underwater_cad.md).
Datums: [CONVENTIONS.md](CONVENTIONS.md) — pitch line, generator line, rake and camber
definitions the briefs leave implicit. Every CSV repeats them in its own header, so a table
never has to be interpreted from memory.
Models: [underwater/](underwater/) · [aerial/](aerial/), one folder per design, each with a
`source-geometry.md` naming the data it needs and the CSVs holding what has been obtained.
Generated tables come from [tools/make-geometry.py](tools/make-geometry.py) (underwater) and
[tools/make-aerial-geometry.py](tools/make-aerial-geometry.py) — re-runnable, byte-identical,
each with its own rules checker. **The two domains do not share rules:** the 1 mm minimum
trailing-edge thickness is wet-specific and must never be applied to an aerial blade, which
wants a sharp TE. Provenance is marked per requirement: `SOURCED` (published table, cited),
`GENERATED` (published equation), `SYNTHETIC` (built here from the brief's own numbers — never
from a real series), `NOT SOURCED` (missing, with the reason). All 24 designs now have geometry. The five remaining
`NOT SOURCED` entries are real-source gaps a synthetic stand-in does not close — four marine
(B-series ×2, DTMB 4381–4384 offsets, Newton–Rader) and one aerial (NACA 6-series ordinates,
which are tabulated rather than equation-derived).

# **Built:** 
6 of 13 underwater, 0 of 11 aerial. All six are watertight and manifold.

- **[ducted-kort](underwater/ducted-kort/model.stl)** — *meets its brief.* Nozzle ID 250, Ø247
  `Z=4`, clearance 1.500 with zero deviation across the tip chord. Checked against real 19A
  ordinates ([source-geometry.md](underwater/ducted-kort/source-geometry.md)): wall is
  cylindrical over the sweep and the tip is square. Nothing outstanding.
- **[surface-piercing](underwater/surface-piercing/model.stl)** — *fix the planform.* The only
  single unioned solid in the set. Tip is tapered, not a square-cut cleaver. Ø285.6 vs 250.
- **[rim-driven](underwater/rim-driven/model.stl)** — *fix the duct.* Rotor correct and truly
  hubless. Duct is a bare annulus; magnets overlap the ring instead of sitting in pockets.
- **[contra-rotating](underwater/contra-rotating/model.stl)** — *delete one body.* Pair is correct
  and the mirror is genuine. A stray third propeller sits at `z=0` and clashes with the sleeve.
- **[pump-jet](underwater/pump-jet/model.stl)** — **rebuild.** Rotor cuts through the shroud by
  9.5 mm; stator sits inside the rotor, not up- or downstream; built on Y.
- **[supercavitating](underwater/supercavitating/model.stl)** — **rebuild.** Blades are detached —
  a 4.62 mm gap, nothing unioned. Ø297.7 vs 250.

# **Not built**

**underwater:** 
- FPP
- CPP
- Tip-loaded
- Skewed
- Toroidal
- Voith Schneider
- Podded azimuth

**aerial:** 
- Fixed-pitch
- Custom carbon
- Collective pitch
- eVTOL proprotor
- Folding
- Ducted fan
- Coaxial
- Q-tip
- Toroidal
- Serrated
- Cyclorotor.
