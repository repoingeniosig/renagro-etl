-- Migration: Add reintentable column
-- Description: Add column to control automatic retry behavior for ERROR records
-- Schema: sc_renagro_mag
-- Date: 2025-12-12
-- Tables affected: control_envios_boletas (only this table needs reintentable)

-- Drop existing objects if migration needs to be re-run
DROP INDEX IF EXISTS "sc_renagro_mag"."idx_control_envios_boletas_reintentable";

-- Add reintentable column to control_envios_boletas
ALTER TABLE "sc_renagro_mag"."control_envios_boletas"
  DROP COLUMN IF EXISTS "reintentable";

ALTER TABLE "sc_renagro_mag"."control_envios_boletas"
  ADD COLUMN "reintentable" BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."reintentable" IS 
  'Indica si el registro con ERROR debe reintentarse automáticamente:
- FALSE (default): Registro exitoso o error 4xx que requiere corrección manual
- TRUE: Error 5xx (servidor) que se reintenta automáticamente, o registro corregido manualmente
- Solo relevante cuando envio_datos_procesados = ERROR';

-- Índice para mejorar performance del query de registros reintenables
CREATE INDEX "idx_control_envios_boletas_reintentable" 
  ON "sc_renagro_mag"."control_envios_boletas" ("envio_datos_procesados", "reintentable")
  WHERE "envio_datos_procesados" = 'ERROR';

-- Query de verificación
-- SELECT _id, envio_datos_procesados, reintentable, error_mensajes_envio 
-- FROM "sc_renagro_mag"."control_envios_boletas" 
-- WHERE envio_datos_procesados = 'ERROR';