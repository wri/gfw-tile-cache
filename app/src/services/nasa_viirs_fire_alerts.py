from typing import Dict, Any, List

from shapely.geometry import box
from sqlalchemy import column, literal_column
from sqlalchemy.sql.elements import ColumnClause, TextClause

from app.src.services import vector_tiles
from fastapi import Response

Geometry = Dict[str, Any]

SCHEMA = "nasa_viirs_fire_alerts"
COLUMNS: List[ColumnClause] = [
    column("latitude"),
    column("longitude"),
    column("acq_date"),
    column("acq_time"),
    column("confidence"),
    column("bright_ti4"),
    column("bright_ti5"),
    column("frp"),
]


async def get_tile(
    version: str, bbox: box, *filters: TextClause, **values: Any
) -> Response:
    """
    Make SQL query to PostgreSQL and return vector tile in PBF format.
    """
    query, values = vector_tiles.get_mvt_table(
        f"{SCHEMA}.{version}", bbox, COLUMNS, *filters, **values
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
        f"{SCHEMA}.{version}", bbox, COLUMNS, *filters, **values
    )

    columns = [
        literal_column("count(*)").label("count"),
        literal_column("mode() WITHIN GROUP (ORDER BY acq_date)").label("acq_date"),
        literal_column("avg(bright_ti4)").label("bright_ti4"),
        literal_column("avg(bright_ti5)").label("bright_ti5"),
        literal_column("sum(frp)").label("frp"),
    ]
    group_by_columns = [column("geom")]

    return await vector_tiles.get_aggregated_tile(
        query, columns, group_by_columns, **values
    )
