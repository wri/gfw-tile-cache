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
    tree_cover_loss_intensity_data: Optional[ImageData] = None
    zoom: int = 12

    # metadata
    input_nbands: int = 2
    output_nbands: int = 4
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:

        self.driver = img.data[0]

        if self.tree_cover_loss_intensity_data is not None:
            self.intensity = self.tree_cover_loss_intensity_data.data[0]
        else:
            # if intensity is defined for area, just set everything to 255 to ignore opacity
            self.intensity = np.ones_like(self.driver) * 255

        # self.mask should be True for pixels where we have valid data which is not
        # filtered out.
        self.mask = self.create_mask()

        rgb = self.create_true_color_rgb()
        alpha = self.create_true_color_alpha()

        data = np.vstack([rgb, alpha[np.newaxis, ...]]).astype(self.output_dtype)
        data = np.ma.MaskedArray(data, mask=False)

        return ImageData(data, assets=img.assets, crs=img.crs, bounds=img.bounds)

    def create_mask(self):
        # it seems to not be creating the mask correctly for non-zero NoData, so just
        # directly applying the NoData
        mask = ~((self.driver == 0) | (self.driver == 255))
        return mask

    def create_true_color_rgb(self):
        r, g, b = self._rgb_zeros_array()

        for k, colors in self.conf_colors.items():
            r[self.driver == k] = colors.red
            g[self.driver == k] = colors.green
            b[self.driver == k] = colors.blue

        return np.stack([r, g, b], axis=0)

    def _rgb_zeros_array(self):
        r = np.zeros_like(self.driver, dtype=np.uint8)
        g = np.zeros_like(self.driver, dtype=np.uint8)
        b = np.zeros_like(self.driver, dtype=np.uint8)

        return r, g, b
    
    def create_true_color_alpha(self):
        # Scale intensity if zoom level < 11, otherwise use original intensity
        if self.zoom < 11:
            scale_pow = self.scale_intensity(self.zoom)
            scaled_intensity = scale_pow(self.intensity).astype("uint8")
        else:
            scaled_intensity = self.intensity.astype("uint8")

        alpha = scaled_intensity * self.mask
        return np.clip(alpha, 0, 255).astype("uint8")
    
    @staticmethod
    def scale_intensity(zoom):
        """
        Returns callable that applies power scaling to an array of
        intensity values based on the given zoom level.

        Adapted from: https://github.com/wri/gfw/blob/develop/providers/datasets-provider/config.js#L28
        """
        
        # Exponent for the power scaling function (only when below raw data resolution of zoom 11)
        exp = 0.3 + ((zoom - 3) / 20) if zoom < 11 else 1
        
        # Min/max of input intensity values
        domain = (0, 255)

        # Min/max of scaled output intensity values
        scale_range = (0, 255)

        # Scaling factor that ensures the scaled intensity value is below the max value
        scaling_factor = scale_range[1] / (domain[1] ** exp)

        # Scaling offset based on min of input intensity value
        b = scale_range[0]

        # Apply the power scaling function to an array of intensity values
        def scale_pow(x: np.ndarray) -> np.ndarray:
            return scaling_factor * x**exp + b

        return scale_pow