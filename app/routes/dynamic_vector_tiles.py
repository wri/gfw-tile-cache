"""
Dynamic vector tiles are generated on the fly.
The dynamic nature of the service allows users to apply filters using query parameters
or to change tile resolution using the `@` operator after the `y` index
"""

from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, Query
from sqlalchemy.sql import Select, TableClause

from app.crud.vector_tiles.filters import geometry_filter

from ..crud import vector_tiles
from ..crud.vector_tiles import get_mvt_table
from ..responses import VectorTileResponse
from . import Bounds, dynamic_version_dependency, xyz

router = APIRouter()


@router.get(
    "/{dataset}/{version}/dynamic/{z}/{x}/{y}.pbf",
    response_class=VectorTileResponse,
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
) -> VectorTileResponse:
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
