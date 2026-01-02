/*
 Navicat Premium Data Transfer

 Source Server         : RENAGRO
 Source Server Type    : PostgreSQL
 Source Server Version : 120004 (120004)
 Source Host           : 10.10.1.37:5432
 Source Catalog        : bdc2
 Source Schema         : sc_renagro_mag

 Target Server Type    : PostgreSQL
 Target Server Version : 120004 (120004)
 File Encoding         : 65001

 Date: 21/08/2025 11:01:54
*/


-- ----------------------------
-- Sequence structure for seq_aud_id
-- ----------------------------
DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_aud_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_aud_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for seq_bol_id
-- ----------------------------
DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_bol_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_bol_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for seq_bov_id
-- ----------------------------
DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_bov_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_bov_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for seq_cul_id
-- ----------------------------
DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_cul_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_cul_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for seq_for_id
-- ----------------------------
DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_for_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_for_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for seq_miho_id
-- ----------------------------
DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_miho_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_miho_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for seq_peot_id
-- ----------------------------
DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_peot_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_peot_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for seq_per_id
-- ----------------------------
DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_per_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_per_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for seq_pol_id
-- ----------------------------
DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_pol_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_pol_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for seq_por_id
-- ----------------------------
DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_por_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_por_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for seq_ter_id
-- ----------------------------
DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_ter_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_ter_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Table structure for auditorias
-- ----------------------------
DROP TABLE IF EXISTS "sc_renagro_mag"."auditorias";
CREATE TABLE "sc_renagro_mag"."auditorias" (
  "aud_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_aud_id'::regclass),
  "aud_reg_usuario" int4 NOT NULL,
  "aud_operacion" varchar(255) COLLATE "pg_catalog"."default",
  "aud_servicio" varchar(255) COLLATE "pg_catalog"."default",
  "aud_reg_fecha" timestamp(6) DEFAULT CURRENT_TIMESTAMP,
  "aud_detalle" jsonb,
  "aud_status_code" varchar(255) COLLATE "pg_catalog"."default",
  "aud_status_det" jsonb
)
;
COMMENT ON COLUMN "sc_renagro_mag"."auditorias"."aud_id" IS 'Identificador secuencial de la tabla';
COMMENT ON COLUMN "sc_renagro_mag"."auditorias"."aud_reg_usuario" IS 'Identificador usuario realiza la peticion';
COMMENT ON COLUMN "sc_renagro_mag"."auditorias"."aud_operacion" IS 'Tipo de operacion';
COMMENT ON COLUMN "sc_renagro_mag"."auditorias"."aud_servicio" IS 'URL del servicio que realiza la peticion';
COMMENT ON COLUMN "sc_renagro_mag"."auditorias"."aud_reg_fecha" IS 'Fecha que solicita el servicio';
COMMENT ON COLUMN "sc_renagro_mag"."auditorias"."aud_detalle" IS 'JSON request';
COMMENT ON COLUMN "sc_renagro_mag"."auditorias"."aud_status_code" IS 'Codigo de status de response';
COMMENT ON COLUMN "sc_renagro_mag"."auditorias"."aud_status_det" IS 'JSON response';

