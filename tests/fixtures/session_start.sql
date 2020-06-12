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
    source_type character varying COLLATE pg_catalog."default" NOT NULL,
    has_geostore boolean,
    metadata jsonb,
    is_mutable boolean,
    source_uri character varying[] COLLATE pg_catalog."default",
    change_log jsonb[],
    status character varying COLLATE pg_catalog."default" NOT NULL,
    creation_options jsonb,
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
    dataset character varying COLLATE pg_catalog."default" NOT NULL,
    version character varying COLLATE pg_catalog."default" NOT NULL,
    asset_type character varying COLLATE pg_catalog."default" NOT NULL,
    asset_uri character varying COLLATE pg_catalog."default" NOT NULL,
    metadata jsonb,
    asset_id uuid NOT NULL,
    creation_options jsonb,
    is_managed boolean NOT NULL,
    status character varying COLLATE pg_catalog."default" NOT NULL,
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
INSERT INTO public.versions (dataset, version, is_latest, status, source_type)
  VALUES ('nasa_viirs_fire_alerts', 'v202003', true, 'saved', 'table');
INSERT INTO public.assets (dataset, version, asset_type, metadata, asset_id, status, asset_uri, is_managed)
    VALUES ('nasa_viirs_fire_alerts', 'v202003', 'Dynamic vector tile cache', '{"fields_": []}', '327fdd68-2d07-4ced-99f1-69e7f74b20b7', 'saved', 'my_uri', true);

INSERT INTO public.datasets (dataset) VALUES ('wdpa_protected_areas');
INSERT INTO public.versions (dataset, version, is_latest, status, source_type)
  VALUES ('wdpa_protected_areas', 'v201912', true, 'saved', 'vector');
INSERT INTO public.assets (dataset, version, asset_type, metadata, asset_id, status, asset_uri, is_managed)
    VALUES ('wdpa_protected_areas', 'v201912', 'Static vector tile cache', '{"fields_": []}', '327fdd68-2d07-4ced-99f1-69e7f74b20b8', 'saved', 'my_uri2', true);
