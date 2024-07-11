import json
from json import JSONDecodeError
from typing import Optional

from fastapi.logger import logger
from pydantic import Field, field_validator
from pydantic_settings import SettingsConfigDict, BaseSettings
from starlette.datastructures import Secret

from ..models.pydantic.database import DatabaseURL


class Globals(BaseSettings):
    env: str = Field("dev", description="Environment name.")
    db_reader_secret: Optional[str] = Field(
        None,
        description="AWS Secret String. As of writing, Fargate doesn't support to fetch secrets by key. Only entire secret object can be obtained",
    )
    bucket: Optional[str] = Field("gfw-tiles-dev", description="Tile Cache bucket name")
    reader_username: Optional[str] = Field(
        None,
        validation_alias="DB_USER_RO",
        description="DB user name. Will be ignored if DB_READER_SECRET is set.",
    )
    reader_password: Optional[Secret] = Field(
        None,
        validation_alias="DB_PASSWORD_RO",
        description="DB password. Will be ignored if DB_READER_SECRET is set.",
    )
    reader_host: Optional[str] = Field(
        None,
        validation_alias="DB_HOST_RO",
        description="DB host name. Will be ignored if DB_READER_SECRET is set.",
    )
    reader_port: Optional[int] = Field(
        None,
        validation_alias="DB_PORT_RO",
        description="DB port number. Will be ignored if DB_READER_SECRET is set.",
    )
    reader_dbname: Optional[str] = Field(
        None,
        validation_alias="DATABASE_RO",
        description="DB database name. Will be ignored if DB_READER_SECRET is set.",
    )
    database_config: Optional[DatabaseURL] = Field(
        None, description="Database URL. Will be set by validator"
    )
    aws_region: str = Field("us-east-1", description="AWS region")
    aws_endpoint_uri: Optional[str] = Field(
        None, description="AWS service endpoint URL"
    )
    lambda_host: Optional[str] = Field(None, description="AWS Lamdba host URL")
    planet_api_key: Optional[str] = Field(None, description="Planet Api key")
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
    token: Optional[str] = Field(
        None,
        validation_alias="TOKEN_SECRET",
        description="GFW Data API token for service account.",
    )
    api_key_name: str = Field("x-api-key", description="Header key name for API key.")

    @field_validator("token", mode="before")
    def get_token(cls, v: Optional[str]) -> Optional[str]:
        if v:
            try:
                return json.loads(v)["token"]
            except (JSONDecodeError, KeyError):
                logger.error(
                    "Could not extract token from token secret. Set token to None."
                )
        return None

    @field_validator("reader_password", mode="before")
    def hide_password(cls, v: Optional[str]) -> Optional[Secret]:
        if v:
            return Secret(v)
        else:
            return v

    @field_validator("database_config", mode="before")
    def set_database_config(cls, v, values, **kwarg) -> DatabaseURL:
        input = values.data
        db_reader_secret = values.data.get("db_reader_secret")
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
                username=input.get("reader_username"),
                password=input.get("reader_password"),
                host=input.get("reader_host"),
                port=input.get("reader_port"),
                database=input.get("reader_dbname"),
            )
        return v

    @field_validator("lambda_host", mode="before")
    def set_lambda_host(cls, v, values, **kwargs) -> str:
        input = values.data
        aws_endpoint_uri = input.get("aws_endpoint_uri")
        if aws_endpoint_uri:
            v = aws_endpoint_uri
        else:
            aws_region = input.get("aws_region")
            v = f"https://lambda.{aws_region}.amazonaws.com"
        return v

    model_config = SettingsConfigDict(case_sensitive=False, validate_assignment=True)


GLOBALS = Globals()