-- ----------------------------
-- Table structure for boletas
-- ----------------------------
DROP TABLE IF EXISTS "sc_renagro_mag"."boletas";
CREATE TABLE "sc_renagro_mag"."boletas" (
  "bol_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_bol_id'::regclass),
  "bol_arado" varchar(255) COLLATE "pg_catalog"."default",
  "bol_autoconsumo_agricola" varchar(255) COLLATE "pg_catalog"."default",
  "bol_autoconsumo_apicola" varchar(255) COLLATE "pg_catalog"."default",
  "bol_autoconsumo_avicola" varchar(255) COLLATE "pg_catalog"."default",
  "bol_autoconsumo_bovina" varchar(255) COLLATE "pg_catalog"."default",
  "bol_autoconsumo_cuyes_conejo" varchar(255) COLLATE "pg_catalog"."default",
  "bol_autoconsumo_forestal" varchar(255) COLLATE "pg_catalog"."default",
  "bol_autoconsumo_otras_ave" varchar(255) COLLATE "pg_catalog"."default",
  "bol_autoconsumo_ovino_caprino" varchar(255) COLLATE "pg_catalog"."default",
  "bol_autoconsumo_porcicola" varchar(255) COLLATE "pg_catalog"."default",
  "bol_bomba_agua" varchar(255) COLLATE "pg_catalog"."default",
  "bol_bomba_estacionaria_fumiga" varchar(255) COLLATE "pg_catalog"."default",
  "bol_bomba_mochila_motor" varchar(255) COLLATE "pg_catalog"."default",
  "bol_canton" varchar(255) COLLATE "pg_catalog"."default",
  "bol_canton_vive" varchar(255) COLLATE "pg_catalog"."default",
  "bol_carreton" varchar(255) COLLATE "pg_catalog"."default",
  "bol_codigo_encuestador" int8,
  "bol_codigo_UPA" varchar(255) COLLATE "pg_catalog"."default",
  "bol_comprador_agricola" varchar(255) COLLATE "pg_catalog"."default",
  "bol_comprador_apicola" varchar(255) COLLATE "pg_catalog"."default",
  "bol_comprador_avicola" varchar(255) COLLATE "pg_catalog"."default",
  "bol_comprador_bovina" varchar(255) COLLATE "pg_catalog"."default",
  "bol_comprador_cuyes_conejo" varchar(255) COLLATE "pg_catalog"."default",
  "bol_comprador_forestal" varchar(255) COLLATE "pg_catalog"."default",
  "bol_comprador_otras_ave" varchar(255) COLLATE "pg_catalog"."default",
  "bol_comprador_ovino_caprino" varchar(255) COLLATE "pg_catalog"."default",
  "bol_comprador_porcicola" varchar(255) COLLATE "pg_catalog"."default",
  "bol_cosechadora" varchar(255) COLLATE "pg_catalog"."default",
  "bol_desgranadora" varchar(255) COLLATE "pg_catalog"."default",
  "bol_direccion_email" varchar(255) COLLATE "pg_catalog"."default",
  "bol_distancia_al_domicilio" float8,
  "bol_empacadora" varchar(255) COLLATE "pg_catalog"."default",
  "bol_empacadora_forestal" varchar(255) COLLATE "pg_catalog"."default",
  "bol_enfardadora" varchar(255) COLLATE "pg_catalog"."default",
  "bol_ensiladora" varchar(255) COLLATE "pg_catalog"."default",
  "bol_estado" int8 DEFAULT 11,
  "bol_exten_agricola_institu" varchar(255) COLLATE "pg_catalog"."default",
  "bol_exten_agricola_recibida" varchar(255) COLLATE "pg_catalog"."default",
  "bol_fangueadora" varchar(255) COLLATE "pg_catalog"."default",
  "bol_fertilizadora" varchar(255) COLLATE "pg_catalog"."default",
  "bol_fuente_agua_riego" varchar(255) COLLATE "pg_catalog"."default",
  "bol_fumigadora" varchar(255) COLLATE "pg_catalog"."default",
  "bol_id_levanta" varchar(255) COLLATE "pg_catalog"."default",
  "bol_informante_relacion" varchar(255) COLLATE "pg_catalog"."default",
  "bol_informante_telefono" varchar(255) COLLATE "pg_catalog"."default",
  "bol_infraestructura_otra" varchar(255) COLLATE "pg_catalog"."default",
  "bol_is_acc_riego" bool,
  "bol_is_agri_familiar_camp" bool,
  "bol_is_agua_otro_medio" bool,
  "bol_is_agua_por_tuberia" bool,
  "bol_is_asesoramiento_tecnico" bool,
  "bol_is_asistencia_tecnica" bool,
  "bol_is_bodega" bool,
  "bol_is_computadora" bool,
  "bol_is_construccion_secado" bool,
  "bol_is_credito" bool,
  "bol_is_cuarto_maquinaria_riego" bool,
  "bol_is_empacador" bool,
  "bol_is_energia_electrica" bool,
  "bol_is_espacio_comercio" bool,
  "bol_is_evita_erosion" bool,
  "bol_is_gestion_financiamiento" bool,
  "bol_is_incorpora_abono" bool,
  "bol_is_infraestructura" bool,
  "bol_is_infraestructura_ninguno" bool,
  "bol_is_internet" bool,
  "bol_is_invernadero" bool,
  "bol_is_kit_agricola" bool,
  "bol_is_legalizacion_tierra" bool,
  "bol_is_maquinaria" bool,
  "bol_is_ninguno" bool,
  "bol_is_no_realiza_mejora" bool,
  "bol_is_otra_practica_mejora" bool,
  "bol_is_pastoreo_rotativo" bool,
  "bol_is_pert_asociacion_coop" bool,
  "bol_is_reservorio" bool,
  "bol_is_rota_cultivo" bool,
  "bol_is_servicio_higienico" bool,
  "bol_is_silo" bool,
  "bol_is_terreno_accede_riego" bool,
  "bol_is_tratamiento_de_agua" bool,
  "bol_is_vacuna_agrocalidad" bool,
  "bol_latitud" float8,
  "bol_longitud" float8,
  "bol_manejo_residuo_agricola" varchar(255) COLLATE "pg_catalog"."default",
  "bol_manejo_residuo_animal" varchar(255) COLLATE "pg_catalog"."default",
  "bol_motocultor" varchar(255) COLLATE "pg_catalog"."default",
  "bol_motoguadania" varchar(255) COLLATE "pg_catalog"."default",
  "bol_motosierra" varchar(255) COLLATE "pg_catalog"."default",
  "bol_necesidad_conocimiento" varchar(255) COLLATE "pg_catalog"."default",
  "bol_nombre_asociacion_coop" varchar(255) COLLATE "pg_catalog"."default",
  "bol_numero_boleta" int8,
  "bol_ocasional_hombre_numero" int8,
  "bol_ocasional_hombre_salario" int8,
  "bol_ocasional_mujer_numero" int8,
  "bol_ocasional_mujer_salario" int8,
  "bol_otra_practica_mejora" varchar(255) COLLATE "pg_catalog"."default",
  "bol_otro_beneficio_estado" varchar(255) COLLATE "pg_catalog"."default",
  "bol_otro_maquinaria_equipo" varchar(255) COLLATE "pg_catalog"."default",
  "bol_otro_maquinaria_equipo_acc" varchar(255) COLLATE "pg_catalog"."default",
  "bol_parroquia" varchar(255) COLLATE "pg_catalog"."default",
  "bol_parroquia_vive" varchar(255) COLLATE "pg_catalog"."default",
  "bol_permanente_hombre_numero" int8,
  "bol_permanente_hombre_salario" int8,
  "bol_permanente_mujer_numero" int8,
  "bol_permanente_mujer_salario" int8,
  "bol_persona_info_id" int8,
  "bol_planta_electrica_termica" varchar(255) COLLATE "pg_catalog"."default",
  "bol_poligono" int8,
  "bol_prestamo_destino" varchar(255) COLLATE "pg_catalog"."default",
  "bol_prestamo_fuente" varchar(255) COLLATE "pg_catalog"."default",
  "bol_prestamo_negacion" varchar(255) COLLATE "pg_catalog"."default",
  "bol_prestamo_persona" varchar(255) COLLATE "pg_catalog"."default",
  "bol_prestamo_razon_no_gestiono" varchar(255) COLLATE "pg_catalog"."default",
  "bol_prin_manejo_envase" varchar(255) COLLATE "pg_catalog"."default",
  "bol_provincia" varchar(255) COLLATE "pg_catalog"."default",
  "bol_provincia_vive" varchar(255) COLLATE "pg_catalog"."default",
  "bol_rastra" varchar(255) COLLATE "pg_catalog"."default",
  "bol_respuesta_negativa_miembro" varchar(255) COLLATE "pg_catalog"."default",
  "bol_romplow" varchar(255) COLLATE "pg_catalog"."default",
  "bol_rotocultor" varchar(255) COLLATE "pg_catalog"."default",
  "bol_secadora" varchar(255) COLLATE "pg_catalog"."default",
  "bol_sector_muestreo" varchar(255) COLLATE "pg_catalog"."default",
  "bol_segadora" varchar(255) COLLATE "pg_catalog"."default",
  "bol_sembradora" varchar(255) COLLATE "pg_catalog"."default",
  "bol_sistema_agua_riego" varchar(255) COLLATE "pg_catalog"."default",
  "bol_sitio_agricola" varchar(255) COLLATE "pg_catalog"."default",
  "bol_sitio_apicola" varchar(255) COLLATE "pg_catalog"."default",
  "bol_sitio_avicola" varchar(255) COLLATE "pg_catalog"."default",
  "bol_sitio_bovina" varchar(255) COLLATE "pg_catalog"."default",
  "bol_sitio_cuyes_conejo" varchar(255) COLLATE "pg_catalog"."default",
  "bol_sitio_forestal" varchar(255) COLLATE "pg_catalog"."default",
  "bol_sitio_otras_ave" varchar(255) COLLATE "pg_catalog"."default",
  "bol_sitio_ovino_caprino" varchar(255) COLLATE "pg_catalog"."default",
  "bol_sitio_porcicola" varchar(255) COLLATE "pg_catalog"."default",
  "bol_subsoladora" varchar(255) COLLATE "pg_catalog"."default",
  "bol_surcadora" varchar(255) COLLATE "pg_catalog"."default",
  "bol_telefono_celular" varchar(255) COLLATE "pg_catalog"."default",
  "bol_telefono_convencional" varchar(255) COLLATE "pg_catalog"."default",
  "bol_tipo_de_miembro" varchar(255) COLLATE "pg_catalog"."default",
  "bol_tractor_forestal" varchar(255) COLLATE "pg_catalog"."default",
  "bol_tractor_jardin" varchar(255) COLLATE "pg_catalog"."default",
  "bol_tractor_oruga" varchar(255) COLLATE "pg_catalog"."default",
  "bol_tractor_rueda" varchar(255) COLLATE "pg_catalog"."default",
  "bol_trilladora" varchar(255) COLLATE "pg_catalog"."default",
  "bol_bomba_mochila" varchar(255) COLLATE "pg_catalog"."default",
  "bov_id" int8,
  "peot_id" int8,
  "pol_id" int8,
  "por_id" int8,
  "per_id" int8,
  "bol_numero_UPA" int8,
  "bol_manejo_res_animal_otro" varchar(255) COLLATE "pg_catalog"."default",
  "bol_manejo_res_agricola_otro" varchar(255) COLLATE "pg_catalog"."default",
  "bol_manejo_envase_otro" varchar(255) COLLATE "pg_catalog"."default",
  "bol_otro_prest_nega" varchar(255) COLLATE "pg_catalog"."default",
  "bol_altitud" float8,
  "bol_reg_usu" int8 NOT NULL,
  "bol_reg_fecha" timestamp(6),
  "bol_act_usu" int8,
  "bol_act_fecha" timestamp(6),
  "bol_estado_boleta" varchar(255) COLLATE "pg_catalog"."default",
  "bol_eliminado" bool DEFAULT false,
  "bol_otra_exten_agri_inst" varchar(255) COLLATE "pg_catalog"."default",
  "bol_otra_nece_conoci" varchar(255) COLLATE "pg_catalog"."default",
  "bol_otro_prest_fuen" varchar(255) COLLATE "pg_catalog"."default",
  "bol_otro_prest_dest" varchar(255) COLLATE "pg_catalog"."default",
  "bol_otra_razon_no_ges_presta" varchar(255) COLLATE "pg_catalog"."default"
)
;
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_id" IS 'Identificador secuencial de la tabla';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_arado" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_autoconsumo_agricola" IS 'Opcion del catalogo 431 para destino produccion';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_autoconsumo_apicola" IS 'Opcion del catalogo 431 para destino produccion';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_autoconsumo_avicola" IS 'Opcion del catalogo 431 para destino produccion';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_autoconsumo_bovina" IS 'Opcion del catalogo 431 para destino produccion';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_autoconsumo_cuyes_conejo" IS 'Opcion del catalogo 431 para destino produccion';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_autoconsumo_forestal" IS 'Opcion del catalogo 431 para destino produccion';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_autoconsumo_otras_ave" IS 'Opcion del catalogo 431 para destino produccion';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_autoconsumo_ovino_caprino" IS 'Opcion del catalogo 431 para destino produccion';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_autoconsumo_porcicola" IS 'Opcion del catalogo 431 para destino produccion';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_bomba_agua" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_bomba_estacionaria_fumiga" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_bomba_mochila_motor" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_canton" IS 'Opcion del catalogo CANT para canton';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_canton_vive" IS 'Opcion del catalogo CANT para canton donde vive';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_carreton" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_codigo_encuestador" IS 'Codigo de persona que realiza el registro';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_codigo_UPA" IS 'Union de parroquiaDpa+poligono+numeroUPA+codigoEncuestador+numeroBoleta';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_comprador_agricola" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_comprador_apicola" IS 'Opcion del catalogo 145 para destino produccion comprador';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_comprador_avicola" IS 'Opcion del catalogo 145 para destino produccion comprador';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_comprador_bovina" IS 'Opcion del catalogo 145 para destino produccion comprador';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_comprador_cuyes_conejo" IS 'Opcion del catalogo 145 para destino produccion comprador';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_comprador_forestal" IS 'Opcion del catalogo 145 para destino produccion comprador';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_comprador_otras_ave" IS 'Opcion del catalogo 145 para destino produccion comprador';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_comprador_ovino_caprino" IS 'Opcion del catalogo 145 para destino produccion comprador';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_comprador_porcicola" IS 'Opcion del catalogo 145 para destino produccion comprador';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_cosechadora" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_desgranadora" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_direccion_email" IS 'Correo persona productora';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_distancia_al_domicilio" IS 'Distancia al domicilio desde terreno principal';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_empacadora" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_empacadora_forestal" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_enfardadora" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_ensiladora" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_estado" IS 'Estado de boleta para eliminado logico 11 activo, 12 eliminado';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_exten_agricola_institu" IS 'Institucion de la que recibio extension agricola';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_exten_agricola_recibida" IS 'Opcion del catalogo 444 para extension agricola';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_fangueadora" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_fertilizadora" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_fuente_agua_riego" IS 'Opcion del catalogo 147 para fuente de agua de riego';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_fumigadora" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_id_levanta" IS 'Codigo de boleta levanta, antes de registrar datos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_informante_relacion" IS 'Relacion de persona encuestado con el productor';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_informante_telefono" IS 'Contacto de persona encuestada si no es el productor';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_infraestructura_otra" IS 'Otra infraestructura presente en los terrenos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_acc_riego" IS 'Si tiene acceso a agua para riego';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_agri_familiar_camp" IS 'Acceso a beneficio por estado, registro agricultura familiar y campesina';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_agua_otro_medio" IS 'cceso a beneficio en vivienda,Agua por otros medios (tanquero, lluvia, río,etc.)';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_agua_por_tuberia" IS 'cceso a beneficio en vivienda,Agua por tuberia';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_asesoramiento_tecnico" IS 'Acceso a beneficio por el estado, asesoriamiento tecnico';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_asistencia_tecnica" IS 'Acceso a beneficio por el estado, asistencia tecnica';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_bodega" IS 'Infraestructura agricola en terreno entrevista, bodega';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_computadora" IS 'Persona productora acceso a computadora';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_construccion_secado" IS 'Construcciòn para el secado/fermentado';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_credito" IS 'Beneficio estado, credito';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_cuarto_maquinaria_riego" IS 'Infraestructura agricola, cuarto para maquinaria riego';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_empacador" IS 'Infraestructura agricola, empacador';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_energia_electrica" IS 'Energía eléctrica - red pública (medidor propio)';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_espacio_comercio" IS 'Espacios para comercializar (fìsicos o virtuales)';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_evita_erosion" IS 'Evitar erosion (terrazas, labranza minima, labranza cero)';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_gestion_financiamiento" IS 'Durante el ultimo año, gestiono financiamiento.';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_incorpora_abono" IS 'Incorporación de abonos orgánicos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_infraestructura" IS 'Beneficio por el estado, infraestructura';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_infraestructura_ninguno" IS 'Beneficio por el estado, ninguna infraestructura dada.';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_internet" IS 'Acceso a internet la persona productora';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_invernadero" IS 'Infraestructura agricola, posse invernadero';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_kit_agricola" IS 'Beneficio por el estado, kits agricola';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_legalizacion_tierra" IS 'Beneficio por el estado, legalizacion de tierra';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_maquinaria" IS 'Beneficio por el estado, maquinaria';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_ninguno" IS 'Beneficio por el estado, ninguna';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_no_realiza_mejora" IS 'Mejora de suelo, no realiza mejora';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_otra_practica_mejora" IS 'Mejora de suelo, otra mejora';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_pastoreo_rotativo" IS 'Mejora de suelo, pastoreo rotativo';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_pert_asociacion_coop" IS 'Persona productora pertenece a cooperativa';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_reservorio" IS 'Infraestructura agricola, posse reservorio';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_rota_cultivo" IS 'Mejora de suelos, rota cultivos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_servicio_higienico" IS 'Persona productora tiene servicio higienico';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_silo" IS 'Infraestructura agricola, silo';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_terreno_accede_riego" IS 'Almenos un terreno tiene acceso a riego';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_tratamiento_de_agua" IS 'Realiza tratamientos de agua de riego despues de usarlo';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_is_vacuna_agrocalidad" IS 'Beneficio  estado, campaña vacunacion agrocalidad';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_latitud" IS 'Latitud donde realizo entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_longitud" IS 'Longitud donde realizo entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_manejo_residuo_agricola" IS 'En el año anterior, como manejo residuo agricola';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_manejo_residuo_animal" IS 'En el año anterior, como manejo residuo animal';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_motocultor" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_motoguadania" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_motosierra" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_necesidad_conocimiento" IS 'Opcion del catalogo 464 para extensión rural, necesidad de conocimientos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_nombre_asociacion_coop" IS 'Nombre de cooperativa si persona productora pertenece';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_numero_boleta" IS 'Numero de boleta';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_ocasional_hombre_numero" IS 'Hombres, numero de personas mano de obra ocasional';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_ocasional_hombre_salario" IS 'Hombres, salario de mano de obra ocasional';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_ocasional_mujer_numero" IS 'Mujeres, numero de personas mano de obra ocasional';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_ocasional_mujer_salario" IS 'Mujeres ,salario de mano de obra ocasional';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_otra_practica_mejora" IS 'Mejora de suelos, otra practica';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_otro_beneficio_estado" IS 'Beneficio del estado, otro beneficio';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_otro_maquinaria_equipo" IS 'Otro equipo maquinaria nombre';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_otro_maquinaria_equipo_acc" IS 'Otra maquinaria equipo acceso catalogo 524';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_parroquia" IS 'Opcion catalogo PARR, de encuesta';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_parroquia_vive" IS 'Opcion catalogo PARR, parroquia donde vive persona productora';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_permanente_hombre_numero" IS 'Hombres, numero de personas mano de obra permanente';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_permanente_hombre_salario" IS 'Hombres ,salario de mano de obra permanente';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_permanente_mujer_numero" IS 'Mujeres, numero de personas mano de obra permanente';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_permanente_mujer_salario" IS 'Mujeres, numero de personas mano de obra permanente';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_persona_info_id" IS 'Id de persona informante si no es el productor';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_planta_electrica_termica" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_poligono" IS 'Valor de poligono, ubicacion geografica';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_prestamo_destino" IS 'Opcion del catalogo 432 para destino principal de prestamo';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_prestamo_fuente" IS 'Opcion del catalogo 187 para fuente de prestamo';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_prestamo_negacion" IS 'Opcion del catalogo 456 para negacion de prestamo';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_prestamo_persona" IS 'Opcion del catalogo 520 quien obtuvo el prestamo';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_prestamo_razon_no_gestiono" IS 'Razon para no gestionar prestamo';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_prin_manejo_envase" IS 'Opcion catalogo 519 principal manejo de los envases';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_provincia" IS 'Opcion catalogo PROV, provincia de encuesta';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_provincia_vive" IS 'Opcion catalogo PROV, provincia donde vive persona productora';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_rastra" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_respuesta_negativa_miembro" IS 'Opcion catalogo 516 razon de no pertenecer a cooperativa';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_romplow" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_rotocultor" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_secadora" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_sector_muestreo" IS 'Sector de muestreo, ubicacion geografica';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_segadora" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_sembradora" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_sistema_agua_riego" IS 'Opcion del catalogo 148 donde proviene el agua de riego';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_sitio_agricola" IS 'Opcion del catalogo 234 sitio para comercializar';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_sitio_apicola" IS 'Opcion del catalogo 234 sitio para comercializar';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_sitio_avicola" IS 'Opcion del catalogo 234 sitio para comercializar';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_sitio_bovina" IS 'Opcion del catalogo 234 sitio para comercializar';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_sitio_cuyes_conejo" IS 'Opcion del catalogo 234 sitio para comercializar';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_sitio_forestal" IS 'Opcion del catalogo 234 sitio para comercializar';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_sitio_otras_ave" IS 'Opcion del catalogo 234 sitio para comercializar';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_sitio_ovino_caprino" IS 'Opcion del catalogo 234 sitio para comercializar';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_sitio_porcicola" IS 'Opcion del catalogo 234 sitio para comercializar';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_subsoladora" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_surcadora" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_telefono_celular" IS 'Medio comunicacion persona productora celular';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_telefono_convencional" IS 'Medio comunicacion persona productora telefono';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_tipo_de_miembro" IS 'Opcion del catalogo 469, tipo de miembro si pertenece a cooperativa';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_tractor_forestal" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_tractor_jardin" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_tractor_oruga" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_tractor_rueda" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_trilladora" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_bomba_mochila" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bov_id" IS 'Identificador del registro bovino';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."peot_id" IS 'Identificador del registro pecuario otro';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."pol_id" IS 'Identificador del registro pollo';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."por_id" IS 'Identificador del registro porcino';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."per_id" IS 'Identificador del registro persona productor';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_numero_UPA" IS 'Numero de UPA';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_manejo_res_animal_otro" IS 'Otro manejo de residuo animal';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_manejo_res_agricola_otro" IS 'Otro manejo de residuo agricola';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_manejo_envase_otro" IS 'Otro manejo de envase principal';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_otro_prest_nega" IS 'Otra razon de negacion de prestamo';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_altitud" IS 'Altitud donde realizo la entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_reg_usu" IS 'Identificador de usuario que registra';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_reg_fecha" IS 'Fecha cuando registra';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_act_usu" IS 'Identificador de usuario que actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_act_fecha" IS 'Fecha cuando actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_estado_boleta" IS 'Estado de boleta';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_eliminado" IS 'Eliminado logico forzado por MAG';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_otra_exten_agri_inst" IS 'Otra extension agricola desde institucion recibida';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_otra_nece_conoci" IS 'Otra mayor nesesidad de conocimientos';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_otro_prest_fuen" IS 'Otra opcion para fuente de prestamo';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_otro_prest_dest" IS 'Otra opcion para destino de prestamo';
COMMENT ON COLUMN "sc_renagro_mag"."boletas"."bol_otra_razon_no_ges_presta" IS 'Otra razon de que no gestiono prestamo';

