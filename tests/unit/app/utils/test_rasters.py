import numpy as np
from rio_tiler.models import ImageData

from app.utils.rasters import sum_tiles


def tile(values, mask) -> ImageData:
    return ImageData(
        np.ma.MaskedArray(np.array([values], dtype="float32"), mask=np.array([mask]))
    )


def test_masked_pixels_count_as_zero_unless_every_raster_is_masked():
    combined = sum_tiles(
        [
            tile([1, 2, 0], [False, False, True]),
            tile([10, 0, 0], [False, True, True]),
        ]
    )

    assert combined.data[0].tolist() == [[11, 2, 0]]
    assert combined.array.mask[0].tolist() == [[False, False, True]]


def test_a_single_raster_is_left_alone():
    only = tile([1, 2, 0], [False, False, True])

    assert sum_tiles([only]) is only
