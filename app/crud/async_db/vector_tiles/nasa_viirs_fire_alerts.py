from typing import List, Optional

from sqlalchemy.sql.elements import ColumnClause, TextClause

from ....application import db
from ....models.types import Bounds
from ....responses import VectorTileResponse
from ...async_db import vector_tiles
from ...sync_db.vector_tile_assets import get_dynamic_fields, get_latest_dynamic_version
from . import get_mvt_table

SCHEMA = "nasa_viirs_fire_alerts"

COLUMNS: List[ColumnClause] = list()
latest_version: Optional[str] = get_latest_dynamic_version(SCHEMA)
if latest_version:
    fields = get_dynamic_fields(SCHEMA, latest_version)
    for field in fields:
        if field["is_feature_info"]:
            COLUMNS.append(db.column(field["field_name"]))


async def get_tile(
    version: str, bbox: Bounds, extent: int, *filters: TextClause
) -> VectorTileResponse:
    """
    Make SQL query to PostgreSQL and return vector tile in PBF format.
    """
    query = get_mvt_table(SCHEMA, version, bbox, extent, COLUMNS, *filters)
    return await vector_tiles.get_tile(query, SCHEMA, extent)


async def get_aggregated_tile(
    version: str, bbox: Bounds, extent: int, attributes: List[str], *filters: TextClause
) -> VectorTileResponse:
    """
    Make SQL query to PostgreSQL and return vector tile in PBF format.
    This function makes a SQL query that aggregates point features based on proximity.
    """

    col_dict = {
        "latitude": db.literal_column("round(avg(latitude),4)").label("latitude"),
        "longitude": db.literal_column("round(avg(longitude),4)").label("longitude"),
        "alert__date": db.literal_column(
            "mode() WITHIN GROUP (ORDER BY alert__date)"
        ).label("alert__date"),
        "alert__time_utc": db.literal_column(
            "mode() WITHIN GROUP (ORDER BY alert__time_utc)"
        ).label("alert__time_utc"),
        "confidence__cat": db.literal_column(
            "mode() WITHIN GROUP (ORDER BY confidence__cat)"
        ).label("confidence__cat"),
        "bright_ti4__K": db.literal_column('round(avg("bright_ti4__K"),3)').label(
            "bright_ti4__K"
        ),
        "bright_ti5__K": db.literal_column('round(avg("bright_ti5__k"),3)').label(
            "bright_ti5__K"
        ),
        "frp__MW": db.literal_column('sum("frp__MW")').label("frp__MW"),
    }

    query = get_mvt_table(SCHEMA, version, bbox, extent, COLUMNS, *filters)
    columns = [
        db.column("geom"),
        db.literal_column("count(*)").label("count"),
    ]

    for attribute in attributes:
        columns.append(col_dict[attribute])

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
