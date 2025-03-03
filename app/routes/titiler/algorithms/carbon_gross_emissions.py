from collections import OrderedDict, namedtuple
from typing import Optional

import numpy as np
from pydantic import ConfigDict
from rio_tiler.models import ImageData
from titiler.core.algorithm import BaseAlgorithm

Colors: namedtuple = namedtuple("Colors", ["red", "green", "blue"])


class CarbonGrossEmissions(BaseAlgorithm):
    """Visualize carbon gross emissions"""

    title: str = "Carbon gross emissions"
    description: str = "Visualize carbon gross emissions"

    model_config = ConfigDict(arbitrary_types_allowed=True)
    conf_colors: OrderedDict[float, tuple] = OrderedDict(
        {
            0.0: Colors(254, 246, 249),
            1.0: Colors(245, 237, 242),
            6.0: Colors(236, 228, 236),
            14.0: Colors(227, 220, 231),
            24.0: Colors(217, 210, 228),
            39.0: Colors(209, 201, 227),
            56.0: Colors(202, 192, 228),
            76.0: Colors(194, 183, 229),
            99.0: Colors(187, 173, 231),
            126.0: Colors(182, 164, 232),
            156.0: Colors(177, 154, 231),
            188.0: Colors(173, 145, 229),
            224.0: Colors(169, 134, 225),
            263.0: Colors(165, 126, 218),
            305.0: Colors(162, 117, 211),
            351.0: Colors(158, 109, 202),
            399.0: Colors(153, 100, 191),
            451.0: Colors(149, 93, 181),
            505.0: Colors(144, 86, 171),
            563.0: Colors(140, 79, 160),
            624.0: Colors(134, 71, 148),
            688.0: Colors(128, 65, 138),
            755.0: Colors(123, 59, 127),
            825.0: Colors(116, 53, 117),
            899.0: Colors(109, 47, 105),
            975.0: Colors(102, 42, 95),
            1055.0: Colors(95, 37, 85),
            1137.0: Colors(88, 32, 76),
            1223.0: Colors(80, 26, 66),
            1312.0: Colors(72, 21, 57),
            1404.0: Colors(64, 15, 50),
            1500.0: Colors(57, 8, 42)
        }
    )

    tree_cover_density_mask: Optional[int] = None
    tree_cover_density_data: Optional[ImageData] = None

    # metadata
    input_nbands: int = 2
    output_nbands: int = 4
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:

        self.emissions = img.data[0]
        self.intensity = img.data[1]
        self.no_data = img.array.mask[0]

        self.mask = self.create_mask()

        rgb = self.create_true_color_rgb()
        alpha = self.create_true_color_alpha()

        data = np.vstack([rgb, alpha[np.newaxis, ...]]).astype(self.output_dtype)
        data = np.ma.MaskedArray(data, mask=False)

        return ImageData(data, assets=img.assets, crs=img.crs, bounds=img.bounds)

    def create_mask(self):
        mask = ~self.no_data

        if self.tree_cover_density_mask:
            mask *= (
                self.tree_cover_density_data.array[0, :, :]
                >= self.tree_cover_density_mask
            )

        return mask

    def create_true_color_rgb(self):
        r, g, b = self._rgb_zeros_array()

        for k, colors in self.conf_colors.items():
            r[self.emissions >= k] = colors.red
            g[self.emissions >= k] = colors.green
            b[self.emissions >= k] = colors.blue

        return np.stack([r, g, b], axis=0)

    def create_true_color_alpha(self):
        """Set the transparency (alpha) channel based on intensity input. The
        intensity multiplier is used to control how isolated pixels fade out at low
        zoom levels, matching the rendering behavior in Flagship.

        Returns:
            np.ndarray: Array representing the alpha (transparency) channel, where pixel
            visibility is adjusted by intensity.

        """
        alpha = np.where(self.mask, self.intensity * 150, 0)
        return np.minimum(255, alpha)

    def _rgb_zeros_array(self):
        r = np.zeros_like(self.emissions, dtype=np.uint8)
        g = np.zeros_like(self.emissions, dtype=np.uint8)
        b = np.zeros_like(self.emissions, dtype=np.uint8)

        return r, g, b
