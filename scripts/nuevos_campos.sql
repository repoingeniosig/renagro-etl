ALTER TABLE boletas
DROP COLUMN IF EXISTS neo_poligono_upa,

ADD COLUMN neo_uuid_boleta UUID,

ADD COLUMN neo_dpa_upa TEXT,

ADD COLUMN neo_is_upa BOOLEAN DEFAULT FALSE,

ADD COLUMN neo_fecha_visita_no_upa TIMESTAMP,
ADD COLUMN neo_superficie_aprox_ha_no_upa FLOAT8,
ADD COLUMN neo_poligono_no_upa TEXT,
ADD COLUMN neo_superficie_poligono_no_upa FLOAT8,
ADD COLUMN neo_foto_no_upa TEXT,
ADD COLUMN neo_observacion_no_upa TEXT,

ADD COLUMN neo_is_informante_calificado_v1 BOOLEAN DEFAULT FALSE,
ADD COLUMN neo_observacion_no_informante_v1 TIMESTAMP,
ADD COLUMN neo_fecha_visita_v1 TIMESTAMP,
ADD COLUMN neo_is_desea_participar_v1 BOOLEAN DEFAULT FALSE,
ADD COLUMN neo_motivo_no_participacion_v1 TEXT,
ADD COLUMN neo_is_volver_v1 BOOLEAN DEFAULT FALSE,
ADD COLUMN neo_superficie_aprox_ha_v1 FLOAT8,
ADD COLUMN neo_coordenada_v1 TEXT,
ADD COLUMN neo_foto_v1 TEXT,
ADD COLUMN neo_observacion_cierre_v1 TEXT,

ADD COLUMN neo_is_informante_calificado_v2 BOOLEAN DEFAULT FALSE,
ADD COLUMN neo_observacion_no_informante_v2 TIMESTAMP,
ADD COLUMN neo_fecha_visita_v2 TIMESTAMP,
ADD COLUMN neo_is_desea_participar_v2 BOOLEAN DEFAULT FALSE,
ADD COLUMN neo_motivo_no_participacion_v2 TEXT,
ADD COLUMN neo_is_volver_v2 BOOLEAN DEFAULT FALSE,
ADD COLUMN neo_superficie_aprox_ha_v2 FLOAT8,
ADD COLUMN neo_coordenada_v2 TEXT,
ADD COLUMN neo_foto_v2 TEXT,
ADD COLUMN neo_observacion_cierre_v2 TEXT,

ADD COLUMN neo_is_informante_calificado_v3 BOOLEAN DEFAULT FALSE,
ADD COLUMN neo_fecha_visita_v3 TIMESTAMP,
ADD COLUMN neo_is_desea_participar_v3 BOOLEAN DEFAULT FALSE,
ADD COLUMN neo_motivo_no_participacion_v3 TEXT,
ADD COLUMN neo_superficie_aprox_ha_v3 FLOAT8,
ADD COLUMN neo_coordenada_v3 TEXT,
ADD COLUMN neo_foto_v3 TEXT,
ADD COLUMN neo_observacion_cierre_v3 TEXT;

CREATE SEQUENCE seq_adj_id
INCREMENT 1
MINVALUE 1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

CREATE TABLE adjuntos (
    adj_id INTEGER NOT NULL DEFAULT nextval('seq_adj_id'::regclass) PRIMARY KEY,
    bol_id INTEGER,

    adj_url_descarga TEXT,
    adj_mimetype TEXT,
    adj_nombre TEXT,

    CONSTRAINT fk_adjunto_boleta
        FOREIGN KEY (bol_id)
        REFERENCES boletas (bol_id)
        ON DELETE CASCADE
);

CREATE SEQUENCE seq_pobo_id
INCREMENT 1
MINVALUE 1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

CREATE TABLE poligonos_boleta (
    pobo_id INTEGER NOT NULL DEFAULT nextval('seq_pobo_id'::regclass) PRIMARY KEY,

    bol_id INTEGER,

    pobo_coordenadas TEXT,
    pobo_area FLOAT8,

    CONSTRAINT fk_poligonos_boleta_boletas
        FOREIGN KEY (bol_id)
        REFERENCES boletas (bol_id)
        ON DELETE CASCADE
);