-- Migración: Agregar campos para manejo de reintentos
-- Fecha: 2025-11-29
-- Descripción: Agregar retry_count y last_error_stage a control_envios_boletas

-- Agregar columna retry_count
ALTER TABLE "sc_renagro_mag"."control_envios_boletas" 
ADD COLUMN IF NOT EXISTS "retry_count" INTEGER NOT NULL DEFAULT 0;

COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."retry_count" IS 'Número de reintentos de procesamiento realizados';

-- Agregar columna last_error_stage
ALTER TABLE "sc_renagro_mag"."control_envios_boletas" 
ADD COLUMN IF NOT EXISTS "last_error_stage" VARCHAR(50) NULL;

COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."last_error_stage" IS 'Última etapa donde ocurrió el error: json_save, etl_transform, db_insert';

-- Índice para mejorar búsqueda de mensajes fallidos en recovery
CREATE INDEX IF NOT EXISTS "idx_control_envios_estado_retry" 
ON "sc_renagro_mag"."control_envios_boletas"("estado_etl", "retry_count") 
WHERE "estado_etl" = 'ERROR';

COMMENT ON INDEX "sc_renagro_mag"."idx_control_envios_estado_retry" IS 'Índice para optimizar recuperación de mensajes fallidos';
