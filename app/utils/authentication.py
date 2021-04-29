from typing import Optional, Tuple

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from app.settings.globals import GLOBALS
from app.utils.data_api import validate_apikey


class APIKeyOriginHeader(APIKeyHeader):
    async def __call__(self, request: Request) -> Tuple[Optional[str], Optional[str]]:
        api_key: str = request.headers.get(self.model.name)
        origin: Optional[str] = request.headers.get("origin")
        return _api_key_origin_auto_error(api_key, origin, self.auto_error)


async def is_valid_apikey(
    api_key_header: Tuple[Optional[str], Optional[str]] = Security(
        APIKeyOriginHeader(name=GLOBALS.api_key_name, auto_error=False)
    ),
) -> bool:
    api_key, origin = api_key_header
    if api_key and origin and await validate_apikey(api_key, origin):
        return True
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="No valid API Key found."
    )


def _api_key_origin_auto_error(
    api_key: Optional[str], origin: Optional[str], auto_error: bool
) -> Tuple[Optional[str], Optional[str]]:
    if not api_key:
        if auto_error:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
            )
        else:
            return None, origin
    return api_key, origin
