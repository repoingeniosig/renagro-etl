DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_cap_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_cap_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;


-----------------------------
-- Table structure for capacitacion
-- ----------------------------
DROP TABLE IF EXISTS "sc_renagro_mag"."capacitacion";
CREATE TABLE "sc_renagro_mag"."capacitacion" (
  "cap_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_cap_id'::regclass),
  "cap_provincia" varchar(255) COLLATE "pg_catalog"."default",
  "cap_canton" varchar(255) COLLATE "pg_catalog"."default",
  "cap_parroquia" varchar(255) COLLATE "pg_catalog"."default",
  "cap_evento" varchar(255) COLLATE "pg_catalog"."default",
  "cap_primer_apellido" varchar(255) COLLATE "pg_catalog"."default",
  "cap_primer_nombre" varchar(255) COLLATE "pg_catalog"."default",
  "cap_tipo" varchar(255) COLLATE "pg_catalog"."default",
  "cap_is_recapacitacion" bool,
  "cap_estado_capacitacion" varchar(255) COLLATE "pg_catalog"."default",
  "cap_funcion" varchar(255) COLLATE "pg_catalog"."default",
  "cap_reg_usu" int8 NOT NULL,
  "cap_reg_fecha" timestamp(6),
  "cap_act_usu" int8,
  "cap_act_fecha" timestamp(6),
  "cap_estado" int8 DEFAULT 11,
  "cap_eliminado" bool DEFAULT false
)
;
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_id" IS 'Identificador secuencial de la tabla';
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_provincia" IS 'Opcion catalogo PROV, provincia de capacitacion';
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_canton" IS 'Opcion del catalogo CANT de capacitacion';
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_parroquia" IS 'Opcion catalogo PARR de capacitacion';
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_evento" IS 'Nombre del evento (capacitacion)';
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_primer_nombre" IS 'Primer nombre de persona capacitada';
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_primer_apellido" IS 'Primer apellido de persona capacitada';
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_tipo" IS 'Opcion del catalogo xxx tipo de capacitacion';
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_is_recapacitacion" IS 'Se recapacita a la persona';
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_estado_capacitacion" IS 'Opcion del catalogo xxx tipo de estado de capacitacion';
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_funcion" IS 'Opcion del catalogo xxx tipo de funcion de la persona';
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_reg_usu" IS 'Identificador de usuario que registra';
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_reg_fecha" IS 'Fecha cuando registra';
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_act_usu" IS 'Identificador de usuario que actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_act_fecha" IS 'Fecha cuando actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_estado" IS 'Estado de capacitacion para eliminado logico 11 activo, 12 eliminado';
COMMENT ON COLUMN "sc_renagro_mag"."capacitacion"."cap_eliminado" IS 'Eliminado logico forzado por MAG';



DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_com_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_com_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;


-----------------------------
-- Table structure for comunicacion
-- ----------------------------
DROP TABLE IF EXISTS "sc_renagro_mag"."comunicacion";
CREATE TABLE "sc_renagro_mag"."comunicacion" (
  "com_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_com_id'::regclass),
  "com_provincia" varchar(255) COLLATE "pg_catalog"."default",
  "com_canton" varchar(255) COLLATE "pg_catalog"."default",
  "com_parroquia" varchar(255) COLLATE "pg_catalog"."default",
  "com_is_sensib_planificada" bool,
  "com_is_socializ_planificada" bool,
  "com_is_avanzada_planificada" bool,
  "com_numero_asociaciones" int8,
  "com_numero_actores" int8,
  "com_numero_plan_levantamiento" int8,
  "com_is_sensib_ejecutada" bool,
  "com_is_socializ_ejecutada" bool,
  "com_is_avanzada_ejecutada" bool,
  "com_reg_usu" int8 NOT NULL,
  "com_reg_fecha" timestamp(6),
  "com_act_usu" int8,
  "com_act_fecha" timestamp(6),
  "com_estado" int8 DEFAULT 11,
  "com_eliminado" bool DEFAULT false
)
;

COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_id" IS 'Identificador secuencial de la tabla';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_provincia" IS 'Opcion catalogo PROV, provincia de comunicacion';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_canton" IS 'Opcion del catalogo CANT de comunicacion';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_parroquia" IS 'Opcion catalogo PARR de comunicacion';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_is_sensib_planificada" IS 'Sensibilizacion planificada';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_is_socializ_planificada" IS 'Socializacion planificada';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_is_avanzada_planif" IS 'Avanzada planificada';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_numero_asociaciones" IS 'Numero de asociaciones involucradas';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_numero_actores" IS 'Numero de actores involucradas';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_numero_plan_levantamiento" IS 'Numero de planes de levantamiento';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_is_sensib_ejecutada" IS 'Sensibilizacion ejecutada';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_is_socializ_ejecutada" IS 'Socializacion ejecutada';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_is_avanzada_ejecutada" IS 'Avanzada ejecutada';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_reg_usu" IS 'Identificador de usuario que registra';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_reg_fecha" IS 'Fecha cuando registra';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_act_usu" IS 'Identificador de usuario que actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_act_fecha" IS 'Fecha cuando actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_estado" IS 'Estado de comunicacion para eliminado logico 11 activo, 12 eliminado';
COMMENT ON COLUMN "sc_renagro_mag"."comunicacion"."com_eliminado" IS 'Eliminado logico forzado por MAG';


DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_pro_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_pro_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-----------------------------
-- Table structure for produccion
-- ----------------------------

