import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Geometry(BaseModel):
    type: str
    coordinates: List[Any]


class Feature(BaseModel):
    properties: Dict[str, Any]
    type: str
    geometry: Geometry


class FeatureCollection(BaseModel):
    features: List[Feature]
    crs: Optional[Dict[str, Any]]
    type: str


class Geostore(BaseModel):
    geostore_id: uuid.UUID
    geojson: FeatureCollection
    area__ha: float
    bbox: List[float]
