import logging
import os
from typing import Optional

import asyncpg
from asyncpg.pool import Pool

ENV: str = os.environ["ENV"]
POOL: Optional[Pool] = None


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


async def get_pool() -> Pool:
    global POOL
    if POOL is None:
        POOL = await asyncpg.create_pool(
            database=os.environ["POSTGRES_NAME"],
            user=os.environ["POSTGRES_USERNAME"],
            password=os.environ["POSTGRES_PASSWORD"],
            port=os.environ["POSTGRES_PORT"],
            host=os.environ["POSTGRES_HOST"],
            command_timeout=60,
        )
    return POOL
