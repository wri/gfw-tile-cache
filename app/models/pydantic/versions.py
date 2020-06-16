from typing import List

from pydantic.main import BaseModel

from app.models.pydantic.responses import Response


class LatestVersion(BaseModel):
    dataset: str
    version: str


class LatestVersionResponse(Response):
    data: List[LatestVersion]
