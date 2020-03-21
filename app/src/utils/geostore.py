from typing import Tuple, Dict, Any

from async_lru import alru_cache
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

import requests

from fastapi import HTTPException

Geometry = Dict[str, Any]


@alru_cache(maxsize=128)
async def get_geostore_geometry(geostore_id: str) -> Tuple[Geometry, BaseGeometry]:
    url = f"https://production-api.globalforestwatch.org/v2/geostore/{geostore_id}"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Call to geostore failed")

    try:
        geometry = response.json()["data"]["attributes"]["geojson"]["features"][0][
            "geometry"
        ]
    except KeyError:
        raise HTTPException(status_code=400, detail="Cannot fetch geostore geometry")

    return geometry, shape(geometry).envelope
