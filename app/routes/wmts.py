from typing import List, Optional, Tuple
from xml.etree.ElementTree import Element, SubElement

from aenum import Enum
from fastapi import APIRouter, Depends, Path, Response

from ..responses import XMLResponse
from ..settings.globals import GLOBALS
from . import raster_tile_cache_version_dependency

router = APIRouter()


class Format(str, Enum):
    png = "image/png"


class TileMatrixSet(str, Enum):
    epsg_3857 = "EPSG:3857"


base_scale = {TileMatrixSet.epsg_3857: 5.590822639508929e8}

#
# @router.get(
#     "/{dataset}/{version}/{implementation}/wmts",
#     response_class=Response,
#     tags=["Raster Tiles"],
#     # response_description="PNG Raster Tile",
# )
# async def wmts(
#     *,
#     dv: Tuple[str, str] = Depends(raster_tile_cache_version_dependency),
#     implementation: str = Path(..., description="Tile Cache implementation"),
#     SERVICE: str = Query("WMTS"),
#     VERSION: str = Query("1.0.0"),
#     REQUEST: WmtsRequest = Query(...),
#     tileMatrixSet: Optional[TileMatrixSet] = Query(
#         None, description="Projection of tiles"
#     ),
#     tileMatrix: Optional[int] = Query(None, description="z index", ge=0, le=22),
#     tileRow: Optional[int] = Query(None, description="y index", ge=0),
#     tileCol: Optional[int] = Query(None, description="x index", ge=0),
#     format: Optional[Format] = Query(None, description="Tile format"),
# ) -> Response:
#     """
#     WMTS Service
#     """
#     dataset, version = dv
#
#     if REQUEST == WmtsRequest.get_capabilities:
#         capabilities = get_capabilities(dataset, version, implementation)
#         return XMLResponse(
#             # With Python 3.9 we can use ET.indent() instead
#             content=parseString(tostring(capabilities)).toprettyxml(),
#         )
#     elif REQUEST == WmtsRequest.get_tiles:
#         if tileMatrix is None or tileCol is None or tileCol is None:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Must provide parameters tileMatrixSet, tileCol and tileRow with GetTile request.",
#             )
#
#         z = tileMatrix
#         x = tileCol
#         y = tileRow
#
#         return RedirectResponse(
#             f"{GLOBALS.tile_cache_url}/{dataset}/{version}/{implementation}/{z}/{x}/{y}.png"
#         )


@router.get(
    "/{dataset}/{version}/{implementation}/wmts/1.0.0/WMTSCapabilities.xml",
    response_class=Response,
    tags=["Raster Tiles"],
    # response_description="PNG Raster Tile",
)
async def wmts(
    *,
    dv: Tuple[str, str] = Depends(raster_tile_cache_version_dependency),
    implementation: str = Path(..., description="Tile Cache implementation"),
) -> XMLResponse:
    """
    WMTS Service using resource-oriented implementation.

    You can point your WMTS client directly to this XML document to discover the tile service.
    """
    dataset, version = dv

    capabilities = get_capabilities(dataset, version, implementation)

    return XMLResponse(
        # With Python 3.9 we can use ET.indent() instead
        content=capabilities,
    )


