# Extraction verification

Checked on 2026-09-08 with Python 3.9.6, NumPy 1.26.4 and SciPy 1.13.1.

- Core 0.6.1: 246 tests passed from source and from the installed wheel.
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

Fresh base installation also passed 189 core tests with 50 optional-translation
skips; geo without its legacy extra passed 46 tests with one skip. Upgrading from
the previous core build through geo's dependency selected core 0.6.1, retained
the analysis commands and passed `pip check`. The minimum core requirement
excludes 0.6.0. See [migration](migration.md) for release order.
