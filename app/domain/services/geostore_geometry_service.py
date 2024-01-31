from app.domain.ports.geostore_geometry_port import GeostoreGeometryPort


class GeostoreGeometryService:
    def __init__(self, geostore_geometry_port: GeostoreGeometryPort):
        self.geostore_geometry_port = geostore_geometry_port

    async def get_geometry(self, geostore_id, geostore_origin):
        return await self.geostore_geometry_port.get_geometry(
            geostore_id, geostore_origin
        )
