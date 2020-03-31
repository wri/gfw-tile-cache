import logging
import os
from typing import Optional

import asyncpg
from asyncpg.pool import Pool
from psycopg2.pool import SimpleConnectionPool

ENV: str = os.environ["ENV"]
A_POOL: Optional[Pool] = None
POOL: Optional[SimpleConnectionPool] = None


def get_module_logger(name) -> logging.Logger:
    """
    The logger
    """

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(sh)
    if ENV != "production":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    return logger


logger = get_module_logger(__name__)


async def a_get_pool() -> Pool:
    """
    Asynchronous connection pool. Use this when ever possible
    """
    global A_POOL
    if A_POOL is None:
        A_POOL = await asyncpg.create_pool(
            database=os.environ["POSTGRES_NAME"],
            user=os.environ["POSTGRES_USERNAME"],
            password=os.environ["POSTGRES_PASSWORD"],
            port=os.environ["POSTGRES_PORT"],
            host=os.environ["POSTGRES_HOST"],
        )
    return A_POOL


def get_pool() -> SimpleConnectionPool:
    """
    Synchronous connection pool. Required for some edge cases
    """
    global POOL
    if POOL is None:
        POOL = SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            database=os.environ["POSTGRES_NAME"],
            user=os.environ["POSTGRES_USERNAME"],
            password=os.environ["POSTGRES_PASSWORD"],
            port=os.environ["POSTGRES_PORT"],
            host=os.environ["POSTGRES_HOST"],
        )
    return POOL
