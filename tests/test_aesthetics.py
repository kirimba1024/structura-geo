import numpy as np

from structura_geo.aesthetics import (
    NATURAL_RUN_LIMIT, construction_tells, flat_wall, longest_straight_run,
    silhouette,
)


def test_a_single_cuboid_fails_the_silhouette_test():
    box = np.ones((12, 12, 12), dtype=bool)
    massed = np.zeros((24, 16, 24), dtype=bool)
    massed[2:14, 0:8, 2:14] = True
    massed[10:20, 0:13, 8:18] = True
    massed[15:19, 0:16, 12:16] = True

    plain, varied = silhouette(box), silhouette(massed)

    assert plain["bbox_fill"] == 1.0 and plain["top_levels"] == 1, (
        "a single box is the first thing building guides tell people to stop "
        "doing: it has one height and fills its own bounding box exactly"
    )
    assert varied["top_levels"] > 2 and varied["bbox_fill"] < 0.6, (
        "three masses at different heights is what passes the silhouette "
        "test -- recognisable as a black shape against a sunset"
    )


def test_the_seven_block_rule_is_measured_not_asserted():
    flat = np.zeros((20, 4, 20), dtype=bool)
    flat[:, 0:3, :] = True
    rugged = flat.copy()
    rng = np.random.default_rng(1)
    for x in range(20):
        for z in range(20):
            rugged[x, 3, z] = bool(rng.integers(0, 2))

    assert longest_straight_run(flat)["over_limit"] > 0.9, (
        f"a flat top is one long straight run, and terraforming guides put the "
        f"limit at about {NATURAL_RUN_LIMIT} blocks on anything meant to look "
        "natural"
    )
    assert longest_straight_run(rugged)["over_limit"] < 0.3, "broken up passes"


def test_flat_wall_and_floating_blocks_are_counted():
    slab = np.zeros((30, 30, 3), dtype=bool)
    slab[:, :, 1] = True
    assert flat_wall(slab) > 0.9, (
        "one flat single-block wall is the most-cited beginner mistake, and it "
        "shows up as nearly all the mass sitting on one vertical slice"
    )

    hovering = np.zeros((9, 9, 9), dtype=bool)
    hovering[4, 5, 4] = True
    tells = construction_tells(hovering)
    assert tells["floating"] == 1, "a block with nothing beneath it is counted"
    assert tells["largest_share"] == 1.0


def test_the_metrics_measure_type_when_read_across_types():
    ground = np.ones((20, 20, 20), dtype=bool)
    house = np.zeros((20, 20, 20), dtype=bool)
    house[4:16, 0:10, 4:16] = True
    house[4:16, 0:10, 4:16][1:-1, 1:-1, 1:-1] = False

    assert silhouette(ground)["bbox_fill"] > silhouette(house)["bbox_fill"], (
        "a captured block of ground is SUPPOSED to fill its box, so the same "
        "number that damns a house is correct here. Every figure in this "
        "module has to be read beside the archetype, or it measures the "
        "archetype instead of the piece"
    )


def test_flags_are_calibrated_against_the_archive_not_guessed():
    from structura_geo.aesthetics import FLAT_WALL_LIMIT, flags

    assert FLAT_WALL_LIMIT < 0.20, (
        "the largest coplanar vertical patch never exceeds 0.20 across the "
        "235-piece archive, so a threshold above that flags nothing. The "
        "first guess was 0.25 and raised zero pieces; a threshold has to be "
        "set from the distribution it will be applied to"
    )

    box = dict(
        silhouette=dict(bbox_fill=0.9, top_levels=2, aspect=1.0),
        flat_wall=0.02, palette=dict(dominance=0.4, distinct=20),
        construction=dict(debris_components=0, largest_share=1.0),
        capture=dict(orphan_canopy=False),
    )
    assert any("box-like" in flag for flag in flags(box))

    good = dict(
        silhouette=dict(bbox_fill=0.3, top_levels=18, aspect=1.2),
        flat_wall=0.05, palette=dict(dominance=0.4, distinct=25),
        construction=dict(debris_components=0, largest_share=1.0),
        capture=dict(orphan_canopy=False),
    )
    assert flags(good) == [], (
        "a well-massed piece with a balanced palette must raise nothing -- "
        "61% of the real archive raises nothing, and a filter that flags the "
        "majority is measuring itself"
    )


