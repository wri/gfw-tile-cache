from typing import Any, Dict, Tuple

import pendulum
from fastapi import APIRouter, Depends, Response

from . import static_version_dependency, xyz

router = APIRouter()
NOW = pendulum.now()

DEFAULT_START = NOW.subtract(weeks=1).to_date_string()
DEFAULT_END = NOW.to_date_string()

Geometry = Dict[str, Any]
Bounds = Tuple[float, float, float, float]


@router.get(
    "/{dataset}/{version}/default/{z}/{x}/{y}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
async def raster_tile(
    *,
    dv: Tuple[str, str] = Depends(static_version_dependency),  # TODO: fix dependency
    bbox_z: Tuple[Bounds, int] = Depends(xyz),
) -> Response:
    """
    Generic raster tile
    """
    # This endpoint is not implemented and only exist for documentation purposes
    # Default vector layers are stored on S3.
    # If tile is not found, Cloud Front will redirect request to dynamic endpoint.
    # Hence, this function should never be called.
    raise NotImplementedError
