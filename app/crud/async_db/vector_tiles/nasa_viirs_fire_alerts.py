from typing import List, Optional

from fastapi.logger import logger
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
    attributes: List[SupportedAttribute],
    filters: List[TextClause],
) -> VectorTileResponse:
    """Make SQL query to PostgreSQL and return vector tile in PBF format.

    This function makes a SQL query that aggregates point features based
    on proximity.
    """

    col_dict = {
        SupportedAttribute.LATITUDE: db.literal_column("round(avg(latitude),4)").label(
            "latitude"
        ),
        SupportedAttribute.LONGITUDE: db.literal_column(
            "round(avg(longitude),4)"
        ).label("longitude"),
        SupportedAttribute.ALERT_DATE: db.literal_column(
            "mode() WITHIN GROUP (ORDER BY alert__date)"
        ).label("alert__date"),
        SupportedAttribute.ALERT_TIME_UTC: db.literal_column(
            "mode() WITHIN GROUP (ORDER BY alert__time_utc)"
        ).label("alert__time_utc"),
        SupportedAttribute.CONFIDENCE_CAT: db.literal_column(
            "mode() WITHIN GROUP (ORDER BY confidence__cat)"
        ).label("confidence__cat"),
        SupportedAttribute.BRIGHT_TI4_K: db.literal_column(
            'round(avg("bright_ti4__K"),3)'
        ).label("bright_ti4__K"),
        SupportedAttribute.BRIGHT_TI5_K: db.literal_column(
            'round(avg("bright_ti5__k"),3)'
        ).label("bright_ti5__K"),
        SupportedAttribute.FRP_MW: db.literal_column('sum("frp__MW")').label("frp__MW"),
        SupportedAttribute.UMD_TREE_COVER_DENSITY__THRESHOLD: db.literal_column(
            'max("umd_tree_cover_density__threshold")'
        ).label("umd_tree_cover_density__threshold"),
        SupportedAttribute.UMD_TREE_COVER_DENSITY_2000__THRESHOLD: db.literal_column(
            'max("umd_tree_cover_density_2000__threshold")'
        ).label("umd_tree_cover_density_2000__threshold"),
    }

    columns: List[ColumnClause] = list()
    for field in get_attributes(SCHEMA, version, None):
        if field["is_feature_info"]:
            columns.append(db.column(field["field_name"]))

    logger.warning(columns)

    query = get_mvt_table(SCHEMA, version, bbox, extent, columns, filters)
    columns = [
        db.column("geom"),
        db.literal_column("count(*)").label("count"),
    ]

    for attribute in attributes:
        logger.warning(attribute)
        logger.warning(col_dict[attribute])
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
