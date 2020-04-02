from typing import Dict, Any, List

from cachetools import cached, TTLCache
from sqlalchemy.orm import Query

from app.database import get_db
from app.models.metadata import Metadata

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


# memorize fields for 15 min
@cached(cache=TTLCache(maxsize=15, ttl=900))
def get_versions(dataset):
    with get_db() as db:
        versions = (
            Query(Metadata, db)
            .with_entities(Metadata.version, Metadata.is_latest)
            .filter(Metadata.dataset == dataset)
            .all()
        )

    return versions
