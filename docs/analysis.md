# Analysis semantics

```python
from structura_core import load_structure
from structura_geo.analyze import StructureAnalyzer

source = load_structure("house.litematic", region="Main")
analyzer = StructureAnalyzer(source)
report = analyzer.report()
```

Paths accepted by `load_structure` can also be passed directly. Use a loaded
`Structure` to select a palette, region, source game version or other loading
options first. Analysis snapshots the relevant data; changing the source does
not change an existing analyzer. Construct a new analyzer after edits. Its input
attributes are for inspection, while returned histograms and component/room
lists are independent copies.

| Metric | Meaning |
|---|---|
| Density | Non-air blocks divided by the declared bounding volume. |
| Components | Non-air cells connected through faces, edges or corners (26 neighbors). The compatibility API returns `range(size)` values, not coordinate collections. |
| Debris fraction | Share outside the largest solid component. |
| Floating fraction | Share in components that do not touch the minimum occupied Y plane. This is an undirected connectivity heuristic, not a gravity or structural support simulation. |
| Rooms | Sizes of face-connected groups of explicit air (6 neighbors). Input air may include outdoor padding; enclosure is not inferred here. |
| Mirror symmetry | Share of occupied cells whose reflected position has the same canonical block state. The reflection uses the declared size; orientation properties are compared literally. |
| Palette entropy | Shannon entropy in bits of the block-name histogram. Different properties of the same block name are grouped. |
| Compression ratio | zlib size divided by the size of the sorted position/state stream. Palette indices are retained in this stream. |
| Footprint elongation | Ratio of principal XZ spreads and the major-axis angle modulo 90 degrees. Solid blocks weight the footprint. |
| Vertical profile | Counts per Y layer, grouped into a fixed-width sparkline. Width must be a positive integer. |
| Floor count | Interior density peaks with 15% prominence and a separation of two layers; at least one for nonempty geometry. Boundary layers are not peaks. This is a heuristic, not a floor-plan detector. |
| Light coverage | Share of explicit air within the specified distance of a known light source. The radius must be finite and nonnegative. Walls, propagation and falloff are not simulated. |
| Material/environment metrics | Name-based classification using `materials.py`. These are review hints, not suitability guarantees. |

Empty input has zero components, rooms, density, debris and floating fraction.
The aesthetic construction report likewise has zero debris components for an
empty mask.

Component cleanup uses the same 26-neighbor relation as analysis.
`keep_largest_component` discards every other component, including intentional
detached geometry. `drop_tiny_components` removes components at or below its
threshold but always retains the largest one. Equal largest components use
spatial order, independently of input record order or the dense/sparse backend.
Kept block records retain their original order and payloads.

Run `python checks/benchmark_analysis.py` from the geo package with its
dependencies installed to measure two ordinary workloads and a sparse structure
whose declared dimensions reach two billion cells per axis. The benchmark warms
imports, excludes loading/snapshot construction from report timing, takes the
minimum of five runs, and measures peak allocations in a separate `tracemalloc`
run. This is not total process RSS, and times depend on the machine.
