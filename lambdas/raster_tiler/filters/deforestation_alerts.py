from datetime import date, datetime

import numpy as np
from numpy import ndarray


def days_since_bog(d: date) -> int:
    """Convert date into number of days since 2014-12-31 (beginning of GLAD)."""

    baseyear = 2015
    year = d.year
    day_in_year = d.timetuple().tm_yday
    offset = (year - baseyear) * 365 + sum(
        [int(not (y % 4)) for y in range(baseyear - 1, year)]
    )

    return offset + day_in_year


def get_alpha(
    rgb: ndarray, start_date: int, end_date: int, confirmed_only: bool
) -> int:
    """Compute alpha value based on RGB encoding and applied filters.
    Expecting 3D array.
    """

    # encode false color tiles
    red, green, blue = rgb
    date = red * 255 + green
    confidence = np.floor(blue / 100) - 1
    intensity = blue % 100

    # build masks
    date_mask = (start_date <= date) * (date <= end_date)
    confidence_mask = (
        (confidence == 1)
        if confirmed_only
        else np.ones(confidence.shape).astype("bool")
    )
    no_data_mask = red + green + blue > 0

    # compute alpha value
    alpha = np.minimim(255, intensity * 50) * date_mask * confidence_mask * no_data_mask

    return alpha


def apply_filter(
    data: ndarray, start_date: str, end_date: str, confirmed_only: bool, **kwargs
) -> ndarray:
    """Decode using Pink alert color and filtering out unwanted alerts."""

    start_day = days_since_bog(datetime.strptime(start_date, "%Y-%m-%d").date())
    end_day = days_since_bog(datetime.strptime(end_date, "%Y-%m-%d").date())

    # Create an all pink image
    pink = np.ones(data.shape).astype("uint8") * [[228], [102], [153]]
    # Compute alpha value
    alpha = get_alpha(data, start_day, end_day, confirmed_only)

    # stack bands and return
    return np.vstack((pink, alpha))
