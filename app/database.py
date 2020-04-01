import os
import urllib.parse
from contextlib import contextmanager
from typing import Iterator, Optional, AsyncIterator

import asyncpg
from asyncpg.connection import Connection
from asyncpg.pool import Pool
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session


DATABASE = os.environ["POSTGRES_NAME"]
USER = os.environ["POSTGRES_USERNAME"]
PASSWORD = os.environ["POSTGRES_PASSWORD"]
PORT = os.environ["POSTGRES_PORT"]
HOST = os.environ["POSTGRES_HOST"]

SQLALCHEMY_DATABASE_URL = f"postgresql://{USER}:{urllib.parse.quote_plus(PASSWORD)}@{HOST}:{PORT}/{DATABASE}"  # pragma: allowlist secret
ENGINE = create_engine(SQLALCHEMY_DATABASE_URL, pool_size=5, max_overflow=0)

POOL: Optional[Pool] = None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)
Base = declarative_base()


async def a_get_pool() -> Pool:
    """
    Asynchronous connection pool. Use this when ever possible
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


async def a_get_db() -> AsyncIterator[Connection]:
    """
    Asynchronous connection pool. Use this when ever possible
    """
    try:
        global POOL
        if POOL is None:
            POOL = await a_get_pool()
        conn = await POOL.acquire()
        yield conn
    finally:
        if POOL is not None:
            await POOL.release(conn)


@contextmanager
def get_db() -> Iterator[Session]:
    db: Optional[Session] = None
    try:
        db = SessionLocal()
        yield db
    finally:
        if db is not None:
            db.close()
