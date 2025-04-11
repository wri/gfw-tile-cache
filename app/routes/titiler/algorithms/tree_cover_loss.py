import numpy as np

from app.routes.titiler.algorithms.tree_cover_loss_base import TreeCoverLossBase


class TreeCoverLoss(TreeCoverLossBase):

    title: str = "Tree Cover Loss"
    description: str = "Decode and visualize tree cover loss"

    def create_true_color_rgb(self):
        # Scale intensity based on zoom level
        scale_pow = self.scale_intensity(self.zoom)
        scaled_intensity = scale_pow(self.intensity).astype("uint8")

        # Red = 228
        r = np.full(self.tree_cover_loss_data.shape, 228, dtype="float32")

        # Green = 102 by default, but scales down with zoom level and intensity
        g = (
            np.ones(self.tree_cover_loss_data.shape, dtype="float32") * 102
            + (72 - self.zoom)
            - (scaled_intensity * (3 / max(self.zoom, 1)))
        )

        # Blue = 153 by default, but scales down with zoom level and intensity
        b = (
            np.ones(self.tree_cover_loss_data.shape, dtype="float32") * 153
            + (33 - self.zoom)
            - (self.intensity / max(self.zoom, 1))
        )

        # Clip values to [0, 255] and convert to uint8
        # Adapted from bugfix: https://gfw.atlassian.net/browse/GTC-2916
        g = np.clip(g, 0, 255).astype("uint8")
        b = np.clip(b, 0, 255).astype("uint8")

        return np.stack([r.astype("uint8"), g, b], axis=0)
