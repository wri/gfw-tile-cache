from typing import Dict, Any, List

from cachetools import cached, TTLCache
from fastapi import Depends
from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Query, Session

from app.database import get_db, Base


class Metadata(Base):
    __tablename__ = "metadata"

    dataset = Column(String, primary_key=True)
    version = Column(String, primary_key=True)
    is_latest = Column(Boolean)
    has_tile_cache = Column(Boolean)
    has_geostore = Column(Boolean)
    has_feature_info = Column(Boolean)
    fields = Column(JSONB)


# memorize metadata for 15 min
@cached(cache=TTLCache(maxsize=1, ttl=900))
def get_metadata():
    with get_db() as db:
        metadata = Query(Metadata, db).all()

    return metadata


# memorize fields for 15 min
@cached(cache=TTLCache(maxsize=15, ttl=900))
def get_fields(dataset, version,) -> List[Dict[str, Any]]:
    with get_db() as db:
        metadata = (
            Query(Metadata, db)
            .filter(Metadata.dataset == dataset)
            .filter(Metadata.version == version)
            .first()
        )

    return metadata.fields
