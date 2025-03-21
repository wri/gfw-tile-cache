from collections import OrderedDict, namedtuple
from typing import Optional

import numpy as np
from pydantic import ConfigDict
from rio_tiler.models import ImageData
from titiler.core.algorithm import BaseAlgorithm

Colors: namedtuple = namedtuple("Colors", ["red", "green", "blue"])


class CarbonNetFlux(BaseAlgorithm):
    """Visualize carbon next flux"""

    title: str = "Carbon net flux"
    description: str = "Visualize carbon net flux"

    model_config = ConfigDict(arbitrary_types_allowed=True)
    conf_colors: OrderedDict[float, tuple] = OrderedDict(
        {
            -1500.0: Colors(21, 29, 68),
            -1419.0: Colors(23, 36, 71),
            -1340.0: Colors(24, 44, 76),
            -1264.0: Colors(26, 51, 80),
            -1189.0: Colors(27, 58, 84),
            -1118.0: Colors(28, 66, 89),
            -1048.0: Colors(28, 72, 93),
            -980.0: Colors(28, 79, 98),
            -915.0: Colors(27, 87, 102),
            -852.0: Colors(26, 93, 106),
            -792.0: Colors(24, 101, 110),
            -733.0: Colors(21, 108, 114),
            -677.0: Colors(19, 115, 117),
            -623.0: Colors(17, 122, 120),
            -571.0: Colors(18, 130, 123),
            -522.0: Colors(23, 136, 125),
            -474.0: Colors(37, 145, 127),
            -429.0: Colors(52, 152, 128),
            -387.0: Colors(65, 157, 130),
            -346.0: Colors(82, 163, 132),
            -308.0: Colors(97, 169, 135),
            -272.0: Colors(111, 173, 139),
            -238.0: Colors(125, 179, 144),
            -206.0: Colors(139, 184, 150),
            -177.0: Colors(151, 189, 156),
            -150.0: Colors(164, 195, 163),
            -125.0: Colors(177, 200, 172),
            -103.0: Colors(188, 206, 180),
            -82.0: Colors(200, 212, 190),
            -64.0: Colors(211, 218, 200),
            -48.0: Colors(221, 224, 209),
            -35.0: Colors(233, 231, 221),

            35.0: Colors(236, 228, 236),
            48.0: Colors(227, 220, 231),
            64.0: Colors(220, 212, 229),
            82.0: Colors(211, 204, 227),
            103.0: Colors(204, 195, 227),
            125.0: Colors(197, 187, 228),
            150.0: Colors(190, 178, 230),
            177.0: Colors(185, 168, 232),
            206.0: Colors(180, 160, 232),
            238.0: Colors(176, 151, 231),
            272.0: Colors(172, 141, 228),
            308.0: Colors(168, 133, 224),
            346.0: Colors(165, 125, 217),
            387.0: Colors(161, 116, 210),
            429.0: Colors(158, 109, 202),
            474.0: Colors(154, 101, 192),
            522.0: Colors(148, 92, 180),
            571.0: Colors(144, 86, 171),
            623.0: Colors(140, 79, 160),
            677.0: Colors(134, 72, 150),
            733.0: Colors(130, 67, 140),
            792.0: Colors(124, 61, 130),
            852.0: Colors(118, 55, 119),
            915.0: Colors(112, 50, 110),
            980.0: Colors(106, 45, 100),
            1048.0: Colors(99, 39, 90),
            1118.0: Colors(92, 35, 82),
            1189.0: Colors(85, 30, 72),
            1264.0: Colors(78, 25, 64),
            1340.0: Colors(71, 20, 56),
            1419.0: Colors(63, 14, 49),
            1500.0: Colors(57, 8, 42),
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

        self.flux = img.data[0]
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
            r[self.flux >= k] = colors.red
            g[self.flux >= k] = colors.green
            b[self.flux >= k] = colors.blue

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
        r = np.zeros_like(self.flux, dtype=np.uint8)
        g = np.zeros_like(self.flux, dtype=np.uint8)
        b = np.zeros_like(self.flux, dtype=np.uint8)

        return r, g, b
