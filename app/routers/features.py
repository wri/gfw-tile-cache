import logging
from typing import Tuple

from asyncpg import Connection
from fastapi import APIRouter, Path, Query, Depends
from fastapi.responses import ORJSONResponse

from app.database import a_get_db
from app.schemas.dynamic_enumerators import get_dataset
from app.schemas.geostore import Geostore
from app.schemas.nasa_viirs_fire_alerts import MaxDate
from app.routers import VERSION_REGEX
from app.services.features import (
    get_feature,
    nasa_viirs_fire_alerts,
    geostore,
    get_features_by_location,
)
from app.utils.dependencies import dataset_version, nasa_viirs_fire_alerts_version
from app.utils.validators import validate_version

router = APIRouter()
LOGGER = logging.Logger(__name__)


@router.get(
    "/{dataset}/{version}/features", response_class=ORJSONResponse, tags=["Features"],
)
async def features(
    *,
    dv: Tuple[str, str] = Depends(dataset_version),
    lat: float = Query(None, title="Latitude", ge=-90, le=90),
    lng: float = Query(None, title="Longitude", ge=-180, le=180),
    z: int = Query(None, title="Zoom level", ge=0, le=22),
    db: Connection = Depends(a_get_db)
):
    """
    Retrieve list of features for given lat/lng coordinate pair.
    Use together with ESRI JS API which does not allow to query vector tile attributes directly to retrieve feature info.
    """
    dataset, version = dv
    return await get_features_by_location(db, dataset, version, lat, lng, z)


@router.get(
    "/{dataset}/{version}/feature/{feature_id}",
    response_class=ORJSONResponse,
    tags=["Features"],
)
async def feature(
    *,
    dv: Tuple[str, str] = Depends(dataset_version),
    feature_id: int = Path(..., title="Feature ID", ge=0),
    db: Connection = Depends(a_get_db)
):
    """
    Retrieve attribute values for a given feature
    """
    dataset, version = dv
    return await get_feature(db, dataset, version, feature_id)


@router.get(
    "/nasa_viirs_fire_alerts/{version}/max_alert__date",
    response_class=ORJSONResponse,
    response_model=MaxDate,
    response_description="Max alert date in selected dataset",
    tags=["Max date"],
)
async def max_date(
    *,
    version: str = Depends(nasa_viirs_fire_alerts_version),
    db: Connection = Depends(a_get_db)
):
    """
    Retrieve max alert date for NASA VIIRS fire alerts for a given version
    """
    validate_version("nasa_viirs_fire_alerts", version)
    return await nasa_viirs_fire_alerts.get_max_date(db, version)


@router.get(
    "/{dataset}/{version}/geostore/{geostore_id}",
    response_class=ORJSONResponse,
    response_model=Geostore,
    tags=["Geostore"],
)
async def get_geostore(
    *,
    dv: Tuple[str, str] = Depends(dataset_version),
    geostore_id: str = Path(..., title="geostore_id"),
    db: Connection = Depends(a_get_db)
):
    """
    Retrieve GeoJSON representation for a given geostore ID.
    Obtain geostore ID from feature attributes.
    """
    dataset, version = dv
    return await geostore.get_geostore(db, dataset, version, geostore_id)
