import logging
import os
from typing import Optional

import asyncpg
from asyncpg.pool import Pool


ENV: str = os.environ["ENV"]
POOL: Optional[Pool] = None
LOGGER: Optional[logging.Logger] = None


def get_module_logger(name) -> logging.Logger:
    global LOGGER

    if not isinstance(LOGGER, logging.Logger):
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        sh = logging.StreamHandler()
        sh.setFormatter(formatter)

        LOGGER = logging.getLogger(name)
        LOGGER.addHandler(sh)
        if ENV != "production":
            LOGGER.setLevel(logging.DEBUG)
        else:
            LOGGER.setLevel(logging.INFO)

    return LOGGER


async def get_pool():
    global POOL

    if not isinstance(POOL, Pool):
        LOGGER.info("Create DB connection pool")
        POOL = await asyncpg.create_pool(
            database=os.environ["POSTGRES_NAME"],
            user=os.environ["POSTGRES_USERNAME"],
            password=os.environ["POSTGRES_PASSWORD"],
            port=os.environ["POSTGRES_PORT"],
            host=os.environ["POSTGRES_HOST"],
        )

    return POOL
