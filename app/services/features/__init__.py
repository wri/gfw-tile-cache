import logging
from asyncpg.pool import Pool
from sqlalchemy import table, select, literal_column
from shapely.geometry import mapping

from app import get_pool
from app.utils.filters import filter_eq, filter_intersects
from app.utils.geostore import geodesic_point_buffer
from app.utils.sql import compile_sql

LOGGER = logging.Logger(__name__)


async def get_feature(dataset, version, feature_id):
    pool: Pool = await get_pool()
    t = table(version)  # TODO validate version
    t.schema = dataset

    columns = [literal_column("*")]
    sql = select(columns).select_from(t).where(filter_eq("object_id", feature_id))
    sql = compile_sql(sql)

    async with pool.acquire() as conn:
        sql = await conn.prepare(str(sql))
        max_date = await sql.fetchval(timeout=30)
    return {"max_date": max_date}


async def get_features_by_location(dataset, version, lat, lng, zoom):
    pool: Pool = await get_pool()
    t = table(version)  # TODO validate version
    t.schema = dataset

    buffer_distance = _get_buffer_distance(zoom)
    geometry = geodesic_point_buffer(lat, lng, buffer_distance)

    columns = [literal_column("*")]
    sql = (
        select(columns)
        .select_from(t)
        .where(filter_intersects("geom", mapping(geometry)))
    )
    sql = compile_sql(sql)

    async with pool.acquire() as conn:
        sql = await conn.prepare(str(sql))
        max_date = await sql.fetchval(timeout=30)
    return {"max_date": max_date}


def _get_buffer_distance(zoom: int) -> int:
    zoom_buffer = {
        "z0": 10000,
        "z1": 5000,
        "z2": 2500,
        "z3": 1250,
        "z4": 600,
        "z5": 300,
        "z6": 500,
        "z7": 80,
        "z8": 40,
        "z9": 20,
    }

    try:
        return zoom_buffer[f"z{zoom}"]
    except KeyError:
        return 0
