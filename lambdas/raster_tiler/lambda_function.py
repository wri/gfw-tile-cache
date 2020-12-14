import os
from typing import Any, Dict

from rasterio import RasterioIOError
from rasterio.windows import Window

from . import utils
from .utils import TILE_SIZE, get_tile_location

ENV: str = os.environ.get("ENV", "dev")


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
        tile = utils.tile(src_tile, window)
    except RasterioIOError:
        response["status"] = "error"
        response["message"] = "Tile not found"
    else:
        # write out 3 band RGB PNG
        png = utils.array_to_img(tile)
        response["status"] = "success"
        response["data"] = png

    return response
