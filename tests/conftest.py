import pytest
from amulet_nbt import CompoundTag, ListTag


@pytest.fixture
def make_structure():
    from amulet_nbt import IntTag

    from structura_core import Structure, parse_state

    def make(blocks=(), *, size=(5, 3, 3), palette=("minecraft:stone", "minecraft:air")):
        return Structure.from_root(CompoundTag({
            "DataVersion": IntTag(3955),
            "size": ListTag([IntTag(value) for value in size]),
            "palette": ListTag([parse_state(state) for state in palette]),
            "blocks": ListTag([
                CompoundTag({"pos": ListTag([IntTag(value) for value in pos]), "state": IntTag(state)})
                for pos, state in blocks
            ]),
            "entities": ListTag(),
        }))

    return make