-- ----------------------------
-- Table structure for bovinos
-- ----------------------------
DROP TABLE IF EXISTS "sc_renagro_mag"."bovinos";
CREATE TABLE "sc_renagro_mag"."bovinos" (
  "bov_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_bov_id'::regclass),
  "bov_capacidad_total_explo" int4,
  "bov_doble_prop_ajeno" int4,
  "bov_doble_prop_propio" int4,
  "bov_galpones_numero" int4,
  "bov_is_ninguna_vacuna" bool,
  "bov_is_no_sabe_vacuna" bool,
  "bov_ordeniadora" varchar COLLATE "pg_catalog"."default",
  "bov_tanque_enfriamiento" varchar COLLATE "pg_catalog"."default",
  "bov_is_vaca_ordeniada_ayer" bool,
  "bov_is_vacuna_brucelosi" bool,
  "bov_is_vacuna_carbunco" bool,
  "bov_is_vacuna_fiebre_aftosa" bool,
  "bov_is_vacuna_ibr" bool,
  "bov_is_vacuna_papilomatosis" bool,
  "bov_litros_leche_obtenido" int4,
  "bov_no_sabe_prop" int4,
  "bov_otra_vacuna" varchar(255) COLLATE "pg_catalog"."default",
  "bov_prin_forma_reproduccion" varchar(255) COLLATE "pg_catalog"."default",
  "bov_prin_produ_ganado" varchar(255) COLLATE "pg_catalog"."default",
  "bov_prop_para_carne_ajeno" int4,
  "bov_prop_para_carne_propio" int4,
  "bov_prop_para_leche_ajeno" int4,
  "bov_prop_para_leche_propio" int4,
  "bov_subtotal_propio" int4,
  "bov_subtotal_ajeno" int4,
  "bov_subtotal_hembra" int4,
  "bov_subtotal_macho" int4,
  "bov_ternera" int4,
  "bov_ternero" int4,
  "bov_torete" int4,
  "bov_toro" int4,
  "bov_total_ganado" int4,
  "bov_total_ganado_prop" int4,
  "bov_vacas_en_produ" int4,
  "bov_vacas_seca" int4,
  "bov_vacona" int4,
  "bov_reg_usu" int8 NOT NULL,
  "bov_reg_fecha" timestamp(6),
  "bov_act_usu" int8,
  "bov_act_fecha" timestamp(6),
  "bov_estado" int4 DEFAULT 11,
  "bov_eliminado" bool DEFAULT false
)
;
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_id" IS 'Identificador secuencial de la tabla';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_capacidad_total_explo" IS 'Capacidad total de explotacion bovino';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_doble_prop_ajeno" IS 'Cabeza de ganado ajeno, numero para doble proposito';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_doble_prop_propio" IS 'Cabeza de ganado propio, numero para doble proposito';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_galpones_numero" IS 'Numero de galpones para manejo bovino';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_is_ninguna_vacuna" IS 'No ha recibido ninguna vacuna';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_is_no_sabe_vacuna" IS 'No sabe/ no responde sobre vacuna';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_ordeniadora" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_tanque_enfriamiento" IS 'Opcion del catalogo 524 para implementos';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_is_vaca_ordeniada_ayer" IS 'Si las vacas fueron ordeñadas el dia de ayer';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_is_vacuna_brucelosi" IS 'Si posse vacuna brucelosis';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_is_vacuna_carbunco" IS 'Si posse vacuna Carbunco (carbón)';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_is_vacuna_fiebre_aftosa" IS 'Si posse vacuna Fiebre aftosa';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_is_vacuna_ibr" IS 'IBR (Rinotraqueitis infecciosa bovina)';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_is_vacuna_papilomatosis" IS 'Si posse vacuna brucelosis';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_litros_leche_obtenido" IS 'Numero de litros de leche obtenido en total';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_no_sabe_prop" IS 'Del total de cabezas de ganado cuantas no sabe el proposito';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_otra_vacuna" IS 'Otro tipo de vacuna';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_prin_forma_reproduccion" IS 'Opcion del catalogo 154, cual es la principal forma de reproduccion';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_prin_produ_ganado" IS 'Opcion del catalogo 462, principal sistema de produccion de ganado';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_prop_para_carne_ajeno" IS 'Cabeza de ganado ajeno, numero para carne';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_prop_para_carne_propio" IS 'Cabeza de ganado propio, numero para carne';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_prop_para_leche_ajeno" IS 'Cabeza de ganado ajeno, numero para leche';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_prop_para_leche_propio" IS 'Cabeza de ganado propio, numero para leche';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_subtotal_propio" IS 'Subtotal de cabeza ganado propio';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_subtotal_ajeno" IS 'Subtotal de cabeza ganado ajeno';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_subtotal_hembra" IS 'Subtotal de cabeza ganado hembra';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_subtotal_macho" IS 'Subtotal de cabeza ganado macho';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_ternera" IS 'Numero de terneras(menor a 1 año)';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_ternero" IS 'Numero de terneros(menor a 1 año)';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_torete" IS 'Numero de toretes (entre 1 y 2 años) ';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_toro" IS 'Numero de toros (mas de 2 años)';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_total_ganado" IS 'Total del ganado subtotalMachos+subtotalHembras';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_total_ganado_prop" IS 'Total del ganado proposito noSabeProposito+subtotalAjenos+subtalPropio';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_vacas_en_produ" IS 'Numero de VACAS (>2 años) en produccion';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_vacas_seca" IS 'Numero de VACAS (>2 años) secas';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_vacona" IS 'Numero de VACONAS (entre 1 y 2 años)';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_reg_usu" IS 'Identificador de usuario que registra';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_reg_fecha" IS 'Fecha cuando registra';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_act_usu" IS 'Identificador de usuario que actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_act_fecha" IS 'Fecha cuando actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_estado" IS 'Estado de registro para eliminado logico 11 activo, 12 eliminado';
COMMENT ON COLUMN "sc_renagro_mag"."bovinos"."bov_eliminado" IS 'Eliminado logico forzado por MAG';

