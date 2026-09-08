# Geo architecture

Geo depends on core for validated structures and format I/O. Core never imports
geo. Geometry, material analysis, morphology and placement policy belong here.

## Analysis

| Module | Responsibility |
|---|---|
| `analyze` | Snapshot the input, own caches and expose the established metric methods. |
| `components` | Shared 6/26-connected labeling of occupied coordinates for analysis and cleanup. |
| `analysis_geometry` | Numerical profiles, floor peaks, footprint PCA and stream compression. |
| `materials` | Classification tables. |
| `analysis_report` | Report fields, warning policy and readable summary. |
| `analysis_cli` | Argument parsing and text/JSON presentation, without loading documents. |

`StructureAnalyzer` accepts a `Structure` or a path supported by `load_structure`.
It copies the relevant input data. Treat its input attributes as a read-only
snapshot; after editing a structure, create a new analyzer. Histogram, component
and room results can be modified by callers without corrupting cached results.
Report methods preserve subclass overrides.

Component labeling retains per-block labels and component sizes rather than a
full labeled volume. Compact masks use SciPy; large or sparse bounding boxes use
a traversal of occupied coordinates. Dense allocation is capped at two million
cells and at 64 cells per input position, with a 4096-cell floor. Both paths use
the same connectivity and spatial tie ordering. Symmetry uses the same allocation
policy and compares canonical states, including properties, rather than palette
indices. Floor profiles collapse long empty gaps to two zero layers: the
two-layer peak separation and peak prominence are retained without allocating
an array across the full height.

See [Analysis semantics](analysis.md) for the metric contracts and limitations.

## Placement preparation

`convert_legacy` uses core translation and NBT I/O. `legacy_cleanup` trims bounds,
repairs connections and selects air for placement. It operates on the owned
block collection without loading or writing files. `voxel` and `components`
provide the numerical operations shared by analysis and cleanup.
