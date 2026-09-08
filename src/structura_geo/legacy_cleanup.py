from dataclasses import dataclass

from amulet_nbt import CompoundTag, StringTag

from structura_core.legacy_blocks import LegacyBlocks

FORCED_REPLACEMENTS = {
    ("minecraft", "bedrock"): ("minecraft", "cobblestone"),
}

_PANE_BAR_DIRS = {
    "east": (1, 0, 0),
    "west": (-1, 0, 0),
    "north": (0, 0, -1),
    "south": (0, 0, 1),
}

_NON_CONNECTING_NEIGHBORS = {
    "sign",
    "wall_sign",
    "hanging_sign",
    "wall_hanging_sign",
    "torch",
    "wall_torch",
    "soul_torch",
    "soul_wall_torch",
    "redstone_torch",
    "redstone_wall_torch",
    "banner",
    "wall_banner",
    "ladder",
    "lever",
    "button",
    "pressure_plate",
    "carpet",
    "rail",
    "powered_rail",
    "detector_rail",
    "activator_rail",
    "tripwire",
    "tripwire_hook",
    "trapdoor",
    "door",
    "slab",
    "stairs",
    "bed",
    "flower_pot",
    "campfire",
    "lantern",
    "skull",
    "head",
}


def _is_connectable_neighbor(name):
    short = name.split(":", 1)[-1]
    if short in ("air", "cave_air", "void_air"):
        return False
    if short.endswith("_pane") or short.endswith("_bars"):
        return True
    return not any(
        short == kw or short.endswith(f"_{kw}") for kw in _NON_CONNECTING_NEIGHBORS
    )


def _fix_pane_bar_connections(blocks, palette_list, palette_index):
    pos_to_idx = {pos: idx for pos, idx, _ in blocks}
    fixes = {}
    for i, (pos, idx, _) in enumerate(blocks):
        name = str(palette_list[idx]["Name"])
        short = name.split(":", 1)[-1]
        if not (short.endswith("_pane") or short.endswith("_bars")):
            continue
        props = palette_list[idx].get("Properties")
        if props is None:
            continue
        changed = {}
        for direction, (dx, dy, dz) in _PANE_BAR_DIRS.items():
            if direction not in props:
                continue
            npos = (pos[0] + dx, pos[1] + dy, pos[2] + dz)
            nidx = pos_to_idx.get(npos)
            nname = (
                str(palette_list[nidx]["Name"]) if nidx is not None else "minecraft:air"
            )
            want = "true" if _is_connectable_neighbor(nname) else "false"
            if str(props[direction]) != want:
                changed[direction] = want
        if changed:
            fixes[i] = changed
    if not fixes:
        return blocks, 0
    new_blocks = list(blocks)
    for i, changed in fixes.items():
        pos, idx, entry_nbt = blocks[i]
        old_props = palette_list[idx]["Properties"]
        new_props = CompoundTag({k: v for k, v in old_props.items()})
        for direction, want in changed.items():
            new_props[direction] = StringTag(want)
        name = palette_list[idx]["Name"]
        state_key = (
            f"{name}["
            + ",".join(
                f"{k}={v}" for k, v in sorted((k, str(v)) for k, v in new_props.items())
            )
            + "]"
        )
        new_idx = palette_index.get(state_key)
        if new_idx is None:
            new_idx = len(palette_list)
            palette_index[state_key] = new_idx
            comp = CompoundTag()
            comp["Name"] = name
            comp["Properties"] = new_props
            palette_list.append(comp)
        new_blocks[i] = (pos, new_idx, entry_nbt)
    return new_blocks, len(fixes)


def _split_exterior_interior_air(
    air_positions, solid_positions, size_x, size_y, size_z
):
    """Classify each air cell as "exterior" (open padding -- omit, so it
    doesn't carve craters into destination terrain) or "interior" (a real
    room -- place explicitly so it's hollowed out even when embedded in a
    hill).

    Recipe: binary_closing with radius 1 seals 1-block windows/doors, then
    binary_fill_holes marks cavities the border flood can't reach. Interior
    air is those cavities, plus the sealed openings that actually touch a
    cavity (the window/door cells themselves).

    An earlier version used a 7x7x7 kernel (radius 3) and then took
    `fill_holes(closed) & ~solid`. That second term includes the whole
    morphological skin closing added around the outside of the building,
    so most of the "interior" was actually a 1-3 block air shell around
    the walls -- which /place then carves into the destination terrain
    as a crater. Radius 3 also sealed 3-block eaves/yards into fake rooms.
    Radius 1 matches the gaps we actually want to seal; keeping only
    holes plus hole-adjacent sealed cells drops the exterior skin.

    border_value=1: scipy's erosion (the second half of closing) treats
    the outside of the array as empty by default, so a wall sitting flush
    against any face of the schematic gets eaten. Treating the outside as
    solid keeps those walls intact. fill_holes still sees the array
    border as true exterior -- only the closing step needs this.
    """
    import numpy as np
    from scipy import ndimage

    solid = np.zeros((size_x, size_y, size_z), dtype=bool)
    for pos in solid_positions:
        solid[pos] = True

    closed = ndimage.binary_closing(
        solid, structure=np.ones((3, 3, 3), dtype=bool), border_value=1
    )
    holes = ndimage.binary_fill_holes(closed) & ~closed
    sealed = closed & ~solid
    windows = sealed & ndimage.binary_dilation(holes)
    interior_mask = holes | windows

    interior = {tuple(p) for p in np.argwhere(interior_mask)} & air_positions
    exterior = air_positions - interior
    return exterior, interior


