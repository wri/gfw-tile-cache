import logging
import os
from typing import Optional

# import asyncpg
# from asyncpg.pool import Pool
from databases import Database

ENV: str = os.environ["ENV"]
# POOL: Optional[Pool] = None
DATABASE: Optional[Database] = None


def get_module_logger(name) -> logging.Logger:

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


async def get_databse() -> Database:
    global DATABASE

    if not isinstance(DATABASE, Database):

        logger.info("Create DB connection pool")

        database = os.environ["POSTGRES_NAME"]
        user = os.environ["POSTGRES_USERNAME"]
        password = os.environ["POSTGRES_PASSWORD"]
        port = os.environ["POSTGRES_PORT"]
        host = os.environ["POSTGRES_HOST"]

        DATABASE = Database(
            f"postgresql://{user}:{password}@{host}:{port}/{database}",  # pragma: allowlist secret
            command_timeout=30,
        )

    return DATABASE


# async def get_pool():
#     global POOL
#
#     if not isinstance(POOL, Pool):
#         logger.info("Create DB connection pool")
#         POOL = await asyncpg.create_pool(
#             database=os.environ["POSTGRES_NAME"],
#             user=os.environ["POSTGRES_USERNAME"],
#             password=os.environ["POSTGRES_PASSWORD"],
#             port=os.environ["POSTGRES_PORT"],
#             host=os.environ["POSTGRES_HOST"],
#         )
#
#     return POOL
