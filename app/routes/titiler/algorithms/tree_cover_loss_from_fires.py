import numpy as np

from app.routes.titiler.algorithms.tree_cover_loss_base import TreeCoverLossBase


class TreeCoverLossFromFires(TreeCoverLossBase):

    title: str = "Tree Cover Loss From Fires"
    description: str = "Decode and visualize tree cover loss from fires."

    def create_true_color_rgb(self):
        r = np.full(self.tree_cover_loss_data.shape, 154, dtype="uint8")
        g = np.full(self.tree_cover_loss_data.shape, 91, dtype="uint8")
        b = np.full(self.tree_cover_loss_data.shape, 80, dtype="uint8")

        return np.stack([r, g, b], axis=0)