DROP TABLE IF EXISTS "sc_renagro_mag"."produccion";
CREATE TABLE "sc_renagro_mag"."produccion" (

  "pro_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_pro_id'::regclass),
  "pro_provincia" varchar(255) COLLATE "pg_catalog"."default",
  "pro_canton" varchar(255) COLLATE "pg_catalog"."default",
  "pro_parroquia" varchar(255) COLLATE "pg_catalog"."default",
  "pro_poligono" varchar(255) COLLATE "pg_catalog"."default",
  "pro_pol_estado" varchar(255) COLLATE "pg_catalog"."default",
  "pro_upa_planificada" int8,  
  "pro_upa_levantada" int8,  
  "pro_per_productora_planificada" int8,  
  "pro_per_productora_levantada" int8,  
  "pro_pol_area_planificada" float8,  
  "pro_pol_area_levantada" float8,  
  "pro_pol_control_calidad" varchar(255) COLLATE "pg_catalog"."default",
  "pro_muestra_planificada" int8,  
  "pro_muestra_ejecutada" int8,
  "pro_boleta_upa_planificada" int8,  
  "pro_boleta_upa_ejecutada" int8,
  "pro_control_calidad" varchar(255) COLLATE "pg_catalog"."default",
  "pro_boleta_control_calidad" varchar(255) COLLATE "pg_catalog"."default",
  "pro_previo_fase_1" int8,  
  "pro_previo_fase_2" int8,  
  "pro_proceso_total" int8,
  "pro_prelevanta_planificado" int8,  
  "pro_prelevanta_levantado" int8,
  "pro_pol_planificado" int8,  
  "pro_pol_ejecutado" int8,
  "pro_pol_area_agrop_planificada" float8,
  "pro_pol_area_agrop_ejecutada" float8,
  "pro_pol_area_fores_planificada" float8,
  "pro_pol_area_fores_ejecutada" float8,
  "pro_boleta_noupa_planificada" int8,  
  "pro_boleta_noupa_ejecutada" int8,
  "pro_equipo" varchar(255) COLLATE "pg_catalog"."default",
  "pro_encuestador" varchar(255) COLLATE "pg_catalog"."default",
  "pro_unidad_numeracion" varchar(255) COLLATE "pg_catalog"."default",
  "pro_unidad_estandar" varchar(255) COLLATE "pg_catalog"."default",
  "pro_reg_usu" int8 NOT NULL,
  "pro_reg_fecha" timestamp(6),
  "pro_act_usu" int8,
  "pro_act_fecha" timestamp(6),
  "pro_estado" int8 DEFAULT 11,
  "pro_eliminado" bool DEFAULT false
)
;


COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_id" IS 'Identificador secuencial de la tabla';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_provincia" IS 'Opcion catalogo PROV, provincia de produccion';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_canton" IS 'Opcion del catalogo CANT de produccion';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_parroquia" IS 'Opcion catalogo PARR de produccion';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_poligono" IS 'Polígono de ejecución';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_pol_estado" IS 'Estado del polígono de ejecución';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_upa_planificada" IS 'Número de upas planificadas';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_upa_levantada" IS 'Número de upas levantadas';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_per_productora_planificada" IS 'Número de personas productoras planificadas';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_per_productora_levantada" IS 'Número de personas productoras levantadas';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_pol_area_planificada" IS 'Área del poligono planificada';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_pol_area_levantada" IS 'Área del poligono levantada';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_pol_control_calidad" IS 'Control del calidad del polígono';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_muestra_planificada" IS 'Muestra planificada';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_muestra_ejecutada" IS 'Muestra ejecutada';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_boleta_upa_planificada" IS 'Número de boletas upa planificadas';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_boleta_upa_ejecutada" IS 'Número de boletas upa ejecutadas';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_control_calidad" IS 'Control de calidad';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_boleta_control_calidad" IS 'Control de calidad de las boletas';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_previo_fase_1" IS 'Previo fase 1';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_previo_fase_2" IS 'Previo fase 2';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_proceso_total" IS 'Proceso total';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_prelevanta_planificado" IS 'Prelevanta planificado';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_prelevanta_levantado" IS 'Prelevanta levantado';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_pol_planificado" IS 'Número de poligonos planificados';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_pol_ejecutado" IS 'Número de poligonos ejecutados';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_pol_area_agrop_planificada" IS 'Polígono del área agropecuaria planificada';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_pol_area_agrop_ejecutada" IS 'Polígono del área agropecuaria ejecutada';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_pol_area_fores_planificada" IS 'Polígono del área forestal planificada';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_pol_area_fores_ejecutada" IS 'Polígono del área forestal ejecutada';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_boleta_noupa_planificada" IS 'Número de boletas de no upas planificada';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_boleta_noupa_ejecutada" IS 'Número de boletas de no upas ejecutada';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_equipo" IS 'Equipo encargado';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_encuestador" IS 'Encuestador';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_unidad_numeracion" IS 'Unidad de numeración';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_unidad_estandar" IS 'Unidad de estandar';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_reg_usu" IS 'Identificador de usuario que registra';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_reg_fecha" IS 'Fecha cuando registra';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_act_usu" IS 'Identificador de usuario que actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_act_fecha" IS 'Fecha cuando actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_estado" IS 'Estado de produccion para eliminado logico 11 activo, 12 eliminado';
COMMENT ON COLUMN "sc_renagro_mag"."produccion"."pro_eliminado" IS 'Eliminado logico forzado por MAG';