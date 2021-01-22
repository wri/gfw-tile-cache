import numpy as np
from rasterio.windows import Window

from lambdas.raster_tiler.lambda_function import array_to_img
from lambdas.raster_tiler.readers.datalake import get_tile_array, get_tile_location
from tests.conftest import TEST_FILE


def test_tile():

    data = get_tile_array(TEST_FILE, Window(0, 0, 256, 256))
    assert data.shape == (4, 256, 256)
    np.testing.assert_equal(data[0][0], [1, 2, 3, 4])

    data = get_tile_array(TEST_FILE, Window(0, 256, 256, 256))
    assert data.shape == (4, 256, 256)
    np.testing.assert_equal(data[0][0], [2, 4, 6, 8])

    data = get_tile_array(TEST_FILE, Window(256, 0, 256, 256))
    assert data.shape == (4, 256, 256)
    np.testing.assert_equal(data[0][0], [3, 6, 9, 12])

    data = get_tile_array(TEST_FILE, Window(256, 256, 256, 256))
    assert data.shape == (4, 256, 256)
    np.testing.assert_equal(data[0][0], [4, 8, 12, 16])


def test_array_to_img():
    data = np.array([[[1, 2, 3, 4], [2, 3, 4, 5], [3, 4, 5, 6], [4, 5, 6, 7]]])
    img = array_to_img(data)
    assert isinstance(img, str)
    assert (
        img
        == "iVBORw0KGgoAAAANSUhEUgAAAAQAAAABCAYAAAD5PA/NAAAAHElEQVR4AQERAO7/AAEAAAAAAAAAAgAAAAAAAAAAMQAEwqwNZAAAAABJRU5ErkJggg=="
    )


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


#     assert col_off == 256
