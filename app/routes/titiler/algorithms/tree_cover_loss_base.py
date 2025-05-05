from abc import ABC, abstractmethod
from typing import Callable, Optional

import numpy as np
from pydantic import ConfigDict
from rio_tiler.models import ImageData
from titiler.core.algorithm import BaseAlgorithm

from app.models.enumerators.titiler import RenderType


class TreeCoverLossBase(BaseAlgorithm, ABC):

    title: str = "Tree Cover Loss"
    description: str = "Decode and visualize tree cover loss"

    model_config = ConfigDict(arbitrary_types_allowed=True)

    start_date: Optional[int] = 2001
    end_year: Optional[int] = 2024
    render_type: RenderType = RenderType.true_color
    zoom: int = 12
    tree_cover_density_threshold: Optional[int] = None
    tree_cover_density_data: Optional[ImageData] = None

    # metadata
    input_nbands: int = 2
    output_nbands: int = 4
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:
        # Read data
        self.tree_cover_loss_data = img.data[0]
        self.intensity = img.data[1]
        self.no_data = img.array.mask[0]

        # Mask by lossyear and tree cover density filters
        self.mask = self.create_mask()

        # Create encoded or true color RGB and alpha arrays
        if self.render_type == RenderType.encoded:
            rgb = self.create_encoded_rgb()
            alpha = self.create_encoded_alpha()
        else:  # true color
            rgb = self.create_true_color_rgb()
            alpha = self.create_true_color_alpha()

        # Stack RGB and alpha channels
        data = np.vstack([rgb, alpha[np.newaxis, ...]]).astype(self.output_dtype)
        data = np.ma.MaskedArray(data, mask=False)

        return ImageData(data, assets=img.assets, crs=img.crs, bounds=img.bounds)

    def create_mask(self):
        mask = ~self.no_data

        # TCL goes from 2001 to 2024 by default, only filter if start_year or end_year is specified
        if self.start_year != 2001:
            start_mask = self.tree_cover_loss_data >= (self.start_year - 2000)
            mask &= start_mask

        if self.end_year != 2024:
            end_mask = self.tree_cover_loss_data <= (self.end_year - 2000)
            mask &= end_mask

        return mask

    def create_encoded_rgb(self):
        # Red = intensity
        r = np.clip(self.intensity, 0, 255).astype("uint8")

        # Green = 0
        g = np.zeros_like(r, dtype="uint8")

        # Blue = year of loss (1–24)
        b = np.where(self.mask, self.tree_cover_loss_data, 0).astype("uint8")

        return np.stack([r, g, b], axis=0)

    def create_encoded_alpha(self):
        # Alpha = 255 where intensity > 0 and mask is True
        alpha = np.where((self.intensity > 0) & self.mask, 255, 0).astype("uint8")

        return alpha

    @abstractmethod
    def create_true_color_rgb(self):
        pass

    def create_true_color_alpha(self):
        # Scale intensity if zoom level < 11, otherwise use original intensity
        if self.zoom < 11:
            scale_pow = self.scale_intensity(self.zoom)
            scaled_intensity = scale_pow(self.intensity).astype("uint8")
        else:
            scaled_intensity = self.intensity.astype("uint8")

        alpha = (scaled_intensity if self.zoom < 13 else self.intensity) * self.mask
        return np.clip(alpha, 0, 255).astype("uint8")

    @staticmethod
    def scale_intensity(zoom) -> Callable:
        """Returns callable that applies power scaling to an array of intensity
        values based on the given zoom level.

        Adapted from: https://github.com/wri/gfw/blob/develop/providers/datasets-provider/config.js#L28
        """

        # Exponent for the power scaling function (only when below raw data resolution of zoom 12)
        exp = 0.3 + ((zoom - 3) / 20) if zoom < 11 else 1

        # Min/max of input intensity values
        domain = (0, 255)

        # Min/max of scaled output intensity values
        scale_range = (0, 255)

        # Scaling factor that ensures the scaled intensity value is below the max value
        scaling_factor = scale_range[1] / domain[1] ** exp

        # Scaling offset based on min of input intensity value
        b = scale_range[0]

        # Apply the power scaling function to an array of intensity values
        def scale_pow(x: np.ndarray) -> np.ndarray:
            return scaling_factor * x**exp + b

        return scale_pow
