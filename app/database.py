import json
import urllib.parse
from contextlib import contextmanager
from typing import Iterator, Optional, AsyncIterator

import asyncpg
import boto3
from asyncpg.connection import Connection
from asyncpg.pool import Pool
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

POOL: Optional[Pool] = None
SessionLocal: Optional[Session] = None
Base = declarative_base()


async def a_get_pool() -> Pool:
    """
    Asynchronous connection pool. Use this when ever possible
    """
    global POOL
    if POOL is None:
        secrets = get_secrets()
        POOL = await asyncpg.create_pool(
            database=secrets["dbname"],
            user=secrets["username"],
            password=secrets["password"],
            port=secrets["port"],
            host=secrets["host"],
        )
    return POOL


# @asynccontextmanager
async def a_get_db() -> AsyncIterator[Connection]:
    """
    Asynchronous connection pool. Use this when ever possible
    """
    global POOL
    conn: Optional[Connection] = None

    try:
        if POOL is None:
            POOL = await a_get_pool()
        conn = await POOL.acquire()
        yield conn
    finally:
        if POOL is not None:
            await POOL.release(conn)


@contextmanager
def get_db() -> Iterator[Session]:

    global SessionLocal

    if SessionLocal is None:
        secrets = get_secrets()
        db_conn = f"postgresql://{secrets['username']}:{urllib.parse.quote_plus(secrets['username'])}@{secrets['host']}:{secrets['port']}/{secrets['dbname']}"  # pragma: allowlist secret
        engine = create_engine(db_conn, pool_size=5, max_overflow=0)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db: Optional[Session] = None
    try:
        db = SessionLocal()
        yield db
    finally:
        if db is not None:
            db.close()


def get_secrets():
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId="core-postgresql-writer-secret")
    return json.loads(response["SecretString"])
