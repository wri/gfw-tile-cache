from typing import Any, Optional, Union

from pydantic import (
    ConfigDict,
    Field,
    field_validator,
)
from sqlalchemy.engine.url import URL
from starlette.datastructures import Secret

from pydantic_settings import BaseSettings


class DatabaseURL(BaseSettings):
    drivername: str = Field(..., alias="driver", description="The database driver.")
    host: str = Field("localhost", description="Server host.")
    port: Optional[Union[str, int]] = Field(None, description="Server access port.")
    username: Optional[str] = Field(None, alias="user", description="Username")
    password: Optional[Union[Secret, str]] = Field(None, description="Password")
    database: str = Field(..., description="Database name.")
    url: Optional[URL] = None
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    @field_validator("url")
    def build_url(cls, v: Any, values):
        if isinstance(v, URL):
            return v
        args = {k: str(v) for k, v in values.data.items() if v is not None}
        return URL(**args)
