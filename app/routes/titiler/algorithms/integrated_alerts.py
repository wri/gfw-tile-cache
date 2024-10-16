from collections import OrderedDict
from .alerts import Alerts

from app.models.enumerators.alerts_confidence import DeforestationAlertConfidence


class IntegratedAlerts(Alerts):
    title: str = "Integrated Deforestation Alerts"
    description: str = "Decode and visualize deforestation alerts"

    conf_colors: OrderedDict = OrderedDict(
        {
            DeforestationAlertConfidence.low: {
                "confidence": 2,
                "colors": (237, 164, 194),
            },
            DeforestationAlertConfidence.high: {
                "confidence": 3,
                "colors": (220, 102, 153),
            },
            DeforestationAlertConfidence.highest: {
                "confidence": 4,
                "colors": (201, 42, 109),
            },
        }
    )

    record_start_date: str = "2014-12-31"
