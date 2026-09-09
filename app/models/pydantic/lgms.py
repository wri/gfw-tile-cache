"""The LGMS sector hierarchy: which raster backs a layer and flux type.

A layer serves its own raster when it has one, and is otherwise the sum of its
children's rasters. Only combinations with published rasters are modelled.
"""

from typing import Dict, List, Literal

from pydantic import BaseModel

from ..enumerators.titiler import LgmsFluxType, LgmsLayer


class UnsupportedLayerFlux(Exception):
    """No raster backs this layer and flux type."""


class LgmsAsset(BaseModel):
    """A raster in the dataset's COG folder, named as it is in the data lake."""

    kind: Literal["mosaic", "cog"]
    file_name: str


class LgmsNode(BaseModel):
    layer: LgmsLayer
    assets: Dict[LgmsFluxType, LgmsAsset] = {}
    children: List["LgmsNode"] = []


cropland = LgmsNode(
    layer=LgmsLayer.cropland,
    assets={
        LgmsFluxType.gross_emissions: LgmsAsset(
            kind="cog", file_name="cropland_emissions.tif"
        )
    },
)

livestock = LgmsNode(
    layer=LgmsLayer.livestock,
    assets={
        LgmsFluxType.gross_emissions: LgmsAsset(
            kind="cog", file_name="livestock_emissions.tif"
        )
    },
)

agriculture = LgmsNode(layer=LgmsLayer.agriculture, children=[cropland, livestock])

lulucf = LgmsNode(
    layer=LgmsLayer.lulucf,
    assets={LgmsFluxType.net: LgmsAsset(kind="mosaic", file_name="mosaic.json")},
)

nodes: Dict[LgmsLayer, LgmsNode] = {
    node.layer: node for node in (lulucf, agriculture, cropland, livestock)
}


def resolve_assets(layer: LgmsLayer, flux_type: LgmsFluxType) -> List[LgmsAsset]:
    """The rasters to read for this layer, summed together if more than one."""

    assets = assets_for(nodes[layer], flux_type)
    if not assets:
        raise UnsupportedLayerFlux(f"No {flux_type} raster for {layer}")
    return assets


def assets_for(node: LgmsNode, flux_type: LgmsFluxType) -> List[LgmsAsset]:
    asset = node.assets.get(flux_type)
    if asset:
        return [asset]
    return [a for child in node.children for a in assets_for(child, flux_type)]
