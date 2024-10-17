# mypy: ignore-errors

import base64
import json
import logging
import math
import os
from datetime import date, datetime
from io import BytesIO
from math import floor
from typing import Any, Callable, Dict, Optional, Tuple, Union
from urllib.error import URLError
from urllib.request import urlopen

import numpy as np
import rasterio
from affine import Affine
from mercantile import CE, Tile, parent, xy_bounds
from numpy import ndarray
from PIL import Image
from rasterio import RasterioIOError, windows
from rasterio.windows import Window

ENV: str = os.environ.get("ENV", "dev")
TILE_SIZE: int = 256
SUFFIX: str = "" if ENV == "production" else f"-{ENV}"
DATA_LAKE_BUCKET: str = os.environ.get("DATA_LAKE_BUCKET")
LOCALSTACK_HOSTNAME: Optional[str] = os.environ.get("LOCALSTACK_HOSTNAME", None)
AWS_ENDPOINT_HOST: Optional[str] = (
    f"{LOCALSTACK_HOSTNAME}:4566" if LOCALSTACK_HOSTNAME else None
)
TILE_CACHE_URL: str = os.environ.get("TILE_CACHE_URL")

log_level = {
    "test": logging.DEBUG,
    "dev": logging.DEBUG,
    "staging": logging.DEBUG,
    "production": logging.INFO,
}

logger = logging.getLogger(__name__)
logger.setLevel(log_level[ENV])


# !Note: To ease deployment I kept all functions within this one module.
# Ideally the different sections in this file would live in separate modules.
# However, it would require to deploy the lambda function differently.
# Depending on how complex this modules becomes, we need to refactor it accordingly.


#############################
# Error Classes
#############################


class TileNotFoundError(Exception):
    pass


#############################
# Annual Loss Filters
#############################


def scale_intensity(zoom: int) -> Callable:
    """Simplified implementing of d3.scalePow().

    Assuming that both domain and range always start with 0.
    """
    exp = 0.3 + ((zoom - 3) / 20) if zoom < 11 else 1
    domain = (0, 255)
    scale_range = (0, 255)
    m = scale_range[1] / domain[1] ** exp
    b = scale_range[0]

    def scale_pow(x: ndarray) -> ndarray:
        return m * x**exp + b

    return scale_pow


def apply_annual_loss_filter(
    data: ndarray, z: str, start_year: Optional[str], end_year: Optional[str], **kwargs
) -> ndarray:

    logger.debug("Apply annual loss filter")

    zoom = int(z)

    intensity, _, year = data[:3]
    scale_pow: Callable = scale_intensity(zoom)
    scaled_intensity: ndarray = scale_pow(intensity).astype("uint8")

    _start_year = 2001 if not start_year else max(2001, int(start_year))
    _end_year = None if not end_year else max(_start_year, int(end_year))

    start_year_mask: Union[bool, ndarray] = year >= _start_year - 2000
    end_year_mask: Union[bool, ndarray] = (_end_year is None) or (
        year <= _end_year - 2000
    )

    # Construct RGBA bands with floating point values for precision
    red: np.ndarray = np.ones(intensity.shape).astype("float32") * 228
    green: ndarray = (
        np.ones(intensity.shape).astype("float32") * 102
        + (72 - zoom)
        - (scaled_intensity * (3 / max(zoom, 1)))
    )
    blue: ndarray = (
        np.ones(intensity.shape).astype("float32") * 153 
        + (33 - zoom) 
        - (intensity / max(zoom, 1))
    )
    alpha: ndarray = (
        (scaled_intensity if zoom < 13 else intensity) * start_year_mask * end_year_mask
    ).astype("float32")

    # Ensure GBA values are in [0, 255] range
    green = np.clip(green, 0, 255).astype("uint8")
    blue = np.clip(blue, 0, 255).astype("uint8")
    alpha = np.clip(alpha, 0, 255).astype("uint8")

    return np.array([red.astype("uint8"), green, blue, alpha])


##############################
# Deforestation Alerts Filters
##############################


def days_since_bog(d: date) -> int:
    """Convert date into number of days since 2014-12-31 (beginning of
    GLAD)."""

    baseyear = 2015
    year = d.year
    day_in_year = d.timetuple().tm_yday
    offset = (year - baseyear) * 365 + sum(
        [int(not (y % 4)) for y in range(baseyear - 1, year)]
    )

    return offset + day_in_year


