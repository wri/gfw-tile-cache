from datetime import date

import numpy as np
import rasterio
from rio_tiler.models import ImageData

from app.models.enumerators.titiler import IntegratedAlertConfidence, RenderType
from app.routes.titiler.algorithms.dist_alerts import DISTAlerts
from app.routes.titiler.algorithms.integrated_alerts import IntegratedAlerts
from tests.conftest import DATE_CONF_TIF, INTENSITY_TIF

today = date.today()
alert_period = 180  # most recent days of alerts to display


def get_tile_data():
    with rasterio.open(DATE_CONF_TIF) as date_conf_file:
        date_conf = date_conf_file.read(1)

    with rasterio.open(INTENSITY_TIF) as intensity_file:
        intensity = intensity_file.read(1)

    data = np.stack([date_conf, intensity], axis=0)

    return ImageData(data)


def get_tcl_data():
    """Tree Cover Loss test data."""
    with rasterio.open(DATE_CONF_TIF) as date_conf_file:
        date_conf = date_conf_file.read(1)

    data = np.zeros_like(date_conf)

    data[122, 109] = 2019
    data[120, 109] = 2022
    data[154, 71] = 2023

    return ImageData(data)


def get_tch_data():
    """Tree Cover Height test data."""

    with rasterio.open(DATE_CONF_TIF) as date_conf_file:
        date_conf = date_conf_file.read(1)

    data = np.zeros_like(date_conf)

    data[122, 109] = 2
    data[120, 109] = 5
    data[154, 71] = 4

    return ImageData(data)


def get_tcd_data():
    """Tree Cover Density test data."""

    with rasterio.open(DATE_CONF_TIF) as date_conf_file:
        date_conf = date_conf_file.read(1)

    data = np.zeros_like(date_conf)

    data[122, 109] = 40
    data[120, 109] = 30
    data[154, 71] = 20

    return ImageData(data)


def test_integrated_alerts_defaults():
    """Test default values of the Alerts class."""
    alerts = IntegratedAlerts()

    assert alerts.render_type == RenderType.true_color


def test_create_date_range_mask():
    """Test mask creation logic and date range filters."""
    alerts = IntegratedAlerts(
        start_date="2022-01-01",
        end_date="2023-06-10",
    )

    img = get_tile_data()
    _ = alerts(img)

    mask = alerts.create_mask()

    assert mask.shape == img.data[0].shape
    assert mask.sum() == 263


def test_create_confidence_mask():
    """Test confidence filters are applied correctly."""
    alerts = IntegratedAlerts(alert_confidence=IntegratedAlertConfidence.highest)
    alerts.start_date = alerts.record_start_date

    img = get_tile_data()
    _ = alerts(img)

    mask = alerts.create_mask()
    assert mask.shape == img.data[0].shape
    assert mask.sum() == 60


def test_mask_logic_with_nodata():
    """Test that the mask properly handles no-data values."""
    alerts = IntegratedAlerts(alert_confidence=IntegratedAlertConfidence.low)

    img = get_tile_data()

    output = alerts(img)

    assert output.data[3, 0, 0] == 0  # Alpha should be 0 for no-data pixel


def test_true_color_rgb():
    """Test that the right pink pixels are used."""
    alerts = IntegratedAlerts(start_date="2022-01-01")

    img = get_tile_data()
    rgba = alerts(img)

    # highest confidence
    np.testing.assert_array_equal(
        rgba.array[:, 120, 109], np.array([201, 42, 109, 255])
    )

    # high confidence
    np.testing.assert_array_equal(
        rgba.array[:, 154, 71], np.array([220, 102, 153, 255])
    )


def test_encoded_rgba():
    """Test encoding used for tiles served to Flagship."""
    alerts = IntegratedAlerts(start_date="2022-01-01", render_type=RenderType.encoded)

    img = get_tile_data()
    rgba = alerts(img)

    # test date encoding in red and green channels
    np.testing.assert_array_equal(rgba.array[:2, 122, 109], np.array([12, 154]))

    # test highest confidence in alpha channel
    assert rgba.array[3, 122, 109] == 24

    # test high confidence in alpha channel
    assert rgba.array[3, 154, 71] == 8


def test_forest_mask():
    """Test that only alerts that match forest criteria are shown."""

    alerts_data = get_tile_data()
    tcl = get_tcl_data()
    tch = get_tch_data()
    tcd = get_tcd_data()

    alerts = DISTAlerts(
        tree_cover_density_mask=30,
        tree_cover_height_mask=3,
        tree_cover_loss_mask=2021,
        render_type=RenderType.true_color,
    )

    alerts.tree_cover_density_data = tcd
    alerts.tree_cover_height_data = tch
    alerts.tree_cover_loss_data = tcl

    rgba = alerts(alerts_data)

    np.testing.assert_array_equal(rgba.array[:, 122, 109], np.array([220, 102, 153, 0]))

    np.testing.assert_array_equal(rgba.array[:, 154, 71], np.array([220, 102, 153, 0]))

    np.testing.assert_array_equal(
        rgba.array[:, 120, 109], np.array([220, 102, 153, 255])
    )
