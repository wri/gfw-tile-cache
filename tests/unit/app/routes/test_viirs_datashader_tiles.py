import io
from datetime import date

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.routes.nasa_viirs_fire_alerts import datashader_tiles as route
from app.utils.viirs_points import PointsStore

PREFIX = "/nasa_viirs_fire_alerts/latest/datashader"
# zoom 10 tile holding the alerts below
TILE = "10/575/547"

ALERTS = [
    (-12.30001, 22.30001, "2026-11-10", "1210", "n"),
    (-12.30001, 22.30001, "2026-11-16", "0130", "h"),
    (-12.30002, 22.30002, "2026-08-01", "0005", "n"),
]


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    path = str(tmp_path / "points.parquet")
    pq.write_table(
        pa.table(
            {
                "latitude": [a[0] for a in ALERTS],
                "longitude": [a[1] for a in ALERTS],
                "acq_date": pa.array([date.fromisoformat(a[2]) for a in ALERTS]),
                "acq_time": [a[3] for a in ALERTS],
                "confidence": [a[4] for a in ALERTS],
            }
        ),
        path,
    )
    monkeypatch.setattr(route, "_store", PointsStore(path, str(tmp_path / "cache")))
    app = FastAPI()
    app.include_router(route.router)
    return TestClient(app)


def image(response) -> Image.Image:
    return Image.open(io.BytesIO(response.content))


def drawn_pixels(response) -> int:
    alpha = image(response).getchannel("A")
    return sum(1 for value in alpha.getdata() if value)


def test_tile_is_a_png_cached_for_an_hour(client):
    response = client.get(f"{PREFIX}/{TILE}.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "max-age=3600"
    assert image(response).size == (256, 256)


def test_retina_tile_is_512_pixels(client):
    response = client.get(f"{PREFIX}/10/575/547@2x.png")

    assert image(response).size == (512, 512)


def test_default_dates_are_the_last_week_of_alerts(client):
    default = client.get(f"{PREFIX}/{TILE}.png")
    august = client.get(
        f"{PREFIX}/{TILE}.png?start_date=2026-08-01&end_date=2026-08-01"
    )
    september = client.get(
        f"{PREFIX}/{TILE}.png?start_date=2026-09-01&end_date=2026-09-30"
    )

    assert drawn_pixels(default) > 0
    assert drawn_pixels(august) > 0
    assert drawn_pixels(september) == 0


def test_more_than_90_days_needs_force_date_range(client):
    url = f"{PREFIX}/{TILE}.png?start_date=2026-01-01&end_date=2026-11-16"

    assert client.get(url).status_code == 403
    assert client.get(url + "&force_date_range=true").status_code == 200


def test_tile_outside_the_grid_is_rejected(client):
    assert client.get(f"{PREFIX}/2/4/0.png").status_code == 400


def test_max_alert_date_is_the_newest_alert(client):
    response = client.get(f"{PREFIX}/max_alert__date")

    assert response.json() == {"data": {"max_date": "2026-11-16"}, "status": "success"}


def test_alerts_near_a_click_use_the_tile_filters(client):
    query = "lat=-12.30001&lng=22.30001&z=10&start_date=2026-11-01&end_date=2026-11-16"

    all_alerts = client.get(f"{PREFIX}/alerts?{query}").json()["data"]
    high = client.get(f"{PREFIX}/alerts?{query}&high_confidence_only=true").json()[
        "data"
    ]

    assert all_alerts["count"] == 2
    assert [a["alert__date"] for a in all_alerts["alerts"]] == [
        "2026-11-16",
        "2026-11-10",
    ]
    assert high == {
        "count": 1,
        "alerts": [
            {
                "latitude": -12.30001,
                "longitude": 22.30001,
                "alert__date": "2026-11-16",
                "alert__time_utc": "0130",
                "confidence__cat": "h",
            }
        ],
    }


def test_unavailable_points_return_503(tmp_path, monkeypatch):
    monkeypatch.setattr(
        route,
        "_store",
        PointsStore(str(tmp_path / "missing.parquet"), str(tmp_path / "cache")),
    )
    app = FastAPI()
    app.include_router(route.router)

    response = TestClient(app).get(f"{PREFIX}/{TILE}.png")

    assert response.status_code == 503
