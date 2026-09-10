"""Combining raster tiles that are read separately."""

from typing import List

import numpy as np
from rio_tiler.models import ImageData


def sum_tiles(images: List[ImageData]) -> ImageData:
    """Sum single-band tiles, treating nodata as zero.

    A pixel is nodata in the result only where every input is nodata. These
    rasters declare NaN as their nodata, so NaN counts as nodata whether or not
    the reader masked it.
    """

    if len(images) == 1:
        return images[0]

    arrays = [image.array[0] for image in images]
    missing = [
        np.ma.getmaskarray(array) | ~np.isfinite(np.ma.filled(array, np.nan))
        for array in arrays
    ]

    total = sum(
        np.where(nodata, 0, np.ma.filled(array, 0))
        for array, nodata in zip(arrays, missing)
    )
    mask = np.logical_and.reduce(missing)

    return ImageData(
        np.ma.MaskedArray(total[np.newaxis, ...], mask=mask[np.newaxis, ...]),
        crs=images[0].crs,
        bounds=images[0].bounds,
    )
