from dataclasses import dataclass
from itertools import product
from math import prod

import numpy as np
from scipy import ndimage

from structura_core.limits import DEFAULT_MAX_BLOCKS


def use_dense_grid(shape, count):
    return prod(int(value) for value in shape) <= min(DEFAULT_MAX_BLOCKS, max(4096, 64 * count))


@dataclass(frozen=True)
class ComponentLabels:
    labels: np.ndarray
    sizes: np.ndarray


def label_positions(positions, *, connectivity=26):
    if connectivity not in (6, 26):
        raise ValueError("connectivity must be 6 or 26")
    coordinates = np.asarray(list(positions), dtype=np.int64).reshape(-1, 3)
    if not len(coordinates):
        return ComponentLabels(np.empty(0, dtype=np.int32), np.array([0]))
    local = coordinates - coordinates.min(axis=0)
    shape = local.max(axis=0) + 1
    if use_dense_grid(shape, len(coordinates)):
        mask = np.zeros(tuple(shape), dtype=bool)
        mask[tuple(local.T)] = True
        grid, _ = ndimage.label(mask, structure=ndimage.generate_binary_structure(3, 1 if connectivity == 6 else 3))
        sizes = np.bincount(grid[mask])
        return ComponentLabels(grid[tuple(local.T)], sizes)
    return _sparse_labels(coordinates, connectivity)


def _sparse_labels(coordinates, connectivity):
    labels = dict.fromkeys(map(tuple, coordinates.tolist()), 0)
    offsets = [
        delta for delta in product((-1, 0, 1), repeat=3)
        if any(delta) and (connectivity == 26 or sum(map(abs, delta)) == 1)
    ]
    sizes = [0]
    for seed in sorted(labels):
        if labels[seed]:
            continue
        label = len(sizes)
        labels[seed] = label
        pending, size = [seed], 0
        while pending:
            x, y, z = pending.pop()
            size += 1
            for dx, dy, dz in offsets:
                neighbor = (x + dx, y + dy, z + dz)
                if labels.get(neighbor) == 0:
                    labels[neighbor] = label
                    pending.append(neighbor)
        sizes.append(size)
    block_labels = np.fromiter((labels[tuple(pos)] for pos in coordinates), dtype=np.int32)
    return ComponentLabels(block_labels, np.asarray(sizes))
