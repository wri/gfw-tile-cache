from typing import Any

from pydantic.main import BaseModel


class Response(BaseModel):
    data: Any = None
    status: str = "success"
