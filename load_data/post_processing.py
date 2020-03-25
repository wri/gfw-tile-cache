import asyncio
import os
from typing import List, Tuple

import asyncpg
import pendulum
from aiostream import stream, pipe
from asyncpg.pool import Pool
from pendulum.parsing.exceptions import ParserError

POOL = None
YEARS = range(2011, 2022)
WEEKS = range(1, 54)
SCHEMA = "nasa_viirs_fire_alerts"
TABLE = "v202003"


async def main() -> None:
    weeks = _get_weeks()

    await create_indicies_only()

    # https://stackoverflow.com/questions/48052217/how-to-use-an-async-for-loop-to-iterate-over-a-list
    xs = stream.iterate(weeks) | pipe.map(partiontions, task_limit=10)

    # Use a stream context for proper resource management
    async with xs.stream() as streamer:
        async for result in streamer:
            print(result)


async def get_pool() -> Pool:
    """
    The database connection pool
    """
    global POOL
    if POOL is None:
        POOL = await asyncpg.create_pool(
            database=os.environ["POSTGRES_NAME"],
            user=os.environ["POSTGRES_USERNAME"],
            password=os.environ["POSTGRES_PASSWORD"],
            port=os.environ["POSTGRES_PORT"],
            host=os.environ["POSTGRES_HOST"],
        )
    return POOL


async def create_indicies_only() -> None:
    """
    This creates an invalid index.
    It will be validated automatically, once all partitions are indexed and attached.
    """
    pool = await get_pool()
    conn = await pool.acquire()

    async with conn.transaction():
        await conn.execute(
            _get_sql("sql/create_indicies.sql.tmpl", schema=SCHEMA, table=TABLE)
        )


async def partiontions(weeks: Tuple[int, str]) -> Tuple[int, str]:
    year = weeks[0]
    week = weeks[1]

    pool = await get_pool()
    conn = await pool.acquire()

    async with conn.transaction():
        await conn.execute(
            _get_sql(
                "sql/update_geometry.sql.tmpl",
                schema=SCHEMA,
                table=TABLE,
                year=year,
                week=week,
            )
        )
    async with conn.transaction():
        await conn.execute(
            _get_sql(
                "sql/create_partition_indicies.sql.tmpl",
                schema=SCHEMA,
                table=TABLE,
                year=year,
                week=week,
            )
        )

    async with conn.transaction():
        await conn.execute(
            _get_sql(
                "sql/cluster_partitions.sql.tmpl",
                schema=SCHEMA,
                table=TABLE,
                year=year,
                week=week,
            )
        )

    return weeks


def _get_sql(sql_tmpl, **kwargs) -> str:
    with open(sql_tmpl, "r") as tmpl:
        sql = tmpl.read().format(**kwargs)
    print(sql)
    return sql


def _get_weeks() -> List[Tuple[int, str]]:
    weeks: List[Tuple[int, str]] = list()
    for year in YEARS:
        for week in WEEKS:
            try:
                # Check if year has that many weeks
                pendulum.parse(f"{year}-W{week}")

                week_str = f"{week:02}"
                weeks.append((year, week_str))
            except ParserError:
                # Year has only 52 weeks
                pass
    return weeks


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
