from typing import List, Optional

from sqlalchemy.sql.elements import ColumnClause, TextClause

from ....application import db
from ....models.enumerators.nasa_viirs_fire_alerts.supported_attributes import (
    SupportedAttribute,
)
from ....models.types import Bounds
from ....responses import VectorTileResponse
from ...async_db import vector_tiles
from ...sync_db.tile_cache_assets import get_attributes
from . import get_mvt_table

SCHEMA = "nasa_viirs_fire_alerts"


async def get_aggregated_tile(
    version: str,
    bbox: Bounds,
    extent: int,
    supported_attributes: List[SupportedAttribute],
    filters: List[TextClause],
) -> VectorTileResponse:
    """Make SQL query to PostgreSQL and return vector tile in PBF format.

    This function makes a SQL query that aggregates point features based
    on proximity.
    """

    columns: List[ColumnClause] = list()
    attributes: List[str] = await get_attributes(SCHEMA, version)
    for attribute in attributes:
        columns.append(db.column(attribute))

    query = get_mvt_table(SCHEMA, version, bbox, extent, columns, filters)
    columns = [
        db.column("geom"),
        db.literal_column("count(*)").label("count"),
    ]

    for attribute in supported_attributes:
        columns.append(attribute.aggregation_rule)

    group_by_columns = [db.column("geom")]

    return await vector_tiles.get_aggregated_tile(
        query, columns, group_by_columns, SCHEMA, extent
    )


# TODO can be replaced with generic contextual filter
#  once we made sure that fire data are normalized
def confidence_filter(high_confidence_only: Optional[bool]) -> Optional[TextClause]:
    if high_confidence_only:
        return db.text("(confidence__cat = 'high' OR confidence__cat = 'h')")
    return None
