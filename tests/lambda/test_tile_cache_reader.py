from unittest.mock import patch

import numpy as np

from lambdas.raster_tiler.lambda_function import read_tile_cache
from tests.conftest import TEST_PNG


@patch("lambdas.raster_tiler.lambda_function.urlopen")
def test_read_tile_cache(mock_url):

    mock_url.return_value = TEST_PNG
    event = {
        "dataset": "test",
        "version": "v1",
        "implementation": "dynamic",
        "x": 1,
        "y": 1,
        "z": 1,
        "extra": "test",
    }

    arr = read_tile_cache(**event)

    assert arr.shape == (3, 256, 256)
    assert np.all(arr[0] == 1)
    assert np.all(arr[1] == 2)
    assert np.all(arr[2] == 3)
