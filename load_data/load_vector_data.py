# ogr2ogr -f "PostgreSQL" PG:"password=$POSTGRES_PASSWORD  host=$POSTGRES_HOST port=$POSTGRES_PORT dbname=$POSTGRES_NAME user=$POSTGRES_USER" \
#     WDPA_Mar2020_Public.gdb -nlt PROMOTE_TO_MULTI -nln v202003__raw WDPA_poly_Mar2020 \
#     --config PG_USE_COPY YES -lco SCHEMA=wdpa_protected_areas -lco GEOMETRY_NAME=geom \
#     -limit 0

#
#
# ALTER TABLE wdpa_protected_areas.v202003__raw ADD COLUMN geom_wm geometry(MultiPolygon,3857);
# ALTER TABLE wdpa_protected_areas.v202003__raw ADD COLUMN gfw_area__ha NUMERIC;
# ALTER TABLE wdpa_protected_areas.v202003__raw ADD COLUMN gfw_geostore_id UUID;
# ALTER TABLE wdpa_protected_areas.v202003__raw ADD COLUMN gfw_geojson TEXT;
# ALTER TABLE wdpa_protected_areas.v202003__raw ADD COLUMN gfw_bbox BOX2D;

## http://blog.cleverelephant.ca/2018/09/postgis-external-storage.html
# ALTER TABLE wdpa_protected_areas.v202003__raw ALTER COLUMN geom SET STORAGE EXTERNAL;
# ALTER TABLE wdpa_protected_areas.v202003__raw ALTER COLUMN geom_wm SET STORAGE EXTERNAL;

# UPDATE wdpa_protected_areas.v202003__raw SET geom = ST_SetSRID(geom, 4326);
# UPDATE wdpa_protected_areas.v202003__raw SET geom_wm = ST_Transform(geom, 3857);

# UPDATE wdpa_protected_areas.v202003__raw SET gfw_area__ha = ST_area(geom::geography)/10000;
# UPDATE wdpa_protected_areas.v202003__raw SET gfw_geostore_id = md5(ST_asgeojson(geom))::uuid;
# UPDATE wdpa_protected_areas.v202003__raw SET gfw_geojson = ST_asgeojson(geom);
# UPDATE wdpa_protected_areas.v202003__raw SET gfw_bbox = box2d(geom);

# CREATE TABLE public.geostore (gfw_geostore_id uuid, gfw_geojson text, gfw_area__ha numeric);
# CREATE INDEX IF NOT EXISTS geostore_gfw_geostore_id_idx
#     ON public.geostore USING hash
#     (gfw_geostore_id);
#
#
# CREATE INDEX IF NOT EXISTS v202003__raw_gfw_geostore_id_idx
#     ON  wdpa_protected_areas.v202003__raw USING hash
#     (gfw_geostore_id);
# ALTER TABLE wdpa_protected_areas.v202003__raw INHERIT public.geostore;

#
# CREATE OR REPLACE FUNCTION public.gfw_createfishnet(
# 	nrow integer,
# 	ncol integer,
# 	xsize double precision,
# 	ysize double precision,
# 	x0 double precision DEFAULT 0,
# 	y0 double precision DEFAULT 0,
# 	OUT "row" integer,
# 	OUT col integer,
# 	OUT geom geometry)
#     RETURNS SETOF record
#     LANGUAGE 'sql'
#
#     COST 100
#     IMMUTABLE STRICT
#     ROWS 1000
# AS $BODY$
# SELECT i + 1 AS row, j + 1 AS col, ST_Translate(cell, j * $3 + $5, i * $4 + $6) AS geom
# FROM generate_series(0, $1 - 1) AS i,
#      generate_series(0, $2 - 1) AS j,
# (
# SELECT ('POLYGON((0 0, 0 '||$4||', '||$3||' '||$4||', '||$3||' 0,0 0))')::geometry AS cell
# ) AS foo;
# $BODY$;


# https://gis.stackexchange.com/questions/16374/creating-regular-polygon-grid-in-postgis
# CREATE MATERIALIZED VIEW public.gfw_grid_1x1
# TABLESPACE pg_default
# AS
#  WITH fishnet AS (
#          SELECT st_x(st_centroid(gfw_createfishnet.geom)) - 0.5::double precision AS left_1,
#             st_y(st_centroid(gfw_createfishnet.geom)) + 0.5::double precision AS top_1,
#             floor(st_x(st_centroid(gfw_createfishnet.geom)) / 10::double precision) * 10::double precision AS left_10,
#             ceil(st_y(st_centroid(gfw_createfishnet.geom)) / 10::double precision) * 10::double precision AS top_10,
#             st_setsrid(gfw_createfishnet.geom, 4326) AS geom
#            FROM gfw_createfishnet(180, 360, 1::double precision, 1::double precision, '-180'::integer::double precision, '-90'::integer::double precision) gfw_createfishnet("row", col, geom)
#         ), grid AS (
#          SELECT
#                 CASE
#                     WHEN fishnet.top_1 < 0::double precision THEN 'S'::text || lpad((fishnet.top_1 * '-1'::integer::double precision)::text, 2, '0'::text)
#                     WHEN fishnet.top_1 = 0::double precision THEN 'N'::text || lpad((fishnet.top_1 * '-1'::integer::double precision)::text, 2, '0'::text)
#                     ELSE 'N'::text || lpad(fishnet.top_1::text, 2, '0'::text)
#                 END AS top_1,
#                 CASE
#                     WHEN fishnet.left_1 < 0::double precision THEN 'W'::text || lpad((fishnet.left_1 * '-1'::integer::double precision)::text, 3, '0'::text)
#                     ELSE 'E'::text || lpad(fishnet.left_1::text, 3, '0'::text)
#                 END AS left_1,
#                 CASE
#                     WHEN fishnet.top_10 < 0::double precision THEN 'S'::text || lpad((fishnet.top_10 * '-1'::integer::double precision)::text, 2, '0'::text)
#                     WHEN fishnet.top_10 = 0::double precision THEN 'N'::text || lpad((fishnet.top_10 * '-1'::integer::double precision)::text, 2, '0'::text)
#                     ELSE 'N'::text || lpad(fishnet.top_10::text, 2, '0'::text)
#                 END AS top_10,
#                 CASE
#                     WHEN fishnet.left_10 < 0::double precision THEN 'W'::text || lpad((fishnet.left_10 * '-1'::integer::double precision)::text, 3, '0'::text)
#                     ELSE 'E'::text || lpad(fishnet.left_10::text, 3, '0'::text)
#                 END AS left_10,
#             fishnet.geom
#            FROM fishnet
#         )
#  SELECT grid.top_1 || grid.left_1 AS gfw_grid_1x1_id,
#     grid.top_10 || grid.left_10 AS gfw_grid_10x10_id,
#     grid.geom
#    FROM grid
# WITH DATA;
#
# CREATE INDEX IF NOT EXISTS gfw_grid_1x1_geom_idx
#     ON public.gfw_grid_1x1 USING gist
#     (geom);

