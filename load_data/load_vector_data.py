# ogr2ogr -f "PostgreSQL" PG:"password=$POSTGRES_PASSWORD  host=$POSTGRES_HOST port=5432 dbname=geostore user=gfw" \
#     WDPA_Mar2020_Public.gdb -nlt PROMOTE_TO_MULTI -nln v202003__raw WDPA_poly_Mar2020 \
#     --config PG_USE_COPY YES -lco SCHEMA=wdpa_protected_areas -lco GEOMETRY_NAME=geom
#
#
# ALTER TABLE wdpa_protected_areas.v202003__raw ADD COLUMN geom_wm geometry(MultiPolygon,3857);
# ALTER TABLE wdpa_protected_areas.v202003__raw ADD COLUMN gfw_area NUMERIC;
# ALTER TABLE wdpa_protected_areas.v202003__raw ADD COLUMN gfw_geostore_id UUID;
# ALTER TABLE wdpa_protected_areas.v202003__raw ADD COLUMN gfw_geojson TEXT;
#
# UPDATE wdpa_protected_areas.v202003__raw SET geom_wm = ST_Transform(geom, 3857);
# UPDATE wdpa_protected_areas.v202003__raw SET gfw_area = ST_area(geom::geography)/10000;
# UPDATE wdpa_protected_areas.v202003__raw SET gfw_geostore_id = md5(ST_asgeojson(geom))::uuid;
# UPDATE wdpa_protected_areas.v202003__raw SET gfw_geojson = ST_asgeojson(geom);
