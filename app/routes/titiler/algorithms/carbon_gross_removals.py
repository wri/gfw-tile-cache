from collections import OrderedDict, namedtuple
from typing import Optional

import numpy as np
from pydantic import ConfigDict
from rio_tiler.models import ImageData
from titiler.core.algorithm import BaseAlgorithm

Colors: namedtuple = namedtuple("Colors", ["red", "green", "blue"])


class CarbonGrossRemovals(BaseAlgorithm):
    """Visualize carbon gross removals."""

    title: str = "Carbon gross removals"
    description: str = "Visualize carbon gross removals"

    model_config = ConfigDict(arbitrary_types_allowed=True)
    conf_colors: OrderedDict[float, tuple] = OrderedDict(
        {
            0.0: Colors(255, 246, 244),
            1.0: Colors(244, 238, 232),
            6.0: Colors(233, 231, 221),
            14.0: Colors(221, 224, 209),
            24.0: Colors(209, 216, 197),
            39.0: Colors(197, 210, 187),
            56.0: Colors(185, 204, 178),
            76.0: Colors(172, 198, 169),
            99.0: Colors(158, 192, 159),
            126.0: Colors(145, 186, 152),
            156.0: Colors(131, 181, 146),
            188.0: Colors(116, 175, 141),
            224.0: Colors(99, 169, 136),
            263.0: Colors(84, 164, 132),
            305.0: Colors(67, 158, 130),
            351.0: Colors(52, 152, 128),
            399.0: Colors(36, 144, 127),
            451.0: Colors(25, 137, 125),
            505.0: Colors(18, 130, 123),
            563.0: Colors(17, 122, 120),
            624.0: Colors(19, 114, 117),
            688.0: Colors(22, 106, 113),
            755.0: Colors(25, 99, 109),
            825.0: Colors(26, 91, 105),
            899.0: Colors(28, 83, 100),
            975.0: Colors(28, 76, 95),
            1055.0: Colors(28, 68, 91),
            1137.0: Colors(27, 61, 86),
            1223.0: Colors(26, 53, 81),
            1312.0: Colors(24, 45, 76),
            1404.0: Colors(23, 37, 72),
            1500.0: Colors(21, 29, 68),
        }
    )

    # Value of None for the *_data fields means the tile didn't exist (tile was all
    # no_data).
    tree_cover_density_mask: Optional[int] = None
    tree_cover_density_data: Optional[ImageData] = None

    tree_cover_gain_from_height_mask: Optional[int] = None
    tree_cover_gain_from_height_data: Optional[ImageData] = None

    mangrove_stock_2000_mask: Optional[float] = None
    mangrove_stock_2000_data: Optional[ImageData] = None

    # metadata
    input_nbands: int = 2
    output_nbands: int = 4
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:

        self.removals = img.data[0]
        self.intensity = img.data[1]
        self.no_data = img.array.mask[0]

        # self.mask should be True for pixels where we have valid data which is not
        # filtered out.
        self.mask = self.create_mask()

        rgb = self.create_true_color_rgb()
        alpha = self.create_true_color_alpha()

        data = np.vstack([rgb, alpha[np.newaxis, ...]]).astype(self.output_dtype)
        data = np.ma.MaskedArray(data, mask=False)

        return ImageData(data, assets=img.assets, crs=img.crs, bounds=img.bounds)

    def create_mask(self):
        mask = ~self.no_data

        # Include a pixel if it has minimum canopy density OR tree cover gain OR
        # mangroves. Since this is ORing and each condition can only possibly be true
        # with real data (not the no-data value), we just skip a condition if its
        # tile was non-existent (all no-data).
        #
        #  The masking out of areas with pre-2000 tree plantations must already be
        #  done in the input dataset.
        or_conditions = np.zeros_like(mask)
        if self.tree_cover_density_data:
            or_conditions = np.where(self.tree_cover_density_data.array[0, :, :]
                                     >= self.tree_cover_density_mask, True, or_conditions)
        if self.tree_cover_gain_from_height_data:
            or_conditions = np.where(self.tree_cover_gain_from_height_data.array[0, :, :]
                                     > self.tree_cover_gain_from_height_mask, True, or_conditions)
        if self.mangrove_stock_2000_data:
            or_conditions = np.where(self.mangrove_stock_2000_data.array[0, :, :]
                                     > self.mangrove_stock_2000_mask, True, or_conditions)
        mask *= or_conditions

        return mask

    def create_true_color_rgb(self):
        r, g, b = self._rgb_zeros_array()

        for k, colors in self.conf_colors.items():
            r[self.removals >= k] = colors.red
            g[self.removals >= k] = colors.green
            b[self.removals >= k] = colors.blue

        return np.stack([r, g, b], axis=0)

    def create_true_color_alpha(self):
        """Set the transparency (alpha) channel based on intensity input. The
        intensity multiplier is used to control how isolated pixels fade out at low
        zoom levels, matching the rendering behavior in Flagship.

        Returns:
            np.ndarray: Array representing the alpha (transparency) channel, where pixel
            visibility is adjusted by intensity.

        """
        alpha = np.where(self.mask, self.intensity, 0)
        return np.minimum(255, alpha)

    def _rgb_zeros_array(self):
        r = np.zeros_like(self.removals, dtype=np.uint8)
        g = np.zeros_like(self.removals, dtype=np.uint8)
        b = np.zeros_like(self.removals, dtype=np.uint8)

        return r, g, b
