from typing import Optional

from pydantic import BaseModel, Field

from app.models.enumerators.pg_types import PGType


class FieldMetadata(BaseModel):
    field_name_: str = Field(..., alias="field_name")
    field_alias: Optional[str]
    field_description: Optional[str]
    field_type: PGType
    is_feature_info: bool = True
    is_filter: bool = True

    class Config:
        orm_mode = True
