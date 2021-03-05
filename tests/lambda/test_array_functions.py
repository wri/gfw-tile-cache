import numpy as np

from lambdas.raster_tiler.lambda_function import (
    array_to_img,
    combine_bands,
    seperate_bands,
)


def test_seperate_bands():
    data = np.array([[[1, 2, 3]], [[1, 2, 3]], [[1, 2, 3]]])

    flip = seperate_bands(data)
    assert flip.shape == (3, 1, 3)
    assert np.all(flip[0] == 1)
    assert np.all(flip[1] == 2)
    assert np.all(flip[2] == 3)

    data = np.array([[[1, 2, 3, 4]], [[1, 2, 3, 4]], [[1, 2, 3, 4]]])

    flip = seperate_bands(data)
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
    assert (
        img
        == "iVBORw0KGgoAAAANSUhEUgAAAAQAAAABCAYAAAD5PA/NAAAAHElEQVR4AQERAO7/AAEAAAAAAAAAAgAAAAAAAAAAMQAEwqwNZAAAAABJRU5ErkJggg=="
    )
