import numpy as np
from rio_tiler.models import ImageData

from app.routes.titiler.algorithms.lgms_flux import AgricultureEmissions, LulucfNetFlux


def render(algorithm, value: float, nodata: bool = False):
    image = ImageData(
        np.ma.MaskedArray(
            np.full((1, 2, 2), value, dtype="float32"), mask=np.full((1, 2, 2), nodata)
        )
    )
    tile = algorithm()(image).data
    return tuple(int(band[0][0]) for band in tile[:3]), int(tile[3].max())


def test_lulucf_treats_near_zero_flux_as_no_flux():
    assert render(LulucfNetFlux, 0.0005)[1] == 0
    assert render(LulucfNetFlux, 5.0)[1] == 255


def test_agriculture_hides_nodata_only():
    """Zero is a modelled value here, not an absence of one."""
    rgb, alpha = render(AgricultureEmissions, 0)

    assert alpha == 255
    assert rgb != (0, 0, 0), "a visible value must have a colour, not render black"
    assert render(AgricultureEmissions, 0, nodata=True)[1] == 0