def get_alpha_band(
    rgb: ndarray,
    start_date: Optional[int],
    end_date: Optional[int],
    confirmed_only: Optional[bool],
) -> ndarray:
    """Compute alpha value based on RGB encoding and applied filters.

    Expecting 3D array.
    """

    logger.debug("Get Deforestation Alert Alpha Band")

    # encode false color tiles
    red, green, blue = rgb

    # date and intensity must be Unit16 to stay in value range
    days = (red.astype("uint16") * 255 + green).astype("uint16")
    confidence = np.floor(blue / 100).astype("uint8")
    intensity = (blue % 100).astype("uint16")

    # build masks
    date_mask: Union[bool, ndarray] = (start_date is None or start_date <= days) * (
        end_date is None or days <= end_date
    )
    confidence_mask: Union[bool, ndarray] = (
        (confidence == 2) if confirmed_only else True
    )
    no_data_mask: ndarray = red + green + blue > 0

    # compute alpha value
    alpha: ndarray = (
        np.minimum(255, intensity * 50) * date_mask * confidence_mask * no_data_mask
    ).astype("uint8")

    return alpha


def apply_deforestation_filter(
    data: ndarray,
    start_date: Optional[str],
    end_date: Optional[str],
    confirmed_only: Optional[bool],
    **kwargs,
) -> ndarray:
    """Decode using Pink alert color and filtering out unwanted alerts."""

    logger.debug("Apply Deforestation Filter")

    start_day = (
        days_since_bog(datetime.strptime(start_date, "%Y-%m-%d").date())
        if start_date
        else None
    )
    end_day = (
        days_since_bog(datetime.strptime(end_date, "%Y-%m-%d").date())
        if end_date
        else None
    )

    # Create an all pink image with varying opacity
    red = np.ones(data[0].shape).astype("uint8") * 228
    green = np.ones(data[1].shape).astype("uint8") * 102
    blue = np.ones(data[2].shape).astype("uint8") * 153

    # Compute alpha value
    alpha = get_alpha_band(data, start_day, end_day, confirmed_only)

    # stack bands and return
    return np.array([red, green, blue, alpha])


############################
# Data Lake Reader
############################


def get_tile_location(x: int, y: int) -> Tuple[int, int, int, int]:
    """Get the ID of the source tile in which the z/x/y tile is located.

    Source tile IDs are defined based on Zoom level and number of
    potential pixels. A Source tile can have a maximum of 65536x65526
    pixel which is equivalent to 256x256 blocks of 256x256 pixels each.
    Tile Ids follow the pattern 000R_000C, indicating the row and column
    of tile in zoom level starting at the top left corner. X and Y
    indices represent one 256x256 block within a tile.
    """

    logger.debug("Get Tile Location")

    row: int = floor(y / TILE_SIZE)
    col: int = floor(x / TILE_SIZE)

    row_off: int = (y - (row * TILE_SIZE)) * TILE_SIZE
    col_off: int = (x - (col * TILE_SIZE)) * TILE_SIZE

    return row, col, row_off, col_off


def get_tile_array(src_tile: str, window: Window) -> np.ndarray:
    """Create mercator tile from GFW WM Tile Set images."""

    logger.debug("Get Tile Array")

    # if running lambda in localstack, need to use special docker IP address
    # provided in env to reach localstack
    if AWS_ENDPOINT_HOST:
        gdal_env = {
            "AWS_HTTPS": "NO",
            "AWS_VIRTUAL_HOSTING": False,
            "AWS_S3_ENDPOINT": AWS_ENDPOINT_HOST,
            "GDAL_DISABLE_READDIR_ON_OPEN": "NO",
        }
    else:
        gdal_env = {
            "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
        }

    logger.debug(f"GDAL_ENV: {gdal_env}")
    with rasterio.Env(**gdal_env), rasterio.open(src_tile) as src:
        profile = src.profile
        bands = profile["count"]
        indexes = tuple(range(1, bands + 1))
        out_shape = (len(indexes), TILE_SIZE, TILE_SIZE)
        data = src.read(
            window=window, boundless=True, out_shape=out_shape, indexes=indexes
        )

    return data


def get_source_window(
    dataset: str,
    version: str,
    implementation: str,
    x: int,
    y: int,
    z: int,
    over_zoom: Optional[int],
) -> Tuple[str, Window]:

    tile = Tile(x, y, z)
    if over_zoom is not None and over_zoom < z:
        parent_tile = parent(tile, zoom=over_zoom)
        row, col, _, _ = get_tile_location(parent_tile.x, parent_tile.y)
        _z = over_zoom
        tile_bounds = xy_bounds(tile)

        pixel_size = CE / math.pow(2, _z) / TILE_SIZE

        top = (CE / 2) - ((row * pixel_size) * (TILE_SIZE**2))
        left = (-CE / 2) + ((col * pixel_size) * (TILE_SIZE**2))

        geotransform = (left, pixel_size, 0.0, top, 0.0, -pixel_size)

        window: Window = windows.from_bounds(
            tile_bounds.left,
            tile_bounds.bottom,
            tile_bounds.right,
            tile_bounds.top,
            transform=Affine.from_gdal(*geotransform),
        )
    else:
        row, col, row_off, col_off = get_tile_location(tile.x, tile.y)
        _z = z
        # We could use windows.from_bounds here as well,
        # however this approach is slightly more efficient
        window = Window(col_off, row_off, TILE_SIZE, TILE_SIZE)

    src_tile = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-3857/zoom_{_z}/{implementation}/geotiff/{str(row).zfill(3)}R_{str(col).zfill(3)}C.tif"

    return src_tile, window


