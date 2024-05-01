from fastapi import HTTPException
from psycopg2._psycopg import QueryCanceledError

from app.crud.async_db.vector_tiles import nasa_viirs_fire_alerts
from app.crud.async_db.vector_tiles.filters import (
    contextual_filter,
    date_filter,
    geometry_filter,
)
from app.domain.services.geostore_geometry_service import GeostoreGeometryService


class NasaViirsFireAlertsService:
    def __init__(self, geostore_geometry_service: GeostoreGeometryService):
        self.geostore_geometry_service = geostore_geometry_service

    async def get_aggregated_tile(
        self,
        version,
        geostore_id,
        geostore_origin,
        bbox,
        extent,
        high_confidence_only,
        start_date,
        end_date,
        contextual_filters,
        include_attribute,
    ):
        geometry = None
        if geostore_id:
            geometry = self.geostore_geometry_service.get_geometry(
                geostore_id, geostore_origin
            )

        filters = [
            await geometry_filter(bbox, geometry),
            nasa_viirs_fire_alerts.confidence_filter(high_confidence_only),
            date_filter("alert__date", start_date, end_date),
        ] + contextual_filter(**contextual_filters)

        # Remove empty filters
        filters = [f for f in filters if f is not None]

        try:
            tile = await nasa_viirs_fire_alerts.get_aggregated_tile(
                version, bbox, extent, include_attribute, filters
            )
        except QueryCanceledError:
            raise HTTPException(
                status_code=524,
                detail="A timeout occurred while processing the request. Request canceled.",
            )
        else:
            return tile
