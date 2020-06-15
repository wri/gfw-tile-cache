"""
Static raster tiles are pre-rendered for faster access. While performance for this tiles will be better,
you will not be able to filter data or change tile resolution.
Any of this operations will have to happen on the frontend.
If tiles for a given zoom level are not present for a selected dataset,
the server will redirect the request to the dynamic service and will attempt to generate it here
"""

from typing import Any, Dict, Tuple

from fastapi import APIRouter, Depends, Response

from . import static_version_dependency, xyz

router = APIRouter()

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
