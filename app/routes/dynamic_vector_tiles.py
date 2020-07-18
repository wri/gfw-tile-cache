"""
Dynamic vector tiles are generated on the fly.
The dynamic nature of the service allows users to apply filters using query parameters
or to change tile resolution using the `@` operator after the `y` index
"""

from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.sql import Select, TableClause

from ..crud.async_db.vector_tiles import get_mvt_table, get_tile
from ..crud.async_db.vector_tiles.filters import geometry_filter
from ..models.enumerators.geostore import GeostoreOrigin
from ..models.types import Bounds
from ..responses import VectorTileResponse
from . import dynamic_version_dependency, xyz

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
    geostore_id: Optional[UUID] = Query(
        None,
        description="Only show fire alerts within selected geostore area. Use RW geostore as of now.",
    ),
    geostore_origin: GeostoreOrigin = Query(
        "gfw", description="Origin service of geostore ID"
    )
) -> VectorTileResponse:
    """
    Generic dynamic vector tile
    """
    dataset, version = dv
    bbox, _, extent = bbox_z

    filters: List[TableClause] = list()

    geom_filter: TableClause = await geometry_filter(geostore_id, bbox, geostore_origin)

    if geom_filter is not None:
        filters.append(geom_filter)

    query: Select = get_mvt_table(dataset, version, bbox, extent, list(), *filters)

    return await get_tile(query, name=dataset, extent=extent)
