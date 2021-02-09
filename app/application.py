from contextlib import contextmanager
from typing import Iterator, Optional

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from .gino import Gino, GinoEngine
from .settings.globals import GLOBALS

READ_ENGINE: Optional[GinoEngine] = None
SessionLocal: Optional[Session] = None
Base = declarative_base()

app = FastAPI(title="GFW Tile Cache API", redoc_url="/")

if not GLOBALS.database_config:
    raise RuntimeError("No database url set.")

db = Gino(
    app,
    host=GLOBALS.database_config.host,
    port=GLOBALS.database_config.port,
    user=GLOBALS.database_config.username,
    password=GLOBALS.database_config.password,
    database=GLOBALS.database_config.database,
    pool_min_size=5,
    pool_max_size=10,
    kwargs=dict(
        server_settings=dict(statement_timeout=f"{GLOBALS.sql_request_timeout}")
    ),
)


@contextmanager
def get_synchronous_db() -> Iterator[Session]:
    global SessionLocal

    if not GLOBALS.database_config:
        raise RuntimeError("No database url set.")

    if SessionLocal is None:
        db_conn = GLOBALS.database_config.url
        engine = create_engine(db_conn, pool_size=5, max_overflow=0)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    synchronous_db: Optional[Session] = None
    try:
        synchronous_db = SessionLocal()
        yield synchronous_db
    finally:
        if synchronous_db is not None:
            synchronous_db.close()
