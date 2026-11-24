"""Small, deterministic geometry checks around RaCo outputs."""

import math


def covariance_is_valid(matrix):
    if len(matrix) != 2 or any(len(row) != 2 for row in matrix):
        return False
    a, b = matrix[0]
    c, d = matrix[1]
    return (
        all(math.isfinite(float(value)) for value in (a, b, c, d))
        and abs(float(b) - float(c)) <= 1e-4
        and float(a) >= 0
        and float(d) >= 0
        and float(a) * float(d) - float(b) * float(c) >= -1e-4
    )


def rotation_repeatability(reference, transformed, width, height, radius=5.0):
    """Measure fraction of reference points with a rotated neighbor (90 deg CCW)."""
    if not reference:
        return 0.0
    # torch.rot90 with image coordinates x right, y down: (x,y)->(y,W-1-x)
    matched = 0
    for x, y in reference:
        target_x, target_y = y, width - 1 - x
        if 0 <= target_x < height and 0 <= target_y < width and any(
            (other_x - target_x) ** 2 + (other_y - target_y) ** 2 <= radius ** 2
            for other_x, other_y in transformed
        ):
            matched += 1
    return matched / len(reference)