-- ----------------------------
-- Table structure for cultivos
-- ----------------------------
DROP TABLE IF EXISTS "sc_renagro_mag"."cultivos";
CREATE TABLE "sc_renagro_mag"."cultivos" (
  "cul_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_cul_id'::regclass),
  "cul_forma_cultivar" varchar(255) COLLATE "pg_catalog"."default",
  "cul_cultivo_asociado" varchar(255) COLLATE "pg_catalog"."default",
  "cul_is_certificacion_organica" bool,
  "cul_is_control_plagas_organico" bool,
  "cul_is_control_plagas_quimico" bool,
  "cul_is_lleva_registro_prod" bool,
  "cul_is_seguro_agricola" bool,
  "cul_is_uso_fert_organico" bool,
  "cul_is_uso_fert_quimico" bool,
  "cul_is_uso_material_vegetativo" bool,
  "cul_is_uso_semilla_nativa_camp" bool,
  "cul_metodo_de_riego" varchar(255) COLLATE "pg_catalog"."default",
  "cul_nombre_cultivo" varchar(255) COLLATE "pg_catalog"."default",
  "cul_sacos_de_urea_usado" int4,
  "cul_superficie_plantada" float8,
  "cul_superficie_plantada_unidad" varchar(255) COLLATE "pg_catalog"."default",
  "cul_superficie_riego" float8,
  "cul_superficie_riego_unidad" varchar(255) COLLATE "pg_catalog"."default",
  "ter_id" int8,
  "cul_reg_usu" int8 NOT NULL,
  "cul_reg_fecha" timestamp(6),
  "cul_act_usu" int8,
  "cul_act_fecha" timestamp(6),
  "cul_estado" int4 DEFAULT 11,
  "cul_eliminado" bool DEFAULT false,
  "cul_otro_nombre_cultivo" varchar(255) COLLATE "pg_catalog"."default"
)
;
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_id" IS 'Identificador secuencial de la tabla';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_forma_cultivar" IS 'Opcion del catalogo 177, forma de cultivar';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_cultivo_asociado" IS 'Opcion del catalogo 139, cultivo asociado a';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_is_certificacion_organica" IS 'Si cultivo cuenta con certificacion organica';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_is_control_plagas_organico" IS 'Control de plagas, uso insumos organicos';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_is_control_plagas_quimico" IS 'Control de plagas, uso insumos quimicos';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_is_lleva_registro_prod" IS 'Persona productora lleva registro de produccion';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_is_seguro_agricola" IS 'Si tiene seguro agricola';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_is_uso_fert_organico" IS 'Uso fertilizante de origen organico';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_is_uso_fert_quimico" IS 'Uso fertilizante de origen quimico';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_is_uso_material_vegetativo" IS 'Utilizó material vegetativo certificado';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_is_uso_semilla_nativa_camp" IS 'Utilizó semillas nativas o campesinas';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_metodo_de_riego" IS 'Opcion del catalogo 146, principal método de riego';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_nombre_cultivo" IS 'Nombre del cultivo';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_sacos_de_urea_usado" IS 'Cuántos sacos de ÚREA utilizó';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_superficie_plantada" IS 'Superficie Plantada/Sembrada';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_superficie_plantada_unidad" IS 'Unidad para medir Superficie Plantada/Sembrada';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_superficie_riego" IS 'Superficie Plantada/Sembrada que recibe riego';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_superficie_riego_unidad" IS 'Unidad para superficie Plantada/Sembrada que recibe riego';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."ter_id" IS 'Identificador del terreno donde se encuentra el cultivo';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_reg_usu" IS 'Identificador de usuario que registra';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_reg_fecha" IS 'Fecha cuando registra';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_act_usu" IS 'Identificador de usuario que actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_act_fecha" IS 'Fecha cuando actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_estado" IS 'Estado de registro para eliminado logico 11 activo, 12 eliminado';
COMMENT ON COLUMN "sc_renagro_mag"."cultivos"."cul_eliminado" IS 'Eliminado logico forzado por MAG';

