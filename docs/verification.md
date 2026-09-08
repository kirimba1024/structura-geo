# Extraction verification

Checked on 2026-09-08 with Python 3.9.6, NumPy 1.26.4 and SciPy 1.13.1.

- Core: 238 tests passed from source and from the installed wheel.
- Geo: 47 tests passed from source and from the installed wheel, including
  component/room metrics, sparse geometry, morphology, aesthetics and legacy
  placement preparation.
- Ruff passed for both packages' source and tests.
- Both wheel and source distributions built; Twine metadata checks passed.
- Native NBT, SNBT, Sponge and Litematic conversion/readback succeeded with
  imports of geo, SciPy, Amulet Core and PyMCTranslate blocked.
- Core's wheel contains no transferred geometry modules. Its base dependency
  list has no SciPy or geo requirement.
- The analysis benchmark completed dense, sparse and distant-coordinate inputs.

These checks validate the local companion core revision. They do not establish
compatibility with the currently published core wheel; see [migration](migration.md).
