# mypy: ignore-errors

import base64
import logging
import os
from datetime import date, datetime
from io import BytesIO
from math import floor
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.request import urlopen

import numpy as np
import rasterio
from numpy import ndarray
from PIL import Image
from rasterio import RasterioIOError
from rasterio.windows import Window

ENV: str = os.environ.get("ENV", "dev")
TILE_SIZE: int = 256
SUFFIX: str = "" if ENV == "production" else f"-{ENV}"
DATA_LAKE_BUCKET: str = os.environ.get("DATA_LAKE_BUCKET")
LOCALSTACK_HOSTNAME: str = os.environ.get("LOCALSTACK_HOSTNAME", None)
AWS_ENDPOINT_HOST: str = f"{LOCALSTACK_HOSTNAME}:4566" if LOCALSTACK_HOSTNAME else None

logger = logging.getLogger(__name__)

# !Note: To ease deployment I kept all functions within this one module.
# Ideally the different sections in this file would live in seperate modules.
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
    """
    Simplified implementing of d3.scalePow()
    Assuming that both domain and range always start with 0
    """
    exp = 0.3 + ((zoom - 3) / 20) if zoom < 11 else 1
    domain = (0, 256)
    scale_range = (0, 256)
    m = scale_range[1] / domain[1] ** exp
    b = scale_range[0]

    def scale_pow(x: ndarray) -> ndarray:
        return m * x ** exp + b

    return scale_pow


def apply_annual_loss_filter(
    data: ndarray, z: str, start_year: str = "2000", end_year: str = "3000", **kwargs
) -> ndarray:

    zoom = int(z)

    intensity, _, year = data
    scale_pow: Callable = scale_intensity(zoom)
    scaled_intensity: ndarray = scale_pow(intensity).astype("uint8")

    start_year_mask: ndarray = year >= (int(start_year) - 2000)
    end_year_mask: ndarray = year <= (int(end_year) - 2000)

    red: ndarray = np.ones(intensity.shape).astype("uint8") * 228
    green: ndarray = (
        np.ones(intensity.shape) * 102 + (72 - zoom) - (3 * scaled_intensity / zoom)
    ).astype("uint8")
    blue: ndarray = (
        np.ones(intensity.shape) * 153 + (33 - zoom) - (intensity / zoom)
    ).astype("uint8")
    alpha: ndarray = (
        (scaled_intensity if zoom < 13 else intensity) * start_year_mask * end_year_mask
    ).astype("uint8")

    return np.vstack((red, green, blue, alpha))


##############################
# Deforestation Alerts Filters
##############################


def days_since_bog(d: date) -> int:
    """Convert date into number of days since 2014-12-31 (beginning of GLAD)."""

    baseyear = 2015
    year = d.year
    day_in_year = d.timetuple().tm_yday
    offset = (year - baseyear) * 365 + sum(
        [int(not (y % 4)) for y in range(baseyear - 1, year)]
    )

    return offset + day_in_year


def get_alpha(
    rgb: ndarray, start_date: int, end_date: int, confirmed_only: bool
) -> int:
    """Compute alpha value based on RGB encoding and applied filters.
    Expecting 3D array.
    """

    # encode false color tiles
    red, green, blue = rgb
    date = red * 255 + green
    confidence = np.floor(blue / 100) - 1
    intensity = blue % 100

    # build masks
    date_mask = (start_date <= date) * (date <= end_date)
    confidence_mask = (
        (confidence == 1)
        if confirmed_only
        else np.ones(confidence.shape).astype("bool")
    )
    no_data_mask = red + green + blue > 0

    # compute alpha value
    alpha = np.minimim(255, intensity * 50) * date_mask * confidence_mask * no_data_mask

    return alpha


def apply_deforestation_filter(
    data: ndarray, start_date: str, end_date: str, confirmed_only: bool, **kwargs
) -> ndarray:
    """Decode using Pink alert color and filtering out unwanted alerts."""

    start_day = days_since_bog(datetime.strptime(start_date, "%Y-%m-%d").date())
    end_day = days_since_bog(datetime.strptime(end_date, "%Y-%m-%d").date())

    # Create an all pink image
    pink = np.ones(data.shape).astype("uint8") * [[228], [102], [153]]
    # Compute alpha value
    alpha = get_alpha(data, start_day, end_day, confirmed_only)

    # stack bands and return
    return np.vstack((pink, alpha))


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

    row: int = floor(y / TILE_SIZE)
    col: int = floor(x / TILE_SIZE)

    row_off: int = (y - (row * TILE_SIZE)) * TILE_SIZE
    col_off: int = (x - (col * TILE_SIZE)) * TILE_SIZE

    return row, col, row_off, col_off


def get_tile_array(src_tile: str, window: Window) -> np.ndarray:
    """Create mercator tile from GFW WM Tile Set images."""
    # if running lambda in localstack, need to use special docker IP address provided in env to reach localstack
    gdal_env = {
        "AWS_HTTPS": "NO" if AWS_ENDPOINT_HOST else "YES",
        "AWS_VIRTUAL_HOSTING": False if AWS_ENDPOINT_HOST else True,
        "AWS_S3_ENDPOINT": AWS_ENDPOINT_HOST,
        "GDAL_DISABLE_READDIR_ON_OPEN": "YES",
    }

    with rasterio.Env(**gdal_env), rasterio.open(src_tile) as src:
        profile = src.profile
        bands = profile["count"]
        indexes = tuple(range(1, bands + 1))
        out_shape = (len(indexes), TILE_SIZE, TILE_SIZE)
        data = src.read(
            window=window, boundless=True, out_shape=out_shape, indexes=indexes
        )

    return data


def read_data_lake(dataset, version, implementation, x, y, z, **kwargs):

    if implementation == "dynamic":
        pixel_meaning: str = "rgb_encoded"
    else:
        pixel_meaning = implementation

    row, col, row_off, col_off = get_tile_location(int(x), int(y))

    src_tile = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-3857/zoom_{z}/{pixel_meaning}/geotiff/{str(row).zfill(3)}R_{str(col).zfill(3)}C.tif"
    window: Window = Window(col_off, row_off, TILE_SIZE, TILE_SIZE)

    print("X, Y, Z: ", (x, y, z))
    print("SCR TILE: ", src_tile)

    try:
        tile = get_tile_array(src_tile, window)
    except RasterioIOError as e:
        raise TileNotFoundError(str(e))

    return tile


#########################
# Tile Cache Reader
#########################


def read_tile_cache(dataset, version, implementation, x, y, z, **kwargs) -> ndarray:
    url = f"https://tiles{SUFFIX}.globalforestwatch.org/{dataset}/{version}/{implementation}/{z}/{x}/{y}.png"
    png = Image.open(urlopen(url))  # nosec
    arr = np.array(png)

    return seperate_bands(arr)


##########################
# Array functions
##########################


def seperate_bands(arr: ndarray) -> ndarray:
    # convert data from (height, width, bands) to (bands, height, width)
    shape = arr.shape
    return arr.transpose((2, 1, 0)).reshape(shape[::-1])


def combine_bands(arr: ndarray) -> ndarray:
    # moves data from (4, 256, 256) format to (256, 256, 4)
    # PIL will read it in both ways, but for some reason
    # only propogates the first band to the other three
    # when in (4, 256, 256)

    band_count = arr.shape[0]
    return np.dstack(tuple([arr[i] for i in range(band_count)]))


def array_to_img(arr: np.ndarray) -> str:
    """Convert a numpy array to an base64 encoded img."""

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
    """Handle tile requests."""

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
