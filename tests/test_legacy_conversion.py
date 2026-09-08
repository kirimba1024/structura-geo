import numpy as np
import pytest
from amulet_nbt import (
    ByteArrayTag, ByteTag, CompoundTag, DoubleTag, IntTag, ListTag, ShortTag, StringTag,
)

pytest.importorskip("amulet")

from structura_core import Structure
from structura_core.nbt_io import write_root
from structura_geo.convert_legacy import convert


def legacy_file(tmp_path):
    blocks = np.zeros(27, dtype=np.int8)
    blocks[12:15] = [54, 1, 7]
    root = CompoundTag({
        "Width": ShortTag(3), "Height": ShortTag(3), "Length": ShortTag(3),
        "Materials": StringTag("Alpha"), "Blocks": ByteArrayTag(blocks),
        "Data": ByteArrayTag(np.zeros(27, dtype=np.int8)),
        "TileEntities": ListTag([CompoundTag({
            "id": StringTag("minecraft:chest"),
            "x": IntTag(0), "y": IntTag(1), "z": IntTag(1),
            "Items": ListTag([CompoundTag({
                "Slot": ByteTag(0), "id": StringTag("minecraft:apple"), "Count": ByteTag(2),
            })]),
        })]),
        "Entities": ListTag([CompoundTag({
            "id": StringTag("example:item_frame"),
            "Pos": ListTag([DoubleTag(1.25), DoubleTag(.5), DoubleTag(1.75)]),
            "label": StringTag("custom entity, not a vanilla frame"),
        })]),
    })
    path = tmp_path / "source.schematic"
    write_root(root, path, name="Schematic")
    return path


def test_historical_placement_cleanup_remains_available(tmp_path, monkeypatch):
    monkeypatch.setenv("AMULET_LEVEL_CACHE_DIR", str(tmp_path / "cache"))
    output = tmp_path / "prepared.nbt"
    convert(str(legacy_file(tmp_path)), str(output), 3955)
    structure = Structure(output)

    assert structure.size == (3, 1, 1)
    assert structure.name_at((2, 0, 0)) == "minecraft:cobblestone"
    assert structure.entities == []