#
# CREATE TYPE gfw_grid_type AS (gfw_grid_1x1 text, gfw_grid_10x10 text, geom geometry);
#
# ALTER TABLE wdpa_protected_areas.v202003__raw ADD COLUMN gfw_grid gfw_grid_type[];
#
#
# update wdpa_protected_areas.v202003__raw
# set gfw_grid = t.gfw_grid
#
# from
# (select wdpaid, array_agg((gfw_grid_1x1_id, gfw_grid_10x10_id, st_intersection(w.geom, g.geom))::gfw_grid_type ) as gfw_grid
# from wdpa_protected_areas.v202003__raw w, gfw_grid_1x1 g where st_intersects(w.geom, g.geom) group by wdpaid limit 10
# ) as t
# where wdpa_protected_areas.v202003__raw.wdpaid = t.wdpaid;


# create table metadata (
# 	dataset text,
# 	version text,
# 	is_latest boolean,
# 	has_tile_cache boolean,
# 	has_geostore boolean,
# 	has_feature_info boolean,
# 	fields jsonb,
# 	last_updated timestamp DEFAULT CURRENT_TIMESTAMP
# )

# #
# Insert into metadata(dataset, version, is_latest, has_tile_cache, has_geostore, has_feature_info, fields)
# values('wdpa_protected_areas', 'v202003', true, true, true, true,
#        '[{
#        "name": "id",
# "type": "integer",
# "is_feature_info": false,
# "is_filter": false
# },
#
# {
#     "name": "geom",
#     "type": "geometry(MultiPolygon,4326)",
#     "is_feature_info": false,
#     "is_filter": false
# },
#
# {
#     "name": "objectid",
#     "type": "bigint",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "wdpaid",
#     "type": "double precision",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "wdpa_pid",
#     "type": "character varying(50)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "pa_def",
#     "type": "character varying(20)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "name",
#     "type": "character varying(254)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "orig_name",
#     "type": "character varying(254)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "desig",
#     "type": "character varying(254)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "desig_eng",
#     "type": "character varying(254)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "desig_type",
#     "type": "character varying(254)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "iucn_cat",
#     "type": "character varying(20)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "int_crit",
#     "type": "character varying(100)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "marine",
#     "type": "character varying(20)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "rep_m_area",
#     "type": "double precision",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "gis_m_area",
#     "type": "double precision",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "rep_area",
#     "type": "double precision",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "gis_area",
#     "type": "double precision",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "no_take",
#     "type": "character varying(50)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "no_tk_area",
#     "type": "double precision",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "status",
#     "type": "character varying(100)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "status_yr",
#     "type": "integer",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "gov_type",
#     "type": "character varying(254)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "own_type",
#     "type": "character varying(254)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "mang_auth",
#     "type": "character varying(254)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "mang_plan",
#     "type": "character varying(254)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "verif",
#     "type": "character varying(20)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "metadataid",
#     "type": "integer",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "sub_loc",
#     "type": "character varying(100)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "parent_iso3",
#     "type": "character varying(50)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "iso3",
#     "type": "character varying(50)",
#     "is_feature_info": true,
#     "is_filter": true
# },
#
# {
#     "name": "shape_length",
#     "type": "double precision",
#     "is_feature_info": false,
#     "is_filter": false
# },
#
# {
#     "name": "shape_area",
#     "type": "double precision",
#     "is_feature_info": false,
#     "is_filter": false
# },
#
# {
#     "name": "gfw_grid",
#     "type": "gfw_grid_type[]",
#     "is_feature_info": false,
#     "is_filter": false
# },
#
# {
#     "name": "geom_wm",
#     "type": "geometry(MultiPolygon,3857)",
#     "is_feature_info": false,
#     "is_filter": false
# },
#
# {
#     "name": "gfw_area__ha",
#     "type": "numeric",
#     "is_feature_info": false,
#     "is_filter": false
# },
#
# {
#     "name": "gfw_geostore_id",
#     "type": "uuid",
#     "is_feature_info": true,
#     "is_filter": false
# },
#
# {
#     "name": "gfw_geojson",
#     "type": "text",
#     "is_feature_info": false,
#     "is_filter": false
# },
#
# {
#     "name": "gfw_bbox",
#     "type": "box2d",
#     "is_feature_info": false,
#     "is_filter": false
# }
# ]')