-- ----------------------------
-- Table structure for forestales
-- ----------------------------
DROP TABLE IF EXISTS "sc_renagro_mag"."forestales";
CREATE TABLE "sc_renagro_mag"."forestales" (
  "for_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_for_id'::regclass),
  "for_edad_especie" int4,
  "for_nombre_especie" varchar(255) COLLATE "pg_catalog"."default",
  "for_principal_destino_uso" varchar(255) COLLATE "pg_catalog"."default",
  "for_superficie_plantada" float8,
  "for_superficie_plantada_unidad" varchar(255) COLLATE "pg_catalog"."default",
  "ter_id" int8,
  "for_reg_usu" int8 NOT NULL,
  "for_reg_fecha" timestamp(6),
  "for_act_usu" int8,
  "for_act_fecha" timestamp(6),
  "for_estado" int4 DEFAULT 11,
  "for_eliminado" bool DEFAULT false,
  "for_otro_nombre_especie" varchar(255) COLLATE "pg_catalog"."default"
)
;
COMMENT ON COLUMN "sc_renagro_mag"."forestales"."for_id" IS 'Identificador secuencial de la tabla';
COMMENT ON COLUMN "sc_renagro_mag"."forestales"."for_edad_especie" IS 'Edad de la especie forestal';
COMMENT ON COLUMN "sc_renagro_mag"."forestales"."for_nombre_especie" IS 'Nombre de la especie forestal';
COMMENT ON COLUMN "sc_renagro_mag"."forestales"."for_principal_destino_uso" IS 'Principal uso del cultivo forestal';
COMMENT ON COLUMN "sc_renagro_mag"."forestales"."for_superficie_plantada" IS 'Medida del cultivo forestal';
COMMENT ON COLUMN "sc_renagro_mag"."forestales"."for_superficie_plantada_unidad" IS 'Unidad de medidad de la superficie plantada';
COMMENT ON COLUMN "sc_renagro_mag"."forestales"."ter_id" IS 'Identificador del terreno donde se encuentra el cultivo forestal';
COMMENT ON COLUMN "sc_renagro_mag"."forestales"."for_reg_usu" IS 'Identificador de usuario que registra';
COMMENT ON COLUMN "sc_renagro_mag"."forestales"."for_reg_fecha" IS 'Fecha cuando registra';
COMMENT ON COLUMN "sc_renagro_mag"."forestales"."for_act_usu" IS 'Identificador de usuario que actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."forestales"."for_act_fecha" IS 'Fecha cuando actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."forestales"."for_estado" IS 'Estado de registro para eliminado logico 11 activo, 12 eliminado';
COMMENT ON COLUMN "sc_renagro_mag"."forestales"."for_eliminado" IS 'Eliminado logico forzado por MAG';

-- ----------------------------
-- Table structure for miembros_hogar
-- ----------------------------
DROP TABLE IF EXISTS "sc_renagro_mag"."miembros_hogar";
CREATE TABLE "sc_renagro_mag"."miembros_hogar" (
  "miho_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_miho_id'::regclass),
  "miho_anio_mas_alto_aprob" int4,
  "miho_autoidentificacion" varchar(255) COLLATE "pg_catalog"."default",
  "miho_identificacion" varchar(255) COLLATE "pg_catalog"."default",
  "miho_edad" int4,
  "miho_genero" varchar(255) COLLATE "pg_catalog"."default",
  "miho_hogar_numero" int4,
  "miho_horas_otras_resp" int4,
  "miho_is_fue_remunerado" bool,
  "miho_manejo_terrenos" varchar(255) COLLATE "pg_catalog"."default",
  "miho_nivel_instruccion" varchar(255) COLLATE "pg_catalog"."default",
  "miho_numero_horas_semanales" int4,
  "miho_primer_apellido" varchar(255) COLLATE "pg_catalog"."default",
  "miho_primer_nombre" varchar(255) COLLATE "pg_catalog"."default",
  "miho_relacion_persona_prod" varchar(255) COLLATE "pg_catalog"."default",
  "bol_id" int8,
  "miho_tipo_identificacion" varchar(255) COLLATE "pg_catalog"."default",
  "miho_reg_usu" int8 NOT NULL,
  "miho_reg_fecha" timestamp(6),
  "miho_act_usu" int8,
  "miho_act_fecha" timestamp(6),
  "miho_estado" int4 DEFAULT 11,
  "miho_eliminado" bool DEFAULT false
)
;
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_id" IS 'Identificador secuencial de la tabla';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_anio_mas_alto_aprob" IS 'Año mas que aprobo';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_autoidentificacion" IS 'Opcion del catalogo 132, auto-identificacion del miembro hogar';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_identificacion" IS 'Numero de identificacion';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_edad" IS 'Edad (años) del miembro';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_genero" IS 'Opcion del catalogo 8, genero';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_hogar_numero" IS 'Numero del miembro hogar';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_horas_otras_resp" IS 'Numero de horas de otras responsabilidades';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_is_fue_remunerado" IS 'Si fue remunerado el trabajo dentro de los terrenos';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_manejo_terrenos" IS 'Opcion del catalogo 521, decicion sobre el manejo de terrenos';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_nivel_instruccion" IS 'Nivel de instruccion maxima alcanzada';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_numero_horas_semanales" IS 'Numero de horas semanales empleados dentro de los terrenos';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_primer_apellido" IS 'Primer apellido del miembro hogar';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_primer_nombre" IS 'Primer nombre del miembro hogar';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_relacion_persona_prod" IS 'Opcion del catalogo 192, parentesco con la persona productora';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."bol_id" IS 'Identificador de la boleta a donde pertenece miembro hogar';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_tipo_identificacion" IS 'Tipo de identificacion del miembro hogar';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_reg_usu" IS 'Identificador de usuario que registra';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_reg_fecha" IS 'Fecha cuando registra';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_act_usu" IS 'Identificador de usuario que actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_act_fecha" IS 'Fecha cuando actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_estado" IS 'Estado de registro para eliminado logico 11 activo, 12 eliminado';
COMMENT ON COLUMN "sc_renagro_mag"."miembros_hogar"."miho_eliminado" IS 'Eliminado logico forzado por MAG';

-- ----------------------------
-- Table structure for pecuarios_otros
-- ----------------------------
DROP TABLE IF EXISTS "sc_renagro_mag"."pecuarios_otros";
CREATE TABLE "sc_renagro_mag"."pecuarios_otros" (
  "peot_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_peot_id'::regclass),
  "peot_alpaca" int4,
  "peot_avestruce" int4,
  "peot_codornice" int4,
  "peot_colmena_abeja_melifera" int4,
  "peot_colmena_abeja_melipona" int4,
  "peot_conejo" int4,
  "peot_cuy" int4,
  "peot_ganado_asno" int4,
  "peot_ganado_caballar" int4,
  "peot_ganado_caprino" int4,
  "peot_ganado_mular" int4,
  "peot_ganado_ovino" int4,
  "peot_llama" int4,
  "peot_otra_especie" int4,
  "peot_pato" int4,
  "peot_pavo" int4,
  "peot_otra_especie_nombre" varchar(255) COLLATE "pg_catalog"."default",
  "peot_reg_usu" int8 NOT NULL,
  "peot_reg_fecha" timestamp(6),
  "peot_act_usu" int8,
  "peot_act_fecha" timestamp(6),
  "peot_estado" int4 DEFAULT 11,
  "peot_eliminado" bool DEFAULT false
)
;
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_id" IS 'Identificador secuencial de la tabla';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_alpaca" IS 'Numero de especies en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_avestruce" IS 'Numero de especies en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_codornice" IS 'Numero de especies en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_colmena_abeja_melifera" IS 'Numero de especies en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_colmena_abeja_melipona" IS 'Numero de especies en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_conejo" IS 'Numero de especies en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_cuy" IS 'Numero de especies en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_ganado_asno" IS 'Numero de especies en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_ganado_caballar" IS 'Numero de especies en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_ganado_caprino" IS 'Numero de especies en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_ganado_mular" IS 'Numero de especies en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_ganado_ovino" IS 'Numero de especies en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_llama" IS 'Numero de especies en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_otra_especie" IS 'Numero de otra especie en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_pato" IS 'Numero de especies en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_pavo" IS 'Numero de especies en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_otra_especie_nombre" IS 'Nombre de otra especie en terrenos de entrevista';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_reg_usu" IS 'Identificador de usuario que registra';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_reg_fecha" IS 'Fecha cuando registra';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_act_usu" IS 'Identificador de usuario que actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_act_fecha" IS 'Fecha cuando actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_estado" IS 'Estado de registro para eliminado logico 11 activo, 12 eliminado';
COMMENT ON COLUMN "sc_renagro_mag"."pecuarios_otros"."peot_eliminado" IS 'Eliminado logico forzado por MAG';

