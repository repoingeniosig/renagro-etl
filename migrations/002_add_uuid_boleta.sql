-- Migración 002: Agregar campo uuid_boleta para almacenar _uuid del JSON
-- Fecha: 2025-11-29
-- Descripción: Agrega uuid_boleta para identificación única de la boleta desde KoboToolbox

-- Agregar columna uuid_boleta
ALTER TABLE "sc_renagro_mag"."control_envios_boletas" 
ADD COLUMN IF NOT EXISTS "uuid_boleta" UUID NULL;

COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."uuid_boleta" IS 'UUID de la boleta extraído del campo _uuid del JSON de KoboToolbox';

-- Crear índice único en uuid_boleta para búsquedas rápidas y prevenir duplicados
CREATE UNIQUE INDEX IF NOT EXISTS "idx_control_uuid_boleta" 
ON "sc_renagro_mag"."control_envios_boletas"("uuid_boleta")
WHERE "uuid_boleta" IS NOT NULL;

COMMENT ON INDEX "sc_renagro_mag"."idx_control_uuid_boleta" IS 'Índice único para UUID de boleta, previene duplicados';

-- Poblar uuid_boleta desde json_data existente
UPDATE "sc_renagro_mag"."control_envios_boletas"
SET "uuid_boleta" = ("json_data"->>'_uuid')::UUID
WHERE "json_data" ? '_uuid' 
AND "uuid_boleta" IS NULL;
