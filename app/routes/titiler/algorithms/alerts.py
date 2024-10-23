from collections import OrderedDict, namedtuple
from datetime import date

import numpy as np
from dateutil.relativedelta import relativedelta
from fastapi.logger import logger
from pydantic import Field
from rio_tiler.models import ImageData
from titiler.core.algorithm import BaseAlgorithm

from app.models.enumerators.titiler import AlertConfidence, RenderType

Colors: namedtuple = namedtuple("Colors", ["red", "green", "blue"])
AlertConfig: namedtuple = namedtuple("AlertConfig", ["confidence", "colors"])


class Alerts(BaseAlgorithm):
    """Decode Deforestation Alerts."""

    title: str = "Deforestation Alerts"
    description: str = "Decode and visualize alerts"

    conf_colors: OrderedDict = OrderedDict(
        {
            AlertConfidence.low: AlertConfig(
                confidence=2, colors=Colors(237, 164, 194)
            ),
            AlertConfidence.high: AlertConfig(
                confidence=3, colors=Colors(220, 102, 153)
            ),
            AlertConfidence.highest: AlertConfig(
                confidence=4, colors=Colors(201, 42, 109)
            ),
        }
    )

    record_start_date: str = "2014-12-31"

    today: date = date.today()

    # Parameters
    default_start_date: str = (today - relativedelta(days=180)).strftime("%Y-%m-%d")
    start_date: str = Field(
        default_start_date,
        description="start date of alert in YYYY-MM-DD format.",
    )

    default_end_date: str = today.strftime("%Y-%m-%d")
    end_date: str = Field(
        default_end_date, description="end date of alert in YYYY-MM-DD format."
    )

    alert_confidence: AlertConfidence = Field(
        AlertConfidence.low, description="Alert confidence"
    )

    render_type: RenderType = Field(
        RenderType.true_color,
        description="Render true color or encoded pixels",
    )

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
        start_mask = self.alert_date >= (
            np.datetime64(self.start_date) - np.datetime64(self.record_start_date)
        )
        end_mask = self.alert_date <= (
            np.datetime64(self.end_date) - np.datetime64(self.record_start_date)
        )

        confidence_mask = (
            self.data_alert_confidence
            >= self.conf_colors[self.alert_confidence].confidence
        )
        mask = ~self.no_data * start_mask * end_mask * confidence_mask

        return mask

    def create_true_color_rgb(self):
        """Map alert confidence levels to RGB values for visualization.

        Returns:
            np.ndarray: A 3D array with RGB channels.
        """
        r, g, b = self._rgb_zeros_array()

        for properties in self.conf_colors.values():
            confidence = properties.confidence
            colors = properties.colors

            r[self.data_alert_confidence >= confidence] = colors.red
            g[self.data_alert_confidence >= confidence] = colors.green
            b[self.data_alert_confidence >= confidence] = colors.blue

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
        """Generate the alpha channel for encoded alerts. The default
        implementation sets pixel visibility based on date/confidence filters
        and intensity input. Can be overridden for specific alert types.

        Returns:
            np.ndarray: An array representing the alpha channel.
        """
        logger.info(
            """Encoded alpha not provided, returning alpha
                    from input layer and date/confidence mask."""
        )
        return self.create_true_color_alpha()

    def _rgb_zeros_array(self):
        r = np.zeros_like(self.data_alert_confidence, dtype=np.uint8)
        g = np.zeros_like(self.data_alert_confidence, dtype=np.uint8)
        b = np.zeros_like(self.data_alert_confidence, dtype=np.uint8)

        return r, g, b
