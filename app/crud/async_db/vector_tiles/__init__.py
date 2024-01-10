from typing import List

from fastapi.logger import logger
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import ColumnClause, TextClause

from ....application import db
from ....models.types import Bounds
from ....responses import VectorTileResponse


def get_mvt_table(
    schema_name: str,
    table_name: str,
    bbox: Bounds,
    extent: int,
    columns: List[ColumnClause],
    filters: List[TextClause],
    order_by: List[ColumnClause] = [],
) -> Select:

    bounds: Select

    bounds = _get_bounds(*bbox)

    query: Select = _get_mvt_table(
        schema_name, table_name, bounds, extent, columns, order_by
    )
    return _filter_mvt_table(query, *filters)


async def get_tile(query: Select, name: str, extent: int) -> VectorTileResponse:
    """Make SQL query to PostgreSQL and return vector tile in PBF format."""
    query = _as_vector_tile(query, name, extent)
    return await _get_tile(query)


async def get_aggregated_tile(
    query: Select,
    columns: List[ColumnClause],
    group_by_columns: List[ColumnClause],
    name: str,
    extent: int,
) -> VectorTileResponse:
    """Make SQL query to PostgreSQL and return vector tile in PBF format.

    This function makes a SQL query that aggregates point features based
    on proximity.
    """
    query = _group_mvt_table(query, columns, group_by_columns).alias(
        "grouped_mvt_table"
    )
    query = _as_vector_tile(query, name=name, extent=extent)
    return await _get_tile(query)


async def _get_tile(query: Select) -> VectorTileResponse:
    logger.warning(query)
    tile = await db.scalar(query)
    logger.warning(tile)
    return VectorTileResponse(content=tile, status_code=200)


def _get_bounds(left: float, bottom: float, right: float, top: float) -> Select:
    """Create bounds query."""
    geom = db.text(
        "ST_MakeEnvelope(:left, :bottom, :right, :top, 3857) AS geom"
        # "ST_SetSRID(ST_MakeBox2D(ST_Point(:left, :bottom), ST_Point(:right, :top)),3857) AS geom"
    )
    values = {"left": left, "bottom": bottom, "top": top, "right": right}
    geom = geom.bindparams(**values)

    bounds = db.select([geom]).alias("bounds")

    return bounds


def _get_mvt_table(
    schema_name: str,
    table_name: str,
    bounds: Select,
    extent: int,
    columns: List[ColumnClause],
    order_by: List[ColumnClause] = [],
) -> Select:
    """Create MVT Geom query."""

    mvt_geom = db.literal_column(
        f"ST_AsMVTGeom(t.geom_wm, bounds.geom::box2d, {extent}, 0,false)"
    ).label("geom")
    cols: List[ColumnClause] = list(columns)
    cols.append(mvt_geom)

    src_table = db.table(table_name)
    src_table.schema = schema_name
    src_table = src_table.alias("t")

    bound_filter = db.text("ST_Intersects(t.geom_wm, bounds.geom)")
    query = (
        db.select(cols).select_from(src_table).select_from(bounds).where(bound_filter)
    )

    if order_by:
        query = query.order_by(*order_by)

    return query


def _filter_mvt_table(query: Select, *filters: TextClause) -> Select:
    for f in filters:
        query = query.where(f)

    return query.alias("mvt_table")


def _group_mvt_table(
    query: Select, columns: List[ColumnClause], group_by_columns: List[ColumnClause]
) -> Select:
    query = db.select(columns).select_from(query)
    for col in group_by_columns:
        query = query.group_by(col)

    return query.alias("grouped_mvt")


def _as_vector_tile(query: Select, name: str = "default", extent: int = 4096) -> Select:
    alias = query.name
    return db.select(
        [db.literal_column(f"ST_AsMVT({alias}.*, '{name}', {extent})")]
    ).select_from(query)
