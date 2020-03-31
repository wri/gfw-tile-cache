import logging
from typing import Dict, Any, List, Tuple

from asyncpg.pool import Pool

from fastapi import Response
from shapely.geometry import box
from sqlalchemy import select, text, literal_column, table
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import TextClause, ColumnClause

from app import a_get_pool
from app.utils.sql import compile_sql

Geometry = Dict[str, Any]
Bounds = Tuple[float, float, float, float]

LOGGER = logging.Logger(__name__)


def get_mvt_table(
    schema_name: str,
    table_name: str,
    bbox: Bounds,
    columns: List[ColumnClause],
    *filters: text,
) -> Select:
    bounds: Select
    bound_values: Dict[str, Any]

    bounds = _get_bounds(*bbox)

    query: Select = _get_mvt_table(schema_name, table_name, bounds, *columns)
    return _filter_mvt_table(query, *filters)


async def get_tile(query: Select) -> Response:
    """
    Make SQL query to PostgreSQL and return vector tile in PBF format.
    """
    query = _as_vector_tile(query)
    return await _get_tile(query)


async def get_aggregated_tile(
    query: Select, columns: List[ColumnClause], group_by_columns: List[ColumnClause]
) -> Response:
    """
    Make SQL query to PostgreSQL and return vector tile in PBF format.
    This function makes a SQL query that aggregates point features based on proximity.
    """
    query = _group_mvt_table(query, columns, group_by_columns).alias(
        "grouped_mvt_table"
    )
    query = _as_vector_tile(query)
    return await _get_tile(query)


async def _get_tile(query: Select) -> Response:
    pool: Pool = await a_get_pool()

    query = compile_sql(query)

    async with pool.acquire() as conn:
        tile = await conn.fetchval(query=str(query))
        logging.debug(tile)

    return Response(
        content=tile,
        status_code=200,
        headers={
            "Content-Type": "application/x-protobuf",
            "Access-Control-Allow-Origin": "*",
        },
    )


def _get_bounds(left: float, bottom: float, right: float, top: float) -> Select:
    """
    Create bounds query
    """
    geom = text(
        "ST_MakeEnvelope(:left, :bottom, :right, :top, 3857) AS geom"
        # "ST_SetSRID(ST_MakeBox2D(ST_Point(:left, :bottom), ST_Point(:right, :top)),3857) AS geom"
    )
    values = {"left": left, "bottom": bottom, "top": top, "right": right}
    geom = geom.bindparams(**values)

    bounds = select([geom]).alias("bounds")

    return bounds


def _get_mvt_table(
    schema_name: str, table_name: str, bounds: Select, *columns: ColumnClause
) -> Select:
    """
    Create MVT Geom query
    """
    mvt_geom = literal_column(
        "ST_AsMVTGeom(t.geom_wm, bounds.geom::box2d, 4096, 0,false)"
    ).label("geom")

    src_table = table(table_name)
    src_table.schema = schema_name
    src_table = src_table.alias("t")

    col = [mvt_geom]
    for c in columns:
        col.append(c)
    bound_filter = text("ST_Intersects(t.geom_wm, bounds.geom)")

    return select(col).select_from(src_table).select_from(bounds).where(bound_filter)


def _filter_mvt_table(query: Select, *filters: TextClause) -> Select:
    for f in filters:
        query = query.where(f)

    return query.alias("mvt_table")


def _group_mvt_table(
    query: Select, columns: List[ColumnClause], group_by_columns: List[ColumnClause]
) -> Select:
    query = select(columns).select_from(query)
    for col in group_by_columns:
        query = query.group_by(col)

    return query.alias("grouped_mvt")


def _as_vector_tile(query: Select) -> Select:
    alias = query.name
    return select([literal_column(f"ST_AsMVT({alias}.*)")]).select_from(query)
