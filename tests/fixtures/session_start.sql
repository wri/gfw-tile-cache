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
    fields jsonb,
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
INSERT INTO public.assets (dataset, version, asset_type, metadata, fields, asset_id, status, asset_uri, is_managed, is_default)
    VALUES ('nasa_viirs_fire_alerts', 'v202003', 'Geo database table', '{}', '[{"field_name":"test", "field_alias": "TEST", "field_type": "text", "field_description": null, "is_feature_info": true, "is_filter": false}]', '327fdd68-2d07-4ced-99f1-69e7f74b20b7', 'saved', 'my_uri', true, true);
INSERT INTO public.assets (dataset, version, asset_type, metadata, fields, asset_id, status, asset_uri, is_managed, is_default)
    VALUES ('nasa_viirs_fire_alerts', 'v202003', 'Dynamic vector tile cache', '{}', '[{"field_name":"dynamic_test", "field_alias": "TEST", "field_type": "text", "field_description": null, "is_feature_info": true, "is_filter": false}]', '33fd3dee-8f21-4ee6-9a90-e2bd2e1d5533', 'saved', 'my_uri2', true, false);

INSERT INTO public.datasets (dataset) VALUES ('wdpa_protected_areas');
INSERT INTO public.versions (dataset, version, is_latest, status)
  VALUES ('wdpa_protected_areas', 'v201912', true, 'saved');
INSERT INTO public.assets (dataset, version, asset_type, metadata, fields, asset_id, status, asset_uri, is_managed, is_default)
    VALUES ('wdpa_protected_areas', 'v201912', 'Geo database table', '{}', '[{"field_name":"test", "field_alias": "TEST", "field_type": "text", "field_description": null, "is_feature_info": true, "is_filter": false}]', 'dc647190-c74b-4c9a-865e-e26e90480ec9', 'saved', 'my_uri3', true, true);

INSERT INTO public.assets (dataset, version, asset_type, metadata, fields, asset_id, status, asset_uri, is_managed, is_default)
    VALUES ('wdpa_protected_areas', 'v201912', 'Static vector tile cache', '{}', '[{"field_name":"static_test", "field_alias": "TEST", "field_type": "text", "field_description": null, "is_feature_info": true, "is_filter": false}]', '0637a11b-18f7-42de-9a15-a0ec488c09b6', 'saved', 'my_uri4', true, false);
