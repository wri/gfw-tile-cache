from collections import OrderedDict, namedtuple

import numpy as np

from app.models.enumerators.titiler import DeforestationAlertConfidence

from .alerts import Alerts


class IntegratedAlerts(Alerts):
    title: str = "Integrated Deforestation Alerts"
    description: str = "Decode and visualize deforestation alerts"

    Colors: namedtuple = namedtuple("Colors", ["red", "green", "blue"])
    DeforestationAlert: namedtuple = namedtuple(
        "DeforestationAlert", ["confidence", "colors"]
    )

    conf_colors: OrderedDict = OrderedDict(
        {
            DeforestationAlertConfidence.low: DeforestationAlert(
                confidence=2, colors=Colors(237, 164, 194)
            ),
            DeforestationAlertConfidence.high: DeforestationAlert(
                confidence=3, colors=Colors(220, 102, 153)
            ),
            DeforestationAlertConfidence.highest: DeforestationAlert(
                confidence=4, colors=Colors(201, 42, 109)
            ),
        }
    )

    record_start_date: str = "2014-12-31"

    def create_encoded_alpha(self):
        # Using the same method used in Data API to provide the confidence encoding
        # GFW Flagship expects in the alpha channel where the three alerts' confidence
        # levels are packed in the alpha channel with 2 bits for each alert (starting at 3rd).
        # The values used are follows (bit layout and decimal value):
        # low confidence
        # GLADL  GLADS2  RADD  Unused
        #   00     00     01     00     = 4 (decimal)
        # high confidence
        # GLADL  GLADS2  RADD  Unused
        #   00     00     10     00     = 8 (decimal)
        # highest confidence
        # GLADL  GLADS2  RADD  Unused
        #   00     01     10     00     = 24 (decimal)
        #  More explanation: https://github.com/wri/gfw-data-api/blob/master/app/tasks/raster_tile_cache_assets/symbology.py#L92

        alpha = np.zeros_like(self.data_alert_confidence, dtype=np.uint8)

        alpha[self.data_alert_confidence == self.conf_colors["low"].confidence] = 4
        alpha[self.data_alert_confidence == self.conf_colors["high"].confidence] = 8
        alpha[self.data_alert_confidence == self.conf_colors["highest"].confidence] = 24

        return alpha
