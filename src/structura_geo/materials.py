GROUND_MARKERS = frozenset(
    {
        "minecraft:grass_block",
        "minecraft:dirt_path",
        "minecraft:coarse_dirt",
        "minecraft:farmland",
        "minecraft:podzol",
        "minecraft:mycelium",
        "minecraft:sand",
        "minecraft:red_sand",
        "minecraft:gravel",
        "minecraft:snow_block",
    }
)

NATURAL_GROUND_BLOCKS = frozenset(
    {
        "minecraft:grass_block",
        "minecraft:dirt",
        "minecraft:coarse_dirt",
        "minecraft:podzol",
        "minecraft:mycelium",
        "minecraft:mud",
        "minecraft:stone",
        "minecraft:mossy_cobblestone",
        "minecraft:andesite",
        "minecraft:diorite",
        "minecraft:granite",
        "minecraft:deepslate",
        "minecraft:moss_block",
        "minecraft:gravel",
        "minecraft:sand",
        "minecraft:red_sand",
    }
)

METRIC_NATURAL_BLOCKS = frozenset(
    {
        "minecraft:dirt",
        "minecraft:grass_block",
        "minecraft:stone",
        "minecraft:gravel",
        "minecraft:sand",
        "minecraft:coarse_dirt",
        "minecraft:podzol",
        "minecraft:mycelium",
        "minecraft:andesite",
        "minecraft:diorite",
        "minecraft:granite",
        "minecraft:clay",
    }
)

_SOIL = frozenset(
    {
        "minecraft:dirt",
        "minecraft:rooted_dirt",
        "minecraft:mud",
        "minecraft:clay",
        "minecraft:soul_sand",
        "minecraft:soul_soil",
        "minecraft:snow",
        "minecraft:suspicious_sand",
        "minecraft:suspicious_gravel",
    }
)

_ROCK = frozenset(
    {
        "minecraft:stone",
        "minecraft:deepslate",
        "minecraft:tuff",
        "minecraft:calcite",
        "minecraft:dripstone_block",
        "minecraft:pointed_dripstone",
        "minecraft:blackstone",
        "minecraft:basalt",
        "minecraft:smooth_basalt",
        "minecraft:magma_block",
        "minecraft:netherrack",
        "minecraft:end_stone",
        "minecraft:bedrock",
    }
)

_MASONRY_LOOKALIKES = frozenset(
    {
        "minecraft:cobblestone",
        "minecraft:mossy_cobblestone",
        "minecraft:obsidian",
        "minecraft:sandstone",
        "minecraft:red_sandstone",
        "minecraft:terracotta",
        "minecraft:ice",
        "minecraft:packed_ice",
        "minecraft:blue_ice",
    }
)

_ORE_SUFFIXES = ("_ore", "_raw_block")

NATURAL_TERRAIN = frozenset(GROUND_MARKERS | _SOIL | _ROCK)


def is_terrain(name):
    if name in NATURAL_TERRAIN:
        return True
    return name.endswith(_ORE_SUFFIXES)


WATER_BLOCKS = {
    "minecraft:prismarine",
    "minecraft:prismarine_bricks",
    "minecraft:dark_prismarine",
    "minecraft:sea_lantern",
    "minecraft:kelp",
    "minecraft:kelp_plant",
    "minecraft:conduit",
    "minecraft:tube_coral_block",
    "minecraft:brain_coral_block",
    "minecraft:sponge",
    "minecraft:wet_sponge",
}

NETHER_BLOCKS = {
    "minecraft:netherrack",
    "minecraft:nether_bricks",
    "minecraft:blackstone",
    "minecraft:basalt",
    "minecraft:soul_sand",
    "minecraft:soul_soil",
    "minecraft:glowstone",
    "minecraft:magma_block",
    "minecraft:crimson_planks",
    "minecraft:warped_planks",
    "minecraft:nether_wart_block",
    "minecraft:shroomlight",
}

LIGHT_SOURCES = {
    "minecraft:torch",
    "minecraft:wall_torch",
    "minecraft:soul_torch",
    "minecraft:soul_wall_torch",
    "minecraft:lantern",
    "minecraft:soul_lantern",
    "minecraft:glowstone",
    "minecraft:sea_lantern",
    "minecraft:jack_o_lantern",
    "minecraft:campfire",
    "minecraft:soul_campfire",
    "minecraft:redstone_lamp",
    "minecraft:shroomlight",
    "minecraft:beacon",
    "minecraft:end_rod",
    "minecraft:ochre_froglight",
    "minecraft:verdant_froglight",
    "minecraft:pearlescent_froglight",
}

MATERIAL_FAMILIES = (
    ("glass", ("glass",)),
    (
        "wood",
        (
            "plank",
            "log",
            "wood",
            "oak",
            "spruce",
            "birch",
            "jungle",
            "acacia",
            "dark_oak",
            "mangrove",
            "cherry",
            "bamboo",
            "crimson",
            "warped",
        ),
    ),
    (
        "stone",
        (
            "stone",
            "cobble",
            "brick",
            "andesite",
            "diorite",
            "granite",
            "deepslate",
            "blackstone",
            "basalt",
            "sandstone",
            "quartz",
            "prismarine",
            "terracotta",
            "concrete",
            "netherrack",
        ),
    ),
    ("metal", ("iron", "copper", "gold", "netherite", "chain")),
    (
        "nature",
        (
            "leaves",
            "grass",
            "dirt",
            "sand",
            "gravel",
            "flower",
            "vine",
            "kelp",
            "coral",
            "mycelium",
            "podzol",
            "moss",
            "sapling",
            "fern",
            "bush",
            "crop",
            "wart",
            "mushroom",
            "lily_pad",
        ),
    ),
    (
        "functional",
        (
            "chest",
            "furnace",
            "door",
            "torch",
            "lantern",
            "_bed",
            "table",
            "shelf",
            "barrel",
            "smoker",
            "loom",
            "anvil",
            "brewing",
            "cauldron",
            "hopper",
            "dispenser",
            "dropper",
            "redstone",
            "lever",
            "button",
            "plate",
            "rail",
            "sign",
            "banner",
            "frame",
            "armor_stand",
        ),
    ),
)
