from collections import OrderedDict, namedtuple
from typing import Optional, Callable

import numpy as np
from fastapi.logger import logger
from rio_tiler.models import ImageData
from titiler.core.algorithm import BaseAlgorithm

from app.models.enumerators.titiler import RenderType

class TreeCoverLoss(BaseAlgorithm):

    title: str = "Tree Cover Loss"
    description: str = "Decode and visualize tree cover loss"

    start_year: int = 1
    end_year: int  = 23
    render_type: RenderType = RenderType.true_color
    zoom: int = 12

    # metadata
    input_nbands: int = 2
    output_nbands: int = 4
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:

        # Read data
        lossyear_data = img.data[0]
        self.intensity = img.data[1]
        self.no_data = img.array.mask[0]

        self.mask = self.create_mask(lossyear_data)

        rgb = self.create_true_color_rgb(lossyear_data)
        alpha = self.create_true_color_alpha()
        data = np.vstack([rgb, alpha[np.newaxis, ...]]).astype(self.output_dtype)
        data = np.ma.MaskedArray(data, mask=False)
        data = np.ma.MaskedArray(data, mask=False)

        #if self.render_type == RenderType.encoded:
        #    return self.create_encoded_rgb()
        #    alpha = self.create_encoded_alpha(self.intensity)
        #else:   # true color
        #return self.create_true_color_rgb(lossyear_data)
        #    alpha = self.create_true_color_alpha(self.intensity)
        
        return ImageData(data, assets=img.assets, crs=img.crs, bounds=img.bounds)

    def create_mask(self, lossyear_data):
        mask = ~self.no_data

        if self.start_year:
            start_mask = lossyear_data >= self.start_year
            mask &= start_mask

        if self.end_year:
            end_mask = lossyear_data <= self.end_year
            mask &= end_mask

        return mask

    #def create_encoded_rgb(self):
    #    r, g, b = self._rgb_zeros_array()
        
    def create_encoded_alpha(self):
        pass
    
    def create_true_color_rgb(self, lossyear_data):
        scale_pow = self.scale_intensity(self.zoom)
        scaled_intensity = scale_pow(self.intensity).astype("uint8")

        r = np.full(lossyear_data.shape, 228, dtype="float32")
        g = (
            np.ones(lossyear_data.shape, dtype="float32") * 102
            + (72 - self.zoom) 
            - (scaled_intensity * (3 / max(self.zoom, 1)))
        )
        b = (
            np.ones(lossyear_data.shape, dtype="float32") * 153
            + (33 - self.zoom) 
            - (self.intensity / max(self.zoom, 1))
        )

        g = np.clip(g, 0, 255).astype("uint8")
        b = np.clip(b, 0, 255).astype("uint8")

        return np.stack([r.astype("uint8"), g, b], axis=0)

    def create_true_color_alpha(self):
        scale_pow = self.scale_intensity(self.zoom)
        scaled_intensity = scale_pow(self.intensity).astype("uint8")

        alpha = (scaled_intensity if self.zoom < 13 else self.intensity) * self.mask
        return np.clip(alpha, 0, 255).astype("uint8")
    
    @staticmethod
    def scale_intensity(zoom) -> Callable:
        """Power scale function for intensity scaling."""
        exp = 0.3 + ((zoom - 3) / 20) if zoom < 11 else 1
        domain = (0, 255)
        scale_range = (0, 255)
        m = scale_range[1] / domain[1] ** exp
        b = scale_range[0]

        def scale_pow(x: np.ndarray) -> np.ndarray:
            return m * x**exp + b

        return scale_pow