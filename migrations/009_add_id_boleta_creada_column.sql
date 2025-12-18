-- Migration: Add id_boleta_creada column to control_envios_boletas
-- Purpose: Store the boletaId returned by the RENAGRO API on successful submission
-- Date: 2025-12-17

-- Add id_boleta_creada column to control_envios_boletas table
ALTER TABLE "sc_renagro_mag"."control_envios_boletas"
ADD COLUMN "id_boleta_creada" INTEGER NULL;

-- Add comment to the column
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."id_boleta_creada" 
IS 'ID de la boleta creada en el sistema remoto RENAGRO (campo boletaId de la respuesta HTTP 200)';

-- Add index for faster lookups by id_boleta_creada
CREATE INDEX IF NOT EXISTS "idx_control_envios_boletas_id_boleta_creada" 
ON "sc_renagro_mag"."control_envios_boletas" ("id_boleta_creada")
WHERE "id_boleta_creada" IS NOT NULL;
