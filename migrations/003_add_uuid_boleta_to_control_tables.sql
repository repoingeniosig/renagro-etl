-- Migration: Add uuid_boleta column to control tables
-- Description: Add UUID column to store the form submission UUID (_uuid field from JSON)
-- Schema: sc_renagro_mag
-- Date: 2025-12-06

-- Table 1: control_envios_boletas
ALTER TABLE "sc_renagro_mag"."control_envios_boletas"
  ADD COLUMN "uuid_boleta" VARCHAR(36) NULL;

COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."uuid_boleta" IS 
  'UUID único de la boleta extraído del campo _uuid del JSON de KoboToolbox';

CREATE UNIQUE INDEX "idx_control_envios_boletas_uuid" 
  ON "sc_renagro_mag"."control_envios_boletas" ("uuid_boleta")
  WHERE "uuid_boleta" IS NOT NULL;

-- Table 2: control_envios_boletas_procesos
ALTER TABLE "sc_renagro_mag"."control_envios_boletas_procesos"
  ADD COLUMN "uuid_boleta" VARCHAR(36) NULL;

COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."uuid_boleta" IS 
  'UUID único de la boleta extraído del campo _uuid del JSON de KoboToolbox';

CREATE UNIQUE INDEX "idx_control_envios_procesos_uuid" 
  ON "sc_renagro_mag"."control_envios_boletas_procesos" ("uuid_boleta")
  WHERE "uuid_boleta" IS NOT NULL;

-- Table 3: control_envios_boletas_simplificadas
ALTER TABLE "sc_renagro_mag"."control_envios_boletas_simplificadas"
  ADD COLUMN "uuid_boleta" VARCHAR(36) NULL;

COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."uuid_boleta" IS 
  'UUID único de la boleta extraído del campo _uuid del JSON de KoboToolbox';

CREATE UNIQUE INDEX "idx_control_envios_simplificadas_uuid" 
  ON "sc_renagro_mag"."control_envios_boletas_simplificadas" ("uuid_boleta")
  WHERE "uuid_boleta" IS NOT NULL;

-- Verification queries:
-- SELECT _id, uuid_boleta, estado_etl FROM "sc_renagro_mag"."control_envios_boletas" LIMIT 10;
-- SELECT _id, uuid_boleta, estado_etl FROM "sc_renagro_mag"."control_envios_boletas_procesos" LIMIT 10;
-- SELECT _id, uuid_boleta, estado_etl FROM "sc_renagro_mag"."control_envios_boletas_simplificadas" LIMIT 10;
