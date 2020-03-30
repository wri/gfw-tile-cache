import logging
from asyncpg.pool import Pool
from geojson import Feature, loads, FeatureCollection
from sqlalchemy import table, select, column

from app import get_pool
from app.utils.filters import filter_eq
from app.utils.sql import compile_sql

LOGGER = logging.Logger(__name__)


async def get_geostore(dataset, version, geostore_id):

    pool: Pool = await get_pool()
    t = table(version)  # TODO validate version
    t.schema = dataset

    columns = [
        column("gfw_geostore_id").label("geostore_id"),
        column("gfw_geojson").label("geojson"),
        column("gfw_area__ha").label("area__ha"),
    ]
    sql = (
        select(columns).select_from(t).where(filter_eq("gfw_geostore_id", geostore_id))
    )
    sql = compile_sql(sql)

    async with pool.acquire() as conn:
        sql = await conn.prepare(str(sql))
        row = await sql.fetchrow(timeout=30)

    response = dict()
    for field, value in row.items():
        if field == "geojson":
            geometry = loads(value)
            feature = Feature(geometry=geometry)
            feature_collection = FeatureCollection([feature])
            response[field] = feature_collection
        else:
            response[field] = value

    return response
