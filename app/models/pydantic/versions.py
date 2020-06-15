from typing import List

from pydantic.main import BaseModel


class LatestVersion(BaseModel):
    dataset: str
    version: str


class LatestVersionResponse(BaseModel):
    data: List[LatestVersion]