def test_value_spread_separates_a_flat_smear_from_a_contrasting_palette():
    from collections import Counter

    from structura_geo.aesthetics import flags, palette_colour

    counts = Counter({"a": 60, "b": 30, "c": 10})
    smear = palette_colour(counts, {"a": (120, 120, 120), "b": (125, 125, 125),
                                    "c": (118, 118, 118)})
    contrast = palette_colour(counts, {"a": (40, 35, 30), "b": (150, 140, 120),
                                       "c": (230, 225, 215)})

    assert smear["value_range"] < 15 and contrast["value_range"] > 100, (
        "value contrast is what makes a build read at distance; hue barely "
        "survives the trip. A palette with no light-to-dark range is a flat "
        "smear however varied it looks up close"
    )
    assert contrast["warm_share"] > 0.9, "warm when red exceeds blue"

    base = dict(
        silhouette=dict(bbox_fill=0.3, top_levels=18, aspect=1.2),
        flat_wall=0.05, palette=dict(dominance=0.4, distinct=25),
        construction=dict(debris_components=0, largest_share=1.0),
        capture=dict(orphan_canopy=False),
    )
    assert any("value spread" in flag for flag in flags({**base, "colour": smear}))
    assert flags({**base, "colour": contrast}) == []


def test_colour_is_optional_so_analysis_never_depends_on_a_renderer():
    from structura_geo.aesthetics import flags, palette_colour

    assert palette_colour({"minecraft:stone": 10}, {}) is None, (
        "the real block colours live in the render library, which reads them "
        "from the client jar. Analysis takes the table as an argument and "
        "works without it, so geo never grows a dependency on a renderer"
    )
    assert flags(dict(
        silhouette=dict(bbox_fill=0.3, top_levels=18, aspect=1.2),
        flat_wall=0.05, palette=dict(dominance=0.4, distinct=25),
        construction=dict(debris_components=0, largest_share=1.0),
        capture=dict(orphan_canopy=False),
    )) == [], "no colour table means no colour flag, not a crash"


def test_hints_are_weighted_by_confidence_not_by_taste():
    from structura_geo.aesthetics import HINT_CONFIDENCE, review_score

    base = dict(
        silhouette=dict(bbox_fill=0.3, top_levels=18, aspect=1.2),
        flat_wall=0.05, palette=dict(dominance=0.4, distinct=25),
        construction=dict(debris_components=0, largest_share=1.0),
        capture=dict(orphan_canopy=False),
    )
    littered = {**base, "construction": dict(debris_components=99, largest_share=1.0)}
    monotone = {**base, "palette": dict(dominance=0.95, distinct=3)}

    assert review_score(littered) > review_score(monotone), (
        "debris is capture litter that nobody built on purpose, so the hint "
        "is nearly always right. A monotone palette may be the author's whole "
        "intention -- a snow build, an obsidian tower -- so it is worth "
        "raising and not worth trusting. Confidence is measurable; severity "
        "is a taste judgement"
    )
    assert review_score(base) == 0.0, "a clean piece never enters the queue"
    assert HINT_CONFIDENCE["monotone palette"] < HINT_CONFIDENCE["debris"]


def test_the_score_is_a_queue_order_and_never_a_rejection():
    from structura_geo.aesthetics import review_score

    worst = dict(
        silhouette=dict(bbox_fill=0.95, top_levels=1, aspect=1.0),
        flat_wall=0.9, palette=dict(dominance=0.99, distinct=1),
        construction=dict(debris_components=500, largest_share=0.2),
        capture=dict(orphan_canopy=True),
        colour=dict(covered=1.0, value_range=1.0),
    )
    assert review_score(worst) < 10, (
        "the score is bounded and small on purpose. It orders what a person "
        "looks at first; it does not accumulate into a verdict, because "
        "passing something mediocre costs one bad structure in a world while "
        "rejecting something excellent loses it permanently"
    )
