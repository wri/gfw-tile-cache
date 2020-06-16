"""
A set of internal (undocumented) endpoints.
Endpoints listed here are for internal use only.
"""
from typing import List

from fastapi import APIRouter
from fastapi.responses import ORJSONResponse

from ..crud.versions import get_latest_versions
from ..models.pydantic.versions import LatestVersionResponse

router = APIRouter()


@router.get(
    "/_latest",
    response_class=ORJSONResponse,
    response_model=LatestVersionResponse,
    include_in_schema=False,
)
async def _latest() -> LatestVersionResponse:
    """
    Queries API to get list of latest dataset version
    """

    return LatestVersionResponse(data=get_latest_versions())
