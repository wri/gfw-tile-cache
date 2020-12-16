import base64
import logging
import os
from io import BytesIO
from math import floor
from typing import Any, Dict, Tuple

import numpy as np
import rasterio
from PIL import Image
from rasterio import RasterioIOError
from rasterio.windows import Window

ENV: str = os.environ.get("ENV", "dev")
TILE_SIZE: int = 256

logger = logging.getLogger(__name__)


def array_to_img(arr: np.ndarray) -> str:
    """Convert a numpy array to an base64 encoded img."""

    img = Image.fromarray(arr, mode="RGBA")

    sio = BytesIO()
    params = {"compress_level": 0}

    img.save(sio, "png", **params)
    sio.seek(0)

    return base64.b64encode(sio.getvalue()).decode()


def get_tile_array(src_tile: str, window: Window) -> np.ndarray:
    """Create mercator tile from GFW WM Tile Set images."""

    indexes = (1, 2, 3, 4)

    out_shape = (len(indexes), TILE_SIZE, TILE_SIZE)

    with rasterio.open(src_tile) as src:
        data = src.read(
            window=window, boundless=True, out_shape=out_shape, indexes=indexes
        )

    # moves data from (4, 256, 256) format to (256, 256, 4)
    # PIL will read it in both ways, but for some reason
    # only propogates the first band to the other three
    # when in (4, 256, 256)
    # print(data)
    data = np.dstack((data[0], data[1], data[2], data[3]))
    return data


def get_tile_location(x: int, y: int) -> Tuple[int, int, int, int]:
    """Get the ID of the source tile in which the z/x/y tile is located.

    Source tile IDs are defined based on Zoom level and number of
    potential pixels. A Source tile can have a maximum of 65536x65526
    pixel which is equivalent to 256x256 blocks of 256x256 pixels each.
    Tile Ids follow the pattern 000R_000C, indicating the row and column
    of tile in zoom level starting at the top left corner. X and Y
    indicies represent one 256x256 block within a tile.
    """

    row: int = floor(y / TILE_SIZE)
    col: int = floor(x / TILE_SIZE)

    row_off: int = (y - (row * TILE_SIZE)) * TILE_SIZE
    col_off: int = (x - (col * TILE_SIZE)) * TILE_SIZE

    return row, col, row_off, col_off


def handler(event: Dict[str, Any], _: Dict[str, Any]) -> Dict[str, str]:
    """Handle tile requests."""
    dataset: str = event["dataset"]
    version: str = event["version"]
    implementation: str = event["implementation"]
    x: int = int(event["x"])
    y: int = int(event["y"])
    z: int = int(event["z"])

    suffix: str = "" if ENV == "production" else f"-{ENV}"

    if implementation == "default":
        pixel_meaning: str = "rgb_encoded"
    else:
        pixel_meaning = implementation

    row, col, row_off, col_off = get_tile_location(x, y)

    src_tile = f"s3://gfw-data-lake{suffix}/{dataset}/{version}/raster/epsg-3857/zoom_{z}/{pixel_meaning}/{str(row).zfill(3)}R_{str(col).zfill(3)}C.tif"
    window: Window = Window(col_off, row_off, TILE_SIZE, TILE_SIZE)

    response: Dict[str, str] = {}

    try:
        tile = get_tile_array(src_tile, window)
    except RasterioIOError:
        response["status"] = "error"
        response["message"] = "Tile not found"
    else:
        # write out 3 band RGB PNG
        png = array_to_img(tile)
        response["status"] = "success"
        response["data"] = png

    return response
