DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_boge_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_boge_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-----------------------------
-- Table structure for boletas_geometria_mag
-- ----------------------------

DROP TABLE IF EXISTS "sc_renagro_mag"."boletas_geometria_mag";
CREATE TABLE "sc_renagro_mag"."boletas_geometria_mag" (

  "boge_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_boge_id'::regclass),
  "boge_geom" GEOMETRY(MultiPolygon, 32717) NOT NULL,
  "boge_descripcion" varchar(255) COLLATE "pg_catalog"."default",
  "bol_id" int8 NOT NULL REFERENCES "sc_renagro_mag"."boletas"(bol_id),
  "boge_reg_usu" int8 NOT NULL,
  "boge_reg_fecha" timestamp(6),
  "boge_act_usu" int8,
  "boge_act_fecha" timestamp(6),
  "boge_estado" int8 DEFAULT 11,
  "boge_eliminado" bool DEFAULT false
)
;

COMMENT ON COLUMN "sc_renagro_mag"."boletas_geometria_mag"."boge_id" IS 'Identificador secuencial de la tabla';
COMMENT ON COLUMN "sc_renagro_mag"."boletas_geometria_mag"."bol_id" IS 'Identificador de la boleta asociada a esta geometría.';
COMMENT ON COLUMN "sc_renagro_mag"."boletas_geometria_mag"."boge_geom" IS 'Geometría espacial tipo MultiPolygon en sistema de coordenadas proyectado WGS 84 / UTM zona 17S (SRID 32717)';
COMMENT ON COLUMN "sc_renagro_mag"."boletas_geometria_mag"."boge_descripcion" IS 'Descripción del polígono de la boleta.';
COMMENT ON COLUMN "sc_renagro_mag"."boletas_geometria_mag"."boge_reg_usu" IS 'Identificador de usuario que registra';
COMMENT ON COLUMN "sc_renagro_mag"."boletas_geometria_mag"."boge_reg_fecha" IS 'Fecha cuando registra';
COMMENT ON COLUMN "sc_renagro_mag"."boletas_geometria_mag"."boge_act_usu" IS 'Identificador de usuario que actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."boletas_geometria_mag"."boge_act_fecha" IS 'Fecha cuando actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."boletas_geometria_mag"."boge_estado" IS 'Estado de geometría para eliminado logico 11 activo, 12 eliminado';
COMMENT ON COLUMN "sc_renagro_mag"."boletas_geometria_mag"."boge_eliminado" IS 'Eliminado logico forzado por MAG';

DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_tege_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_tege_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-----------------------------
-- Table structure for terrenos_geometria_mag
-- ----------------------------

DROP TABLE IF EXISTS "sc_renagro_mag"."terrenos_geometria_mag";
CREATE TABLE "sc_renagro_mag"."terrenos_geometria_mag" (

  "tege_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_tege_id'::regclass),
  "tege_geom" GEOMETRY(MultiPolygon, 32717) NOT NULL,
  "tege_descripcion" varchar(255) COLLATE "pg_catalog"."default",
  "ter_id" int8 NOT NULL REFERENCES "sc_renagro_mag"."terrenos"(ter_id),
  "tege_reg_usu" int8 NOT NULL,
  "tege_reg_fecha" timestamp(6),
  "tege_act_usu" int8,
  "tege_act_fecha" timestamp(6),
  "tege_estado" int8 DEFAULT 11,
  "tege_eliminado" bool DEFAULT false
)
;

COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."tege_id" IS 'Identificador secuencial de la tabla';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."ter_id" IS 'Identificador del terreno asociado a esta geometría.';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."tege_geom" IS 'Geometría espacial tipo MultiPolygon en sistema de coordenadas WGS84 (SRID 4326)';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."tege_descripcion" IS 'Descripción del polígono del terreno.';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."tege_reg_usu" IS 'Identificador de usuario que registra';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."tege_reg_fecha" IS 'Fecha cuando registra';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."tege_act_usu" IS 'Identificador de usuario que actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."tege_act_fecha" IS 'Fecha cuando actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."tege_estado" IS 'Estado de geometría para eliminado logico 11 activo, 12 eliminado';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."tege_eliminado" IS 'Eliminado logico forzado por MAG';