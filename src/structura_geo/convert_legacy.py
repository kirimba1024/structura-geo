import argparse

from structura_core.legacy_blocks import open_legacy, read_blocks, structure_root
from structura_core.legacy_entities import _legacy_entities, _legacy_tile_text, _structure_entity, restore_sign_text
from structura_core.nbt_io import load_root, write_root
from structura_core.validation import int32
from structura_core.version import DATA_VERSION, JAVA_VERSION

from .legacy_cleanup import FORCED_REPLACEMENTS, prepare_placement


def _placement_report(result):
    if result.origin != (0, 0, 0) or result.previous_size != result.size:
        before = "x".join(map(str, result.previous_size))
        after = "x".join(map(str, result.size))
        offset = ",".join(map(str, result.origin))
        print(f"    trimmed bounding box: {before} -> {after} (offset {offset})")
    if result.pane_fixes:
        print(f"    pane/bars connection fixes: {result.pane_fixes}")
    print(f"    air: {result.exterior_air} exterior (omitted), "
          f"{result.interior_air} interior, {result.door_air} door-clearance (placed explicitly)")


def _structure_root(data, entities, origin, data_version, prepare_for_placement):
    records = []
    for position, payload in entities:
        pos = tuple(value - offset for value, offset in zip(position, origin))
        if prepare_for_placement and not all(0 <= value < limit for value, limit in zip(pos, data.size)):
            continue
        records.append(_structure_entity(pos, payload))
    return structure_root(data, records, data_version)


def convert(
    src_path: str,
    dst_path: str,
    data_version: int,
    target_version=JAVA_VERSION,
    quiet_errors: bool = True,
    preserve_all_entities: bool = False,
    *,
    prepare_for_placement: bool = True,
):
    """Translate legacy input, optionally applying the historical placement cleanup."""
    data_version = int32(data_version, "DataVersion")
    if len(target_version) != 3 or any(part < 0 for part in target_version):
        raise ValueError(f"invalid Java target version: {target_version!r}")
    target_version = tuple(int32(part, "Java version component") for part in target_version)
    with open_legacy(src_path, quiet_errors) as level:
        data = read_blocks(level, ("java", target_version), omit_air=prepare_for_placement,
                           replacements=FORCED_REPLACEMENTS if prepare_for_placement else {})
        legacy_root = load_root(src_path)
        entities = _legacy_entities(legacy_root, preserve_all_entities)
        legacy_text = _legacy_tile_text(legacy_root)
        origin = (0, 0, 0)
        if prepare_for_placement:
            placement = prepare_placement(data, entities, preserve_all_entities, src_path)
            origin = placement.origin
            _placement_report(placement)
        restored = restore_sign_text(data.blocks, legacy_text, origin)
        print(f"    sign text restored: {restored}")
        root = _structure_root(data, entities, origin, data_version, prepare_for_placement)
        print(f"    entities carried: {len(root['entities'])}")
        write_root(root, dst_path)
        print(f"OK  {src_path}")
        print(f"    -> {dst_path}")
        print(f"    size: {'x'.join(map(str, data.size))}")
        print(f"    palette entries: {len(data.palette_list)}")
        print(f"    blocks written: {len(data.blocks)}")
        print(f"    block entities: {data.block_entities_count}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="legacy .schematic path")
    ap.add_argument("dst", help="output vanilla structure .nbt path")
    ap.add_argument("--data-version", type=int, default=DATA_VERSION)
    ap.add_argument(
        "--preserve-layout", action="store_true",
        help="preserve selection bounds, air, materials and connections instead of placement cleanup",
    )
    ap.add_argument("--all-entities", action="store_true", help="retain every source entity")
    ap.add_argument(
        "--target-version",
        default="1.21.1",
        help="Amulet block translation target, for example 1.21.1",
    )
    args = ap.parse_args()
    try:
        target_version = tuple(int(part) for part in args.target_version.split("."))
    except ValueError:
        ap.error("--target-version must contain three integers, for example 1.21.1")
    if len(target_version) != 3:
        ap.error("--target-version must contain three integers, for example 1.21.1")
    convert(
        args.src, args.dst, args.data_version, target_version,
        preserve_all_entities=args.all_entities,
        prepare_for_placement=not args.preserve_layout,
    )


if __name__ == "__main__":
    main()
