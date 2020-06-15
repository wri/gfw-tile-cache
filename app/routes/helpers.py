"""
A set of internal (undocumented) endpoints.
Endpoints listed here are for internal use only.
"""
from typing import List

from fastapi import APIRouter
from fastapi.responses import ORJSONResponse

from ..crud.versions import get_latest_versions
from ..models.pydantic.versions import LatestVersion, LatestVersionResponse

router = APIRouter()


@router.get(
    "/_latest",
    response_class=ORJSONResponse,
    response_model=List[LatestVersion],
    include_in_schema=False,
)
async def _latest() -> List[LatestVersion]:
    """
    Queries API to get list of latest dataset version
    """

    return get_latest_versions()
