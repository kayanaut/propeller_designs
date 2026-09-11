# Underwater Designs

Thirteen marine propulsor types, what each is for, and where it lives in this repo. Ranges are
**typical of the design class**, not the parameters of our models — those are in the
[build briefs](cad/underwater_cad.md), and are deliberately not repeated here.

`built` marks a model that exists as geometry in [cad/](cad/README.md); all thirteen have source
geometry. Model links are marked *(authoritative)* where the source publishes real offsets, and
*(third-party)* where it is an unvalidated user upload — useful to look at, not to build from.

---

- **Fixed-pitch (FPP)** — Solid cast blade at one pitch; the marine baseline. Cheapest thrust per
  unit cost with nothing to fail, but **one design point only, and astern means reversing the shaft**.
  *Use for* any vessel with a single dominant operating condition. Z 3–6 · P/D 0.6–1.4 · BAR 0.4–0.8.
  → [brief](cad/underwater_cad.md) · [geometry](cad/underwater/fixed-pitch/) — real DTMB 4119 as a
  substitute; the B-series tables themselves are copyrighted and still open ·
  [B-series generator](https://www.wageningen-b-series-propeller.com/) *(authoritative — emits STL/STEP)* ·
  also in air: [aerial fixed-pitch](aerial_designs.md)
  *Available:* Wärtsilä, Kongsberg, MAN Alpha, MMG; small-craft stock props from ~$100.

- **Controllable-pitch (CPP)** — Hub mechanism rotates the blades in service, so thrust and reverse
  are set without reversing shaft rpm. **The oversized hub costs 1–3% efficiency**, plus an oil
  system, higher capex and real maintenance. *Use for* vessels that must hold station, tow, and
  transit. Z 4–5 · hub 0.25–0.32 D · pitch travel ~±35°.
  → [brief](cad/underwater_cad.md) · [geometry](cad/underwater/controllable-pitch/) — **real SVA
  Potsdam VP1304 blade offsets at Ø250 mm**, the repo's best measured data ·
  [Wärtsilä CPP](https://www.wartsila.com/marine/products/propulsors-and-gears/propellers/wartsila-controllable-pitch-propeller-systems)
  *Available:* Wärtsilä, Kongsberg, MAN Alpha VBS, Berg, Schottel. Effectively unavailable below
  small-workboat size.

- **Tip-loaded (Kappel / CLT)** — Tip bent into an end plate — suction side on a Kappel, pressure
  side on a CLT — to hold loading out at the tip instead of spilling it over. **Gains are wake- and
  scale-dependent so they vary by hull, tips are fragile, and it carries a price premium.**
  *Use for* full-form hulls where a few percent at one speed justifies the premium. Otherwise a
  conventional Z 4–6 blade.
  → [brief](cad/underwater_cad.md) · [geometry](cad/underwater/tip-loaded/) — synthetic tip-rake law ·
  [Tip rake on Kappel propellers](https://www.mdpi.com/2077-1312/11/4/748)
  *No model link:* both forms are proprietary (MAN Alpha Kappel, SISTEMAR CLT) and no tip-rake law
  is published. *Available:* SISTEMAR CLT; MAN Alpha Kappel FP.

- **Ducted propeller / Kort nozzle** `built` — Propeller inside a fixed accelerating nozzle. Big
  bollard-pull gain when heavily loaded, but **duct drag penalises free-running above ~10 kn, it
  collects debris, and tip-gap losses get proportionally worse as diameter shrinks**.
  *Use for* tugs, trawlers, ROV thrusters. Kaplan-type blade · tip clearance ≤1% D · L/D 0.5.
  → [brief](cad/underwater_cad.md) · [geometry](cad/underwater/ducted-kort/) — **real 19A nozzle
  ordinates and Ka-series sections** · [built model](cad/README.md): meets its brief, clearance 1.500
  with zero deviation · [Kort nozzle](https://www.wartsila.com/encyclopedia/term/kort-nozzle) ·
  also in air: [ducted fan](aerial_designs.md)
  *Available:* Schottel, Wärtsilä, Kongsberg. Vehicle scale — Blue Robotics, Tecnadyne, Copenhagen Subsea.

- **Pump-jet** `built` — Rotor and stator fully enclosed in a long **decelerating** shroud; a variant
  of the ducted propeller inverted for quiet running. Suppresses tip-vortex cavitation, at the cost of
  **weight, length and complexity that only pay where acoustic signature dominates**.
  *Use for* submarines and torpedoes. Rotor Z ~7 · stator V ≥ 2Z · tip gap ~0.2% D.
  → [brief](cad/underwater_cad.md) · [geometry](cad/underwater/pump-jet/) — note 19A is the **wrong**
  duct family here; this one decelerates · [built model](cad/README.md): **needs rebuild**, the rotor
  passes through the shroud ·
  [Pump-jets vs. propellers](https://www.twz.com/31708/veteran-sonarman-explains-why-pump-jets-are-superior-to-props-on-modern-submarines)

- **Rim-driven (hubless)** `built` — Blades carried on a motor-rotor ring with no hub and no shaft;
  the ring runs inside a stator built into the duct. **Gap viscous losses and low-Reynolds penalties
  bite hard at small scale; bearing wear, sealing and magnet corrosion set service life; premium price.**
  *Use for* compact, retractable or low-signature installations where the shaft line is the problem.
  → [brief](cad/underwater_cad.md) · [geometry](cad/underwater/rim-driven/) — blade thickness runs
  **inverted**, thickest at the ring, because the structural root is at the tip radius ·
  [built model](cad/README.md): rotor correct, duct and magnet pockets unmodelled ·
  [SCHOTTEL RimThruster](https://www.schottel.de/en/portfolio/products/product-details/srt-schottel-rimthruster)
  *Available:* Schottel SRT 200–800 kW; Copenhagen Subsea at vehicle scale.

- **Contra-rotating (CRP)** `built` — Two coaxial propellers turning opposite ways recover the swirl energy a
  single screw sheds into its wake. **Concentric shafting, bearings and seals raise cost and add
  blade-interaction noise.** *Use for* small craft where the drive already exists as a package.
  Aft disc ~0.9 D of the forward one · blade counts coprime (3+4, 4+5).
  → [brief](cad/underwater_cad.md) · [geometry](cad/underwater/contra-rotating/) — aft-disc pitch is a
  first-order estimate and **needs a lifting-line run**, not a table ·
  [built model](cad/README.md): pair correct, delete the stray third propeller ·
  [Brunvoll CRP](https://www.brunvoll.no/products/crp-contra-rotating-propellers) ·
  also in air: [coaxial](aerial_designs.md)
  *Available:* Volvo Penta IPS and Duoprop, Mercury Bravo Three — genuinely off-the-shelf at small scale.

- **Surface-piercing (SPP)** `built` — Cleaver blades run half out of the water, ventilating instead
  of cavitating; cuts appendage and wetted drag on planing hulls. **Once-per-revolution blade loading,
  heavy vibration, poor low-speed thrust and expensive drive hardware.**
  *Use for* fast planing craft above ~35 kn. Wedge sections · high P/D · articulating drive leg.
  → [brief](cad/underwater_cad.md) · [geometry](cad/underwater/surface-piercing/) — synthetic cleaver
  outline · [built model](cad/README.md): tip is tapered where a cleaver is square ·
  [Arneson surface drives](https://twindisc.com/arneson/)
  *No model link:* cleaver outlines are commercial (Rolla, Mercury Bravo) and unpublished.
  *Available:* Twin Disc Arneson ASD, France Hélices, Rolla.

- **Supercavitating** `built` — Wedge sections force a vapour cavity off the leading edge that closes
  behind the blade, so the collapse never touches metal. **The geometry is poor below its design
  speed**, which makes recording that speed part of the design rather than a footnote.
  *Use for* craft that live above ~45 kn and nowhere else. Z ~3 · P/D 1.4–1.8 · max thickness at the TE.
  → [brief](cad/underwater_cad.md) · [geometry](cad/underwater/supercavitating/) — synthetic wedge,
  design speed recorded as an explicit assumption · [built model](cad/README.md): **needs rebuild**,
  blades are detached from the hub ·
  [Supercavitating propellers](https://www.globalsecurity.org/military/systems/ship/systems/propellers-supercavitating.htm)
  *No model link:* the Newton–Rader (1961) section series is paywalled.

- **Skewed blade** — Blades swept back along the disc so each section enters the wake peak in turn;
  delays and quiets cavitation. Now the default merchant stern propeller, but **higher root stress,
  weaker astern, and more expensive pattern-making and finishing**.
  *Use for* any hull with a non-uniform wake — which is most of them. Z 4–7 · tip skew 30–70° · mild rake.
  → [brief](cad/underwater_cad.md) · [geometry](cad/underwater/skewed/) — the real DTMB 4381–4384
  series at 0/36/72/108° tip skew ·
  [Skew and tonal noise](https://www.sciencedirect.com/science/article/abs/pii/S0029801823006029) ·
  [PropCad](https://www.hydrocompinc.com/solutions/propcad/) *(authoritative — commercial parametric tool)*
  *Available:* a standard offering, not a specialty, from every large propeller OEM.

- **Loop / toroidal (Sharrow)** — Each blade closes into a loop with no free tip. Strong gains through
  the mid range, but they **converge with a well-matched conventional prop at wide-open throttle, and
  it costs much more blade area and friction, weight and money**.
  *Use for* mid-range cruise and noise, not top speed. Typically three loops · cast or 5-axis machined.
  → [brief](cad/underwater_cad.md) · [geometry](cad/underwater/toroidal/) — synthetic loop path ·
  [Sharrow Marine](https://www.sharrowmarine.com/prop) ·
  [Marine toroidal blades](https://grabcad.com/library/e-foil-and-marine-toroidal-propeller-blades-1) *(third-party)* ·
  also in air: [aerial toroidal](aerial_designs.md)
  *Available:* Sharrow with Yamaha Precision Propellers; VEEM licence for inboards up to 5 m.

- **Voith Schneider (cycloidal)** — Vertical foils on a rotating disc with cyclic pitch; full thrust
  vectoring with no rudder and no reversing. **Lower transit efficiency, deep draught, mechanically
  complex, expensive and effectively single-source.**
  *Use for* tugs and ferries where manoeuvring dominates and transit speed does not.
  4–6 foils · disc speed held constant · thrust set by eccentricity.
  → [brief](cad/underwater_cad.md) · [geometry](cad/underwater/voith-schneider/) — NACA 0016 generated
  exactly from the published equation ·
  [Voith-Schneider Propulsor](https://www.wartsila.com/encyclopedia/term/voith-schneider-propulsor-(vsp)-cycloidal-propeller) ·
  [VSP kinematics tutorial](https://grabcad.com/tutorials/voith-schneider-propeller-cycloidal-rotor-pitch-control-catia-dmu-kinematics-tutorial) *(third-party)*
  *Available:* Voith Turbo, single source.

- **Podded azimuth thruster** — Motor in a submerged steerable pod driving a fixed-pitch propeller
  directly; gearless, steers through 360°. **Pod and strut drag, slip rings and bearings, high capex,
  and any underwater repair means docking the ship.**
  *Use for* cruise ships, icebreakers, DP vessels — anything where manoeuvring and layout freedom pay
  for the capex. Puller or pusher · pod Ø ~0.5 D · pod length ~2.5 D.
  → [brief](cad/underwater_cad.md) · [geometry](cad/underwater/podded-azimuth/) — pod fairing and
  strut section · [ABB Azipod](https://new.abb.com/marine/systems-and-solutions/azipod)
  *Available:* ABB Azipod ~1–22 MW; Kongsberg Azipull, Schottel SRP, Wärtsilä steerable thrusters.

---

*Scope: propulsors in production or serious commercial development, marine and underwater. Waterjets,
tunnel thrusters and bolt-on energy-saving devices are propulsion but not propellers, and are out of
scope. Vendor and configuration data from the working notes in `_work/designs.md`. Links checked
2026-09-08; the CAESES B-series article previously cited here has been dropped — it describes the
design process but publishes no geometry.*
