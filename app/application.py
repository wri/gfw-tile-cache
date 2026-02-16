from contextlib import contextmanager
from typing import Iterator, Optional

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from .gino import Gino, GinoEngine
from .settings.globals import GLOBALS

# Explicitly register the gino asyncpg dialect with SQLAlchemy
# This ensures it's available before any database connections are attempted
try:
    from sqlalchemy.dialects import registry
    import gino.dialects.asyncpg
    registry.register("asyncpg", "gino.dialects.asyncpg", "AsyncpgDialect")
    registry.register("postgresql.asyncpg", "gino.dialects.asyncpg", "AsyncpgDialect")
except Exception:
    # If registration fails, the normal import should still work
    pass

READ_ENGINE: Optional[GinoEngine] = None
SessionLocal: Optional[Session] = None
Base = declarative_base()

app = FastAPI(title="GFW Tile Cache API", redoc_url="/")

if not GLOBALS.database_config:
    raise RuntimeError("No database url set.")

db = Gino(
    app,
    driver="asyncpg",
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
        # Create a synchronous database URL using psycopg2 instead of asyncpg
        # asyncpg only works with async engines, not synchronous ones
        from sqlalchemy.engine.url import URL

        db_config = GLOBALS.database_config
        sync_url = URL(
            drivername="postgresql+psycopg2",
            username=db_config.username,
            password=str(db_config.password) if db_config.password else None,
            host=db_config.host,
            port=db_config.port,
            database=db_config.database,
        )
        engine = create_engine(sync_url, pool_size=5, max_overflow=0)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    synchronous_db: Optional[Session] = None
    try:
        synchronous_db = SessionLocal()
        yield synchronous_db
    finally:
        if synchronous_db is not None:
            synchronous_db.close()
