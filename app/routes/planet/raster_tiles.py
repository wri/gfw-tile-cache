from typing import List, Tuple

import httpx
from aenum import Enum, extend_enum
from fastapi import APIRouter, Depends, Query, Response

from app.routes import raster_xyz
from app.settings.globals import GLOBALS

router = APIRouter()


class PlanetImageMode(str, Enum):
    rgb = "rgb"
    cir = "cir"


class PlanetDateRange(str, Enum):
    """Available date ranges of Planet Mosaics"""


def get_planet_date_ranges() -> List[str]:
    url = f"https://api.planet.com/basemaps/v1/mosaics?api_key={GLOBALS.planet_api_key}"
    resp = httpx.get(url)
    return [mosaic["name"][34:-7] for mosaic in resp.json()["mosaics"]]


for _date_range in get_planet_date_ranges():
    extend_enum(PlanetDateRange, _date_range, _date_range)


@router.get(
    "/planet/v1/planet_medres_normalized_analytic/{z}/{x}/{y}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def planet_raster_tile(
    *,
    response: Response,
    xyz: Tuple[int, int, int] = Depends(raster_xyz),
    date_range: PlanetDateRange = Query(
        ...,
        description=PlanetDateRange.__doc__,
    ),
    proc: PlanetImageMode = Query(
        PlanetImageMode.rgb,
        description="Image mode. `rgb`=Red|Gree|Blue, `cir` = Close Infra Red|Red|Green",
    ),
) -> Response:
    """
    A proxy for Planet Mosaic Tiles
    """
    x, y, z = xyz

    async with httpx.AsyncClient() as client:
        proxy = await client.get(
            f"https://tiles.planet.com/basemaps/v1/planet-tiles/planet_medres_normalized_analytic_{date_range}_mosaic/gmap/{z}/{x}/{y}.png?proc={proc}&api_key={GLOBALS.planet_api_key}"
        )
        response.body = proxy.content
        response.status_code = proxy.status_code
    return response
