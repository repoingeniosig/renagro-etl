-- Migration: Add PROCESANDO state to estado_envio_enum
-- Description: Agrega estado PROCESANDO para evitar duplicados durante construcción de JSON
-- Author: Sistema RENAGRO
-- Date: 2025-12-09
-- Schema: sc_renagro_mag

-- Agregar nuevo valor al ENUM
ALTER TYPE "sc_renagro_mag"."estado_envio_enum" ADD VALUE IF NOT EXISTS 'PROCESANDO';

-- Actualizar comentario del tipo ENUM
COMMENT ON TYPE "sc_renagro_mag"."estado_envio_enum" IS 
'Estados del envío de datos a API MAG:
- PENDIENTE: Listo para procesar (estado_etl=PROCESADO)
- PROCESANDO: Construyendo JSON desde BD (evita duplicados en timer)
- ENTREGANDO: Enviando HTTP POST a API remota
- ENVIADO: Respuesta HTTP 201 exitosa
- ERROR: Fallo permanente (error construcción JSON, 4xx sin reintentos, 5xx agotados)';

-- Verificar estados existentes
DO $$
DECLARE
    r RECORD;
BEGIN
    RAISE NOTICE 'Estados disponibles en estado_envio_enum:';
    FOR r IN SELECT enumlabel FROM pg_enum WHERE enumtypid = 'sc_renagro_mag.estado_envio_enum'::regtype ORDER BY enumsortorder
    LOOP
        RAISE NOTICE '  - %', r.enumlabel;
    END LOOP;
END $$;
