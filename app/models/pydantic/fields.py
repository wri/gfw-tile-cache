from typing import Optional

from pydantic import ConfigDict, BaseModel, Field

from app.models.enumerators.pg_types import PGType


class FieldMetadata(BaseModel):
    field_name_: str = Field(..., alias="field_name")
    field_alias: Optional[str] = None
    field_description: Optional[str] = None
    field_type: PGType
    is_feature_info: bool = True
    is_filter: bool = True
    model_config = ConfigDict(from_attributes=True)
