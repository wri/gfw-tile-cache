"""Dynamic vector tiles are generated on the fly.

The dynamic nature of the service allows users to apply filters using
query parameters or to change tile resolution using the `@` operator
after the `y` index
"""
from typing import List, Optional, Tuple
from uuid import UUID

from asyncpg.exceptions import QueryCanceledError
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.sql import Select, TableClause
from sqlalchemy.sql.elements import ColumnClause

from ..application import db
from ..crud.async_db.vector_tiles import get_mvt_table, get_tile
from ..crud.async_db.vector_tiles.filters import geometry_filter
from ..crud.sync_db.tile_cache_assets import get_attributes
from ..models.enumerators.geostore import GeostoreOrigin
from ..models.types import Bounds
from ..responses import VectorTileResponse
from . import dynamic_vector_tile_cache_version_dependency, vector_xyz

router = APIRouter()


@router.get(
    "/{dataset}/{version}/dynamic/{z}/{x}/{y}.pbf",
    response_class=VectorTileResponse,
    tags=["Dynamic Vector Tiles"],
    response_description="PBF Vector Tile",
)
async def dynamic_vector_tile(
    *,
    dv: Tuple[str, str] = Depends(dynamic_vector_tile_cache_version_dependency),
    bbox_z: Tuple[Bounds, int, int] = Depends(vector_xyz),
    geostore_id: Optional[UUID] = Query(
        None,
        description="Only show fire alerts within selected geostore area. Use RW geostore as of now.",
    ),
    geostore_origin: GeostoreOrigin = Query(
        "gfw", description="Origin service of geostore ID"
    ),
    include_attribute: Optional[List[str]] = Query(
        None,
        title="Included Attributes",
        description="Select which attributes to include in vector tile."
        "Please check data-api for available attribute values."
        "If not specified, all attributes will be shown.",
    ),
) -> VectorTileResponse:
    """Generic dynamic vector tile."""
    dataset, version = dv
    bbox, _, extent = bbox_z

    filters: List[TableClause] = list()

    geom_filter: TableClause = await geometry_filter(geostore_id, bbox, geostore_origin)

    if geom_filter is not None:
        filters.append(geom_filter)

    attributes: List[str] = await get_attributes(dataset, version)

    # if no attributes specified get all feature info fields
    if not include_attribute:
        columns: List[ColumnClause] = [db.column(attribute) for attribute in attributes]
    # otherwise run provided list against feature info list and keep common elements
    else:
        columns = [
            db.column(attribute)
            for attribute in attributes
            if attribute in include_attribute
        ]

    query: Select = get_mvt_table(dataset, version, bbox, extent, columns, filters)

    try:
        tile = await get_tile(query, name=dataset, extent=extent)
    except QueryCanceledError:
        raise HTTPException(
            status_code=524,
            detail="A timeout occurred while processing the request. Request canceled.",
        )
    else:
        return tile