-- ----------------------------
-- Table structure for personas
-- ----------------------------
DROP TABLE IF EXISTS "sc_renagro_mag"."personas";
CREATE TABLE "sc_renagro_mag"."personas" (
  "per_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_per_id'::regclass),
  "per_identificacion" varchar(255) COLLATE "pg_catalog"."default",
  "per_persona_natural" bool,
  "per_primer_apellido" varchar(255) COLLATE "pg_catalog"."default",
  "per_primer_nombre" varchar(255) COLLATE "pg_catalog"."default",
  "per_razon_social" varchar(255) COLLATE "pg_catalog"."default",
  "per_segundo_apellido" varchar(255) COLLATE "pg_catalog"."default",
  "per_segundo_nombre" varchar(255) COLLATE "pg_catalog"."default",
  "per_tipo_identificacion" varchar(255) COLLATE "pg_catalog"."default",
  "per_reg_usu" int8 NOT NULL,
  "per_reg_fecha" timestamp(6),
  "per_act_usu" int8,
  "per_act_fecha" timestamp(6),
  "per_estado" int4 DEFAULT 11,
  "per_eliminado" bool DEFAULT false
)
;
COMMENT ON COLUMN "sc_renagro_mag"."personas"."per_id" IS 'Identificador secuencial de la tabla';
COMMENT ON COLUMN "sc_renagro_mag"."personas"."per_identificacion" IS 'Valor de identificacion de persona productora';
COMMENT ON COLUMN "sc_renagro_mag"."personas"."per_persona_natural" IS 'Si persona productora es persona natura';
COMMENT ON COLUMN "sc_renagro_mag"."personas"."per_primer_apellido" IS 'Primer apellido de persona productora';
COMMENT ON COLUMN "sc_renagro_mag"."personas"."per_primer_nombre" IS 'Primer nombre de persona productora';
COMMENT ON COLUMN "sc_renagro_mag"."personas"."per_razon_social" IS 'Razon social de persona productora';
COMMENT ON COLUMN "sc_renagro_mag"."personas"."per_segundo_apellido" IS 'Segundo apellido de persona productora';
COMMENT ON COLUMN "sc_renagro_mag"."personas"."per_segundo_nombre" IS 'Segundo nombre de persona productora';
COMMENT ON COLUMN "sc_renagro_mag"."personas"."per_tipo_identificacion" IS 'Opcion de catalogo 7, tipo de identificacion';
COMMENT ON COLUMN "sc_renagro_mag"."personas"."per_reg_usu" IS 'Identificador de usuario que registra';
COMMENT ON COLUMN "sc_renagro_mag"."personas"."per_reg_fecha" IS 'Fecha cuando registra';
COMMENT ON COLUMN "sc_renagro_mag"."personas"."per_act_usu" IS 'Identificador de usuario que actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."personas"."per_act_fecha" IS 'Fecha cuando actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."personas"."per_estado" IS 'Estado de registro para eliminado logico 11 activo, 12 eliminado';
COMMENT ON COLUMN "sc_renagro_mag"."personas"."per_eliminado" IS 'Eliminado logico forzado por MAG';

-- ----------------------------
-- Table structure for pollos
-- ----------------------------
DROP TABLE IF EXISTS "sc_renagro_mag"."pollos";
CREATE TABLE "sc_renagro_mag"."pollos" (
  "pol_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_pol_id'::regclass),
  "pol_explotacion_pollo" int4,
  "pol_galpones_pollo" int4,
  "pol_is_bronquitis_enfer" bool,
  "pol_is_gumboro_enfer" bool,
  "pol_is_llaringotraqueitis_enf" bool,
  "pol_is_mycoplasma_enfer" bool,
  "pol_is_newcastle_enfer" bool,
  "pol_is_ninguna_enfer" bool,
  "pol_otra_enfermedad" varchar COLLATE "pg_catalog"."default",
  "pol_is_salmonella_enfer" bool,
  "pol_is_trt_enfer" bool,
  "pol_num_aves_traspatio" int4,
  "pol_num_broiler" int4,
  "pol_num_ciclos_broiler" int4,
  "pol_num_ciclos_ponedora" int4,
  "pol_num_ciclos_repro_liviano" int4,
  "pol_num_ciclos_repro_pesado" int4,
  "pol_num_ponedora" int4,
  "pol_num_repro_liviano" int4,
  "pol_num_repro_pesado" int4,
  "pol_otra_razon_no_registro" varchar(255) COLLATE "pg_catalog"."default",
  "pol_is_pollos_corresponde" bool,
  "pol_razon_no_registro" varchar(255) COLLATE "pg_catalog"."default",
  "pol_reg_usu" int8 NOT NULL,
  "pol_reg_fecha" timestamp(6),
  "pol_act_usu" int8,
  "pol_act_fecha" timestamp(6),
  "pol_estado" int4 DEFAULT 11,
  "pol_eliminado" bool DEFAULT false
)
;
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_id" IS 'Identificador secuencial de la tabla';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_explotacion_pollo" IS 'Capacidad máxima de aves en la explotación';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_galpones_pollo" IS 'Numero de galpones para pollos';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_is_bronquitis_enfer" IS 'Vacuno contra Bronquitis (gripe)';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_is_gumboro_enfer" IS 'Vacuno contra Gumboro (plumas erizadas)';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_is_llaringotraqueitis_enf" IS 'Vacuno contra Laringotraqueitis (tos y jadeo)';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_is_mycoplasma_enfer" IS 'Vacuno contra Mycoplasma (mocos)';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_is_newcastle_enfer" IS 'Vacuno contra Newcastle (parálisis)';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_is_ninguna_enfer" IS 'No vacuno contra enfermedades';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_otra_enfermedad" IS 'Vacuno contra otra efermedad, nombre';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_is_salmonella_enfer" IS 'Vacuno contra Salmonella (diarrea)';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_is_trt_enfer" IS 'Vacuno contra TRT (cabeza hinchada)';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_num_aves_traspatio" IS 'Aves de traspatio, numero de aves';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_num_broiler" IS 'Aves de plantel, Numero Broilers (engorde)';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_num_ciclos_broiler" IS 'Aves de plantel, No. Ciclos en el año anterior Broilers (engorde)';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_num_ciclos_ponedora" IS 'Aves de plantel, No. Ciclos en el año anterior Ponedoras';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_num_ciclos_repro_liviano" IS 'Aves de plantel,  No. Ciclos en el año anterior Reproductoras livianas';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_num_ciclos_repro_pesado" IS 'Aves de plantel, No. Ciclos en el año anterior Reproductoras pesadas';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_num_ponedora" IS 'Aves de plantel, Numero de ponedoras';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_num_repro_liviano" IS 'Aves de plantel, Numero Reproductoras livianas';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_num_repro_pesado" IS 'Aves de plantel, Numero Reproductoras pesadas';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_otra_razon_no_registro" IS 'Otra razon no registro pollo de traspatio o plantel';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_is_pollos_corresponde" IS 'Pollos corresponden a *Aves plantel: true, *Aves de traspatio: false';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_razon_no_registro" IS 'Opcion de catalogo 523, razon no registro aves';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_reg_usu" IS 'Identificador de usuario que registra';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_reg_fecha" IS 'Fecha cuando registra';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_act_usu" IS 'Identificador de usuario que actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_act_fecha" IS 'Fecha cuando actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_estado" IS 'Estado de registro para eliminado logico 11 activo, 12 eliminado';
COMMENT ON COLUMN "sc_renagro_mag"."pollos"."pol_eliminado" IS 'Eliminado logico forzado por MAG';

