from typing import Callable

from numpy import ndarray, np


def scale_intensity(zoom: int) -> Callable:
    """
    Simplified implementing of d3.scalePow()
    Assuming that both domain and range always start with 0
    """
    exp = 0.3 + ((zoom - 3) / 20) if zoom < 11 else 1
    domain = (0, 256)
    range = (0, 256)
    m = range[1] / domain[1] ** exp
    b = range[0]

    def scale_pow(x: ndarray) -> ndarray:
        return m * x ** exp + b

    return scale_pow


def apply_filter(
    data: ndarray, z: str, start_year: str = "2000", end_year: str = "3000", **kwargs
) -> ndarray:

    zoom = int(z)

    intensity, _, year = data
    scale_pow: Callable = scale_intensity(zoom)
    scaled_intensity: ndarray = scale_pow(intensity).astype("uint8")

    start_year_mask: ndarray = year >= (int(start_year) - 2000)
    end_year_mask: ndarray = year <= (int(end_year) - 2000)

    red: ndarray = np.ones(intensity.shape).astype("uint8") * 228
    green: ndarray = (
        np.ones(intensity.shape) * 102 + (72 - zoom) - (3 * scaled_intensity / zoom)
    ).astype("uint8")
    blue: ndarray = (
        np.ones(intensity.shape) * 153 + (33 - zoom) - (intensity / zoom)
    ).astype("uint8")
    alpha: ndarray = (
        (scaled_intensity if zoom < 13 else intensity) * start_year_mask * end_year_mask
    ).astype("uint8")

    return np.vstack((red, green, blue, alpha))
