"""
A set of internal (undocumented) endpoints.
Endpoints listed here are for internal use only.
"""

from fastapi import APIRouter, Response
from fastapi.responses import ORJSONResponse

from ..crud.sync_db.versions import get_latest_versions
from ..models.pydantic.versions import LatestVersionResponse

router = APIRouter()


@router.get(
    "/_latest",
    response_class=ORJSONResponse,
    response_model=LatestVersionResponse,
    include_in_schema=False,
)
async def _latest(response: Response) -> LatestVersionResponse:
    """
    Queries API to get list of latest dataset version
    """
    response.headers["Cache-Control"] = "max-age=300"  # 5min
    return LatestVersionResponse(data=get_latest_versions())
