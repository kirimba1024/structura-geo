# Migration from core

Core owns validated structures, format readers/writers, world reading and
conversion. Geo owns geometric analysis, metrics, morphology and placement
preparation. The dependency is one-way: geo imports core; core does not import
geo or SciPy.

## Python imports

Replace the `structura_core` prefix with `structura_geo` for these modules:

- `analyze`, `analysis_geometry`, `analysis_report`, `analysis_cli`
- `components`, `largest_component`, `voxel`
- `materials`, `aesthetics`, `check_doors`, `check_leaks`, `legacy_cleanup`

`StructureAnalyzer` remains available from `structura_geo.analyze`; its input
and report contracts are unchanged. Existing core data and format imports stay
in `structura_core`. There are no core-to-geo compatibility re-exports.

## Commands

Installing geo provides `structura-analyze`, `structura-check-doors` and
`structura-check-leaks` with their existing arguments. `python -m` invocations
use the new module prefix as well.

`structura-convert-legacy` stays in core and preserves bounds, explicit air,
materials and connections. Its existing entity selection is unchanged;
`--all-entities` retains every entity. `--preserve-layout` is accepted as a no-op.
The Python option `prepare_for_placement=True` raises an error identifying the
new entry point before opening input or writing output.

`structura-prepare-legacy` and `structura_geo.convert_legacy.convert` perform
the historical placement cleanup, including trimming, bedrock replacement,
connection repair and air selection. Install geo's `legacy` extra for these.

## Development and releases

The extraction requires the companion core checkout containing the shared
`blockstates`, `validation`, `entity_positions` and legacy data helpers. Install
both local projects together as shown in the README. The currently published
core 0.6.0 does not contain this migration. Coordinate the next core/geo releases
and downstream version bounds before publishing packages to PyPI.

The useful geometry tests move with their implementation, including the parent
workspace's aesthetic tests. Core retains conversion and preservation coverage.
The analysis benchmark lives in `checks/benchmark_analysis.py` here.

Envelope and cavern generation belong to geo. Historical recovered sources in
the parent workspace are archival material, not part of this runtime extraction.
