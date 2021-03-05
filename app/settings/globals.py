import json
from typing import Optional

from pydantic import BaseSettings, Field, validator
from starlette.datastructures import Secret

from ..models.pydantic.database import DatabaseURL


class Globals(BaseSettings):
    env: str = Field("dev", description="Environment name.")
    db_reader_secret: Optional[str] = Field(
        None,
        description="AWS Secret String. As of writing, Fargate doesn't support to fetch secrets by key. Only entire secret object can be obtained",
    )
    bucket: Optional[str] = Field(None, description="Tile Cache bucket name")
    reader_username: Optional[str] = Field(
        None,
        env="DB_USER_RO",
        description="DB user name. Will be ignored if DB_READER_SECRET is set.",
    )
    reader_password: Optional[Secret] = Field(
        None,
        env="DB_PASSWORD_RO",
        description="DB password. Will be ignored if DB_READER_SECRET is set.",
    )
    reader_host: Optional[str] = Field(
        None,
        env="DB_HOST_RO",
        description="DB host name. Will be ignored if DB_READER_SECRET is set.",
    )
    reader_port: Optional[int] = Field(
        None,
        env="DB_PORT_RO",
        description="DB port number. Will be ignored if DB_READER_SECRET is set.",
    )
    reader_dbname: Optional[str] = Field(
        None,
        env="DATABASE_RO",
        description="DB database name. Will be ignored if DB_READER_SECRET is set.",
    )
    database_config: Optional[DatabaseURL] = Field(
        None, description="Database URL. Will be set by validatro"
    )
    aws_region: str = Field("us-east-1", description="AWS region")
    aws_endpoint_uri: str = Field(None, description="AWS service endpoint URL")
    lambda_host: Optional[str] = Field(None, description="AWS Lamdba host URL")
    tile_cache_url: Optional[str] = Field(None, description="Tile Cache URL")
    sql_request_timeout: int = Field(
        58000, description="SQL timeout time (server side)"
    )
    raster_tiler_lambda_name: Optional[str] = Field(
        None, description="Name of Raster Tiler Lambda function"
    )
    httpx_timeout: int = Field(
        30, description="Timeout for HTTPX requests used for async lambda calls."
    )

    @validator("reader_password", pre=True)
    def hide_password(cls, v: Optional[str]) -> Optional[Secret]:
        if v:
            return Secret(v)
        else:
            return v

    @validator("database_config", pre=True)
    def set_database_config(cls, v, values, **kwargs) -> DatabaseURL:
        db_reader_secret = values.get("db_reader_secret")
        if db_reader_secret:
            secret = json.loads(db_reader_secret)
            v = DatabaseURL(
                drivername="postgresql",
                username=secret["username"],
                password=secret["password"],
                host=secret["host"],
                port=secret["port"],
                database=secret["dbname"],
            )
        else:
            v = DatabaseURL(
                drivername="postgresql",
                username=values.get("reader_username"),
                password=values.get("reader_password"),
                host=values.get("reader_host"),
                port=values.get("reader_port"),
                database=values.get("reader_dbname"),
            )
        return v

    @validator("lambda_host", pre=True)
    def set_lambda_host(cls, v, values, **kwargs) -> str:
        aws_endpoint_uri = values.get("aws_endpoint_uri")
        if aws_endpoint_uri:
            v = aws_endpoint_uri
        else:
            aws_region = values.get("aws_region")
            v = f"https://lambda.{aws_region}.amazonaws.com"
        return v

    class Config:
        case_sensitive = False
        validate_assignment = True


GLOBALS = Globals()
