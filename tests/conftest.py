import os

import boto3
import numpy as np
import pytest
import rasterio
from fastapi.testclient import TestClient
from rasterio.enums import ColorInterp
from rasterio.windows import Window

from app.application import get_synchronous_db

AWS_ENDPOINT_URI = os.environ.get("AWS_ENDPOINT_URI", None)


##################
# Create Test data
##################

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

fixtures = os.path.join(os.path.dirname(__file__), "fixtures")
TEST_FILE = os.path.join(fixtures, "test.tif")

with rasterio.open(TEST_FILE, "w", **profile) as dst:
    for band in bands:
        for i, window in enumerate(windows):
            data = np.ones(shape=(256, 256), dtype="uint8") * (i + 1) * band
            dst.write(data, window=Window(window[0], window[1], 256, 256), indexes=band)
    dst.colorinterp = [
        ColorInterp.red,
        ColorInterp.green,
        ColorInterp.blue,
        # ColorInterp.alpha,
    ]

s3_client = boto3.client("s3", endpoint_url=AWS_ENDPOINT_URI)
s3_client.upload_file(
    TEST_FILE,
    "gfw-data-lake-test",
    "gfw_radd_alerts/v20201214/raster/epsg-3857/zoom_14/rgb_encoded/geotiff/000R_000C.tif",
)


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """

    with get_synchronous_db() as db:
        sql_file = f"{os.path.dirname(__file__)}/fixtures/session_start.sql"
        with open(sql_file) as f:
            sql = f.read()

        db.execute(sql)
        db.commit()


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    with get_synchronous_db() as db:
        sql_file = f"{os.path.dirname(__file__)}/fixtures/session_end.sql"
        with open(sql_file) as f:
            sql = f.read()

        db.execute(sql)
        db.commit()


@pytest.fixture(autouse=True)
def client():
    """
    Set up a clean database before running a test
    Run all migrations before test and downgrade afterwards
    """
    from app.main import app

    with TestClient(app) as client:
        yield client
