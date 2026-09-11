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


cropland_emissions = LgmsAsset(kind="cog", file_name="cropland_per_ha_v2.tif")
livestock_emissions = LgmsAsset(kind="cog", file_name="livestock_per_ha_v2.tif")

# These sectors have no removals, so their net flux is their emissions.
cropland = LgmsNode(
    layer=LgmsLayer.cropland,
    assets={
        LgmsFluxType.gross_emissions: cropland_emissions,
        LgmsFluxType.net: cropland_emissions,
    },
)

livestock = LgmsNode(
    layer=LgmsLayer.livestock,
    assets={
        LgmsFluxType.gross_emissions: livestock_emissions,
        LgmsFluxType.net: livestock_emissions,
    },
)

agriculture = LgmsNode(layer=LgmsLayer.agriculture, children=[cropland, livestock])

lulucf = LgmsNode(
    layer=LgmsLayer.lulucf,
    assets={LgmsFluxType.net: LgmsAsset(kind="mosaic", file_name="mosaic.json")},
)

lgms = LgmsNode(layer=LgmsLayer.lgms, children=[lulucf, agriculture])

nodes: Dict[LgmsLayer, LgmsNode] = {
    node.layer: node for node in (lgms, lulucf, agriculture, cropland, livestock)
}


def resolve_assets(layer: LgmsLayer, flux_type: LgmsFluxType) -> List[LgmsAsset]:
    """The rasters to read for this layer, summed together if more than one."""

    assets = assets_for(nodes[layer], flux_type)
    if not assets:
        raise UnsupportedLayerFlux(f"No {flux_type} raster for {layer}")
    return assets


def assets_for(node: LgmsNode, flux_type: LgmsFluxType) -> List[LgmsAsset]:
    """A derived layer needs every child, or its total would be partial."""

    asset = node.assets.get(flux_type)
    if asset:
        return [asset]

    children = [assets_for(child, flux_type) for child in node.children]
    if not children or not all(children):
        return []
    return [asset for child in children for asset in child]
