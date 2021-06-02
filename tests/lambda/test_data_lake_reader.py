import boto3
import numpy as np
import pytest
from rasterio.windows import Window

from lambdas.raster_tiler.lambda_function import (
    DATA_LAKE_BUCKET,
    TILE_SIZE,
    TileNotFoundError,
    get_source_window,
    get_tile_array,
    get_tile_location,
    read_data_lake,
)
from tests.conftest import AWS_ENDPOINT_URI, TEST_TIF
from tests.fixtures.payloads import umd_tree_cover_loss_payload


def test_get_tile_location():
    row, col, row_off, col_off = get_tile_location(0, 0)
    assert row == 0
    assert col == 0
    assert row_off == 0
    assert col_off == 0

    row, col, row_off, col_off = get_tile_location(256, 256)
    assert row == 1
    assert col == 1
    assert row_off == 0
    assert col_off == 0

    row, col, row_off, col_off = get_tile_location(255, 255)
    assert row == 0
    assert col == 0
    assert row_off == 256 * 255
    assert col_off == 256 * 255

    row, col, row_off, col_off = get_tile_location(257, 257)
    assert row == 1
    assert col == 1
    assert row_off == 256


def test_get_tile_array():
    rgb = get_tile_array(TEST_TIF, Window(0, 0, 256, 256))
    assert rgb.shape == (3, 256, 256)
    red, green, blue = rgb
    np.all(red == 1)
    np.all(green == 2)
    np.all(blue == 3)

    data = get_tile_array(TEST_TIF, Window(0, 256, 256, 256))
    assert data.shape == (3, 256, 256)
    red, green, blue = rgb
    np.all(red == 2)
    np.all(green == 3)
    np.all(blue == 6)

    data = get_tile_array(TEST_TIF, Window(256, 0, 256, 256))
    assert data.shape == (3, 256, 256)
    red, green, blue = rgb
    np.all(red == 3)
    np.all(green == 6)
    np.all(blue == 9)

    data = get_tile_array(TEST_TIF, Window(256, 256, 256, 256))
    assert data.shape == (3, 256, 256)
    red, green, blue = rgb
    np.all(red == 4)
    np.all(green == 8)
    np.all(blue == 12)


def test_get_tile_array_over_zoom():
    """when requesting smaller windows, we should still receive 256x256 arrays"""

    rgb = get_tile_array(TEST_TIF, Window(0, 0, 128, 128))
    assert rgb.shape == (3, 256, 256)
    red, green, blue = rgb
    np.all(red == 1)
    np.all(green == 2)
    np.all(blue == 3)

    data = get_tile_array(TEST_TIF, Window(0, 256, 128, 128))
    assert data.shape == (3, 256, 256)
    red, green, blue = rgb
    np.all(red == 2)
    np.all(green == 3)
    np.all(blue == 6)

    data = get_tile_array(TEST_TIF, Window(256, 0, 128, 128))
    assert data.shape == (3, 256, 256)
    red, green, blue = rgb
    np.all(red == 3)
    np.all(green == 6)
    np.all(blue == 9)

    data = get_tile_array(TEST_TIF, Window(256, 256, 128, 128))
    assert data.shape == (3, 256, 256)
    red, green, blue = rgb
    np.all(red == 4)
    np.all(green == 8)
    np.all(blue == 12)


@pytest.mark.parametrize(
    "params, payload",
    [
        umd_tree_cover_loss_payload(x=0, y=0, z=0, over_zoom=None),
        umd_tree_cover_loss_payload(x=0, y=0, z=0, over_zoom=0),
        umd_tree_cover_loss_payload(x=0, y=0, z=1, over_zoom=1),
        umd_tree_cover_loss_payload(x=1, y=1, z=1, over_zoom=1),
        umd_tree_cover_loss_payload(x=0, y=0, z=1, over_zoom=0),
        umd_tree_cover_loss_payload(x=1, y=1, z=1, over_zoom=0),
    ],
)
def test_get_source_window(params, payload):

    dataset = payload["dataset"]
    version = payload["version"]
    implementation = payload["implementation"]
    x = payload["x"]
    y = payload["y"]
    z = payload["z"]
    over_zoom = payload["over_zoom"]

    source, window = get_source_window(
        dataset, version, implementation, x, y, z, over_zoom
    )

    if over_zoom is not None and over_zoom < z:
        divisor = 2 ** (z - over_zoom)
        _z = over_zoom
    else:
        divisor = 1
        _z = z

    assert window.width == pytest.approx(TILE_SIZE / divisor)
    assert window.height == pytest.approx(TILE_SIZE / divisor)

    if x == 0 and y == 0:
        assert window.row_off == 0
        assert window.col_off == 0
    else:
        assert window.row_off == pytest.approx(TILE_SIZE / divisor)
        assert window.col_off == pytest.approx(TILE_SIZE / divisor)

    expected_source = f"s3://{DATA_LAKE_BUCKET}/{dataset}/{version}/raster/epsg-3857/zoom_{_z}/{implementation}/geotiff/{str(0).zfill(3)}R_{str(0).zfill(3)}C.tif"

    assert source == expected_source


@pytest.mark.parametrize(
    "params, payload",
    [
        umd_tree_cover_loss_payload(x=4084, y=2984, z=13, over_zoom=12),
        umd_tree_cover_loss_payload(x=184, y=1004, z=12, over_zoom=11),
        umd_tree_cover_loss_payload(x=4084, y=2984, z=14, over_zoom=10),
        umd_tree_cover_loss_payload(x=5035, y=7954, z=15, over_zoom=9),
    ],
)
def test_get_source_window_over_zoom(params, payload):
    """Make sure that offset is still within parent image"""

    dataset = payload["dataset"]
    version = payload["version"]
    implementation = payload["implementation"]
    x = payload["x"]
    y = payload["y"]
    z = payload["z"]
    over_zoom = payload["over_zoom"]

    _, window = get_source_window(dataset, version, implementation, x, y, z, over_zoom)

    divisor = 2 ** (z - over_zoom)

    assert window.width == pytest.approx(TILE_SIZE / divisor)
    assert window.height == pytest.approx(TILE_SIZE / divisor)

    assert window.row_off >= 0
    assert window.row_off < TILE_SIZE ** 2
    assert window.col_off >= 0
    assert window.col_off < TILE_SIZE ** 2


def test_read_data_lake():

    s3_client = boto3.client("s3", endpoint_url=AWS_ENDPOINT_URI)
    s3_client.head_object(
        Bucket="gfw-data-lake-test",
        Key="wur_radd_alerts/v20201214/raster/epsg-3857/zoom_14/default/geotiff/000R_000C.tif",
    )

    input_data = {
        "dataset": "wur_radd_alerts",
        "version": "v20201214",
        "implementation": "default",
        "x": 0,
        "y": 0,
        "z": 14,
        "unused": "test",
        "over_zoom": 14,
    }

    data = read_data_lake(**input_data)
    assert data.shape == (3, 256, 256)

    input_data["version"] = "v20201215"

    with pytest.raises(TileNotFoundError):
        read_data_lake(**input_data)
