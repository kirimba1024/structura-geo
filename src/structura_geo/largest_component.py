"""Optional cleanup that keeps one connected solid component, or drops
only confidently-tiny debris while leaving everything else untouched."""

import argparse
from collections import Counter

import numpy as np

from structura_core.structure import AIR_NAMES, Structure
from structura_core.structure_writer import save_structure

from .components import label_positions


def keep_largest_component(blocks):
    """Keep the largest 26-connected component, retaining input record order."""
    if not blocks:
        return blocks, 0
    components = label_positions(block[0] for block in blocks)
    sizes = components.sizes
    if len(sizes) <= 2:
        return blocks, 0
    largest = int(np.argmax(sizes[1:]) + 1)
    filtered = [block for block, label in zip(blocks, components.labels) if label == largest]
    return filtered, len(blocks) - len(filtered)


def drop_tiny_components(blocks, max_size):
    """Drop components at or below max_size; always retain the largest one."""
    if not blocks:
        return blocks, 0
    components = label_positions(block[0] for block in blocks)
    sizes = components.sizes
    if len(sizes) <= 2:
        return blocks, 0
    largest = int(np.argmax(sizes[1:]) + 1)
    keep_labels = {label for label in range(1, len(sizes)) if sizes[label] > max_size}
    keep_labels.add(largest)
    filtered = [block for block, label in zip(blocks, components.labels) if label in keep_labels]
    return filtered, len(blocks) - len(filtered)


def clean_structure(src_path, dst_path, mode="largest", max_size=6, report_only=False):
    if mode not in {"largest", "tiny"}:
        raise ValueError("mode must be largest or tiny")
    src = Structure(src_path)
    solids = [
        (pos, index)
        for pos, index in src.present.items()
        if src.palette[index] not in AIR_NAMES
    ]
    if mode == "tiny":
        filtered, removed = drop_tiny_components(solids, max_size)
    else:
        filtered, removed = keep_largest_component(solids)
    keep = {pos for pos, _ in filtered}
    removed_positions = [pos for pos, _ in solids if pos not in keep]
    tally = Counter(src.name_at(pos) for pos in removed_positions)
    blocks = ", ".join(f"{name} x{n}" for name, n in sorted(tally.items()))
    print(f"mode={mode} removed={removed} blocks=[{blocks}]")
    if report_only:
        return
    src.present = {
        pos: index
        for pos, index in src.present.items()
        if src.palette[index] in AIR_NAMES or pos in keep
    }
    src.block_nbt = {
        pos: nbt for pos, nbt in src.block_nbt.items() if pos in src.present
    }
    if src.present:
        xs, ys, zs = zip(*src.present)
        ox, oy, oz = min(xs), min(ys), min(zs)
        new_size = (max(xs) - ox + 1, max(ys) - oy + 1, max(zs) - oz + 1)
    else:
        ox, oy, oz = 0, 0, 0
        new_size = src.size
    save_structure(src, dst_path, new_size, shift=(-ox, -oy, -oz))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("dst", nargs="?")
    parser.add_argument(
        "--mode",
        choices=("largest", "tiny"),
        default="largest",
        help="'largest': keep only the single biggest component (blunt, "
        "human-reviewed use only). 'tiny': drop only components at "
        "or below --max-size, keep everything else (safe to automate).",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=6,
        help="mode=tiny: components at or below this many blocks are dropped",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="print what would be removed, write nothing",
    )
    args = parser.parse_args()
    if not args.report_only and not args.dst:
        parser.error("dst is required unless --report-only")
    clean_structure(args.src, args.dst, args.mode, args.max_size, args.report_only)


if __name__ == "__main__":
    main()
