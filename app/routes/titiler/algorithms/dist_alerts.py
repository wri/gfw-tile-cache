from collections import OrderedDict
from typing import Optional

from pydantic import ConfigDict
from rio_tiler.models import ImageData

from app.models.enumerators.titiler import AlertConfidence

from .alerts import AlertConfig, Alerts, Colors


class DISTAlerts(Alerts):
    title: str = "Land Disturbance (DIST) Alerts"
    description: str = "Decode and visualize DIST alerts"

    model_config = ConfigDict(arbitrary_types_allowed=True)
    conf_colors: OrderedDict = OrderedDict(
        {
            AlertConfidence.low: AlertConfig(
                confidence=2, colors=Colors(237, 164, 194)
            ),
            AlertConfidence.high: AlertConfig(
                confidence=3, colors=Colors(220, 102, 153)
            ),
        }
    )

    record_start_date: str = "2020-12-31"

    tree_cover_density_mask: Optional[int] = None
    tree_cover_density_data: Optional[ImageData] = None

    tree_cover_height_mask: Optional[int] = None
    tree_cover_height_data: Optional[ImageData] = None

    # the highest loss year that is used to exclude alerts for
    # the purpose of showing only alerts in forests
    tree_cover_loss_mask: Optional[int] = None
    tree_cover_loss_data: Optional[ImageData] = None

    def create_mask(self):
        mask = super().create_mask()

        if self.tree_cover_density_mask:
            mask *= (
                self.tree_cover_density_data.array[0, :, :]
                >= self.tree_cover_density_mask
            )

        if self.tree_cover_height_mask:
            mask *= (
                self.tree_cover_height_data.array[0, :, :]
                >= self.tree_cover_height_mask
            )

        if self.tree_cover_loss_mask:
            # Tree cover loss data before 2020 can't be used to filter out pixels as not forest.
            # Instead, we use tree cover height taken that year as source of truth.
            # For example, if a pixel had tree cover loss in 2018, but has tree cover
            # height (2020) that meets the forest threshold, the pixel meets
            # the forest criteria for alerts and is not masked out.
            mask *= (
                self.tree_cover_loss_data.array[0, :, :] > self.tree_cover_loss_mask
            ) | (self.tree_cover_loss_data.array[0, :, :] <= 2020)

        return mask
