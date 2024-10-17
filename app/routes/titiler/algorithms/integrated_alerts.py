from collections import OrderedDict, namedtuple
from .alerts import Alerts

from app.models.enumerators.alerts_confidence import DeforestationAlertConfidence


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
