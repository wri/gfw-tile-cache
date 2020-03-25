import os
from typing import List, Tuple


import concurrent.futures

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pendulum
from pendulum.parsing.exceptions import ParserError

POOL = None
YEARS = range(2011, 2022)
WEEKS = range(1, 54)
SCHEMA = "nasa_viirs_fire_alerts"
TABLE = "v202003"


def cli() -> None:
    """
    Post processing of VIRRS fire data
    -> update geographic columns
    -> create indicies
    -> cluster partitions
    Tasks are run asynchronously for each partition
    """

    pool = get_pool()
    weeks = _get_weeks()

    create_indicies_only()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(partiontions, weeks)

    pool.closeall()


def get_pool() -> ThreadedConnectionPool:
    """
    The database connection pool
    """
    global POOL
    if POOL is None:
        POOL = psycopg2.pool.ThreadedConnectionPool(
            1,
            10,
            database=os.environ["POSTGRES_NAME"],
            user=os.environ["POSTGRES_USERNAME"],
            password=os.environ["POSTGRES_PASSWORD"],
            port=os.environ["POSTGRES_PORT"],
            host=os.environ["POSTGRES_HOST"],
        )
    return POOL


def create_indicies_only() -> None:
    """
    This creates an invalid index.
    It will be validated automatically, once all partitions are indexed and attached.
    """
    pool = get_pool()
    conn = pool.getconn()

    with conn.cursor() as cursor:
        cursor.execute(
            _get_sql("sql/create_indicies.sql.tmpl", schema=SCHEMA, table=TABLE)
        )


def partiontions(weeks: Tuple[int, str]) -> None:

    year = weeks[0]
    week = weeks[1]

    pool = get_pool()
    conn = pool.getconn()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    cursor.execute(
        _get_sql(
            "sql/update_geometry.sql.tmpl",
            schema=SCHEMA,
            table=TABLE,
            year=year,
            week=week,
        )
    )

    cursor.execute(
        _get_sql(
            "sql/create_partition_indicies.sql.tmpl",
            schema=SCHEMA,
            table=TABLE,
            year=year,
            week=week,
            column="geom",
            index="gist",
        )
    )

    cursor.execute(
        _get_sql(
            "sql/create_partition_indicies.sql.tmpl",
            schema=SCHEMA,
            table=TABLE,
            year=year,
            week=week,
            column="geom_wm",
            index="gist",
        )
    )

    cursor.execute(
        _get_sql(
            "sql/create_partition_indicies.sql.tmpl",
            schema=SCHEMA,
            table=TABLE,
            year=year,
            week=week,
            column="alert__date",
            index="btree",
        )
    )

    cursor.execute(
        _get_sql(
            "sql/cluster_partitions.sql.tmpl",
            schema=SCHEMA,
            table=TABLE,
            year=year,
            week=week,
        )
    )

    cursor.close()

    pool.putconn(conn)


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
    cli()
