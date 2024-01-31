from typing import Any, Callable, Coroutine, Dict
from uuid import UUID

from fastapi import HTTPException

from app.domain.ports.geostore_geometry_port import GeostoreGeometryPort
from app.errors import BadResponseError, InvalidResponseError
from app.models.enumerators.geostore import GeostoreOrigin
from app.models.types import Geometry
from app.utils import rw_api


class DataApiGeostoreGeometryAdapter(GeostoreGeometryPort):
    async def get_geometry(self, geostore_id, geostore_origin):
        geostore_constructor: Dict[
            str, Callable[[UUID], Coroutine[Any, Any, Geometry]]
        ] = {
            # GeostoreOrigin.gfw: geostore.get_geostore_geometry,
            GeostoreOrigin.rw: rw_api.get_geostore_geometry
        }

        try:
            return await geostore_constructor[geostore_origin](geostore_id)
        except KeyError:
            raise HTTPException(
                status_code=501,
                detail=f"Geostore origin {geostore_origin} not fully implemented.",
            )

        except InvalidResponseError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except BadResponseError as e:
            raise HTTPException(status_code=400, detail=str(e))
