import logging

from asyncpg import Connection
from sqlalchemy import table, select, literal_column

from app.utils.sql import compile_sql

LOGGER = logging.Logger(__name__)


async def get_max_date(db: Connection, version):

    t = table(version)
    t.schema = "nasa_viirs_fire_alerts"
    sql = select(
        [literal_column("max(alert__date)").label("Max alert date")]
    ).select_from(t)

    sql = compile_sql(sql)

    sql = await db.prepare(sql)
    max_date = await sql.fetchval(timeout=30)
    return {"max_date": max_date}
