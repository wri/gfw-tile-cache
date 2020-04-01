from typing import Dict, Any, List, Tuple

from asyncpg import Connection
from shapely.geometry import box
from sqlalchemy import column, literal_column
from sqlalchemy.sql.elements import ColumnClause, TextClause

from app.services import vector_tiles
from app.models.nasa_viirs_fire_alerts import NasaViirsFireAlertsBase
from fastapi import Response

Geometry = Dict[str, Any]
Bounds = Tuple[float, float, float, float]

SCHEMA = "nasa_viirs_fire_alerts"
COLUMNS: List[ColumnClause] = [
    column(col) for col in NasaViirsFireAlertsBase.schema()["properties"].keys()
]


async def get_tile(
    db: Connection, version: str, bbox: Bounds, *filters: TextClause
) -> Response:
    """
    Make SQL query to PostgreSQL and return vector tile in PBF format.
    """
    query = vector_tiles.get_mvt_table(SCHEMA, version, bbox, COLUMNS, *filters)
    return await vector_tiles.get_tile(db, query)


async def get_aggregated_tile(
    db: Connection, version: str, bbox: Bounds, *filters: TextClause
) -> Response:
    """
    Make SQL query to PostgreSQL and return vector tile in PBF format.
    This function makes a SQL query that aggregates point features based on proximity.
    """
    query = vector_tiles.get_mvt_table(SCHEMA, version, bbox, COLUMNS, *filters)

    columns = [
        column("geom"),
        literal_column("count(*)").label("count"),
        literal_column("mode() WITHIN GROUP (ORDER BY alert__date)").label(
            "alert__date"
        ),
        literal_column("avg(bright_ti4__k)").label("bright_ti4__k"),
        literal_column("avg(bright_ti5__k)").label("bright_ti5__k"),
        literal_column("sum(frp__mw)").label("frp__mw"),
    ]
    group_by_columns = [column("geom")]

    return await vector_tiles.get_aggregated_tile(db, query, columns, group_by_columns)
