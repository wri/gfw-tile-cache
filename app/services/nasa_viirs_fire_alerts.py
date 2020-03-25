from typing import Dict, Any, List

from shapely.geometry import box
from sqlalchemy import column, literal_column
from sqlalchemy.sql.elements import ColumnClause, TextClause

from app.services import vector_tiles
from app.models.nasa_viirs_fire_alerts import NasaViirsFireAlertsBase
from fastapi import Response

Geometry = Dict[str, Any]

SCHEMA = "nasa_viirs_fire_alerts"
COLUMNS: List[ColumnClause] = [
    column(col) for col in NasaViirsFireAlertsBase.schema()["properties"].keys()
]


async def get_tile(
    version: str, bbox: box, *filters: TextClause, **values: Any
) -> Response:
    """
    Make SQL query to PostgreSQL and return vector tile in PBF format.
    """
    query, values = vector_tiles.get_mvt_table(
        SCHEMA, version, bbox, COLUMNS, *filters, **values
    )
    return await vector_tiles.get_tile(query, **values)


async def get_aggregated_tile(
    version: str, bbox: box, *filters: TextClause, **values: Any
) -> Response:
    """
    Make SQL query to PostgreSQL and return vector tile in PBF format.
    This function makes a SQL query that aggregates point features based on proximity.
    """
    query, values = vector_tiles.get_mvt_table(
        SCHEMA, version, bbox, COLUMNS, *filters, **values
    )

    columns = [
        literal_column("count(*)").label("count"),
        literal_column("mode() WITHIN GROUP (ORDER BY alert__date)").label(
            "alert__date"
        ),
        literal_column("avg(bright_ti4__k)").label("bright_ti4__K"),
        literal_column("avg(bright_ti5__k)").label("bright_ti5__K"),
        literal_column("sum(frp__mw)").label("frp__MW"),
    ]
    group_by_columns = [column("geom")]

    return await vector_tiles.get_aggregated_tile(
        query, columns, group_by_columns, **values
    )
