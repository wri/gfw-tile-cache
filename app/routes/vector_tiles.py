"""
Static vector tiles are pre-rendered for faster access. While performance for this tiles will be better,
you will not be able to filter data or change tile resolution.
Any of this operations will have to happen on the frontend.
If tiles for a given zoom level are not present for a selected dataset,
the server will redirect the request to the dynamic service and will attempt to generate it here
"""

from typing import Tuple

from fastapi import APIRouter, Depends, HTTPException

from ..models.types import Bounds
from ..responses import VectorTileResponse
from . import static_version_dependency, xyz

router = APIRouter()


@router.get(
    "/{dataset}/{version}/default/{z}/{x}/{y}.pbf",
    response_class=VectorTileResponse,
    tags=["Vector Tiles"],
    response_description="PBF Vector Tile",
)
async def vector_tile(
    *,
    dv: Tuple[str, str] = Depends(static_version_dependency),
    bbox_z: Tuple[Bounds, int] = Depends(xyz),
) -> VectorTileResponse:
    """
    Generic vector tile
    """
    # This endpoint is not implemented and only exist for documentation purposes
    # Default vector layers are stored on S3.
    # If tile is not found, Cloud Front will redirect request to dynamic endpoint.
    # Hence, this function should never be called.
    raise HTTPException(status_code=501, detail="Not implemented.")
