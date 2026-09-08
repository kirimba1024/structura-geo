def summary_line(report: dict) -> str:
    """One line synthesized from an already-built report() dict --
    the fastest way to grasp "what is this" without reading every
    field or opening a render."""
    sx, sy, sz = report["size"]
    materials = ", ".join(
        f"{fam} {pct}%"
        for fam, pct in list(report["material_families"].items())[:2]
    )
    angle = report["footprint_axis_deg"]
    aligned = "grid-aligned" if angle < 5 or angle > 85 else f"rotated {angle} deg"
    bits = [
        f"{sx}x{sy}x{sz}",
        f"{report['floor_count']} floor(s)",
        f"{report['room_count']} room(s)",
        materials,
        aligned,
        f"{report['door_count']} door(s)",
        f"light coverage {report['light_coverage'] * 100:.0f}%",
    ]
    if report["warnings"]:
        bits.append(f"{len(report['warnings'])} warning(s)")
    return " | ".join(bits)


def build_report(analyzer) -> dict:
    comps = analyzer.connected_components()
    rooms = analyzer.rooms()
    elongation, axis_angle = analyzer.footprint_elongation()
    doors = analyzer.doors()
    light_count, light_coverage = analyzer.light_coverage()
    debris_fraction = analyzer.debris_fraction()
    floating_fraction = analyzer.floating_fraction()
    r = {
        "path": analyzer.path,
        "size": analyzer.size,
        "block_count": len(analyzer.positions),
        "palette_size": len(analyzer.palette),
        "density": round(analyzer.density(), 4),
        "components": len(comps),
        "main_component_size": len(comps[0]) if comps else 0,
        "debris_fraction": round(debris_fraction, 4),
        "floating_fraction": round(floating_fraction, 4),
        "palette_entropy_bits": round(analyzer.palette_entropy(), 3),
        "compression_ratio": round(analyzer.compression_ratio(), 4),
        "mirror_symmetry_x": round(analyzer.mirror_symmetry("x"), 3),
        "mirror_symmetry_z": round(analyzer.mirror_symmetry("z"), 3),
        "natural_terrain_fraction": round(analyzer.natural_terrain_fraction(), 4),
        "bedrock_fraction": round(analyzer.bedrock_fraction(), 4),
        "room_count": len(rooms),
        "room_sizes": rooms[:8],
        "footprint_elongation": round(elongation, 2),
        "footprint_axis_deg": axis_angle,
        "floor_count": analyzer.floor_count(),
        "vertical_profile": analyzer.vertical_profile(),
        "terrain_profile": analyzer.terrain_profile(),
        "environment_fit": analyzer.environment_fit(),
        "material_families": analyzer.material_families(),
        "door_count": len(doors),
        "doors": doors,
        "light_source_count": light_count,
        "light_coverage": light_coverage,
        "warnings": analyzer._warnings(comps, debris_fraction, floating_fraction),
    }
    r["summary"] = analyzer.summary_line(r)
    return r


def analysis_warnings(analyzer, comps, debris_fraction, floating_fraction):
    warnings = []
    if debris_fraction > 0.005:
        warnings.append(
            f"debris: {len(comps) - 1} disconnected component(s), "
            f"{debris_fraction * 100:.1f}% of blocks -- consider dropping"
        )
    if floating_fraction > 0.02:
        warnings.append(
            f"floating: {floating_fraction * 100:.1f}% of blocks have no "
            f"support chain to the floor plane -- check for a detached wing"
        )
    if analyzer.density() < 0.02:
        warnings.append(
            f"very low density ({analyzer.density() * 100:.2f}%) -- bounding box "
            f"likely still has untrimmed padding"
        )
    ntf = analyzer.natural_terrain_fraction()
    if ntf > 0.15:
        warnings.append(
            f"likely captured terrain: {ntf * 100:.1f}% of blocks are natural "
            f"material (dirt/grass/stone/...) -- check for an attached hill/tree"
        )
    bf = analyzer.bedrock_fraction()
    if bf > 0.001:
        warnings.append(
            f"bedrock: {bf * 100:.1f}% of blocks -- almost never a deliberate "
            f"material choice, near-certain sign the selection reached the "
            "world floor"
        )
    return warnings
