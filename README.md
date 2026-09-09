# Propeller Designs

- [aerial_designs.md](aerial_designs.md) 
- [underwater_designs.md](underwater_designs.md)

## CAD prompts

- [cad/aerial_cad.md](cad/aerial_cad.md) — build briefs for the aerial designs
- [cad/underwater_cad.md](cad/underwater_cad.md) — build briefs for the underwater designs

## Geometry creation

- [CadQuery](https://cadquery.readthedocs.io/) — Python parametric CAD on OCCT; the scripting tool the build briefs assume
- [Parametric Propeller CAD Generator](https://github.com/Andre-AH/Parametric-Propeller-CAD-Generator) — FreeCAD, blade count, diameter and angles driven from a spreadsheet
- [bladegen](https://github.com/tallakt/bladegen) — OpenSCAD blade generator
- [OpenVSP](https://github.com/nasa/OpenVSP) — NASA parametric geometry tool with a real propeller component: activity factor, feathering, folding
- [PropCad](https://www.hydrocompinc.com/solutions/propcad/) — marine propeller geometry from chord, thickness, skew and rake distributions
- [B-Series propeller generator](https://www.wageningen-b-series-propeller.com/) — Wageningen B geometry straight to STL or STEP
- [APC geometry files](https://www.apcprop.com/technical-information/file-downloads/) — `.peo` text files with real blade offsets for every APC size
- [UIUC airfoil coordinates](https://m-selig.ae.illinois.edu/ads/coord_database.html) — ~1,600 section coordinate sets; every blade loft starts here

## Data and tools

- [UIUC propeller database](https://m-selig.ae.illinois.edu/props/propDB.html) — measured low-Reynolds propeller performance
- [APC performance data](https://www.apcprop.com/technical-information/performance-data/) — computed curves for every APC size
- [XFOIL](https://web.mit.edu/drela/Public/web/xfoil/) — section polars at the low Reynolds numbers small blades actually run at
- [XROTOR](https://web.mit.edu/drela/Public/web/xrotor/) — lifting-line design and analysis for free-tip and ducted propellers
- [QPROP](https://web.mit.edu/drela/Public/web/qprop/) — propeller and motor as one system, for matching a blade to its drive
- [JBLADE](https://sites.google.com/site/joaomorgado23/downloads) — open-source BEM propeller design, coupled to XFOIL for polars
- [OpenProp](https://www.epps.com/openprop) — GPL lifting-line design code, used for AUV and ROV thrusters
- [JavaProp](https://www.mh-aerotools.de/airfoils/javaprop.htm) — free propeller design and analysis for small aircraft and boats
- [ITTC open water test procedure](https://www.ittc.info/media/9621/75-02-03-021.pdf) — how marine propeller performance is actually measured and reported
- [trimesh](https://trimesh.org/) — watertight and manifold checks on an exported mesh

*Links checked 2026-09-08.*
