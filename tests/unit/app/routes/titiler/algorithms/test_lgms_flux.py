import numpy as np
from rio_tiler.models import ImageData

from app.routes.titiler.algorithms.lgms_flux import AgricultureEmissions, LulucfNetFlux


def render(algorithm, value: float):
    image = ImageData(
        np.ma.MaskedArray(np.full((1, 2, 2), value, dtype="float32"), mask=False)
    )
    tile = algorithm()(image).data
    return tuple(int(band[0][0]) for band in tile[:3]), int(tile[3].max())


def alpha_for(algorithm, value: float) -> int:
    return render(algorithm, value)[1]


def test_lulucf_treats_near_zero_flux_as_no_flux():
    assert alpha_for(LulucfNetFlux, 0.0005) == 0
    assert alpha_for(LulucfNetFlux, 5.0) == 255


def test_agriculture_shows_every_modelled_value():
    """Nearly a fifth of cropland cells fall below LULUCF's near-zero cutoff."""
    rgb, alpha = render(AgricultureEmissions, 0.0005)

    assert alpha == 255
    assert rgb != (0, 0, 0), "a visible value must have a colour, not render black"
    assert alpha_for(AgricultureEmissions, 0) == 0
