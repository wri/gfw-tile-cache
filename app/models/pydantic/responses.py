from typing import Any

from pydantic.main import BaseModel


class Response(BaseModel):
    data: Any
    status: str = "success"
