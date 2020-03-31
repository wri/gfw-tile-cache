import logging
from enum import Enum

from fastapi import APIRouter, Path, Query
from fastapi.responses import ORJSONResponse

from app.models.dataset import Dataset
from app.models.geostore import Geostore
from app.models.max_date import MaxDate
from app.routers import VERSION_REGEX
from app.services.features import (
    get_feature,
    nasa_viirs_fire_alerts,
    geostore,
    get_features_by_location,
)

router = APIRouter()
LOGGER = logging.Logger(__name__)


@router.get(
    "/{dataset}/{version}/features", response_class=ORJSONResponse, tags=["Features"],
)
async def features(
    *,
    dataset: Dataset,
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
    lat: float = Query(None, title="Latitude", ge=-90, le=90),
    lng: float = Query(None, title="Longitude", ge=-180, le=180),
    z: int = Query(None, title="Zoom level", ge=0, le=22),
):
    return await get_features_by_location(dataset, version, lat, lng, z)


@router.get(
    "/{dataset}/{version}/feature/{feature_id}",
    response_class=ORJSONResponse,
    tags=["Features"],
)
async def feature(
    *,
    dataset: Dataset,
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
    feature_id: int = Path(..., title="Feature ID", ge=0),
):
    return await get_feature(dataset, version, feature_id)


@router.get(
    "/nasa_viirs_fire_alerts/{version}/max_alert__date",
    response_class=ORJSONResponse,
    response_model=MaxDate,
    tags=["Max date"],
)
async def max_date(
    *, version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
):
    return await nasa_viirs_fire_alerts.get_max_date(version)


@router.get(
    "/{dataset}/{version}/geostore/{geostore_id}",
    response_class=ORJSONResponse,
    response_model=Geostore,
    tags=["Geostore"],
)
async def get_geostore(
    *,
    dataset: Dataset,
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
    geostore_id: str = Path(..., title="geostore_id"),
):
    return await geostore.get_geostore(dataset, version, geostore_id)
