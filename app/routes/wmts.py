from typing import Optional, Tuple

from fastapi import APIRouter, Depends, Query, Response

from ..models.enumerators.wmts import WmtsRequest
from . import raster_tile_cache_version_dependency

router = APIRouter()


@router.get(
    "/{dataset}/{version}/default/wmts",
    response_class=Response,
    tags=["Raster Tiles"],
    # response_description="PNG Raster Tile",
)
async def wmts(
    *,
    dv: Tuple[str, str] = Depends(raster_tile_cache_version_dependency),
    SERVICE: str = Query("WMTS"),
    VERSION: str = Query("1.0.0"),
    REQUEST: WmtsRequest = Query(...),
    tileMatrixSet: Optional[str] = Query(None, description="Projection of tiles"),
    tileMatrix: Optional[int] = Query(None, description="z index"),
    tileRow: Optional[int] = Query(None, description="y index"),
    tileCol: Optional[int] = Query(None, description="x index"),
) -> Response:
    """
    WMTS Service
    """
    # dataset = dv[0]
    # version = dv[1]
    if REQUEST == WmtsRequest.get_capabilities:
        pass
    elif REQUEST == WmtsRequest.get_tiles:
        pass
