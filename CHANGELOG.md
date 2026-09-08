# Changelog

## 0.1.0

- Extract analysis, room/component metrics, morphology, aesthetics and placement
  preparation from core, preserving their numerical contracts.
- Supply the existing analysis and diagnostics commands under `structura_geo`.
- Add `structura-prepare-legacy` for the previous placement preparation workflow.
- Require core >=0.6.1,<0.7 so package installation selects the shared data API
  needed by geo. Core remains independent of geo and SciPy.
- Carry geometry tests and repeatable analysis benchmarks with their implementation.
