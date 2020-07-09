from datetime import date

from pydantic import BaseModel, Field

from .responses import Response


class MaxDate(BaseModel):
    max_date: date = Field(None, example="2020-01-01")


class MaxDateResponse(Response):
    data: MaxDate