_DOOR_FACING = {
    "north": (0, 0, -1),
    "south": (0, 0, 1),
    "east": (1, 0, 0),
    "west": (-1, 0, 0),
}


def _door_clearance(blocks, palette_list, size, solid_positions, interior_air):
    """Force explicit air 2 steps on both sides of every door.

    Interior rooms already have air from the classifier. Exterior door
    faces would otherwise be omitted, and destination terrain would plug
    the opening. Facing says which way the leaf swings, not which side
    is outside -- so both directions get cleared. Never overwrites solid.
    """
    sx, sy, sz = size
    extra = set()
    for pos, idx, _ in blocks:
        name = str(palette_list[idx]["Name"])
        if not name.endswith("_door"):
            continue
        props = palette_list[idx].get("Properties")
        if props is None or str(props.get("half", "")) != "lower":
            continue
        if "facing" not in props:
            continue
        vec = _DOOR_FACING.get(str(props["facing"]))
        if vec is None:
            continue
        x, y, z = pos
        dx, _, dz = vec
        for sign in (1, -1):
            for step in (1, 2):
                for dy in (0, 1):
                    p = (x + dx * step * sign, y + dy, z + dz * step * sign)
                    px, py, pz = p
                    if not (0 <= px < sx and 0 <= py < sy and 0 <= pz < sz):
                        continue
                    if p in solid_positions or p in interior_air:
                        continue
                    extra.add(p)
    return extra


@dataclass(frozen=True)
class PlacementSummary:
    origin: tuple
    previous_size: tuple
    size: tuple
    pane_fixes: int
    exterior_air: int
    interior_air: int
    door_air: int


def _trim(data, entities, preserve_all_entities, src_path):
    trim_positions = [p for p, _, _ in data.blocks]
    if preserve_all_entities:
        trim_positions.extend(
            tuple(int(value // 1) for value in pos)
            for pos, _payload in entities
            if all(0 <= value < limit for value, limit in zip(pos, data.size))
        )
    if not trim_positions:
        raise ValueError(f"source contains no renderable blocks or entities: {src_path}")
    axes = tuple(zip(*trim_positions))
    origin = tuple(min(values) for values in axes)
    size = tuple(max(values) - offset + 1 for values, offset in zip(axes, origin))
    if origin != (0, 0, 0) or size != data.size:
        data.blocks = [
            (tuple(v - offset for v, offset in zip(pos, origin)), idx, nbt)
            for pos, idx, nbt in data.blocks
        ]
        data.air_positions = {
            tuple(v - offset for v, offset in zip(pos, origin))
            for pos in data.air_positions
            if all(offset <= v < offset + limit for v, offset, limit in zip(pos, origin, size))
        }
        data.size = size
    return origin


def prepare_placement(data: LegacyBlocks, entities, preserve_all_entities, src_path):
    previous_size = data.size
    origin = _trim(data, entities, preserve_all_entities, src_path)
    data.blocks, pane_fixes = _fix_pane_bar_connections(data.blocks, data.palette_list, data.palette_index)
    solid_positions = {pos for pos, _, _ in data.blocks}
    exterior, interior = _split_exterior_interior_air(data.air_positions, solid_positions, *data.size)
    door_air = _door_clearance(data.blocks, data.palette_list, data.size, solid_positions, interior)
    air_to_place = interior | door_air
    if air_to_place:
        air_idx = data.palette_index.get("minecraft:air")
        if air_idx is None:
            air_idx = len(data.palette_list)
            data.palette_index["minecraft:air"] = air_idx
            data.palette_list.append(CompoundTag({"Name": StringTag("minecraft:air")}))
        data.blocks.extend((pos, air_idx, None) for pos in air_to_place)
    return PlacementSummary(origin, previous_size, data.size, pane_fixes,
                            len(exterior), len(interior), len(door_air))
