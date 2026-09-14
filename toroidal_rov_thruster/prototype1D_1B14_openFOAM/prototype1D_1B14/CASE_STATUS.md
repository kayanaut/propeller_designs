# Case status

- Case dictionaries: prepared.
- Mesh levels and acceptance criteria: prepared.
- Exact 1B-14 rotor/duct surfaces: **required from the prior parametric geometry package**.
- OpenFOAM execution: not performed; solver executables are not installed in this workspace.
- CFD performance claims: none.

The case becomes runnable after the exact STL pair passes `scripts/validate_geometry.py` and OpenFOAM `surfaceCheck`.
