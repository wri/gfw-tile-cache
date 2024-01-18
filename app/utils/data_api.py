from typing import List, Optional

from async_lru import alru_cache
from fastapi import HTTPException
from fastapi.logger import logger
from httpx import AsyncClient, ReadTimeout
from httpx import Response as HTTPXResponse

from ..settings.globals import GLOBALS


def _env_prefix() -> str:
    """Set GFW DATA API environment."""
    # We will develop against the staging API in dev,
    # since we only have feature branch deployments in this environment
    if GLOBALS.env == "dev" or GLOBALS.env == "staging":
        prefix = "staging-"
    else:
        prefix = ""

    return prefix


async def make_api_request(
    endpoint: str,
    headers: dict = None,
    params: dict = None,
    timeout: float = 10.0,
    accepted_codes: List[int] = [200],
) -> HTTPXResponse:
    prefix = _env_prefix()
    url = f"https://{prefix}data-api.globalforestwatch.org/{endpoint}"

    try:
        async with AsyncClient() as client:
            response: HTTPXResponse = await client.get(
                url, headers=headers, params=params, timeout=timeout
            )

    except ReadTimeout:
        logger.error(f"Call to {url} timed out")
        raise HTTPException(
            status_code=500,
            detail="Call to DATA API timed out. Please try again.",
        )

    if response.status_code not in accepted_codes:
        logger.error(
            f"DATA API returned unexpected status code `{response.status_code}` "
            f"Response message: `{response.text}` for URL: {url}"
        )
        raise HTTPException(status_code=500, detail="Call to DATA API failed.")

    return response


@alru_cache(maxsize=128)
async def validate_apikey(
    api_key: str, origin: Optional[str], referrer: Optional[str]
) -> bool:
    logger.info("Calling DATA API to validate API KEY")
    headers = {"Authorization": f"Bearer {GLOBALS.token}"}
    params = {"origin": origin, "referrer": referrer}
    endpoint = f"auth/apikey/{api_key}/validate"

    response = await make_api_request(
        endpoint, headers=headers, params=params, accepted_codes=[200, 404]
    )

    return response.status_code == 200 and response.json()["data"]["is_valid"]


@alru_cache(maxsize=128)
async def get_version_fields(dataset: str, version: str) -> List[str]:
    logger.info(f"Calling DATA API to Get Fields for {dataset}, version {version}")
    endpoint = f"dataset/{dataset}/{version}/fields"

    response = await make_api_request(endpoint, accepted_codes=[200])

    attributes: List[str] = []
    for item in response.json()["data"]:
        if item["is_feature_info"]:
            attributes.append(item["name"])

    return attributes
