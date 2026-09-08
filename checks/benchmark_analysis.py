import gc
import json
import tempfile
import time
import tracemalloc
from pathlib import Path

from amulet_nbt import CompoundTag, IntTag, ListTag

from structura_geo.analyze import StructureAnalyzer
from structura_core.nbt import parse_state, write_root


def write_fixture(path, size, blocks):
    write_root(CompoundTag({
        "DataVersion": IntTag(3955), "size": ListTag([IntTag(value) for value in size]),
        "palette": ListTag([parse_state("minecraft:stone")]), "entities": ListTag(),
        "blocks": ListTag([
            CompoundTag({"pos": ListTag([IntTag(value) for value in pos]), "state": IntTag(0)})
            for pos in blocks
        ]),
    }), path)


def measure(path):
    StructureAnalyzer(path).report()
    elapsed = []
    for _ in range(5):
        analyzer = StructureAnalyzer(path)
        start = time.perf_counter()
        report = analyzer.report()
        elapsed.append(time.perf_counter() - start)
    analyzer = StructureAnalyzer(path)
    gc.collect()
    tracemalloc.start()
    analyzer.report()
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    report.pop("path")
    return {"blocks": len(analyzer.positions), "seconds_min": min(elapsed), "peak_bytes": peak, "report": report}


def main():
    results = {}
    with tempfile.TemporaryDirectory() as directory:
        for name, size, stride in [("dense", (40, 20, 30), 1), ("sparse", (160, 20, 160), 8)]:
            path = Path(directory) / f"{name}.nbt"
            blocks = ((x, y, z) for x in range(0, size[0], stride)
                      for y in range(size[1]) for z in range(0, size[2], stride))
            write_fixture(path, size, blocks)
            results[name] = measure(path)
        path = Path(directory) / "distant.nbt"
        write_fixture(path, (2_000_000_000, 2_000_000_000, 2),
                      [(0, 0, 0), (1, 1, 1), (1_999_999_999, 1_999_999_999, 1)])
        results["distant"] = measure(path)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
