# mypy: ignore-errors

import base64
import logging
import os
from io import BytesIO
from typing import Any, Dict, Optional

import numpy as np
from filters import annual_loss, deforestation_alerts
from PIL import Image
from readers import datalake, tilecache

ENV: str = os.environ.get("ENV", "dev")
TILE_SIZE: int = 256
SUFFIX: str = "" if ENV == "production" else f"-{ENV}"

logger = logging.getLogger(__name__)

reader_constructor = {"datalake": datalake.read, "tilecache": tilecache.read}

filter_constructor = {
    "annual_loss": annual_loss.apply_filter,
    "deforestation_alerts": deforestation_alerts.apply_filter,
}


class TileNotFoundError(Exception):
    pass


def array_to_img(arr: np.ndarray) -> str:
    """Convert a numpy array to an base64 encoded img."""

    # moves data from (4, 256, 256) format to (256, 256, 4)
    # PIL will read it in both ways, but for some reason
    # only propogates the first band to the other three
    # when in (4, 256, 256)

    band_count = arr.shape[0]
    arr = np.dstack(tuple([arr[i] for i in range(band_count)]))

    modes = {3: "RGB", 4: "RGBA"}

    img = Image.fromarray(arr, mode=modes[band_count])

    sio = BytesIO()
    params = {"compress_level": 0}

    img.save(sio, "png", **params)
    sio.seek(0)

    return base64.b64encode(sio.getvalue()).decode()


def handler(event: Dict[str, Any], _: Dict[str, Any]) -> Dict[str, str]:
    """Handle tile requests."""

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
