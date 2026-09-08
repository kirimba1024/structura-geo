# structura-geo

Geometric analysis and placement preparation for Minecraft structures.
Core owns structure data and format conversion; geo owns spatial algorithms,
room/component metrics, morphology, aesthetic analysis and placement cleanup.
The dependency points from geo to core. Core does not require geo or SciPy.

## Development installation

Geo 0.1.0 requires core >=0.6.1,<0.7. Install both local checkouts together
while preparing the paired release:

```bash
python -m pip install -e ./libs/structura-core -e ./libs/structura-geo
```

After core 0.6.1 and geo 0.1.0 are published, `pip install structura-geo`
resolves the supported core version automatically.

## Analysis

```python
from structura_core import load_structure
from structura_geo.analyze import StructureAnalyzer

source = load_structure("house.litematic", region="Main")
report = StructureAnalyzer(source).report()
print(report["room_count"], report["room_sizes"])
```

```bash
structura-analyze house.nbt --json
structura-check-doors house.nbt
structura-check-leaks house.nbt
```

`structura_geo.voxel` provides dilation, erosion, closing and signed distance.
`structura_geo.largest_component` provides explicit component cleanup.
See [metric semantics](docs/analysis.md) and [migration](docs/migration.md).

## Legacy placement preparation

Install the `legacy` extra, then run `structura-prepare-legacy old.schematic house.nbt`.
This retains the previous explicit preparation workflow: trim bounds, classify
interior air, clear door approaches, fix pane connections and replace bedrock.
`structura_core.convert_legacy.convert` now preserves layout by default.

## Envelope and cavern

Envelope construction, cavern volumes and related spatial generation belong in
this package. The historical implementation remains archived in the parent
workspace under `docs/recovered-geo`; it has not been silently restored as runtime
code. This extraction transfers the working analysis and placement functionality.
