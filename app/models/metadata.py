from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import JSONB


from app.database import Base


class Metadata(Base):
    __tablename__ = "metadata"

    dataset = Column(String, primary_key=True)
    version = Column(String, primary_key=True)
    is_latest = Column(Boolean)
    has_tile_cache = Column(Boolean)
    has_geostore = Column(Boolean)
    has_feature_info = Column(Boolean)
    fields = Column(JSONB)
