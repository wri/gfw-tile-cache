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


def _create_tcl_3band_data():
    intensity = (np.ones((4, 3)) * 100).astype("uint8")
    all_zeros = (np.zeros((4, 3))).astype("uint8")
    year_2000 = (np.zeros((1, 3))).astype("uint8")
    year_2005 = (np.ones((1, 3)) * 5).astype("uint8")
    year_2010 = (np.ones((1, 3)) * 10).astype("uint8")
    year_2015 = (np.ones((1, 3)) * 15).astype("uint8")
    years = np.vstack([year_2000, year_2005, year_2010, year_2015])
    return np.array([intensity, all_zeros, years])


def _create_tcl_4band_data():
    """
    This creates Tree Cover Loss (TCL) test data >= v1.9.
    In this version, a 4th band is created as an 'alpha' channel for year_intensity symbology
    https://github.com/wri/gfw-data-api/commit/d3c32ac8f9378bdcd50584b020e02d557860cbef
    """
    tcl_3band_data = _create_tcl_3band_data()
    tcl_4th_band = (np.ones((4, 3)) * 255).astype("uint8")
    return np.append(tcl_3band_data, [tcl_4th_band], axis=0)


def _apply_filter_with(data, zoom_level="10", start_year=None, end_year=None):
    return apply_annual_loss_filter(
        data, z=zoom_level, start_year=start_year, end_year=end_year
    )


def test_red_band_intensity_is_invariant_with_zoom_level():
    input_data = _create_tcl_3band_data()
    red = 0

    zoomed_in = _apply_filter_with(input_data, zoom_level="12")
    zoomed_out = _apply_filter_with(input_data, zoom_level="10")

    assert np.all(zoomed_in[red] == zoomed_out[red])


def test_green_band_gains_intensity_as_zoom_increases():
    input_data = _create_tcl_3band_data()
    green = 1

    zoomed_in = _apply_filter_with(input_data, zoom_level="12")
    zoomed_out = _apply_filter_with(input_data, zoom_level="10")

    assert np.all(zoomed_in[green] > zoomed_out[green])


def test_blue_band_gains_intensity_as_zoom_decreases():
    input_data = _create_tcl_3band_data()
    blue = 2

    zoomed_in = _apply_filter_with(input_data, zoom_level="12")
    zoomed_out = _apply_filter_with(input_data, zoom_level="10")

    assert np.all(zoomed_in[blue] < zoomed_out[blue])


def test_apply_annual_loss_filter():
    input_data = _create_tcl_3band_data()

    result = apply_annual_loss_filter(
        input_data, z="12", start_year="2000", end_year="2020"
    )
    alpha = result[3]
    assert np.all(alpha[0] == 0)
    assert np.all(alpha[1] == 100)
    assert np.all(alpha[2] == 100)
    assert np.all(alpha[3] == 100)

    result = apply_annual_loss_filter(
        input_data, z="12", start_year="2006", end_year="2014"
    )
    alpha = result[3]
    assert np.all(alpha[0] == 0)
    assert np.all(alpha[1] == 0)
    assert np.all(alpha[2] == 100)
    assert np.all(alpha[3] == 0)

    result = apply_annual_loss_filter(
        input_data, z="12", start_year=None, end_year=None
    )
    alpha = result[3]
    assert np.all(alpha[0] == 0)
    assert np.all(alpha[1] == 100)
    assert np.all(alpha[2] == 100)
    assert np.all(alpha[3] == 100)

    result = apply_annual_loss_filter(
        input_data, z="10", start_year="2001", end_year="2020"
    )
    alpha = result[3]
    assert np.all(alpha[0] == 0)
    assert np.all(alpha[1] == 138)
    assert np.all(alpha[2] == 138)
    assert np.all(alpha[3] == 138)


def test_apply_annual_loss_filter_ignores_alpha_channel_already_in_data():
    input_data_3band = _create_tcl_3band_data()
    input_data_4band = _create_tcl_4band_data()

    result_3band = _apply_filter_with(
        input_data_3band, zoom_level="10", start_year="2001", end_year="2020"
    )
    result_4band = _apply_filter_with(
        input_data_4band, zoom_level="10", start_year="2001", end_year="2020"
    )

    assert np.all(result_3band == result_4band)
