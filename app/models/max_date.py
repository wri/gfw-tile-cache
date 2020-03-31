from pydantic import BaseModel, Field


class MaxDate(BaseModel):
    max_date: str = Field(None, example="2020-01-01")
