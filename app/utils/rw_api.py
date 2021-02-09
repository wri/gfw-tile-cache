from uuid import UUID

from async_lru import alru_cache
from httpx import AsyncClient
from httpx import Response as HTTPXResponse

from ..errors import BadResponseError, InvalidResponseError
from ..models.types import Geometry
from ..settings.globals import GLOBALS


@alru_cache(maxsize=128)
async def get_geostore_geometry(geostore_id: UUID) -> Geometry:
    """Get RW Geostore geometry."""

    prefix = _env_prefix()
    geostore_id_str: str = str(geostore_id).replace("-", "")

    url = f"https://{prefix}-api.globalforestwatch.org/v2/geostore/{geostore_id_str}"
    async with AsyncClient() as client:
        response: HTTPXResponse = await client.get(url)

    if response.status_code != 200:
        raise InvalidResponseError("Call to Geostore failed")
    try:
        geometry = response.json()["data"]["attributes"]["geojson"]["features"][0][
            "geometry"
        ]
    except KeyError:
        raise BadResponseError("Cannot fetch geostore geometry")

    return geometry


def _env_prefix() -> str:
    """Set RW environment."""
    if GLOBALS.env == "dev":
        prefix = "staging"
    else:
        prefix = GLOBALS.env

    return prefix
