-- Migration: Add APROBADO state to estado_etl_enum
-- Description: Agrega estado APROBADO para registros procesados que están listos para envío a MAG
-- Author: Sistema RENAGRO
-- Date: 2025-12-18
-- Schema: sc_renagro_mag

-- Agregar nuevo valor al ENUM
ALTER TYPE "sc_renagro_mag"."estado_etl_enum" ADD VALUE IF NOT EXISTS 'APROBADO';

-- Actualizar comentario del tipo ENUM
COMMENT ON TYPE "sc_renagro_mag"."estado_etl_enum" IS 
'Estados del procesamiento ETL:
- PENDIENTE: JSON recibido, esperando procesamiento
- PROCESADO: ETL completado, datos insertados en BD
- APROBADO: Datos validados y aprobados, listos para envío a MAG
- ERROR: Fallo en procesamiento ETL (transformación o inserción DB)';

-- Actualizar comentario de la columna en control_envios_boletas
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."estado_etl" IS 
'Estado del procesamiento ETL: PENDIENTE, PROCESADO, APROBADO, ERROR';

-- Actualizar comentario de la columna en control_envios_boletas_procesos
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."estado_etl" IS 
'Estado del procesamiento ETL: PENDIENTE, PROCESADO, APROBADO, ERROR';

-- Actualizar comentario de la columna en control_envios_boletas_simplificadas
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."estado_etl" IS 
'Estado del procesamiento ETL: PENDIENTE, PROCESADO, APROBADO, ERROR';

-- Verificar estados existentes
DO $$
DECLARE
    r RECORD;
BEGIN
    RAISE NOTICE 'Estados disponibles en estado_etl_enum:';
    FOR r IN SELECT enumlabel FROM pg_enum WHERE enumtypid = 'sc_renagro_mag.estado_etl_enum'::regtype ORDER BY enumsortorder
    LOOP
        RAISE NOTICE '  - %', r.enumlabel;
    END LOOP;
END $$;
