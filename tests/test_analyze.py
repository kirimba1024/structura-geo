import json

import pytest
from amulet_nbt import CompoundTag, IntTag, ListTag

from structura_geo.analyze import StructureAnalyzer
from structura_core.nbt import parse_state, write_root


def analysis_file(tmp_path, blocks):
    path = tmp_path / "structure.nbt"
    write_root(CompoundTag({
        "DataVersion": IntTag(3955),
        "size": ListTag([IntTag(v) for v in (5, 3, 3)]),
        "palette": ListTag([parse_state("minecraft:stone"), parse_state("minecraft:air")]),
        "blocks": ListTag([
            CompoundTag({"pos": ListTag([IntTag(v) for v in pos]), "state": IntTag(state)})
            for pos, state in blocks
        ]),
        "entities": ListTag(),
    }), path)
    return str(path)


def test_report_keeps_geometry_metrics_and_repeated_results(tmp_path):
    analyzer = StructureAnalyzer(analysis_file(tmp_path, [
        ((0, 0, 0), 0), ((1, 0, 0), 0), ((4, 2, 2), 0),
        ((0, 1, 0), 1), ((1, 1, 0), 1),
    ]))
    report = analyzer.report()

    assert report["block_count"] == 3
    assert report["density"] == 0.0667
    assert report["components"] == 2
    assert report["main_component_size"] == 2
    assert report["debris_fraction"] == 0.3333
    assert report["floating_fraction"] == 0.3333
    assert report["room_count"] == 1
    assert report["room_sizes"] == [2]
    assert report["summary"] == analyzer.summary_line(report)
    assert any(warning.startswith("debris:") for warning in report["warnings"])
    assert analyzer.report() == report


def test_report_respects_custom_summary_and_warning_policy(tmp_path):
    class CustomAnalyzer(StructureAnalyzer):
        def summary_line(self, report):
            return f"Blocks: {report['block_count']}"

        def _warnings(self, comps, debris_fraction, floating_fraction):
            return ["custom policy"]

    report = CustomAnalyzer(analysis_file(tmp_path, [((0, 0, 0), 0)])).report()
    assert report["summary"] == "Blocks: 1"
    assert report["warnings"] == ["custom policy"]


def test_empty_structure_report_has_no_components_or_rooms(tmp_path):
    report = StructureAnalyzer(analysis_file(tmp_path, [])).report()
    assert report["block_count"] == report["components"] == report["room_count"] == 0
    assert report["density"] == report["debris_fraction"] == report["floating_fraction"] == 0


def test_in_memory_analysis_owns_its_input_snapshot(make_structure):
    source = make_structure([((0, 0, 0), 0)])
    analyzer = StructureAnalyzer(source)
    before = analyzer.report()
    source.present.clear()
    source.palette_raw.clear()

    assert analyzer.report() == before
    assert json.loads(json.dumps(before))["path"] == "<memory>"


def test_histogram_results_can_be_modified_without_corrupting_analysis(make_structure):
    analyzer = StructureAnalyzer(make_structure([((0, 0, 0), 0), ((1, 0, 0), 0)]))
    histogram = analyzer.block_histogram()
    histogram["minecraft:stone"] = 100

    assert analyzer.block_histogram() == {"minecraft:stone": 2}
    assert analyzer.report()["block_count"] == 2


def test_component_and_room_results_do_not_expose_caches(make_structure):
    analyzer = StructureAnalyzer(make_structure([((0, 0, 0), 0), ((0, 1, 0), 1)]))
    analyzer.connected_components().clear()
    analyzer.rooms().clear()

    assert [len(component) for component in analyzer.connected_components()] == [1]
    assert analyzer.rooms() == [1]


@pytest.mark.parametrize("radius", [True, -1, float("nan"), float("inf"), "7"])
def test_light_coverage_rejects_invalid_radius_even_without_lights(make_structure, radius):
    with pytest.raises(ValueError, match="radius"):
        StructureAnalyzer(make_structure()).light_coverage(radius)


