import logging
from typing import Tuple

import mercantile
from shapely.geometry import box

Bounds = Tuple[float, float, float, float]


def to_bbox(x: int, y: int, z: int) -> Bounds:
    logging.debug(f"{x},{y},{z}")
    left, bottom, right, top = mercantile.xy_bounds(x, y, z)
    logging.debug(f"{left},{bottom},{right},{top}")
    return box(left, bottom, right, top).bounds
