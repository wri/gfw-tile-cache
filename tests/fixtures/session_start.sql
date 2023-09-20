-- Table: public.datasets

DROP TABLE IF EXISTS public.datasets CASCADE;

CREATE TABLE public.datasets
(
    created_on timestamp without time zone DEFAULT now(),
    updated_on timestamp without time zone DEFAULT now(),
    dataset character varying COLLATE pg_catalog."default" NOT NULL,
    metadata jsonb,
    CONSTRAINT datasets_pkey PRIMARY KEY (dataset)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.datasets
    OWNER to gfw;

GRANT ALL ON TABLE public.datasets TO gfw;

-- GRANT SELECT ON TABLE public.datasets TO gfw_readonly;


-- Table: public.versions

DROP TABLE IF EXISTS public.versions CASCADE;

CREATE TABLE public.versions
(
    created_on timestamp without time zone DEFAULT now(),
    updated_on timestamp without time zone DEFAULT now(),
    dataset character varying COLLATE pg_catalog."default" NOT NULL,
    version character varying COLLATE pg_catalog."default" NOT NULL,
    is_latest boolean,
    is_mutable boolean,
    status character varying COLLATE pg_catalog."default" NOT NULL,
    metadata jsonb,
    change_log jsonb[],
    CONSTRAINT versions_pkey PRIMARY KEY (dataset, version),
    CONSTRAINT fk FOREIGN KEY (dataset)
        REFERENCES public.datasets (dataset) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.versions
    OWNER to gfw;

GRANT ALL ON TABLE public.versions TO gfw;

-- GRANT SELECT ON TABLE public.versions TO gfw_readonly;

-- Trigger: latest_version

-- DROP TRIGGER latest_version ON public.versions;

-- CREATE TRIGGER latest_version
--     BEFORE INSERT OR UPDATE
--     ON public.versions
--     FOR EACH ROW
--     EXECUTE PROCEDURE public.reset_latest();


-- Table: public.assets

DROP TABLE IF EXISTS public.assets CASCADE;

CREATE TABLE public.assets
(
    created_on timestamp without time zone DEFAULT now(),
    updated_on timestamp without time zone DEFAULT now(),
    asset_id uuid NOT NULL,
    dataset character varying COLLATE pg_catalog."default" NOT NULL,
    version character varying COLLATE pg_catalog."default" NOT NULL,
    asset_type character varying COLLATE pg_catalog."default" NOT NULL,
    asset_uri character varying COLLATE pg_catalog."default" NOT NULL,
    status character varying COLLATE pg_catalog."default" NOT NULL,
    is_managed boolean NOT NULL,
    is_default boolean NOT NULL,
    creation_options jsonb,
    metadata jsonb,
    stats jsonb,
    change_log jsonb[],
    CONSTRAINT assets_pkey PRIMARY KEY (dataset, version, asset_type),
    CONSTRAINT uq_asset_type UNIQUE (dataset, version, asset_type),
    CONSTRAINT uq_asset_uri UNIQUE (asset_uri),
    CONSTRAINT fk FOREIGN KEY (dataset, version)
        REFERENCES public.versions (dataset, version) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.assets
    OWNER to gfw;

-- GRANT SELECT ON TABLE public.assets TO gfw_readonly;

GRANT ALL ON TABLE public.assets TO gfw;


-- Table: public.geostore

DROP TABLE IF EXISTS public.geostore CASCADE;

CREATE TABLE public.geostore
(
    created_on timestamp without time zone DEFAULT now(),
    updated_on timestamp without time zone DEFAULT now(),
    gfw_geostore_id uuid NOT NULL,
    gfw_area__ha numeric,
    gfw_bbox geometry(Polygon,4326),
    gfw_geojson character varying COLLATE pg_catalog."default",
    CONSTRAINT geostore_pkey PRIMARY KEY (gfw_geostore_id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.geostore
    OWNER to gfw;

GRANT ALL ON TABLE public.geostore TO gfw;

DROP TABLE IF EXISTS public.version_metadata CASCADE;

CREATE TABLE public.version_metadata
(
    created_on timestamp without time zone DEFAULT now(),
    updated_on timestamp without time zone DEFAULT now(),
    id uuid NOT NULL,
    title character varying,
    dataset character varying,
    version character varying,
    content_date date,
    content_start_date date,
    content_end_date date,
    last_update date,
    description character varying,
    resolution numeric,
    geographic_coverage character varying,
    citation character varying,
    scale character varying,
    CONSTRAINT version_meta_pkey PRIMARY KEY (id),
    CONSTRAINT fk FOREIGN KEY (dataset, version)
        REFERENCES public.versions (dataset, version) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.version_metadata
    OWNER to gfw;

GRANT ALL ON TABLE public.datasets TO gfw;
-- GRANT SELECT ON TABLE public.geostore TO gfw_readonly;

-- Index: geostore_gfw_geostore_id_idx

-- DROP INDEX public.geostore_gfw_geostore_id_idx;

CREATE INDEX geostore_gfw_geostore_id_idx
    ON public.geostore USING hash
    (gfw_geostore_id)
    TABLESPACE pg_default;


INSERT INTO public.datasets (dataset) VALUES ('nasa_viirs_fire_alerts');
INSERT INTO public.versions (dataset, version, is_latest, status)
  VALUES ('nasa_viirs_fire_alerts', 'v202003', true, 'saved');
INSERT INTO public.assets (dataset, version, asset_type, creation_options, metadata, asset_id, status, asset_uri, is_managed, is_default)
    VALUES ('nasa_viirs_fire_alerts', 'v202003', 'Geo database table', '{}', '{"fields":[{"name":"test", "alias": "TEST", "data_type": "text", "description": null, "is_feature_info": true, "is_filter": false}]}', '327fdd68-2d07-4ced-99f1-69e7f74b20b7', 'saved', 'my_uri', true, true);
INSERT INTO public.assets (dataset, version, asset_type, creation_options, metadata, asset_id, status, asset_uri, is_managed, is_default)
    VALUES ('nasa_viirs_fire_alerts', 'v202003', 'Dynamic vector tile cache', '{"min_zoom": 0, "max_zoom": 12, "field_attributes": null}', '{"fields":[{"name":"dynamic_test", "alias": "TEST", "data_type": "text", "description": null, "is_feature_info": true, "is_filter": false}]}', '33fd3dee-8f21-4ee6-9a90-e2bd2e1d5533', 'saved', 'my_uri2', true, false);
INSERT INTO public.version_metadata (dataset, version, content_start_date, content_end_date, id)
    VALUES ('nasa_viirs_fire_alerts', 'v202003', '2019-01-01', '2020-01-01', 'bb5b7bd2-eb83-11ed-a05b-0242ac120003');

INSERT INTO public.datasets (dataset) VALUES ('umd_modis_burned_areas');
INSERT INTO public.versions (dataset, version, is_latest, status)
  VALUES ('umd_modis_burned_areas', 'v202003', true, 'saved');
INSERT INTO public.version_metadata (dataset, version, content_start_date, content_end_date, id)
    VALUES ('umd_modis_burned_areas', 'v202003', '2019-01-01', '2020-01-01', '10246476-eb84-11ed-a05b-0242ac120003');

INSERT INTO public.assets (dataset, version, asset_type, creation_options, fields, asset_id, status, asset_uri, is_managed, is_default)
    VALUES ('umd_modis_burned_areas', 'v202003', 'Geo database table', '{}', '{"fields":[{"name":"test", "alias": "TEST", "data_type": "text", "description": null, "is_feature_info": true, "is_filter": false}]}', '327fdd68-2d07-4ced-99f1-69e7f74b20b7', 'saved', 'my_uri8', true, true);
INSERT INTO public.assets (dataset, version, asset_type, creation_options, fields, asset_id, status, asset_uri, is_managed, is_default)
    VALUES ('umd_modis_burned_areas', 'v202003', 'Dynamic vector tile cache', '{"min_zoom": 0, "max_zoom": 12, "attributes": null}', '{"fields":[{"name":"dynamic_test", "alias": "TEST", "data_type": "text", "description": null, "is_feature_info": true, "is_filter": false}]', '33fd3dee-8f21-4ee6-9a90-e2bd2e1d5533', 'saved', 'my_uri9', true, false);

INSERT INTO public.datasets (dataset) VALUES ('wdpa_protected_areas');
INSERT INTO public.versions (dataset, version, is_latest, status)
  VALUES ('wdpa_protected_areas', 'v201912', true, 'saved');
INSERT INTO public.assets (dataset, version, asset_type, creation_options, metadata, asset_id, status, asset_uri, is_managed, is_default)
    VALUES ('wdpa_protected_areas', 'v201912', 'Geo database table', '{}', '{"fields":[{"name":"test", "alias": "TEST", "data_type": "text", "description": null, "is_feature_info": true, "is_filter": false}]}', 'dc647190-c74b-4c9a-865e-e26e90480ec9', 'saved', 'my_uri3', true, true);

INSERT INTO public.assets (dataset, version, asset_type, creation_options, metadata, asset_id, status, asset_uri, is_managed, is_default)
    VALUES ('wdpa_protected_areas', 'v201912', 'Static vector tile cache', '{"min_zoom": 0, "max_zoom": 9, "field_attributes": null, "tile_strategy": "discontinuous", "implementation": "default", "layer_style": null}', '{"fields":[{"name":"static_test", "alias": "TEST", "data_type": "text", "description": null, "is_feature_info": true, "is_filter": false}]}', '0637a11b-18f7-42de-9a15-a0ec488c09b6', 'saved', 'my_uri4', true, false);

INSERT INTO public.datasets (dataset) VALUES ('wur_radd_alerts');
INSERT INTO public.versions (dataset, version, is_latest, status)
  VALUES ('wur_radd_alerts', 'v20201214', true, 'saved');

INSERT INTO public.assets (dataset, version, asset_type, creation_options, metadata, asset_id, status, asset_uri, is_managed, is_default)
    VALUES ('wur_radd_alerts', 'v20201214', 'Raster tile cache', '{"min_zoom": 0, "max_zoom": 14, "max_static_zoom": 9, "implementation": "default", "symbology": null, "source_asset_id": null, "resampling":"average"}', '{}', '0637a11b-18f7-42de-9a15-a0ec488c09b7', 'saved', 'my_uri5', true, false);

INSERT INTO public.datasets (dataset) VALUES ('umd_tree_cover_loss');
INSERT INTO public.versions (dataset, version, is_latest, status)
  VALUES ('umd_tree_cover_loss', 'v1.8', true, 'saved');

INSERT INTO public.assets (dataset, version, asset_type, creation_options, metadata, asset_id, status, asset_uri, is_managed, is_default)
    VALUES ('umd_tree_cover_loss', 'v1.8', 'Raster tile cache', '{"min_zoom": 0, "max_zoom": 12, "max_static_zoom": 12, "implementation": "tcd_30", "symbology": null, "source_asset_id": null, "resampling":"average"}', '{}', '8086c7f5-5f2f-491f-8792-5fc67b6a7b96', 'saved', 'my_uri6', true, false);

INSERT INTO public.datasets (dataset) VALUES ('umd_glad_landsat_alerts');
INSERT INTO public.versions (dataset, version, is_latest, status)
  VALUES ('umd_glad_landsat_alerts', 'v20210101', true, 'saved');

INSERT INTO public.assets (dataset, version, asset_type, creation_options, metadata, asset_id, status, asset_uri, is_managed, is_default)
    VALUES ('umd_glad_landsat_alerts', 'v20210101', 'Raster tile cache', '{"min_zoom": 0, "max_zoom": 12, "max_static_zoom": 9, "implementation": "default", "symbology": null, "source_asset_id": null, "resampling":"average"}', '{}', '3ac4028e-798d-4854-9b5e-6a9771ed06ed', 'saved', 'my_uri7', true, false);


CREATE SCHEMA umd_modis_burned_areas;
CREATE TABLE umd_modis_burned_areas.v202003 (alert__date date, gfw_area__ha numeric, geom_wm geometry);
