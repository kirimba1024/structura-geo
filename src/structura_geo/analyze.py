import math
from collections import Counter
from copy import deepcopy
from numbers import Real
from typing import Union

import numpy as np

from structura_core.blockstates import state_key
from structura_core.formats import load_structure
from structura_core.nbt_io import PathInput
from structura_core.structure import AIR_NAMES, Structure

from . import analysis_geometry as geometry
from .analysis_report import analysis_warnings, build_report, summary_line
from .components import label_positions, use_dense_grid
from .materials import (
    LIGHT_SOURCES,
    MATERIAL_FAMILIES,
    METRIC_NATURAL_BLOCKS,
    NETHER_BLOCKS,
    WATER_BLOCKS,
)


class StructureAnalyzer:
    def __init__(self, path: Union[PathInput, Structure]):
        source = path if isinstance(path, Structure) else load_structure(path)
        if isinstance(path, Structure):
            source.validate()
        self.path = str(source.path)
        self.size = source.size
        self.palette = list(source.palette)
        self.palette_raw = deepcopy(source.palette_raw)
        self.positions = {
            pos: idx
            for pos, idx in source.present.items()
            if source.palette[idx] not in AIR_NAMES
        }
        self.air_positions = {
            pos for pos, idx in source.present.items() if source.palette[idx] in AIR_NAMES
        }
        self._components = None
        self._rooms = None
        self._label_cache = None
        self._state_grid_cache = None
        self._histogram_cache = None

    def bbox_volume(self) -> int:
        sx, sy, sz = self.size
        return sx * sy * sz

    def density(self) -> float:
        return len(self.positions) / self.bbox_volume()

    def _label_solid(self):
        if self._label_cache is None:
            self._label_cache = label_positions(self.positions)
        return self._label_cache

    def connected_components(self):
        if self._components is None:
            sizes = sorted(self._label_solid().sizes[1:].tolist(), reverse=True)
            self._components = [range(size) for size in sizes]
        return list(self._components)

    def debris_fraction(self) -> float:
        comps = self.connected_components()
        if not comps:
            return 0.0
        main = len(comps[0])
        total = sum(len(c) for c in comps)
        return 1 - main / total

    def floating_fraction(self) -> float:
        if not self.positions:
            return 0.0
        components = self._label_solid()
        ys = np.fromiter((pos[1] for pos in self.positions), dtype=np.int32)
        touching = np.unique(components.labels[ys == ys.min()])
        grounded = int(components.sizes[touching].sum())
        return 1 - grounded / len(self.positions)

    def block_histogram(self):
        if self._histogram_cache is None:
            counts = Counter(self.positions.values())
            self._histogram_cache = Counter()
            for index, count in counts.items():
                self._histogram_cache[self.palette[index]] += count
        return self._histogram_cache.copy()

    def palette_entropy(self) -> float:
        hist = self.block_histogram()
        total = sum(hist.values())
        entropy = 0.0
        for n in hist.values():
            p = n / total
            entropy -= p * math.log2(p)
        return entropy

    def compression_ratio(self):
        return geometry.compression_ratio(self.positions)

    def _state_grid(self):
        if self._state_grid_cache is not None:
            return self._state_grid_cache
        grid = np.full(self.size, -1, dtype=np.int32)
        if self.positions:
            positions = np.array(list(self.positions.keys()), dtype=np.int32)
            keys = [state_key(entry) for entry in self.palette_raw]
            lookup = {}
            states = [lookup.setdefault(key, len(lookup)) for key in keys]
            indices = np.array([states[index] for index in self.positions.values()], dtype=np.int32)
            grid[tuple(positions.T)] = indices
        self._state_grid_cache = grid
        return grid

    def mirror_symmetry(self, axis: str = "x") -> float:
        if axis not in ("x", "y", "z"):
            raise ValueError("axis must be x, y or z")
        if not self.positions:
            return 0.0
        axis_i = {"x": 0, "y": 1, "z": 2}[axis]
        if not use_dense_grid(self.size, len(self.positions)):
            states = [state_key(entry) for entry in self.palette_raw]
            matches = 0
            for pos, index in self.positions.items():
                mirrored = list(pos)
                mirrored[axis_i] = self.size[axis_i] - 1 - pos[axis_i]
                other = self.positions.get(tuple(mirrored))
                matches += other is not None and states[index] == states[other]
            return matches / len(self.positions)
        grid = self._state_grid()
        mirrored = np.flip(grid, axis=axis_i)
        match = int(np.sum((grid == mirrored) & (grid != -1)))
        return match / len(self.positions)

    def natural_terrain_fraction(self) -> float:
        hist = self.block_histogram()
        total = sum(hist.values())
        if not total:
            return 0.0
        natural = sum(n for name, n in hist.items() if name in self._NATURAL_BLOCKS)
        return natural / total

    def bedrock_fraction(self) -> float:
        hist = self.block_histogram()
        total = sum(hist.values())
        if not total:
            return 0.0
        return hist.get("minecraft:bedrock", 0) / total

    def terrain_profile(self):
        natural_ys = [
            pos[1]
            for pos, idx in self.positions.items()
            if self.palette[idx] in self._NATURAL_BLOCKS
        ]
        if not natural_ys:
            return None
        y0, y1 = min(natural_ys), max(natural_ys)
        return {
            "min_y": y0,
            "max_y": y1,
            "span": y1 - y0 + 1,
            "block_count": len(natural_ys),
            "density_profile": geometry.sparkline(Counter(natural_ys), y0, y1),
        }

    def rooms(self):
        if self._rooms is None:
            sizes = label_positions(self.air_positions, connectivity=6).sizes[1:]
            self._rooms = sorted(sizes.tolist(), reverse=True)
        return list(self._rooms)

    def footprint_elongation(self):
        return geometry.footprint_elongation(self.positions)

    def vertical_profile(self, width: int = 40) -> str:
        return geometry.vertical_profile(self.positions, width)

    def floor_count(self):
        return geometry.floor_count(self.positions)

    def environment_fit(self) -> dict:
        hist = self.block_histogram()
        total = sum(hist.values()) or 1
        water = sum(n for name, n in hist.items() if name in self._WATER_BLOCKS) / total
        nether = (
            sum(n for name, n in hist.items() if name in self._NETHER_BLOCKS) / total
        )
        glass = sum(n for name, n in hist.items() if "glass" in name) / total
        stone_family = (
            sum(
                n
                for name, n in hist.items()
                if "stone" in name or "cobble" in name or "brick" in name
            )
            / total
        )
        return {
            "water_material_fraction": round(water, 4),
            "nether_material_fraction": round(nether, 4),
            "glass_fraction": round(glass, 4),
            "stone_family_fraction": round(stone_family, 4),
            "has_own_ground": self.natural_terrain_fraction() > 0.15,
            "cave_friendly_guess": stone_family > 0.5 and glass < 0.05,
        }

    def light_coverage(self, radius: float = 7.0):
        if isinstance(radius, bool) or not isinstance(radius, Real) or not math.isfinite(radius) or radius < 0:
            raise ValueError("radius must be finite and nonnegative")
        lights = [
            pos
            for pos, idx in self.positions.items()
            if self.palette[idx] in self._LIGHT_SOURCES
        ]
        if not lights or not self.air_positions:
            return len(lights), 0.0
        from scipy.spatial import cKDTree

        tree = cKDTree(np.array(lights))
        distances, _ = tree.query(np.array(list(self.air_positions)))
        covered = int((distances <= radius).sum())
        return len(lights), round(covered / len(self.air_positions), 4)

    def doors(self):
        found = []
        for pos, index in self.positions.items():
            name = self.palette[index]
            if not name.endswith("_door"):
                continue
            entry = self.palette_raw[index]
            props = entry.get("Properties")
            if props is None or str(props.get("half", "")) != "lower":
                continue
            facing = props.get("facing")
            if facing is None or str(facing) not in self._DOOR_FACING:
                continue
            found.append({"pos": list(pos), "block": name, "facing": str(facing)})
        return found

    def material_families(self) -> dict:
        hist = self.block_histogram()
        total = sum(hist.values()) or 1
        totals = Counter()
        for name, n in hist.items():
            base = name.split(":", 1)[-1]
            family = next(
                (
                    fam
                    for fam, keys in self._MATERIAL_FAMILIES
                    if any(k in base for k in keys)
                ),
                "other",
            )
            totals[family] += n
        return {fam: round(100 * n / total, 1) for fam, n in totals.most_common()}

    _NATURAL_BLOCKS = METRIC_NATURAL_BLOCKS
    _DOOR_FACING = ("north", "south", "east", "west")
    _WATER_BLOCKS = WATER_BLOCKS
    _NETHER_BLOCKS = NETHER_BLOCKS
    _LIGHT_SOURCES = LIGHT_SOURCES
    _MATERIAL_FAMILIES = MATERIAL_FAMILIES

    def summary_line(self, report: dict) -> str:
        return summary_line(report)

    def report(self) -> dict:
        return build_report(self)

    def _warnings(self, comps, debris_fraction, floating_fraction):
        return analysis_warnings(self, comps, debris_fraction, floating_fraction)


def main(argv=None):
    from .analysis_cli import parse_args, print_analysis

    args = parse_args(argv)
    print_analysis(StructureAnalyzer(args.path), histogram=args.histogram, json_output=args.json)


if __name__ == "__main__":
    main()
