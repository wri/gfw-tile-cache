import logging
from enum import Enum

from fastapi import APIRouter, Path
from fastapi.responses import ORJSONResponse

from app.routers import VERSION_REGEX
from app.services.features import get_feature, nasa_viirs_fire_alerts, geostore


router = APIRouter()
LOGGER = logging.Logger(__name__)


class Dataset(str, Enum):
    wdpa_protected_areas = "wdpa_protected_areas"


@router.get(
    "/{dataset}/{version}/features", response_class=ORJSONResponse, tags=["features"],
)
async def features(
    *,
    dataset: Dataset,
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
    lat: float = Path(..., title="Latitude", ge=-90, le=90),
    lng: float = Path(..., title="Longitude", ge=-180, le=180),
    z: int = Path(..., title="Zoom level", ge=0, le=22),
):
    pass


@router.get(
    "/{dataset}/{version}/feature/{feature_id}",
    response_class=ORJSONResponse,
    tags=["features"],
)
async def feature(
    *,
    dataset: Dataset,
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
    feature_id: int = Path(..., title="Feature ID", ge=0),
):
    return get_feature(dataset, version, feature_id)


@router.get(
    "/nasa_viirs_fire_alerts/{version}/max_alert__date",
    response_class=ORJSONResponse,
    tags=["features"],
)
async def max_date(
    *, version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
):
    return nasa_viirs_fire_alerts.get_max_date(version)


@router.get(
    "/{dataset}/{version}/geostore/{geostore_id}",
    response_class=ORJSONResponse,
    tags=["features"],
)
async def get_geostore(
    *,
    dataset: Dataset,
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
    geostore_id: str = Path(..., title="geostore_id"),
):
    return geostore.get_geostore(dataset, version, geostore_id)
