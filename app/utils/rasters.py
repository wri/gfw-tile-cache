"""Combining raster tiles that are read separately."""

from typing import List

import numpy as np
from rio_tiler.models import ImageData


def sum_tiles(images: List[ImageData]) -> ImageData:
    """Sum single-band tiles, treating nodata as zero.

    A pixel is nodata in the result only where every input is nodata.
    """

    if len(images) == 1:
        return images[0]

    total = sum(np.ma.filled(image.array[0], 0) for image in images)
    mask = np.logical_and.reduce([image.array.mask[0] for image in images])

    return ImageData(
        np.ma.MaskedArray(total[np.newaxis, ...], mask=mask[np.newaxis, ...]),
        crs=images[0].crs,
        bounds=images[0].bounds,
    )
