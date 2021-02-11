from datetime import datetime

import numpy as np

from lambdas.raster_tiler.lambda_function import (
    apply_deforestation_filter,
    days_since_bog,
    get_alpha_band,
)


def test_days_since_bog():
    d = datetime.strptime("2015-01-01", "%Y-%m-%d").date()
    assert days_since_bog(d) == 1

    d = datetime.strptime("2016-01-01", "%Y-%m-%d").date()
    assert days_since_bog(d) == 366

    d = datetime.strptime("2017-01-01", "%Y-%m-%d").date()
    assert days_since_bog(d) == 732

    d = datetime.strptime("2018-01-01", "%Y-%m-%d").date()
    assert days_since_bog(d) == 1097


def test_get_alpha_band():
    red = (np.ones((4, 3)) * 2).astype("uint8")
    green = (np.ones((4, 3)) * 100).astype("uint8")
    blue = (np.ones((4, 3)) * 150).astype("uint8")

    input_data = np.array([red, green, blue])

    result = get_alpha_band(input_data, 611, 900, True)
    assert np.all(result == 0)

    result = get_alpha_band(input_data, 611, 900, False)
    assert np.all(result == 0)

    result = get_alpha_band(input_data, 610, 900, False)
    assert np.all(result == 255)

    result = get_alpha_band(input_data, None, 610, True)
    assert np.all(result == 0)

    result = get_alpha_band(input_data, None, 610, False)
    assert np.all(result == 255)

    result = get_alpha_band(input_data, None, 609, False)
    assert np.all(result == 0)

    result = get_alpha_band(input_data, None, None, False)
    assert np.all(result == 255)

    red = (np.ones((4, 3)) * 3).astype("uint8")
    green = (np.ones((4, 3)) * 2).astype("uint8")
    blue = (np.ones((4, 3)) * 201).astype("uint8")

    input_data = np.array([red, green, blue])

    result = get_alpha_band(input_data, 767, 900, True)
    assert np.all(result == 50)

    result = get_alpha_band(input_data, 767, 900, False)
    assert np.all(result == 50)

    result = get_alpha_band(input_data, 768, 900, False)
    assert np.all(result == 0)

    result = get_alpha_band(input_data, None, 900, False)
    assert np.all(result == 50)

    result = get_alpha_band(input_data, None, 766, False)
    assert np.all(result == 0)

    result = get_alpha_band(input_data, None, None, False)
    assert np.all(result == 50)

    result = get_alpha_band(input_data, None, None, True)
    assert np.all(result == 50)


def test_apply_deforestation_filter():
    red = (np.ones((4, 3)) * 3).astype("uint8")
    green = (np.ones((4, 3)) * 2).astype("uint8")
    blue = (np.ones((4, 3)) * 201).astype("uint8")

    rgb = np.array([red, green, blue])

    input_data = {
        "data": rgb,
        "start_date": "2017-02-05",
        "end_date": "2018-02-05",
        "confirmed_only": True,
        "unused": "test",
    }

    rgba = apply_deforestation_filter(**input_data)

    red, green, blue, alpha = rgba
    assert np.all(red == 228)
    assert np.all(green == 102)
    assert np.all(blue == 153)
    assert np.all(alpha == 50)

    input_data = {
        "data": rgb,
        "start_date": "2017-02-06",
        "end_date": "2018-02-05",
        "confirmed_only": True,
        "unused": "test",
    }

    rgba = apply_deforestation_filter(**input_data)

    red, green, blue, alpha = rgba
    assert np.all(red == 228)
    assert np.all(green == 102)
    assert np.all(blue == 153)
    assert np.all(alpha == 0)
