import numpy as np
from rio_tiler.models import ImageData

from app.utils.rasters import sum_tiles


def tile(values, mask) -> ImageData:
    return ImageData(
        np.ma.MaskedArray(np.array([values], dtype="float32"), mask=np.array([mask]))
    )


def test_nodata_counts_as_zero_unless_every_raster_lacks_data():
    """Masked and NaN both mean nodata; the rasters declare NaN but rarely mask."""
    combined = sum_tiles(
        [
            tile([1, 2, np.nan, 0], [False, False, False, True]),
            tile([10, 0, 3, 0], [False, True, False, True]),
        ]
    )

    assert combined.data[0].tolist() == [[11, 2, 3, 0]]
    assert combined.array.mask[0].tolist() == [[False, False, False, True]]


def test_a_single_raster_is_left_alone():
    only = tile([1, 2, 0], [False, False, True])

    assert sum_tiles([only]) is only