def read_data_lake(dataset, version, implementation, x, y, z, over_zoom, **kwargs):

    logger.debug("Read data lake")

    if over_zoom is not None:
        _over_zoom = int(over_zoom)
    else:
        _over_zoom = None

    src_tile, window = get_source_window(
        dataset, version, implementation, int(x), int(y), int(z), _over_zoom
    )

    logger.debug(f"X, Y, Z: {(x, y, z)}")
    logger.debug(f"Window: {window}")
    logger.debug(f"SCR TILE: {src_tile}")

    try:
        tile = get_tile_array(src_tile, window)
    except RasterioIOError:
        logger.exception(f"Cannot open file {src_tile} with window {window}")
        raise TileNotFoundError()

    return tile


#########################
# Tile Cache Reader
#########################


def read_tile_cache(dataset, version, implementation, x, y, z, **kwargs) -> ndarray:

    logger.debug("Read Tile Cache")

    url = f"{TILE_CACHE_URL}/{dataset}/{version}/{implementation}/{z}/{x}/{y}.png"
    try:
        png = Image.open(urlopen(url))  # nosec
    except URLError:
        logger.exception(f"Cannot open remote tile {url}")
        raise TileNotFoundError()

    arr = np.array(png)

    return separat_bands(arr)


##########################
# Array functions
##########################


def separat_bands(arr: ndarray) -> ndarray:

    logger.debug("Store bands in separate arrays")
    # convert data from (height, width, bands) to (bands, height, width)
    shape = arr.shape
    return arr.transpose((2, 1, 0)).reshape(shape[::-1])


def combine_bands(arr: ndarray) -> ndarray:

    logger.debug("Combine bands in one array.")
    # moves data from (4, 256, 256) format to (256, 256, 4)
    # PIL will read it in both ways, but for some reason
    # only propagates the first band to the other three
    # when in (4, 256, 256)

    return np.dstack([*arr])


def array_to_img(arr: np.ndarray) -> str:
    """Convert a numpy array to a base64 encoded img."""

    logger.debug("Convert array into image")

    band_count = arr.shape[0]
    arr = combine_bands(arr)

    modes = {3: "RGB", 4: "RGBA"}

    img = Image.fromarray(arr, mode=modes[band_count])

    sio = BytesIO()
    params = {"compress_level": 0}

    img.save(sio, "png", **params)
    sio.seek(0)

    return base64.b64encode(sio.getvalue()).decode()


###########################
# Handler
###########################


def handler(event: Dict[str, Any], _: Dict[str, Any]) -> Dict[str, str]:
    """Handle tile requests.

    expected event model:

    dataset: str
    version: str
    x: int
    y: int
    z: int
    source: str = "datalake"
    filter_type: Optional[str] = None
    over_zoom: Optional[int] = None
    """

    logger.debug(f"EVENT DATA: {json.dumps(event)}")

    reader_constructor = {"datalake": read_data_lake, "tilecache": read_tile_cache}

    filter_constructor = {
        "annual_loss": apply_annual_loss_filter,
        "deforestation_alerts": apply_deforestation_filter,
    }

    source: str = event.get("source", "datalake")
    filter_type: Optional[str] = event.get("filter_type")

    response: Dict[str, str] = {}

    # There is a risk of recursively call this lambda function over and over again when using tile cache source.
    # Hence we can only call this when applying a filter (which will call the unfiltered tile from tile cache)
    if source == "tilecache" and not filter_type:
        response["status"] = "error"
        response["message"] = "Cannot use tilecache source without filter."
        return response

    try:
        tile = reader_constructor[source](**event)
    except TileNotFoundError:
        response["status"] = "error"
        response["message"] = "Tile not found"
        return response
    except KeyError:
        response["status"] = "error"
        response["message"] = "Reader not implemented"
        return response

    if filter_type:
        try:
            tile = filter_constructor[filter_type](tile, **event)
        except KeyError:
            response["status"] = "error"
            response["message"] = "Filter not implemented"
            return response

    png = array_to_img(tile)
    response["status"] = "success"
    response["data"] = png

    return response
