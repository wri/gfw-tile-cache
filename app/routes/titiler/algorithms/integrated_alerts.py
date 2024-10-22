from collections import OrderedDict

from app.models.enumerators.alerts_confidence import AlertConfidence

from .alerts import AlertConfig, Alerts, Colors


class IntegratedAlerts(Alerts):
    title: str = "Integrated Deforestation Alerts"
    description: str = "Decode and visualize deforestation alerts"

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
