from contextlib import contextmanager
from typing import Iterator, Optional

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from .gino import Gino, GinoEngine
from .settings.globals import DATABASE_CONFIG, SQL_REQUEST_TIMEOUT

READ_ENGINE: Optional[GinoEngine] = None
SessionLocal: Optional[Session] = None
Base = declarative_base()

app = FastAPI(title="GFW Tile Cache API", redoc_url="/")


db = Gino(
    app,
    host=DATABASE_CONFIG.host,
    port=DATABASE_CONFIG.port,
    user=DATABASE_CONFIG.username,
    password=DATABASE_CONFIG.password,
    database=DATABASE_CONFIG.database,
    pool_min_size=5,
    pool_max_size=10,
    kwargs=dict(server_settings=dict(statement_timeout=f"{SQL_REQUEST_TIMEOUT}")),
)


@contextmanager
def get_synchronous_db() -> Iterator[Session]:

    global SessionLocal

    if SessionLocal is None:
        db_conn = DATABASE_CONFIG.url
        engine = create_engine(db_conn, pool_size=5, max_overflow=0)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    synchronous_db: Optional[Session] = None
    try:
        synchronous_db = SessionLocal()
        yield synchronous_db
    finally:
        if synchronous_db is not None:
            synchronous_db.close()