def test_empty_geometry_has_no_debris():
    import numpy as np

    from structura_geo.aesthetics import construction_tells

    result = construction_tells(np.zeros((2, 2, 2), dtype=bool))

    assert result == {"floating": 0, "floating_share": 0, "whisker_columns": 0,
                      "debris_components": 0, "largest_share": 0}


def test_cli_json_and_histogram_share_the_analyzer(tmp_path, capsys):
    from structura_geo.analyze import main

    path = analysis_file(tmp_path, [((0, 0, 0), 0)])
    main([path, "--json"])
    assert json.loads(capsys.readouterr().out)["block_count"] == 1
    main([path, "--histogram", "--json"])
    assert json.loads(capsys.readouterr().out) == [{"block": "minecraft:stone", "count": 1, "percent": 100.0}]


@pytest.mark.parametrize("extension", [".nbt", ".snbt", ".litematic", ".schem"])
def test_analyzer_accepts_native_formats_and_path_objects(tmp_path, make_structure, extension):
    from structura_core import convert_structure

    source = make_structure([((0, 0, 0), 0)], size=(1, 1, 1))
    path = convert_structure(source, tmp_path / ("one" + extension))
    report = StructureAnalyzer(path).report()

    assert json.loads(json.dumps(report))["path"] == str(path)
    assert report["block_count"] == 1
    assert report["main_component_size"] == 1


@pytest.mark.parametrize("size", [(3, 1, 1), (2_000_000_000, 1, 1)])
def test_symmetry_compares_states_instead_of_palette_indices(make_structure, size):
    source = make_structure([((0, 0, 0), 0), ((size[0] - 1, 0, 0), 1)], size=size,
                            palette=("minecraft:oak_log[axis=x]", "minecraft:oak_log[axis=x]"))
    assert StructureAnalyzer(source).mirror_symmetry() == 1.0
    source.palette_raw[1] = CompoundTag({"Name": source.palette_raw[0]["Name"]})
    assert StructureAnalyzer(source).mirror_symmetry() == 0.0


def test_sparse_report_handles_distant_blocks_and_air_without_dense_volume(make_structure):
    source = make_structure([
        ((0, 0, 0), 0), ((1, 1, 1), 0), ((1_999_999_999, 1_999_999_999, 1), 0),
        ((0, 1, 0), 1), ((1, 1, 0), 1), ((1_999_999_999, 1_999_999_999, 0), 1),
    ], size=(2_000_000_000, 2_000_000_000, 2))
    report = StructureAnalyzer(source).report()

    assert report["main_component_size"] == 2
    assert report["components"] == 2
    assert report["floating_fraction"] == 0.3333
    assert report["room_sizes"] == [2, 1]
    assert len(report["vertical_profile"]) == 40
    assert report["floor_count"] == 1


def test_rooms_use_face_connections_while_solids_include_corners(make_structure):
    solids = [((0, 0, 0), 0), ((1, 1, 1), 0), ((2, 2, 2), 0)]
    air = [((0, 1, 0), 1), ((1, 2, 1), 1)]
    analyzer = StructureAnalyzer(make_structure(solids + air))

    assert [len(component) for component in analyzer.connected_components()] == [3]
    assert analyzer.rooms() == [1, 1]


@pytest.mark.parametrize("width", [0, -1, True, 1.5])
def test_vertical_profile_rejects_invalid_width_even_when_empty(make_structure, width):
    with pytest.raises(ValueError, match="width"):
        StructureAnalyzer(make_structure()).vertical_profile(width)


def test_invalid_symmetry_axis_is_explicit_even_when_empty(make_structure):
    with pytest.raises(ValueError, match="axis"):
        StructureAnalyzer(make_structure()).mirror_symmetry("invalid")


@pytest.mark.parametrize("gap", [1, 3, 100_000_000])
def test_floor_peaks_are_preserved_across_empty_layer_gaps(make_structure, gap):
    layers = [(0, 1), (gap, 5), (gap + 1, 1), (2 * gap + 2, 5), (2 * gap + 3, 1)]
    blocks = [((x, y, 0), 0) for y, count in layers for x in range(count)]
    analyzer = StructureAnalyzer(make_structure(blocks, size=(5, 2 * gap + 4, 1)))

    assert analyzer.floor_count() == 2
