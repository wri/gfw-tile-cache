import numpy as np

from lambdas.raster_tiler.lambda_function import (
    apply_annual_loss_filter,
    scale_intensity,
)


def test_scale_intensity():

    scale_zoom_12 = scale_intensity(12)
    assert scale_zoom_12(0) == 0
    assert scale_zoom_12(50) == 50
    assert scale_zoom_12(100) == 100
    assert scale_zoom_12(255) == 255

    scale_zoom_10 = scale_intensity(10)
    assert scale_zoom_10(0) == 0
    assert scale_zoom_10(50) == 88.43406042264562
    assert scale_zoom_10(100) == 138.7679150400963
    assert scale_zoom_10(255) == 255

    scale_zoom_2 = scale_intensity(2)
    assert scale_zoom_2(0) == 0
    assert scale_zoom_2(50) == 169.68663461251847
    assert scale_zoom_2(100) == 201.79255320207398
    assert scale_zoom_2(255) == 255


def test_apply_annual_loss_filter():
    # Create test data

    intensity = (np.ones((4, 3)) * 100).astype("uint8")
    year_2000 = (np.zeros((1, 3))).astype("uint8")
    year_2005 = (np.ones((1, 3)) * 5).astype("uint8")
    year_2010 = (np.ones((1, 3)) * 10).astype("uint8")
    year_2015 = (np.ones((1, 3)) * 15).astype("uint8")
    years = np.vstack([year_2000, year_2005, year_2010, year_2015])
    input_data = np.array([intensity, intensity, years])

    result = apply_annual_loss_filter(
        input_data, z="12", start_year="2000", end_year="2020"
    )
    red, green, blue, alpha = result
    assert np.all(red == 228)
    assert np.all(green == 137)
    assert np.all(blue == 165)
    assert np.all(alpha[0] == 0)
    assert np.all(alpha[1] == 100)
    assert np.all(alpha[2] == 100)
    assert np.all(alpha[3] == 100)

    result = apply_annual_loss_filter(
        input_data, z="12", start_year="2006", end_year="2014"
    )
    red, green, blue, alpha = result
    assert np.all(red == 228)
    assert np.all(green == 137)
    assert np.all(blue == 165)
    assert np.all(alpha[0] == 0)
    assert np.all(alpha[1] == 0)
    assert np.all(alpha[2] == 100)
    assert np.all(alpha[3] == 0)

    result = apply_annual_loss_filter(
        input_data, z="12", start_year=None, end_year=None
    )
    red, green, blue, alpha = result
    assert np.all(red == 228)
    assert np.all(green == 137)
    assert np.all(blue == 165)
    assert np.all(alpha[0] == 0)
    assert np.all(alpha[1] == 100)
    assert np.all(alpha[2] == 100)
    assert np.all(alpha[3] == 100)

    result = apply_annual_loss_filter(
        input_data, z="10", start_year="2001", end_year="2020"
    )
    red, green, blue, alpha = result
    assert np.all(red == 228)
    assert np.all(green == 122)
    assert np.all(blue == 166)
    assert np.all(alpha[0] == 0)
    assert np.all(alpha[1] == 138)
    assert np.all(alpha[2] == 138)
    assert np.all(alpha[3] == 138)
