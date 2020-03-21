import mercantile
from shapely.geometry import box


def to_bbox(x: int, y: int, z: int) -> box:
    tile = mercantile.Tile(x, y, z)
    left, bottom, right, top = mercantile.bounds(tile)

    return box(left, bottom, right, top)
