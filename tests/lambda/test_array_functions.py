import base64
from io import BytesIO

import numpy as np
from PIL import Image

from lambdas.raster_tiler.lambda_function import (
    array_to_img,
    combine_bands,
    separat_bands,
)


def test_separat_bands():
    data = np.array([[[1, 2, 3]], [[1, 2, 3]], [[1, 2, 3]]])

    flip = separat_bands(data)
    assert flip.shape == (3, 1, 3)
    assert np.all(flip[0] == 1)
    assert np.all(flip[1] == 2)
    assert np.all(flip[2] == 3)

    data = np.array([[[1, 2, 3, 4]], [[1, 2, 3, 4]], [[1, 2, 3, 4]]])

    flip = separat_bands(data)
    assert flip.shape == (4, 1, 3)
    assert np.all(flip[0] == 1)
    assert np.all(flip[1] == 2)
    assert np.all(flip[2] == 3)
    assert np.all(flip[3] == 4)


def test_combine_bands():
    data = np.array([[[1, 1, 1]], [[2, 2, 2]], [[3, 3, 3]]])
    data = combine_bands(data)
    assert data.shape == (1, 3, 3)
    np.testing.assert_equal(data[0][0], [1, 2, 3])

    data = np.array(
        [
            [[1, 1, 1]],
            [[2, 2, 2]],
            [[3, 3, 3]],
            [[4, 4, 4]],
        ]
    )

    data = combine_bands(data)
    assert data.shape == (1, 3, 4)
    np.testing.assert_equal(data[0][0], [1, 2, 3, 4])


def test_array_to_img():
    data = np.array([[[1, 2, 4, 5]], [[2, 3, 5, 6]], [[3, 4, 5, 6]], [[4, 5, 6, 7]]])
    img = array_to_img(data)
    assert isinstance(img, str)

    # Decode back and verify pixel data instead of the raw bytes
    decoded = Image.open(BytesIO(base64.b64decode(img)))
    result = np.array(decoded)
    expected = np.moveaxis(data, 0, -1)  # convert from (bands, h, w) to (h, w, bands)
    np.testing.assert_array_equal(result, expected)
