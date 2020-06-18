from typing import Any, Dict, Tuple

from sqlalchemy.sql.elements import TextClause

Filter = Tuple[TextClause, Dict[str, Any]]
Geometry = Dict[str, Any]
Bounds = Tuple[float, float, float, float]
