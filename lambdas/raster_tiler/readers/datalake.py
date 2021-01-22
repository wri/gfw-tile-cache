from math import floor
from typing import Tuple

import numpy as np
import rasterio
from rasterio import RasterioIOError
from rasterio.windows import Window

from ..lambda_function import SUFFIX, TILE_SIZE, TileNotFoundError


def get_tile_location(x: int, y: int) -> Tuple[int, int, int, int]:
    """Get the ID of the source tile in which the z/x/y tile is located.

    Source tile IDs are defined based on Zoom level and number of
    potential pixels. A Source tile can have a maximum of 65536x65526
    pixel which is equivalent to 256x256 blocks of 256x256 pixels each.
    Tile Ids follow the pattern 000R_000C, indicating the row and column
    of tile in zoom level starting at the top left corner. X and Y
    indices represent one 256x256 block within a tile.
    """

    row: int = floor(y / TILE_SIZE)
    col: int = floor(x / TILE_SIZE)

    row_off: int = (y - (row * TILE_SIZE)) * TILE_SIZE
    col_off: int = (x - (col * TILE_SIZE)) * TILE_SIZE

    return row, col, row_off, col_off


def get_tile_array(src_tile: str, window: Window) -> np.ndarray:
    """Create mercator tile from GFW WM Tile Set images."""

    with rasterio.open(src_tile) as src:
        profile = src.profile
        bands = profile["count"]
        indexes = tuple(range(1, bands + 1))
        out_shape = (len(indexes), TILE_SIZE, TILE_SIZE)
        data = src.read(
            window=window, boundless=True, out_shape=out_shape, indexes=indexes
        )

    return data


def read(dataset, version, implementation, x, y, z, **kwargs):

    if implementation == "dynamic":
        pixel_meaning: str = "rgb_encoded"
    else:
        pixel_meaning = implementation

    row, col, row_off, col_off = get_tile_location(int(x), int(y))

    src_tile = f"s3://gfw-data-lake{SUFFIX}/{dataset}/{version}/raster/epsg-3857/zoom_{z}/{pixel_meaning}/geotiff/{str(row).zfill(3)}R_{str(col).zfill(3)}C.tif"
    window: Window = Window(col_off, row_off, TILE_SIZE, TILE_SIZE)

    print("X, Y, Z: ", (x, y, z))
    print("SCR TILE: ", src_tile)

    try:
        tile = get_tile_array(src_tile, window)
    except RasterioIOError as e:
        raise TileNotFoundError(str(e))

    return tile
