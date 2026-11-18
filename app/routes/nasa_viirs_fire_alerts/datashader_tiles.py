"""NASA VIIRS fire alerts as raster tiles rendered with datashader from a
Parquet file of alert points (see app/utils/viirs_points.py)."""

import threading
from datetime import date, timedelta
from typing import List, Optional, Tuple

import pendulum
from fastapi import APIRouter, HTTPException, Path, Query, Response
from fastapi.logger import logger
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel

from ...models.pydantic.nasa_viirs_fire_alerts import MaxDate, MaxDateResponse
from ...settings.globals import GLOBALS
from ...utils.viirs_points import Points, PointsStore, nearby_alerts, render_tile
from .. import DATE_REGEX, validate_dates

router = APIRouter()

PREFIX = "/nasa_viirs_fire_alerts/latest/datashader"
CACHE_CONTROL = "max-age=3600"
DEFAULT_DAYS = 7
TILE_Y_REGEX = r"^\d+(@2x)?$"

_store: Optional[PointsStore] = None
_store_lock = threading.Lock()


def store() -> PointsStore:
    global _store
    with _store_lock:
        if _store is None:
            _store = PointsStore(
                GLOBALS.viirs_points_uri, GLOBALS.viirs_points_cache_dir
            )
        return _store


def warm_up() -> None:
    """Load the points in the background, so the first tile request doesn't
    wait for the download."""

    def load():
        try:
            points = store().get()
            # compile datashader's numba code before the first real request
            end = date.fromisoformat(points.max_alert_date)
            for high_confidence_only in (False, True):
                render_tile(
                    points, 0, 0, 0, end - timedelta(days=6), end, high_confidence_only
                )
        except Exception:
            logger.exception("Could not load VIIRS points; will retry on request")

    threading.Thread(target=load, daemon=True).start()


def current_points() -> Points:
    try:
        return store().get()
    except Exception:
        logger.exception("VIIRS points unavailable")
        raise HTTPException(status_code=503, detail="VIIRS alerts not available yet")


def date_range(
    points: Points,
    start_date: Optional[str],
    end_date: Optional[str],
    force_date_range: bool,
) -> Tuple[date, date]:
    """The requested dates, defaulting to the last week of alerts, checked
    like the dynamic VIIRS vector tiles' dates."""
    end = end_date or points.max_alert_date
    start = (
        start_date
        or (date.fromisoformat(end) - timedelta(days=DEFAULT_DAYS - 1)).isoformat()
    )
    validate_dates(start, end, force_date_range)
    return (
        pendulum.from_format(start, "YYYY-MM-DD").date(),
        pendulum.from_format(end, "YYYY-MM-DD").date(),
    )


START_DATE = Query(
    None,
    pattern=DATE_REGEX,
    description="Only show alerts for given date and after. Defaults to 6 days "
    "before the end date.",
)
END_DATE = Query(
    None,
    pattern=DATE_REGEX,
    description="Only show alerts until given date. Defaults to the newest alert date.",
)
FORCE_DATE_RANGE = Query(
    False,
    description="Bypass the built-in limitation to query more than 90 days at a "
    "time. Use cautiously!",
)
HIGH_CONFIDENCE_ONLY = Query(False, title="Only show high confidence alerts")


@router.get(
    f"{PREFIX}/max_alert__date",
    response_class=ORJSONResponse,
    response_model=MaxDateResponse,
    response_description="Newest alert date in the datashader VIIRS tiles",
    tags=["Raster Tiles"],
)
def viirs_datashader_max_date(response: Response) -> MaxDateResponse:
    """Newest alert date served by the datashader VIIRS fire alert tiles."""
    points = current_points()
    response.headers["Cache-Control"] = CACHE_CONTROL
    return MaxDateResponse(data=MaxDate(max_date=points.max_alert_date))


class Alert(BaseModel):
    latitude: float
    longitude: float
    alert__date: date
    alert__time_utc: str
    confidence__cat: str


class NearbyAlerts(BaseModel):
    count: int
    alerts: List[Alert]


class NearbyAlertsResponse(BaseModel):
    data: NearbyAlerts
    status: str = "success"


@router.get(
    f"{PREFIX}/alerts",
    response_class=ORJSONResponse,
    response_model=NearbyAlertsResponse,
    response_description="Alerts near a point, newest first",
    tags=["Raster Tiles"],
)
def viirs_datashader_alerts(
    response: Response,
    lat: float = Query(
        ..., ge=-85.0511, le=85.0511, description="Latitude of the click"
    ),
    lng: float = Query(..., ge=-180, le=180, description="Longitude of the click"),
    z: int = Query(..., ge=0, le=22, description="Zoom level of the tiles shown"),
    start_date: Optional[str] = START_DATE,
    end_date: Optional[str] = END_DATE,
    force_date_range: bool = FORCE_DATE_RANGE,
    high_confidence_only: bool = HIGH_CONFIDENCE_ONLY,
    limit: int = Query(20, ge=1, le=100, description="Most alerts to return"),
) -> NearbyAlertsResponse:
    """The alerts drawn within a few pixels of a clicked point on the
    datashader VIIRS tiles, with the same dates and confidence as the tiles,
    newest first. `count` is the total; at most `limit` alerts are listed."""
    points = current_points()
    start, end = date_range(points, start_date, end_date, force_date_range)
    count, alerts = nearby_alerts(
        points, lng, lat, z, start, end, high_confidence_only, limit=limit
    )
    response.headers["Cache-Control"] = CACHE_CONTROL
    return NearbyAlertsResponse(data=NearbyAlerts(count=count, alerts=alerts))


@router.get(
    f"{PREFIX}/{{z}}/{{x}}/{{y}}.png",
    response_class=Response,
    tags=["Raster Tiles"],
    response_description="PNG Raster Tile",
)
def viirs_datashader_tile(
    z: int = Path(..., ge=0, le=22, description="Zoom level"),
    x: int = Path(..., ge=0, description="Tile grid column"),
    y: str = Path(
        ...,
        pattern=TILE_Y_REGEX,
        description="Tile grid row, optionally with @2x for 512-pixel tiles",
    ),
    start_date: Optional[str] = START_DATE,
    end_date: Optional[str] = END_DATE,
    force_date_range: bool = FORCE_DATE_RANGE,
    high_confidence_only: bool = HIGH_CONFIDENCE_ONLY,
) -> Response:
    """NASA VIIRS fire alerts as 256-pixel PNG tiles
    (512 with @2x), styled like the dynamic VIIRS vector tiles: nearby alerts
    are counted together, and dots range from orange (few alerts) to black
    (16 or more). Any period of up to 90 days in the data can be shown;
    by default, the last 7 days of alerts are shown."""
    row, _, scale = y.partition("@")
    tile_y = int(row)
    if x >= 2**z or tile_y >= 2**z:
        raise HTTPException(status_code=400, detail="Tile index is out of bounds")
    points = current_points()
    start, end = date_range(points, start_date, end_date, force_date_range)
    png = render_tile(
        points,
        z,
        x,
        tile_y,
        start,
        end,
        high_confidence_only,
        scale=2 if scale else 1,
    )
    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": CACHE_CONTROL},
    )