-- ----------------------------
-- Table structure for porcinos
-- ----------------------------
DROP TABLE IF EXISTS "sc_renagro_mag"."porcinos";
CREATE TABLE "sc_renagro_mag"."porcinos" (
  "por_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_por_id'::regclass),
  "por_capaci_explot_cerdo" int4,
  "por_fuente_reprodruccion_por" varchar(255) COLLATE "pg_catalog"."default",
  "por_galpon_existente_por" int4,
  "por_is_colibacilosis_diarrea" bool,
  "por_is_fiebre_aftosa" bool,
  "por_is_neumonía_por_enzootica" bool,
  "por_is_ninguna" bool,
  "por_is_no_sabe_no_responde" bool,
  "por_is_otra" bool,
  "por_is_parvovirus_moquera" bool,
  "por_is_pasteurella_neumonia" bool,
  "por_is_peste_por_clasica" bool,
  "por_mas_dos_mes_hembra_por" int4,
  "por_mas_dos_mes_macho_por" int4,
  "por_menos_dos_mes_hembra_por" int4,
  "por_menos_dos_mes_macho_por" int4,
  "por_propio_hembra_por" int4,
  "por_propio_macho_por" int4,
  "por_reproductor_hembra_por" int4,
  "por_reproductor_macho_por" int4,
  "por_total_hembra_por" int4,
  "por_total_macho_por" int4,
  "por_reg_usu" int8 NOT NULL,
  "por_reg_fecha" timestamp(6),
  "por_act_usu" int8,
  "por_act_fecha" timestamp(6),
  "por_estado" int4 DEFAULT 11,
  "por_eliminado" bool DEFAULT false
)
;
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_id" IS 'Identificador secuencial de la tabla';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_capaci_explot_cerdo" IS 'Máxima capacidad de la explotación en número de cerdos';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_fuente_reprodruccion_por" IS 'Opcion del catalogo 161, forma de reproducción del ganado porcino';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_galpon_existente_por" IS 'Numero de galpones existentes para porcinos';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_is_colibacilosis_diarrea" IS 'Vacuno contra Colibacilosis (diarrea)';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_is_fiebre_aftosa" IS 'Vacuno contra Fiebre aftosa';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_is_neumonía_por_enzootica" IS 'Vacuno contra Neumonía Porcina Enzootica (tos)';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_is_ninguna" IS 'No vacuno contra ninguna enfermedad';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_is_no_sabe_no_responde" IS 'No sabe o no responde si vacuno';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_is_otra" IS 'Es otra vacuna';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_is_parvovirus_moquera" IS 'Vacuno contra Parvovirus-leptospirosis-erisipela (moquera)';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_is_pasteurella_neumonia" IS 'Vacuno contra Pasteurella (neumonía)';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_is_peste_por_clasica" IS 'Vacuno contra Peste porcina clásica (PPC)';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_mas_dos_mes_hembra_por" IS 'Porcino hembra mas de dos meses';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_mas_dos_mes_macho_por" IS 'Porcino macho mas de dos meses';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_menos_dos_mes_hembra_por" IS 'Porcino hembra menos de dos meses';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_menos_dos_mes_macho_por" IS 'Porcino macho menos de dos meses';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_propio_hembra_por" IS 'Hembras Del total, ¿cuantos son propios?';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_propio_macho_por" IS 'Machos Del total, ¿cuantos son propios?';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_reproductor_hembra_por" IS 'Hembras Del total, ¿cuantos son reproductores?';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_reproductor_macho_por" IS 'Machos Del total, ¿cuantos son reproductores?';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_total_hembra_por" IS 'Ganado porcino hembra total';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_total_macho_por" IS 'Ganado porcino macho total';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_reg_usu" IS 'Identificador de usuario que registra';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_reg_fecha" IS 'Fecha cuando registra';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_act_usu" IS 'Identificador de usuario que actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_act_fecha" IS 'Fecha cuando actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_estado" IS 'Estado de registro para eliminado logico 11 activo, 12 eliminado';
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_eliminado" IS 'Eliminado logico forzado por MAG';

-- ----------------------------
-- Table structure for terrenos
-- ----------------------------
DROP TABLE IF EXISTS "sc_renagro_mag"."terrenos";
CREATE TABLE "sc_renagro_mag"."terrenos" (
  "ter_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_ter_id'::regclass),
  "ter_acceso_tierra" varchar(255) COLLATE "pg_catalog"."default",
  "ter_cobertura_tierra" varchar(255) COLLATE "pg_catalog"."default",
  "ter_is_cultivo_en_terreno" bool,
  "ter_is_infraestructura" bool,
  "ter_is_mano_de_obra" bool,
  "ter_is_maquinaria_implemento" bool,
  "ter_is_terreno_principal" bool,
  "ter_superficie" float8,
  "ter_superficie_unidad" varchar(255) COLLATE "pg_catalog"."default",
  "ter_tenencia" varchar(255) COLLATE "pg_catalog"."default",
  "ter_terreno_numero" int4,
  "bol_id" int8,
  "ter_reg_usu" int8 NOT NULL,
  "ter_reg_fecha" timestamp(6),
  "ter_act_usu" int8,
  "ter_act_fecha" timestamp(6),
  "ter_estado" int4 DEFAULT 11,
  "ter_eliminado" bool DEFAULT false
)
;
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_id" IS 'Identificador secuencial de la tabla';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_acceso_tierra" IS 'Opcion del catalogo 504, acceso a la tierra';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_cobertura_tierra" IS 'Opcion del catalogo 505, cobertura de uso de la tierra';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_is_cultivo_en_terreno" IS 'Existe cultivo en el terreno';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_is_infraestructura" IS 'Posee infraestructura agricola en el terreno';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_is_mano_de_obra" IS 'Posee mano de obra en el terreno';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_is_maquinaria_implemento" IS 'Posse maquinaria en el terreno';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_is_terreno_principal" IS 'Si es el terreno principal';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_superficie" IS 'Valor de superficie del terreno';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_superficie_unidad" IS 'Unidad de medida de la superficie del terreno';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_tenencia" IS 'Opcion del catalogo 466, tenencia de la tierra';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_terreno_numero" IS 'Numero del terreno';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."bol_id" IS 'Identificador de boleta a donde pertenece ganado';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_reg_usu" IS 'Identificador de usuario que registra';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_reg_fecha" IS 'Fecha cuando registra';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_act_usu" IS 'Identificador de usuario que actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_act_fecha" IS 'Fecha cuando actualiza registro';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_estado" IS 'Estado de registro para eliminado logico 11 activo, 12 eliminado';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos"."ter_eliminado" IS 'Eliminado logico forzado por MAG';

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"sc_renagro_mag"."seq_aud_id"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"sc_renagro_mag"."seq_bol_id"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"sc_renagro_mag"."seq_bov_id"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"sc_renagro_mag"."seq_cul_id"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"sc_renagro_mag"."seq_for_id"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"sc_renagro_mag"."seq_miho_id"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"sc_renagro_mag"."seq_peot_id"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"sc_renagro_mag"."seq_per_id"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"sc_renagro_mag"."seq_pol_id"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"sc_renagro_mag"."seq_por_id"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"sc_renagro_mag"."seq_ter_id"', 1, true);

-- ----------------------------
-- Primary Key structure for table auditorias
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."auditorias" ADD CONSTRAINT "auditorias_pkey" PRIMARY KEY ("aud_id");

-- ----------------------------
-- Primary Key structure for table boletas
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."boletas" ADD CONSTRAINT "pk_boleta" PRIMARY KEY ("bol_id");

-- ----------------------------
-- Primary Key structure for table bovinos
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."bovinos" ADD CONSTRAINT "pk_bovino" PRIMARY KEY ("bov_id");

-- ----------------------------
-- Primary Key structure for table cultivos
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."cultivos" ADD CONSTRAINT "pk_cultivo" PRIMARY KEY ("cul_id");

-- ----------------------------
-- Primary Key structure for table forestales
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."forestales" ADD CONSTRAINT "pk_forestal" PRIMARY KEY ("for_id");

-- ----------------------------
-- Primary Key structure for table miembros_hogar
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."miembros_hogar" ADD CONSTRAINT "pk_miembro_hogar" PRIMARY KEY ("miho_id");

-- ----------------------------
-- Primary Key structure for table pecuarios_otros
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."pecuarios_otros" ADD CONSTRAINT "pk_pecuario_otro" PRIMARY KEY ("peot_id");

-- ----------------------------
-- Primary Key structure for table personas
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."personas" ADD CONSTRAINT "pk_persona" PRIMARY KEY ("per_id");

-- ----------------------------
-- Primary Key structure for table pollos
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."pollos" ADD CONSTRAINT "pk_pollo" PRIMARY KEY ("pol_id");

-- ----------------------------
-- Primary Key structure for table porcinos
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."porcinos" ADD CONSTRAINT "pk_porcino" PRIMARY KEY ("por_id");

-- ----------------------------
-- Primary Key structure for table terrenos
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."terrenos" ADD CONSTRAINT "pk_terreno" PRIMARY KEY ("ter_id");

-- ----------------------------
-- Foreign Keys structure for table boletas
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."boletas" ADD CONSTRAINT "fk_boleta_bovino" FOREIGN KEY ("bov_id") REFERENCES "sc_renagro_mag"."bovinos" ("bov_id") ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE "sc_renagro_mag"."boletas" ADD CONSTRAINT "fk_boleta_pecuario_otro" FOREIGN KEY ("peot_id") REFERENCES "sc_renagro_mag"."pecuarios_otros" ("peot_id") ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE "sc_renagro_mag"."boletas" ADD CONSTRAINT "fk_boleta_persona" FOREIGN KEY ("per_id") REFERENCES "sc_renagro_mag"."personas" ("per_id") ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE "sc_renagro_mag"."boletas" ADD CONSTRAINT "fk_boleta_pollo" FOREIGN KEY ("pol_id") REFERENCES "sc_renagro_mag"."pollos" ("pol_id") ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE "sc_renagro_mag"."boletas" ADD CONSTRAINT "fk_boleta_porcino" FOREIGN KEY ("por_id") REFERENCES "sc_renagro_mag"."porcinos" ("por_id") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table cultivos
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."cultivos" ADD CONSTRAINT "fk_cultivo_terreno" FOREIGN KEY ("ter_id") REFERENCES "sc_renagro_mag"."terrenos" ("ter_id") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table forestales
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."forestales" ADD CONSTRAINT "fk_forestal_terreno" FOREIGN KEY ("ter_id") REFERENCES "sc_renagro_mag"."terrenos" ("ter_id") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table miembros_hogar
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."miembros_hogar" ADD CONSTRAINT "fk_miembro_hogar_boleta" FOREIGN KEY ("bol_id") REFERENCES "sc_renagro_mag"."boletas" ("bol_id") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table terrenos
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."terrenos" ADD CONSTRAINT "fk_terreno_boleta" FOREIGN KEY ("bol_id") REFERENCES "sc_renagro_mag"."boletas" ("bol_id") ON DELETE NO ACTION ON UPDATE NO ACTION;


