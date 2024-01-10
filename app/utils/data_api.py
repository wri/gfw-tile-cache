from typing import List, Optional

import requests
from async_lru import alru_cache
from fastapi import HTTPException
from fastapi.logger import logger
from httpx import AsyncClient, ReadTimeout
from httpx import Response as HTTPXResponse

from ..models.enumerators.nasa_viirs_fire_alerts.attributes import (
    Attributes,
    get_attributes_enum,
)
from ..settings.globals import GLOBALS


@alru_cache(maxsize=128)
async def validate_apikey(
    api_key: str, origin: Optional[str], referrer: Optional[str]
) -> bool:
    """Get RW Geostore geometry."""

    prefix = _env_prefix()
    headers = {"Authorization": f"Bearer {GLOBALS.token}"}
    params = {"origin": origin, "referrer": referrer}
    url = (
        f"https://{prefix}data-api.globalforestwatch.org/auth/apikey/{api_key}/validate"
    )
    logger.info("Calling DATA API to validate API KEY")
    try:
        async with AsyncClient() as client:
            response: HTTPXResponse = await client.get(
                url, headers=headers, params=params, timeout=10.0
            )

    except ReadTimeout:
        raise HTTPException(
            status_code=500,
            detail="Call to authorization server timed-out. Please try again.",
        )

    if response.status_code not in [200, 404]:
        logger.error(
            f"Data API return unexpected status code `{response.status_code}` when validating API key. "
            f"Response message: `{response.text}`"
        )
        raise HTTPException(
            status_code=500, detail="Call to authorization server failed."
        )

    return response.status_code == 200 and response.json()["data"]["is_valid"]


def get_version_fields(dataset: str, version: str) -> List[Attributes]:
    prefix = _env_prefix()
    url = f"https://{prefix}data-api.globalforestwatch.org/dataset/{dataset}/{version}/fields"
    logger.warning(f"Calling DATA API to Get Fields: {url}")

    try:
        response = requests.get(url, timeout=10.0)

    except ReadTimeout:
        logger.error("Call to DATA API timed out")
        raise HTTPException(
            status_code=500,
            detail="Call to DATA API timed out. Please try again.",
        )

    if response.status_code != 200:
        logger.error(
            f"DATA API return unexpected status code `{response.status_code}`"
            f"Response message: `{response.text}`"
        )
        raise HTTPException(status_code=500, detail="Call to DATA API failed.")

    # Convert the attributes into an enum
    attributes: List[str] = []
    for item in response.json()["data"]:
        if item["is_feature_info"]:
            attributes.append(item["name"])

    return get_attributes_enum(attributes)


def _env_prefix() -> str:
    """Set GFW DATA API environment."""
    # We will develop against the staging API in dev,
    # since we only have feature branch deployments in this environment
    if GLOBALS.env == "dev" or GLOBALS.env == "staging":
        prefix = "staging-"
    else:
        prefix = ""

    return prefix
