import json
import os
from typing import Any, Dict

import boto3
import numpy as np
import pytest
import pytest_asyncio
import rasterio
from fastapi.testclient import TestClient
from PIL import Image
from rasterio.enums import ColorInterp
from rasterio.windows import Window

from app.application import db, get_synchronous_db
from app.settings.globals import GLOBALS

AWS_ENDPOINT_URI = os.environ.get("AWS_ENDPOINT_URI", None)

##################
# Create Test data
##################

fixtures = os.path.join(os.path.dirname(__file__), "fixtures")
TEST_TIF = os.path.join(fixtures, "test.tif")
TEST_PNG = os.path.join(fixtures, "test.png")


def create_test_tif():
    band_count = 3
    profile = {
        "driver": "GTiff",
        "height": 512,
        "width": 512,
        "count": band_count,
        "dtype": "uint8",
    }

    bands = range(1, band_count + 1)
    windows = ((0, 0), (0, 256), (256, 0), (256, 256))

    with rasterio.open(TEST_TIF, "w", **profile) as dst:
        for band in bands:
            for i, window in enumerate(windows):
                data = np.ones(shape=(256, 256), dtype="uint8") * (i + 1) * band
                dst.write(
                    data, window=Window(window[0], window[1], 256, 256), indexes=band
                )
        dst.colorinterp = [
            ColorInterp.red,
            ColorInterp.green,
            ColorInterp.blue,
            # ColorInterp.alpha,
        ]

    s3_client = boto3.client("s3", endpoint_url=AWS_ENDPOINT_URI)
    s3_client.upload_file(
        TEST_TIF,
        "gfw-data-lake-test",
        "wur_radd_alerts/v20201214/raster/epsg-3857/zoom_14/default/geotiff/000R_000C.tif",
    )
    s3_client.upload_file(
        TEST_TIF,
        "gfw-data-lake-test",
        "umd_tree_cover_loss/v1.8/raster/epsg-3857/zoom_12/tcd_30/geotiff/000R_000C.tif",
    )
    s3_client.upload_file(
        TEST_TIF,
        "gfw-data-lake-test",
        "umd_glad_landsat_alerts/v20210101/raster/epsg-3857/zoom_12/default/geotiff/000R_000C.tif",
    )


##################
# Create Test data
##################
def create_test_png():
    data = (np.ones(shape=(256, 256, 3)) * [1, 2, 3]).astype("uint8")
    img = Image.fromarray(data, mode="RGB")
    params = {"compress_level": 0}
    img.save(TEST_PNG, "png", **params)


def pytest_sessionstart(session):
    """Called after the Session object has been created and before performing
    collection and entering the run test loop."""

    with get_synchronous_db() as db:
        sql_file = f"{os.path.dirname(__file__)}/fixtures/session_start.sql"
        with open(sql_file) as f:
            sql = f.read()

        db.execute(sql)
        db.commit()

    create_test_tif()
    create_test_png()


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished, right before returning the exit
    status to the system."""
    with get_synchronous_db() as db:
        sql_file = f"{os.path.dirname(__file__)}/fixtures/session_end.sql"
        with open(sql_file) as f:
            sql = f.read()

        db.execute(sql)
        db.commit()

    os.remove(TEST_PNG)
    s3_client = boto3.client("s3", endpoint_url=AWS_ENDPOINT_URI)
    s3_client.delete_object(
        Bucket="gfw-data-lake-test",
        Key="wur_radd_alerts/v20201214/raster/epsg-3857/zoom_14/default/geotiff/000R_000C.tif",
    )
    s3_client.delete_object(
        Bucket="gfw-data-lake-test",
        Key="umd_tree_cover_loss/v1.8/raster/epsg-3857/zoom_12/tcd_30/geotiff/000R_000C.tif",
    )
    s3_client.delete_object(
        Bucket="gfw-data-lake-test",
        Key="umd_glad_landsat_alerts/v20210101/raster/epsg-3857/zoom_12/default/geotiff/000R_000C.tif",
    )


@pytest.fixture(autouse=False)
def client():
    """Test client for tile cache app."""
    from app.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture(name="mock_get_dynamic_tile", scope="session")
def fixture_mock_get_dynamic_tile():
    """Mock lambda raster tile and return payload as byte obj instead of raster
    image.

    This will allow to verify if route service correctly process the
    payload.
    """

    def _mock_get_dynamic_tile(
        payload: Dict[str, Any], implementation, background_tasks
    ):
        response = {"data": payload, "status": "success"}
        return json.dumps(response).encode()

    return _mock_get_dynamic_tile


@pytest_asyncio.fixture(scope="function")
async def connect_db():
    await db.set_bind(GLOBALS.database_config.url)
    yield db

    # Teardown: close the database connection
    bind = db.pop_bind()
    if bind:
        await bind.close()