def get_capabilities(
    dataset: str,
    version: str,
    implementation: str,
    formats: List[str] = [Format.png],
    tile_matrix_sets: List[str] = [TileMatrixSet.epsg_3857],
    max_zoom: int = 22,
    styles: Optional[List[str]] = None,
    tile_url: Optional[str] = None,
):

    capabilities = Element("Capabilities")
    capabilities.set("xmlns", "http://www.opengis.net/wmts/1.0")
    capabilities.set("xmlns:gml", "http://www.opengis.net/gml")
    capabilities.set("xmlns:ows", "http://www.opengis.net/ows/1.1")
    capabilities.set("xmlns:xlink", "http://www.w3.org/1999/xlink")
    capabilities.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    capabilities.set(
        "xsi:schemaLocation",
        "http://www.opengis.net/wmts/1.0 http://schemas.opengis.net/wmts/1.0/wmtsGetCapabilities_response.xsd",
    )
    capabilities.set("version", "1.0.0")
    service_metadata = SubElement(capabilities, "ServiceMetadataURL")
    service_metadata.set(
        "xlink:href",
        f"{GLOBALS.tile_cache_url}/{dataset}/{version}/{implementation}/wmts/1.0.0/WMTSCapabilities.xml",
    )

    get_service_identification(capabilities)
    get_service_provider(capabilities)
    # get_operation_metadata(capabilities, dataset, version, implementation)
    get_content(
        capabilities,
        dataset,
        version,
        implementation,
        formats,
        tile_matrix_sets,
        max_zoom,
        styles,
        tile_url,
    )
    return capabilities


def get_service_identification(parent: Element):
    service_identification = SubElement(parent, "ows:ServiceIdentification")
    title = SubElement(service_identification, "ows:Title")
    title.text = "GFW Web Map Tile Service"
    service_type = SubElement(service_identification, "ows:ServiceType")
    service_type.text = "OGC WMTS"
    service_type_version = SubElement(service_identification, "ows:ServiceTypeVersion")
    service_type_version.text = "1.0.0"
    profile = SubElement(service_identification, "ows:Profile")
    profile.text = "http://www.opengis.net/spec/wmts-simple/1.0/conf/simple-profile"
    fees = SubElement(service_identification, "ows:Fees")
    fees.text = "none"
    access_constraints = SubElement(service_identification, "ows:AccessConstraints")
    access_constraints.text = "none"


def get_service_provider(parent: Element):
    service_provider = SubElement(parent, "ows:ServiceProvider")
    name = SubElement(service_provider, "ows:ProviderName")
    name.text = "Global Forest Watch"
    website = SubElement(service_provider, "ows:ProviderSite")
    website.set("xlink:href", "https://www.globalforestwatch.org")
    contact = SubElement(service_provider, "ows:ServiceContact")
    contact_name = SubElement(contact, "ows:IndividualName")
    contact_name.text = "GFW Engineering"


def get_content(
    parent: Element,
    dataset: str,
    version: str,
    implementation: str,
    formats: List[str],
    tile_matrix_sets: List[str],
    max_zoom: int,
    styles: Optional[List[str]],
    tile_url: Optional[str],
):
    content = SubElement(parent, "Contents")
    get_layer(
        content,
        dataset,
        version,
        implementation,
        formats,
        tile_matrix_sets,
        styles,
        tile_url,
    )
    for tile_matrix_set in tile_matrix_sets:
        get_tile_matrix_set(content, tile_matrix_set, max_zoom)


def get_layer(
    parent: Element,
    dataset: str,
    version: str,
    implementation: str,
    formats: List[str],
    tile_matix_sets: List[str],
    styles: Optional[List[str]],
    tile_url: Optional[str],
):

    if tile_url is None:
        tile_url = f"{GLOBALS.tile_cache_url}/{dataset}/{version}/{implementation}/{{TileMatrix}}/{{TileCol}}/{{TileRow}}.png"
    layer = SubElement(parent, "Layer")
    title = SubElement(layer, "ows:Title")
    title.text = dataset
    bbox = SubElement(layer, "ows:WGS84BoundingBox")
    lower_corner = SubElement(bbox, "ows:LowerCorner")
    lower_corner.text = "-180.0 -90.0"
    upper_corner = SubElement(bbox, "ows:UpperCorner")
    upper_corner.text = "180.0 90.0"
    get_style(layer, styles)

    simple_resource_url = SubElement(layer, "ResourceURL")
    simple_resource_url.set("format", Format.png)
    simple_resource_url.set("resourceType", "simpleProfileTile")
    simple_resource_url.set(
        "template",
        tile_url,
    )
    tile_resource_url = SubElement(layer, "ResourceURL")
    tile_resource_url.set("format", Format.png)
    tile_resource_url.set("resourceType", "tile")
    tile_resource_url.set(
        "template",
        tile_url,
    )
    for format_name in formats:
        get_format(layer, format_name)
    for tile_matix_set in tile_matix_sets:
        get_tile_matrix_set_link(layer, tile_matix_set)


