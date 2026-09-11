# Aerial Designs

Eleven air propeller and rotor types, what each is for, and where it lives in this repo. Ranges are
**typical of the design class**, not the parameters of our models — those are in the
[build briefs](cad/aerial_cad.md), and are deliberately not repeated here.

None is built yet; all eleven have source geometry in [cad/](cad/README.md). Model links are marked
*(authoritative)* where the source publishes real offsets, and *(third-party)* where it is an
unvalidated user upload — useful to look at, not to build from.

---

- **Fixed-pitch (low-Re)** — Moulded or carbon blade cut for one rpm; the baseline, and the only class
  with public measured data across most sizes. **One operating point: efficiency falls away either
  side of it, and at these Reynolds numbers the section does most of the work.**
  *Use for* fixed-rpm multirotors and any airframe with one dominant condition.
  Z 2–3 · D 5–15 in · P/D 0.4–0.8 · tip Re 50k–200k.
  → [brief](cad/aerial_cad.md) · [geometry](cad/aerial/fixed-pitch/) — **real APC 10×5E mould
  geometry, 51 stations**, plus UIUC Clark-Y and Eppler E63 coordinates ·
  [UIUC propeller database](https://m-selig.ae.illinois.edu/props/propDB.html) *(authoritative — measured performance)* ·
  [APC geometry files](https://www.apcprop.com/technical-information/file-downloads/) *(authoritative — mould offsets)* ·
  also in water: [marine FPP](underwater_designs.md)

- **Custom carbon blade** — Planform and pitch made to order for one airframe and motor pairing.
  **No measured data exists for a one-off**, so it lives or dies on the design-point solve, and a
  thin sharp-TE carbon blade is less forgiving of a bad pitch choice than a moulded plastic one.
  *Use for* a known thrust, rpm and forward speed you can actually solve for.
  t/c 12% root to 7% tip · sharp trailing edge · cylindrical clamped shank.
  → [brief](cad/aerial_cad.md) · [geometry](cad/aerial/custom-carbon/) — the chord/twist CSV is the
  interface; replace it with a JavaProp/QPROP/XROTOR solve ·
  [Mejzlik](https://www.mejzlik.eu/) ·
  [propeller-FreeCAD](https://github.com/Rigel-Alves/propeller-FreeCAD) *(third-party)*

- **Collective pitch** — A variant of the custom carbon blade: pitch actuated in flight, so thrust
  changes without changing rpm. **Hub mass, linkage wear and a lot of moving parts** bought for
  response time. *Use for* aerobatic and fast-response airframes where rpm-change lag is the limit.
  Pitch ±25° · shank ~8 mm · two bearings per grip.
  → [brief](cad/aerial_cad.md) · [geometry](cad/aerial/collective-pitch/) — bearing options ·
  [T-Motor VP props](https://store.tmotor.com/categorys/manual-variable-pitch-polymer-propeller) ·
  [Variable-pitch propeller](https://grabcad.com/library/variable-pitch-reverse-thrust-propeller) *(third-party)*

- **eVTOL proprotor** — Rigid blade with no cyclic that must work as a rotor in hover and a propeller
  in wing-borne cruise. **It is optimal in neither**: the blade is a compromise, and the blend weight
  between the two design points is the entire design problem.
  *Use for* tiltrotor and tilt-wing conversions. High twist (XV-15 runs −40°) · tip Mach ≤ 0.55.
  → [brief](cad/aerial_cad.md) · [geometry](cad/aerial/evtol-proprotor/) — **real XV-15 reference
  planform**, plus hover and cruise twist with a live blend weight ·
  [Tilt-wing proprotor optimisation](https://www.sciencedirect.com/science/article/pii/S1270963823007319) ·
  [Tiltrotor UAV](https://grabcad.com/library/tiltrotor-uav-1) *(third-party)*

- **Folding blade** — Blades fold back when unpowered to cut drag in winged cruise. **Hinge wear and
  a deployment that depends on mass distribution**: the blade's centre of mass must sit outboard of
  the hinge pin or it never opens. *Use for* VTOL fixed-wing craft with lift rotors that stop.
  Hinge pin Ø ~3 mm · fold range to ~175° · running-clearance fit, not line-to-line.
  → [brief](cad/aerial_cad.md) · [geometry](cad/aerial/folding/) — hinge fit classes ·
  [T-Motor folding props](https://store.tmotor.com/categorys/folding-carbon-fiber-propeller) ·
  [Folding propellers (STL)](https://www.printables.com/model/89982-folding-propellers-for-rocket-drones) *(third-party)*

- **Ducted fan** — Rotor in a close-fitting duct; high static thrust for the disc area. **The duct's
  gain fades with forward speed and costs weight and wetted area**, and tip clearance dominates
  performance at small scale. *Use for* high static thrust in a constrained diameter.
  Hub ratio 0.4–0.5 · tip clearance ~0.5% D · stator V ≥ 2Z for tone cut-off.
  → [brief](cad/aerial_cad.md) · [geometry](cad/aerial/ducted-fan/) — duct wall cylindrical across the
  rotor plane, rotor tip pinned to the clearance ·
  [Schübeler](https://www.schubeler.com/home/) ·
  [EDF unit, 5 blade](https://grabcad.com/library/edf-ducted-fan-unit-2-5inch-5-blade) *(third-party)* ·
  also in water: [Kort nozzle](underwater_designs.md)

- **Coaxial contra-rotating** — Two rotors on one axis turning opposite ways; cancels torque and packs
  two discs into one footprint. **The lower rotor works in the upper's wake and the pair falls well
  short of double the thrust** — induced power climbs steeply as spacing shrinks.
  *Use for* footprint-limited airframes, sized against what a pair actually delivers.
  Spacing 0.1–0.2 D · lower rotor pitched up for the upper's downwash.
  → [brief](cad/aerial_cad.md) · [geometry](cad/aerial/coaxial/) — lower-rotor pitch from a
  first-order actuator-disc estimate ·
  [Coaxial swashplateless UAV](https://arxiv.org/abs/2511.04251) ·
  [Coaxial propeller V2](https://grabcad.com/library/coaxial-propeller-v2-1) *(third-party)* ·
  also in water: [marine CRP](underwater_designs.md)

- **Tip device (Q-tip)** — Tip curled aft as an inverted winglet; the certified, conservative way to
  break up the tip vortex. **It shrinks the swept disc** — a few percent of radius traded for ground
  clearance and tip noise. *Use for* noise or clearance limits on an otherwise settled blade.
  Bend from r/R ~0.92 · ~75° aft · bend radius small against the blade.
  → [brief](cad/aerial_cad.md) · [geometry](cad/aerial/q-tip/) — bend path reporting projected versus
  developed diameter, which is the trade ·
  [Hartzell Q-Tip](https://hartzellprop.com/products/top-prop/piper/twin-comanche-2-blade-q-tip/) ·
  [Swept profile blade](https://grabcad.com/library/swept-profile-propeller-blade) *(third-party)*

- **Toroidal** — Looped blade with no free tip. **Redistributes tonal noise rather than reliably
  removing it, and measured examples pay for it in torque** — the marketing and the measurements
  disagree, so read the second link before committing.
  *Use for* cases where shifting tones out of the annoying band is worth a torque penalty.
  Two or three loops · no free tip · chord scheduled along the loop path.
  → [brief](cad/aerial_cad.md) · [geometry](cad/aerial/toroidal/) — Catmull-Rom loop path, implemented
  independently because the generator below is GPL-3.0 ·
  [MIT Lincoln Laboratory](https://www.ll.mit.edu/partner-us/available-technologies/toroidal-propeller) ·
  [Measured against conventional blades](https://acta-acustica.edpsciences.org/articles/aacus/full_html/2026/01/aacus260084/aacus260084.html) ·
  [Toroidal generator](https://github.com/RaulBejarano/Ultimate-Toroidal-Propeller-Generator) *(authoritative — GPL-3.0, check before reuse)* ·
  also in water: [Sharrow loop](underwater_designs.md)

- **Serrated edge** — Owl-inspired saw-tooth edges that break up edge noise without changing the
  planform. **Broadband gain is modest and manufacturing is harder**, and the serration must follow
  the blade's own surface or it bites deeper at the root than the tip.
  *Use for* a retrofit noise fix that leaves performance essentially alone.
  Amplitude ~5% and wavelength ~10% of local chord · applied outboard of r/R 0.5.
  → [brief](cad/aerial_cad.md) · [geometry](cad/aerial/serrated/) — amplitude scheduled off local
  chord at every station ·
  [Serrated TE for drone noise](https://www.sciencedirect.com/science/article/abs/pii/S0003682X25005171)
  *No model link:* serrations are applied to a base blade, so there is no separate model to point at.

- **Cyclorotor** — Vertical blades on a drum with cyclic pitch; instant thrust vectoring at low tip
  speed. **Structural and bearing loads are severe and efficiency trails a conventional rotor** —
  this is a research configuration, not something you buy.
  *Use for* experimental craft where vectoring response is the objective.
  4–6 blades · c/R ~0.35 · pitch ±35° · symmetric section.
  → [brief](cad/aerial_cad.md) · [geometry](cad/aerial/cyclorotor/) — NACA 0015 generated exactly from
  the published equation ·
  [Hover performance study](https://sites.utexas.edu/sirohi/files/2017/07/010_parsons07_jahs.pdf)
  *No model link:* no production hardware exists to model.

---

*Scope: air propellers and rotors for UAV and eVTOL scale, plus the full-scale designs (Q-tip,
proprotor) that the small-scale versions are derived from. Helicopter main rotors with cyclic and
flapping hinges are a different discipline and are out of scope. Links checked 2026-09-08.*
