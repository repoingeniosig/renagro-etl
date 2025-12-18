-- Migration: Add RECHAZADO state to estado_etl_enum
-- Description: Agrega estado RECHAZADO para registros procesados que NO pasan validación
-- Author: Sistema RENAGRO
-- Date: 2025-12-18
-- Schema: sc_renagro_mag

-- Agregar nuevo valor al ENUM
ALTER TYPE "sc_renagro_mag"."estado_etl_enum" ADD VALUE IF NOT EXISTS 'RECHAZADO';

-- Actualizar comentario del tipo ENUM
COMMENT ON TYPE "sc_renagro_mag"."estado_etl_enum" IS 
'Estados del procesamiento ETL:
- PENDIENTE: JSON recibido, esperando procesamiento
- PROCESADO: ETL completado, datos insertados en BD
- APROBADO: Datos validados y aprobados, listos para envío a MAG
- RECHAZADO: Datos procesados pero rechazados por validación, NO se enviarán
- ERROR: Fallo en procesamiento ETL (transformación o inserción DB)';

-- Actualizar comentario de la columna en control_envios_boletas
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."estado_etl" IS 
'Estado del procesamiento ETL: PENDIENTE, PROCESADO, APROBADO, RECHAZADO, ERROR';

-- Actualizar comentario de la columna en control_envios_boletas_procesos
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."estado_etl" IS 
'Estado del procesamiento ETL: PENDIENTE, PROCESADO, APROBADO, RECHAZADO, ERROR';

-- Actualizar comentario de la columna en control_envios_boletas_simplificadas
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."estado_etl" IS 
'Estado del procesamiento ETL: PENDIENTE, PROCESADO, APROBADO, RECHAZADO, ERROR';
