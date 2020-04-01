import logging
from typing import Type

from asyncpg import Connection
from fastapi import APIRouter, Path, Query, Depends
from fastapi.responses import ORJSONResponse

from app.database import a_get_db
from app.models.dataset import get_dataset
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
    dataset: get_dataset(),  # type: ignore
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
    lat: float = Query(None, title="Latitude", ge=-90, le=90),
    lng: float = Query(None, title="Longitude", ge=-180, le=180),
    z: int = Query(None, title="Zoom level", ge=0, le=22),
    db: Connection = Depends(a_get_db)
):
    return await get_features_by_location(db, dataset, version, lat, lng, z)


@router.get(
    "/{dataset}/{version}/feature/{feature_id}",
    response_class=ORJSONResponse,
    tags=["Features"],
)
async def feature(
    *,
    dataset: get_dataset(),  # type: ignore
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
    feature_id: int = Path(..., title="Feature ID", ge=0),
    db: Connection = Depends(a_get_db)
):
    return await get_feature(db, dataset, version, feature_id)


@router.get(
    "/nasa_viirs_fire_alerts/{version}/max_alert__date",
    response_class=ORJSONResponse,
    response_model=MaxDate,
    tags=["Max date"],
)
async def max_date(
    *,
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
    db: Connection = Depends(a_get_db)
):
    return await nasa_viirs_fire_alerts.get_max_date(db, version)


@router.get(
    "/{dataset}/{version}/geostore/{geostore_id}",
    response_class=ORJSONResponse,
    response_model=Geostore,
    tags=["Geostore"],
)
async def get_geostore(
    *,
    dataset: get_dataset(),  # type: ignore
    version: str = Path(..., title="Dataset version", regex=VERSION_REGEX),
    geostore_id: str = Path(..., title="geostore_id"),
    db: Connection = Depends(a_get_db)
):
    return await geostore.get_geostore(db, dataset, version, geostore_id)
