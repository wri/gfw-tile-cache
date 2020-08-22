from typing import Any, Dict, List

from pydantic import BaseModel, Field


class SpatialReference(BaseModel):
    wkid: int
    latestWkid: int


class Extent(BaseModel):
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    spatialReference: SpatialReference


class Origin(BaseModel):
    x: float
    y: float


class LOD(BaseModel):
    level: int
    resolution: float
    scale: float


class TileInfo(BaseModel):
    rows: int = Field(None, example=512)
    cols: int = Field(None, example=512)
    dpi: int = Field(None, example=96)
    format: str = Field(None, example="pbf")
    origin: Origin
    spatialReference: SpatialReference
    lods: List[LOD]


class StorageInfo(BaseModel):
    packetSize: int = Field(None, example=128)
    storageFormat: str = Field(None, example="compactV2")


class CacheInfo(BaseModel):
    storageInfo: StorageInfo


class ResourceInfo(BaseModel):
    styleVersion: int
    tileCompression: str = Field(None, example="gzip")
    cacheInfo: CacheInfo


class VectorTileService(BaseModel):
    currentVersion: float = Field(None, example=10.7)
    name: str
    copyrightText: str
    capabilities: str = Field(None, example="TilesOnly")
    type: str = Field(None, example="indexedVector")
    defaultStyles: str
    tiles: List[str] = Field(None, example=["{z}/{x}/{y}.pbf?key=value"])
    exportTilesAllowed: bool = Field(None, example=False)
    initialExtent: Extent
    fullExtent: Extent
    minScale: int
    maxScale: int
    tileInfo: TileInfo
    maxzoom: int
    minLOD: int
    maxLOD: int
    resourceInfo: ResourceInfo
    serviceItemId: str


class RootJson(BaseModel):
    version: int
    sources: Dict[str, Any]
    layers: List[Dict[str, Any]]
