# mypy: ignore-errors

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
DATA_LAKE_BUCKET: str = os.environ["DATA_LAKE_BUCKET"]
LOCALSTACK_HOSTNAME: str = os.environ.get("LOCALSTACK_HOSTNAME", None)
AWS_ENDPOINT_HOST: str = f"{LOCALSTACK_HOSTNAME}:4566" if LOCALSTACK_HOSTNAME else None

log_level = {
    "test": logging.DEBUG,
    "dev": logging.DEBUG,
    "staging": logging.DEBUG,
    "production": logging.INFO,
}

logger = logging.getLogger(__name__)
logger.setLevel(log_level[ENV])


def array_to_img(arr: np.ndarray) -> str:
    """Convert a numpy array to an base64 encoded img."""

    modes = {3: "RGB", 4: "RGBA"}

    img = Image.fromarray(arr, mode=modes[arr.shape[2]])

    sio = BytesIO()
    params = {"compress_level": 0}

    img.save(sio, "png", **params)
    sio.seek(0)

    return base64.b64encode(sio.getvalue()).decode()


def get_tile_array(src_tile: str, window: Window) -> np.ndarray:
    """Create mercator tile from GFW WM Tile Set images."""
    # if running lambda in localstack, need to use special docker IP address provided in env to reach localstack
    gdal_env = {
        "AWS_HTTPS": "NO" if AWS_ENDPOINT_HOST else "YES",
        "AWS_VIRTUAL_HOSTING": False if AWS_ENDPOINT_HOST else True,
        "AWS_S3_ENDPOINT": AWS_ENDPOINT_HOST,
        "GDAL_DISABLE_READDIR_ON_OPEN": "NO" if AWS_ENDPOINT_HOST else "YES",
    }

    logger.debug(gdal_env)

    with rasterio.Env(**gdal_env), rasterio.open(src_tile) as src:
        profile = src.profile
        bands = profile["count"]
        indexes = tuple(range(1, bands + 1))
        out_shape = (len(indexes), TILE_SIZE, TILE_SIZE)
        data = src.read(
            window=window, boundless=True, out_shape=out_shape, indexes=indexes
        )

    # moves data from (4, 256, 256) format to (256, 256, 4)
    # PIL will read it in both ways, but for some reason
    # only propagates the first band to the other three
    # when in (4, 256, 256)
    # print(data)
    data = np.dstack(tuple([data[i - 1] for i in indexes]))
    return data


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


def handler(event: Dict[str, Any], _: Dict[str, Any]) -> Dict[str, str]:
    """Handle tile requests."""
    dataset: str = event["dataset"]
    version: str = event["version"]
    implementation: str = event["implementation"]
    x: int = int(event["x"])
    y: int = int(event["y"])
    z: int = int(event["z"])

    if implementation == "dynamic":
        pixel_meaning: str = "rgb_encoded"
    else:
        pixel_meaning = implementation

    row, col, row_off, col_off = get_tile_location(x, y)

    src_tile = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-3857/zoom_{z}/{pixel_meaning}/geotiff/{str(row).zfill(3)}R_{str(col).zfill(3)}C.tif"
    window: Window = Window(col_off, row_off, TILE_SIZE, TILE_SIZE)

    print("X, Y, Z: ", (x, y, z))
    print("SRC TILE: ", src_tile)

    response: Dict[str, str] = {}

    try:
        tile = get_tile_array(src_tile, window)
    except RasterioIOError as e:
        logger.debug(f"Cannot find tile. Full traceback: {str(e)}")
        response["status"] = "error"
        response["message"] = "Tile not found"
    else:
        # write out 3 band RGB PNG
        png = array_to_img(tile)
        response["status"] = "success"
        response["data"] = png

    logger.debug(response)

    return response
