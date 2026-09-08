import math
import struct
import zlib
from collections import Counter

import numpy as np


def sparkline(counts, y0, y1, width=40):
    if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
        raise ValueError("width must be a positive integer")
    if not counts:
        return ""
    span = y1 - y0 + 1
    buckets = [0] * min(width, span)
    for y, n in counts.items():
        i = min(len(buckets) - 1, (y - y0) * len(buckets) // span)
        buckets[i] += n
    peak = max(buckets) or 1
    ramp = " ▁▂▃▄▅▆▇█"
    return "".join(ramp[round(b / peak * (len(ramp) - 1))] for b in buckets)


def vertical_profile(positions, width=40):
    counts = Counter(pos[1] for pos in positions)
    return sparkline(counts, min(counts, default=0), max(counts, default=0), width)


def compression_ratio(positions) -> float:
    items = sorted(positions.items())
    raw = b"".join(struct.pack(">iiiI", *pos, state) for pos, state in items)
    if not raw:
        return 0.0
    compressed = zlib.compress(raw, level=9)
    return len(compressed) / len(raw)


def footprint_elongation(positions):
    if len(positions) < 2:
        return 1.0, 0.0
    pts = np.array([(p[0], p[2]) for p in positions], dtype=float)
    pts -= pts.mean(axis=0)
    cov = np.cov(pts.T)
    eigvals, eigvecs = np.linalg.eigh(cov)
    order = np.argsort(eigvals)[::-1]
    eigvals = np.clip(eigvals[order], 1e-9, None)
    major = eigvecs[:, order[0]]
    angle = math.degrees(math.atan2(major[1], major[0])) % 90.0
    return float(math.sqrt(eigvals[0] / eigvals[1])), round(angle, 1)


def floor_count(positions) -> int:
    if not positions:
        return 0
    from scipy.signal import find_peaks

    ys = [p[1] for p in positions]
    y0, y1 = min(ys), max(ys)
    if y1 == y0:
        return 1
    counts = []
    previous = y0 - 1
    for y, count in sorted(Counter(ys).items()):
        counts.extend([0] * min(y - previous - 1, 2))
        counts.append(count)
        previous = y
    counts = np.asarray(counts)
    peaks, _ = find_peaks(counts, prominence=counts.max() * 0.15, distance=2)
    return max(1, len(peaks))
