import json
from pathlib import Path
from typing import Optional

from starlette.config import Config
from starlette.datastructures import Secret

from ..models.pydantic.database import DatabaseURL

# Read .env file, if exists
p: Path = Path(__file__).parents[2] / ".env"
config: Config = Config(p if p.exists() else None)

empty_secret = {
    "dbInstanceIdentifier": None,
    "dbname": None,
    "engine": None,
    "host": "localhost",
    "password": None,  # pragma: allowlist secret
    "port": 5432,
    "username": None,
}

# As of writing, Fargate doesn't support to fetch secrets by key.
# Only entire secret object can be obtained.
DB_READER_SECRET = json.loads(
    config("DB_READER_SECRET", cast=str, default=json.dumps(empty_secret))
)

ENV = config("ENV", cast=str, default="dev")
BUCKET = config("BUCKET", cast=str, default=None)

READER_USERNAME: Optional[str] = config(
    "DB_USER_RO", cast=str, default=DB_READER_SECRET["username"]
)
READER_PASSWORD: Optional[Secret] = config(
    "DB_PASSWORD_RO", cast=Secret, default=DB_READER_SECRET["password"]
)
READER_HOST: str = config("DB_HOST_RO", cast=str, default=DB_READER_SECRET["host"])
READER_PORT: int = config("DB_PORT_RO", cast=int, default=DB_READER_SECRET["port"])
READER_DBNAME = config("DATABASE_RO", cast=str, default=DB_READER_SECRET["dbname"])

# We are using this to create a psycopg2 database connection
DATABASE_CONFIG: DatabaseURL = DatabaseURL(
    drivername="postgresql",
    username=READER_USERNAME,
    password=READER_PASSWORD,
    host=READER_HOST,
    port=READER_PORT,
    database=READER_DBNAME,
)


AWS_REGION = config("AWS_REGION", cast=str, default="us-east-1")
AWS_ENDPOINT_URI = config("AWS_ENDPOINT_URI", cast=str, default="")
LAMBDA_HOST = (
    AWS_ENDPOINT_URI
    if AWS_ENDPOINT_URI
    else f"https://lambda.{AWS_REGION}.amazonaws.com"
)

TILE_CACHE_URL: Optional[str] = config("TILE_CACHE_URL", cast=str, default=None)
SQL_REQUEST_TIMEOUT: int = 58000
RASTER_TILER_LAMBDA_NAME = config("RASTER_TILER_LAMBDA_NAME", cast=str)
