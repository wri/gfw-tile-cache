import pytest
from fastapi.testclient import TestClient

from app.routes import raster_tile_cache_version_dependency


@pytest.fixture
def client_500():
    """
    Set up a clean database before running a test
    Run all migrations before test and downgrade afterwards
    """
    from app.main import app

    def mock_error(dataset, version):
        if dataset == "dataset":
            raise Exception("This went wrong")

    app.dependency_overrides[raster_tile_cache_version_dependency] = mock_error

    with TestClient(app) as client:
        yield client


def test_404(client):
    resp = client.get("/doesnotexist")
    assert resp.status_code == 404
    assert resp.json().get("status") == "failed"
    assert resp.json().get("message") == "Not Found"


def test_422(client):
    resp = client.get("/dataset/version/default/1/1/1.png")
    assert resp.status_code == 422
    assert resp.json().get("status") == "failed"
    assert len(resp.json().get("message")) == 2
    assert resp.json().get("message")[0]["loc"] == ["path", "version"]
    assert resp.json().get("message")[1]["loc"] == ["path", "dataset"]


@pytest.mark.skip(
    reason="While error is correctly handled, the exception is still thrown. See FixMe remarks in main.py"
)
def test_500(client_500):
    resp = client_500.get("/dataset/version/default/1/1/1.png")
    assert resp.status_code == 500
    assert resp.json().get("status") == "error"
    assert resp.json().get("message") == "Internal Server Error"
