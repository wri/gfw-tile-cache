from functools import partial
import logging
from typing import Tuple, Dict, Any

import pyproj
import requests

from async_lru import alru_cache
from fastapi import HTTPException
from shapely.geometry import shape, Point
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform


LOGGER = logging.Logger(__name__)
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


def geodesic_point_buffer(lat, lng, meter):
    """
    https://gis.stackexchange.com/questions/289044/creating-buffer-circle-x-kilometers-from-point-using-python
    """
    proj_wgs84 = pyproj.Proj(init="epsg:4326")
    # Azimuthal equidistant projection
    aeqd_proj = "+proj=aeqd +lat_0={lat} +lon_0={lon} +x_0=0 +y_0=0"
    project = partial(
        pyproj.transform, pyproj.Proj(aeqd_proj.format(lat=lat, lon=lng)), proj_wgs84
    )
    buf = Point(0, 0).buffer(meter)  # distance in metres

    return [transform(project, buf).exterior.coords[:]]
