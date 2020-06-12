from typing import Any, Dict, List, Optional, Text, Tuple

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.sql import Select, TableClause

from app.crud.vector_tiles.filters import geometry_filter

from ..crud import vector_tiles
from ..crud.vector_tiles import get_mvt_table
from . import Bounds, dynamic_version_dependency, static_version_dependency, xyz

router = APIRouter()


@router.get(
    "/{dataset}/{version}/dynamic/{z}/{x}/{y}.pbf",
    response_class=Response,
    tags=["Dynamic Vector Tiles"],
    response_description="PBF Vector Tile",
)
async def dynamic_vector_tile(
    *,
    dv: Tuple[str, str] = Depends(dynamic_version_dependency),
    bbox_z: Tuple[Bounds, int, int] = Depends(xyz),
    geostore_id: Optional[str] = Query(
        None, title="Only show fire alerts within selected geostore area"
    ),
) -> Response:
    """
    Dynamic vector tile
    """
    dataset, version = dv
    bbox, _, extent = bbox_z

    filters: List[TableClause] = list()

    geom_filter: TableClause = await geometry_filter(geostore_id, bbox)

    if geom_filter is not None:
        filters.append(geom_filter)

    query: Select = get_mvt_table(dataset, version, bbox, extent, list(), *filters)

    return await vector_tiles.get_tile(query, name=dataset, extent=extent)


@router.get(
    "/{dataset}/{version}/default/{z}/{x}/{y}.pbf",
    response_class=Response,
    tags=["Vector Tiles"],
    response_description="PBF Vector Tile",
)
async def vector_tile(
    *,
    dv: Tuple[str, str] = Depends(static_version_dependency),
    bbox_z: Tuple[Bounds, int] = Depends(xyz),
) -> Response:
    """
    Generic vector tile
    """
    # This endpoint is not implemented and only exist for documentation purposes
    # Default vector layers are stored on S3.
    # If tile is not found, Cloud Front will redirect request to dynamic endpoint.
    # Hence, this function should never be called.
    raise NotImplementedError
