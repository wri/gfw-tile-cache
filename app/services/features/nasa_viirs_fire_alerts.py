import logging
from asyncpg.pool import Pool
from sqlalchemy import table, select, literal_column

from app import a_get_pool


LOGGER = logging.Logger(__name__)


async def get_max_date(version):

    pool: Pool = await a_get_pool()
    t = table(version)
    t.schema = "nasa_viirs_fire_alerts"
    sql = select(
        [literal_column("max(alert__date)").label("Max alert date")]
    ).select_from(t)

    async with pool.acquire() as conn:
        sql = await conn.prepare(sql)
        max_date = await sql.fetchval(timeout=30)
    return {"max_date": max_date}
