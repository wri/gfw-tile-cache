import mercantile
from shapely.geometry import box


def to_bbox(x: int, y: int, z: int) -> box:
    tile = mercantile.Tile(x, y, z)
    left, bottom, right, top = mercantile.xy_bounds(tile)

    return box(left, bottom, right, top)
