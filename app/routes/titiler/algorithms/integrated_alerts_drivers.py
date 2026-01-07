from collections import OrderedDict, namedtuple
from typing import Optional

import numpy as np
from fastapi import HTTPException, status
from pydantic import ConfigDict
from rio_tiler.models import ImageData
from titiler.core.algorithm import BaseAlgorithm

from app.models.enumerators.titiler import IntegratedAlertConfidence, RenderType

Colors: namedtuple = namedtuple("Colors", ["red", "green", "blue"])


class IntegratedAlertsDrivers(BaseAlgorithm):
    """Decode Deforestation Alerts."""

    title: str = "Deforestation Alerts Drivers"
    description: str = "Decode and visualize alerts"
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    conf_colors: OrderedDict[int, tuple] = OrderedDict(
        {
            1: Colors(255, 217, 102),   # Small-scale agriculture 
            2: Colors(255, 140, 66),    # Small-scale agriculture with fire 
            3: Colors(244, 177, 131),   # Large-scale agriculture 
            4: Colors(206, 77, 30),     # Large-scale agriculture with fire
            5: Colors(255, 0, 0),       # Road development 
            6: Colors(0, 176, 240),     # Selective logging & skidding 
            7: Colors(188, 157, 217),   # Mining 
            8: Colors(70, 153, 144),    # Flooding
            9: Colors(137, 81, 40),     # Wildfire 
            10: Colors(58, 31, 154),    # Other natural disturbance
            11: Colors(237, 164, 195),  # Unconfident / unlabeled 
        }
    )

    conf_mapping: OrderedDict = OrderedDict(
        {
            IntegratedAlertConfidence.low: 2,
            IntegratedAlertConfidence.high: 3,
            IntegratedAlertConfidence.highest: 4,
        }
    )

    record_start_date: str = "2014-12-31"

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    alert_confidence: Optional[str] = None
    alert_drivers: Optional[ImageData] = None
    render_type: RenderType = RenderType.true_color

    # metadata
    input_nbands: int = 2
    output_nbands: int = 4
    output_dtype: str = "uint8"

    def __call__(self, img: ImageData) -> ImageData:
        """Process the input image and decode deforestation or land disturbance
        alert raster data into RGBA format.

        Args:
            img (ImageData): Input image data with alert date/confidence and intensity
            (zoom-level visibility) layers.

        Returns:
            ImageData: Processed image with RGBA channels either with true colors ready for
            visualization or encoding date and confidence for front-end processing.
        """
        date_conf_data = img.data[0]

        self.intensity = img.data[1]
        self.no_data = img.array.mask[0]
        self.data_alert_confidence = date_conf_data // 10000
        self.alert_date = date_conf_data % 10000

        self.mask = self.create_mask()

        if self.render_type == RenderType.true_color:
            rgb = self.create_true_color_rgb()
            alpha = self.create_true_color_alpha()
        else:  # encoded
            rgb = self.create_encoded_rgb()
            alpha = self.create_encoded_alpha()

        data = np.vstack([rgb, alpha[np.newaxis, ...]]).astype(self.output_dtype)
        data = np.ma.MaskedArray(data, mask=False)

        return ImageData(data, assets=img.assets, crs=img.crs, bounds=img.bounds)

    def create_mask(self):
        """Generate a mask for pixel visibility based on date and confidence
        filters, and no data values.

        Returns:
            np.ndarray: A mask array pixels with no alert or alerts not meeting filter
            condition are masked.
        """

        mask = ~self.no_data * (self.alert_drivers > 0)

        if self.alert_confidence:
            confidence_mask = (
                self.data_alert_confidence
                >= self.conf_mapping[self.alert_confidence]
            )
            mask *= confidence_mask

        if self.start_date:
            start_mask = self.alert_date >= (
                np.datetime64(self.start_date) - np.datetime64(self.record_start_date)
            )
            mask *= start_mask

        if self.end_date:
            end_mask = self.alert_date <= (
                np.datetime64(self.end_date) - np.datetime64(self.record_start_date)
            )
            mask *= end_mask

        return mask

    def create_true_color_rgb(self):
        """Map alert driver to RGB values for visualization.

        Returns:
            np.ndarray: A 3D array with RGB channels.
        """
        r, g, b = self._rgb_zeros_array()

        for k, colors in self.conf_colors.items():
            r[self.alert_drivers == k] = colors.red
            g[self.alert_drivers == k] = colors.green
            b[self.alert_drivers == k] = colors.blue

        return np.stack([r, g, b], axis=0)

    def create_encoded_rgb(self):
        """Encode the alert date and confidence into the RGB channels, allowing
        interactive date filtering and color control on Flagship.

        Returns:
            np.ndarray: A 3D array with encoded RGB values.
        """
        r, g, b = self._rgb_zeros_array()
        r = self.alert_date // 255
        g = self.alert_date % 255
        b = (self.data_alert_confidence // 3 + 1) * 100 + self.intensity

        return np.stack([r, g, b], axis=0)

    def create_true_color_alpha(self):
        """Set the transparency (alpha) channel for alert pixels based on date,
        confidence filters, and intensity input. The intensity multiplier is
        used to control how isolated alerts fade out at low zoom levels,
        matching the rendering behavior in Flagship.

        Returns:
            np.ndarray: Array representing the alpha (transparency) channel, where pixel
            visibility is adjusted by intensity.
        """
        alpha = np.where(self.mask, self.intensity * 150, 0)
        return np.minimum(255, alpha)

    def create_encoded_alpha(self):
        """Encode driver class in alpha"""
        return self.alert_drivers

    def _rgb_zeros_array(self):
        r = np.zeros_like(self.data_alert_confidence, dtype=np.uint8)
        g = np.zeros_like(self.data_alert_confidence, dtype=np.uint8)
        b = np.zeros_like(self.data_alert_confidence, dtype=np.uint8)

        return r, g, b
