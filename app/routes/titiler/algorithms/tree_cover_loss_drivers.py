from collections import OrderedDict, namedtuple
from typing import Optional

import numpy as np
from pydantic import ConfigDict
from rio_tiler.models import ImageData
from titiler.core.algorithm import BaseAlgorithm

Colors: namedtuple = namedtuple("Colors", ["red", "green", "blue"])


class TreeCoverLossDrivers(BaseAlgorithm):
    """Visualize drivers of tree cover loss"""

    title: str = "Drivers of tree cover loss"
    description: str = "Visualize drivers of tree cover loss"

    model_config = ConfigDict(arbitrary_types_allowed=True)
    conf_colors: OrderedDict[int, tuple] = OrderedDict(
        {
            1: Colors(227, 157, 41),   # Permanent agriculture
            2: Colors(229, 128, 116),  # Hard commodities
            3: Colors(233, 215, 0),    # Shifting cultivation
            4: Colors(81, 164, 78),    # Forest management
            5: Colors(137, 81, 40),    # Wildfires
            6: Colors(163, 84, 160),   # Settlements and infrastructure
            7: Colors(58, 32, 154),    # Other natural disturbances
        }
    )

    # Value of None for the *_data fields means the tile didn't exist (tile was all
    # no_data).
    tree_cover_density_mask: Optional[int] = None
    tree_cover_density_data: Optional[ImageData] = None

    # metadata
    input_nbands: int = 2
    output_nbands: int = 4
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:

        self.driver = img.data[0]
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

        if self.tree_cover_density_mask:
            if self.tree_cover_density_data:
                mask *= (
                    self.tree_cover_density_data.array[0, :, :]
                    >= self.tree_cover_density_mask
                )
            else:
                # There was a full no-data tile for tcd, so we should mask
                # out everything on the base raster.
                mask = np.zeros_like(mask)

        return mask

    def create_true_color_rgb(self):
        r, g, b = self._rgb_zeros_array()

        for k, colors in self.conf_colors.items():
            r[self.driver == k] = colors.red
            g[self.driver == k] = colors.green
            b[self.driver == k] = colors.blue

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
        r = np.zeros_like(self.driver, dtype=np.uint8)
        g = np.zeros_like(self.driver, dtype=np.uint8)
        b = np.zeros_like(self.driver, dtype=np.uint8)

        return r, g, b
