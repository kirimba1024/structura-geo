import pytest

from structura_geo.largest_component import drop_tiny_components, keep_largest_component


@pytest.mark.parametrize("offset", [5, 2_000_000_000])
def test_cleanup_preserves_records_order_and_corner_connections(offset):
    main = [((x, x, x), index, {"payload": index}) for index, x in enumerate((-3, -2, -1))]
    wing = [((offset, 0, 0), 4, {}), ((offset + 1, 0, 0), 5, {})]
    debris = [((0, 5, 0), 6, {})]
    blocks = [wing[0], main[0], debris[0], main[1], wing[1], main[2]]

    assert keep_largest_component(blocks) == (main, 3)
    assert drop_tiny_components(blocks, 1) == ([wing[0], main[0], main[1], wing[1], main[2]], 1)
    assert drop_tiny_components(blocks, 100) == (main, 3)
    assert blocks[2] is debris[0]


@pytest.mark.parametrize("offset", [5, 2_000_000_000])
def test_largest_tie_is_spatially_deterministic(offset):
    left, right = ((-1, 0, 0), 1), ((offset, 0, 0), 2)

    assert keep_largest_component([right, left]) == ([left], 1)
    assert drop_tiny_components([right, left], 1) == ([left], 1)


def test_cleanup_keeps_an_empty_input_empty():
    assert keep_largest_component([]) == ([], 0)
    assert drop_tiny_components([], 6) == ([], 0)


def test_cleanup_file_preserves_air_metadata_and_rebases_block_entities(tmp_path, make_structure):
    from amulet_nbt import CompoundTag, IntTag, StringTag

    from structura_core import Structure, save_structure
    from structura_geo.largest_component import clean_structure

    source = make_structure([((1, 1, 1), 0), ((2, 1, 1), 0), ((4, 2, 2), 0), ((1, 2, 1), 1)])
    source.block_nbt[1, 1, 1] = CompoundTag({"x": IntTag(1), "y": IntTag(1), "z": IntTag(1)})
    source._root["author"] = StringTag("Builder")
    src, dst = tmp_path / "source.nbt", tmp_path / "clean.nbt"
    assert save_structure(source, src, source.size) == 4
    clean_structure(src, dst)
    restored = Structure(dst)

    assert restored.size == (2, 2, 1)
    assert restored.is_air((0, 1, 0))
    assert restored._root["author"] == StringTag("Builder")
    assert restored.block_nbt[0, 0, 0] == CompoundTag({axis: IntTag(0) for axis in "xyz"})
    assert len(Structure(src).present) == 4


def test_cleanup_rejects_unknown_modes_without_writing(tmp_path):
    from structura_geo.largest_component import clean_structure

    output = tmp_path / "out.nbt"
    with pytest.raises(ValueError, match="mode"):
        clean_structure(tmp_path / "source.nbt", output, mode="typo")
    assert not output.exists()
