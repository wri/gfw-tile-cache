from collections import OrderedDict, namedtuple
from datetime import date

import numpy as np
from dateutil.relativedelta import relativedelta
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
        """Decode deforestation and land disturbance alert raster data to
        RGBA."""
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
        r, g, b = self._rgb_zeros_array()

        for properties in self.conf_colors.values():
            confidence = properties.confidence
            colors = properties.colors

            r[self.data_alert_confidence >= confidence] = colors.red
            g[self.data_alert_confidence >= confidence] = colors.green
            b[self.data_alert_confidence >= confidence] = colors.blue

        return np.stack([r, g, b], axis=0)

    def create_encoded_rgb(self):
        r, g, b = self._rgb_zeros_array()
        r = self.alert_date // 255
        g = self.alert_date % 255
        b = (self.data_alert_confidence // 3 + 1) * 100 + self.intensity

        return np.stack([r, g, b], axis=0)

    def create_true_color_alpha(self):
        alpha = np.where(self.mask, self.intensity * 150, 0)
        return np.minimum(255, alpha)

    def create_encoded_alpha(self):
        """To be overridden by alert types that implement it."""
        return self.create_true_color_alpha()

    def _rgb_zeros_array(self):
        r = np.zeros_like(self.data_alert_confidence, dtype=np.uint8)
        g = np.zeros_like(self.data_alert_confidence, dtype=np.uint8)
        b = np.zeros_like(self.data_alert_confidence, dtype=np.uint8)

        return r, g, b
