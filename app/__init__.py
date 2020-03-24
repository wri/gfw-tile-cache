import logging
import os
from typing import Optional

from databases import Database

ENV: str = os.environ["ENV"]
DATABASE: Optional[Database] = None


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


async def get_database() -> Database:
    """
    Database connection pool
    """

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
