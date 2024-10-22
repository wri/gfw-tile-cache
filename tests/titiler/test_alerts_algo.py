from datetime import date

import numpy as np
import rasterio
from dateutil.relativedelta import relativedelta
from rio_tiler.models import ImageData

from app.models.enumerators.titiler import AlertConfidence, RenderType
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


def test_integrated_alerts_defaults():
    """Test default values of the Alerts class."""
    alerts = IntegratedAlerts()

    assert alerts.start_date == (today - relativedelta(days=alert_period)).strftime(
        "%Y-%m-%d"
    )
    assert alerts.end_date == today.strftime("%Y-%m-%d")
    assert alerts.alert_confidence == AlertConfidence.low
    assert alerts.record_start_date == "2014-12-31"


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
    alerts = IntegratedAlerts(alert_confidence=AlertConfidence.highest)
    alerts.start_date = alerts.record_start_date

    img = get_tile_data()
    _ = alerts(img)

    mask = alerts.create_mask()
    assert mask.shape == img.data[0].shape
    assert mask.sum() == 60


def test_mask_logic_with_nodata():
    """Test that the mask properly handles no-data values."""
    alerts = IntegratedAlerts(alert_confidence=AlertConfidence.low)

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
    """Test encoding used for tiled served to Flagship."""
    alerts = IntegratedAlerts(start_date="2022-01-01", render_type=RenderType.encoded)

    img = get_tile_data()
    rgba = alerts(img)

    # test date encoding in red and green channels
    np.testing.assert_array_equal(rgba.array[:2, 122, 109], np.array([12, 154]))

    # test highest confidence in alpha channel
    assert rgba.array[3, 122, 109] == 24

    # test high confidence in alpha channel
    assert rgba.array[3, 154, 71] == 8
