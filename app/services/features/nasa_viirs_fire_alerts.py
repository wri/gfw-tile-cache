from asyncpg import Connection
from sqlalchemy import table, select, literal_column
from fastapi.logger import logger

from app.utils.sql import compile_sql


async def get_max_date(db: Connection, version):

    t = table(version)
    t.schema = "nasa_viirs_fire_alerts"
    sql = select(
        [literal_column("max(alert__date)").label("Max alert date")]
    ).select_from(t)

    sql = compile_sql(sql)

    query = await db.prepare(str(sql))
    max_date = await query.fetchval(timeout=30)
    return {"max_date": max_date}