def get_style(parent: Element, styles: Optional[List[str]]):
    if not styles:
        styles = ["default"]
    for i, style_id in enumerate(styles):
        style = SubElement(parent, "Style")
        if i == 0:
            style.set("isDefault", "true")
        identifier = SubElement(style, "ows:Identifier")
        identifier.text = style_id


def get_format(parent: Element, format_name: str):
    layer_format = SubElement(parent, "Format")
    layer_format.text = format_name


def get_tile_matrix_set_link(parent: Element, tile_matix_set_name: str):
    set_link = SubElement(parent, "TileMatrixSetLink")
    tile_matrix_set = SubElement(set_link, "TileMatrixSet")
    tile_matrix_set.text = tile_matix_set_name


def get_tile_matrix_set(parent: Element, tile_matix_set_name: str, max_zoom: int):
    org, code = tile_matix_set_name.split(":")
    tile_matrix_set = SubElement(parent, "TileMatrixSet")
    identifier = SubElement(tile_matrix_set, "ows:Identifier")
    identifier.text = tile_matix_set_name
    supported_crs = SubElement(tile_matrix_set, "ows:SupportedCRS")
    supported_crs.text = f"urn:ogc:def:crs:{org}::{code}"
    for zoom in range(0, max_zoom + 1):
        get_tile_matrix(tile_matrix_set, tile_matix_set_name, zoom)


def get_tile_matrix(parent: Element, tile_matrix_set: str, zoom: int):
    tile_matrix = SubElement(parent, "TileMatrix")
    identifier = SubElement(tile_matrix, "ows:Identifier")
    identifier.text = f"{zoom}"
    scale_denominator = SubElement(tile_matrix, "ScaleDenominator")
    scale_denominator.text = str(base_scale[tile_matrix_set] / (2 ** zoom))
    top_left = SubElement(tile_matrix, "TopLeftCorner")
    top_left.text = "-2.003750834E7 2.0037508E7"
    tile_width = SubElement(tile_matrix, "TileWidth")
    tile_width.text = "256"
    tile_height = SubElement(tile_matrix, "TileHeight")
    tile_height.text = "256"
    matrix_width = SubElement(tile_matrix, "MatrixWidth")
    matrix_width.text = str(2 ** zoom)
    matrix_height = SubElement(tile_matrix, "MatrixHeight")
    matrix_height.text = str(2 ** zoom)


#
# def get_operation_metadata(parent, dataset, version, implementations):
#     url = f"{GLOBALS.tile_cache_url}/{dataset}/{version}/{implementations}/wmts"
#
#     operation_metadata = SubElement(parent, "ows:OperationsMetadata")
#     get_operation(operation_metadata, "GetCapabilities", url)
#     get_operation(operation_metadata, "GetTile", url)
#     get_operation(operation_metadata, "GetFeatureInfo", url)


#
#
# def get_operation(parent: Element, operation_name: str, url: str):
#     operation = SubElement(parent, "ows:Operation")
#     operation.set("name", operation_name)
#     dcp = SubElement(operation, "ows:DCP")
#     http = SubElement(dcp, "ows:HTTP")
#     get = SubElement(http, "ows:GET")
#     get.set("xlink:href", url)
#     constraint = SubElement(get, "ows:Constrain")
#     constraint.set("name", "GetEncoding")
#     allowed_values = SubElement(constraint, "ows:AllowedValues")
#     value = SubElement(allowed_values, "ows:Value")
#     value.text = "KVP"