-- ----------------------------
-- nuevos campos ETL
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."boletas"
ADD COLUMN "neo_unidad_numeracion" VARCHAR(255),
ADD COLUMN "neo_segmento" VARCHAR(255),
ADD COLUMN "neo_unidad_estandar" VARCHAR(255),
ADD COLUMN "neo_poligono_upa" TEXT;

ALTER TABLE "sc_renagro_mag"."terrenos"
ADD COLUMN "neo_poligono_terreno" TEXT;


-- ----------------------------
-- nuevos campos algunos faltantes y otros solo para registro interno
-- ----------------------------

ALTER TABLE "sc_renagro_mag"."terrenos"
ADD COLUMN "neo_is_especie_forestal" BOOLEAN DEFAULT FALSE;

ALTER TABLE "sc_renagro_mag"."bovinos"
ADD COLUMN "neo_is_registro_produccion" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_infraestructura_descanso" BOOLEAN DEFAULT FALSE;

ALTER TABLE "sc_renagro_mag"."pecuarios_otros"
ADD COLUMN "neo_is_ovino" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_caprino" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_caballar" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_mular" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_asno" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_colmena_mielifera" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_colmena_melipona" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_alpaca" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_llama" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_cuy" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_conejo" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_pavo" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_avestruz" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_codorniz" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_pato" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_otra_especie" BOOLEAN DEFAULT FALSE;

ALTER TABLE "sc_renagro_mag"."pollos"
ADD COLUMN "neo_is_registro_produccion" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_otra_enfer" BOOLEAN DEFAULT FALSE;


ALTER TABLE "sc_renagro_mag"."porcinos"
ADD COLUMN "neo_is_registro_produccion" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_infraestructura_descanso" BOOLEAN DEFAULT FALSE;


ALTER TABLE "sc_renagro_mag"."personas"
ADD COLUMN "neo_is_persona_juridica" BOOLEAN DEFAULT FALSE;


ALTER TABLE "sc_renagro_mag"."boletas"
ADD COLUMN "neo_is_uso_suelo_agricola" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_vive_terreno_entrevista" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_telefono_convencional" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_telefono_celular" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_direccion_email" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_otro_beneficio" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_pecuario_terreno" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_bovino_terreno" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_porcino_terreno" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_pollo_terreno" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_infraestructura_otra" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_extension_agricola" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_obtuvo_prestamo" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_pago_efectivo_hombre" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_pago_efectivo_mujer" BOOLEAN DEFAULT FALSE,
ADD COLUMN "neo_is_informante_productor" BOOLEAN DEFAULT FALSE;

DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_bosi_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_bosi_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

DROP TABLE IF EXISTS "sc_renagro_mag"."boletas_simplificada";
CREATE TABLE "sc_renagro_mag"."boletas_simplificada" (
  "bosi_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_bosi_id'::regclass),
  "bosi_provincia" varchar(255) COLLATE "pg_catalog"."default",
  "bosi_canton" varchar(255) COLLATE "pg_catalog"."default",
  "bosi_poligono" varchar(255) COLLATE "pg_catalog"."default",
  "bosi_codigo_upa" varchar(255) COLLATE "pg_catalog"."default",
  "bosi_codigo_encuestador" varchar(255) COLLATE "pg_catalog"."default",
  "bosi_numero_boleta" varchar(255) COLLATE "pg_catalog"."default",
  "bosi_superficie" float8,
  "bosi_unidad" varchar(255) COLLATE "pg_catalog"."default",
  "bosi_is_riego" bool,
  "bosi_is_infraestructura" bool,
  "bosi_is_bovino" bool,
  "bosi_bovino_subtotal_macho" int4,
  "bosi_bovino_subtotal_hembra" int4,
  "bosi_bovino_subtotal_propio" int4,
  "bosi_bovino_subtotal_ajeno" int4,
  "bosi_is_porcino" bool,
  "bosi_porcino_total_hembra" int4,
  "bosi_porcino_total_macho" int4,
  "bosi_is_pollo" bool,
  "bosi_pollo_ave_traspatio" int4,
  "bosi_pollo_broiler" int4,
  "bosi_id_levanta" varchar(255) COLLATE "pg_catalog"."default",
  "bosi_estado" int8 DEFAULT 11,
  "bosi_reg_usu" int8 NOT NULL,
  "bosi_reg_fecha" timestamp(6)
	);

DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_tesi_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_tesi_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Table structure for terrenos
-- ----------------------------
DROP TABLE IF EXISTS "sc_renagro_mag"."terrenos_simplificado";
CREATE TABLE "sc_renagro_mag"."terrenos_simplificado" (
  "tesi_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_tesi_id'::regclass),
  "tesi_cobertura_tierra" varchar(255) COLLATE "pg_catalog"."default",
  "tesi_superficie" float8,
  "tesi_superficie_unidad" varchar(255) COLLATE "pg_catalog"."default",
  "bosi_id" int8,
  "tesi_reg_usu" int8 NOT NULL,
  "tesi_reg_fecha" timestamp(6),
  "tesi_estado" int4 DEFAULT 11
);


-- ----------------------------
-- Primary Key structure for table boletas simplificada
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."boletas_simplificada" ADD CONSTRAINT "pk_boleta_simplificada" PRIMARY KEY ("bosi_id");

-- ----------------------------
-- Primary Key structure for table terrenos simplificado
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."terrenos_simplificado" ADD CONSTRAINT "pk_terreno_simplificado" PRIMARY KEY ("tesi_id");

-- ----------------------------
-- Foreign Keys structure for table terrenos simplificado
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."terrenos_simplificado" ADD CONSTRAINT "fk_terreno_boleta_simplificado" FOREIGN KEY ("bosi_id") REFERENCES "sc_renagro_mag"."boletas_simplificada" ("bosi_id") ON DELETE NO ACTION ON UPDATE NO ACTION;


DROP SEQUENCE IF EXISTS "sc_renagro_mag"."seq_pro_id";
CREATE SEQUENCE "sc_renagro_mag"."seq_pro_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

DROP TABLE IF EXISTS "sc_renagro_mag"."procesos";
CREATE TABLE "sc_renagro_mag"."procesos" (
  "pro_id" int8 NOT NULL DEFAULT nextval('"sc_renagro_mag".seq_pro_id'::regclass),
  "pro_provincia" varchar(255) COLLATE "pg_catalog"."default",
  "pro_canton" varchar(255) COLLATE "pg_catalog"."default",
  "pro_parroquia" varchar(255) COLLATE "pg_catalog"."default",
  "pro_poligono" varchar(255) COLLATE "pg_catalog"."default",
  "pro_segmento" varchar(255) COLLATE "pg_catalog"."default",
  "pro_latitud" float8,
  "pro_longitud" float8,
  "pro_altitud" float8,
  "pro_precision_hdop" float8,
  "pro_fecha" timestamp(6),
  "pro_supervisor" varchar(255) COLLATE "pg_catalog"."default",
  "pro_equipo" varchar(255) COLLATE "pg_catalog"."default",
  "pro_hora_inicio" varchar(255) COLLATE "pg_catalog"."default",
  "pro_hora_finalizacion" varchar(255) COLLATE "pg_catalog"."default",
  "pro_presentacion_personal" varchar(255) COLLATE "pg_catalog"."default",
  "pro_intrumento_recoleccion" varchar(255) COLLATE "pg_catalog"."default",
  "pro_aplicacion_guia" varchar(255) COLLATE "pg_catalog"."default",
  "pro_interaccion_productores" varchar(255) COLLATE "pg_catalog"."default",
  "pro_cumplimiento_procedimiento" varchar(255) COLLATE "pg_catalog"."default",
  "pro_seguridad_campo" varchar(255) COLLATE "pg_catalog"."default",
  "pro_observacion" varchar(255) COLLATE "pg_catalog"."default",
  "pro_nombre_supervisor" varchar(255) COLLATE "pg_catalog"."default",
  "pro_nombre_tecnico" varchar(255) COLLATE "pg_catalog"."default",
  "pro_id_levanta" varchar(255) COLLATE "pg_catalog"."default",
  "pro_estado" int8 DEFAULT 11,
  "pro_reg_usu" int8 NOT NULL,
  "pro_reg_fecha" timestamp(6)

);

-- ----------------------------
-- Primary Key structure for table procesos
-- ----------------------------
ALTER TABLE "sc_renagro_mag"."procesos" ADD CONSTRAINT "pk_procesos" PRIMARY KEY ("pro_id");
