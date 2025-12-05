-- Migration: Add error_mensajes_envio column
-- Description: Add new column to store error messages specific to API sending failures (Phase 2)
-- Schema: sc_renagro_mag
-- Date: 2025-12-05

-- Table 1: control_envios_boletas
ALTER TABLE "sc_renagro_mag"."control_envios_boletas"
  ADD COLUMN "error_mensajes_envio" TEXT NULL;

COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."error_mensajes_envio" IS 
  'Mensaje de error específico del envío a la API de terceros. Se almacena cuando envio_datos_procesados = ERROR. Incluye detalles como código HTTP, mensaje de respuesta, número de reintentos, etc.';

CREATE INDEX "idx_control_envios_boletas_error_mensajes" 
  ON "sc_renagro_mag"."control_envios_boletas" ("error_mensajes_envio")
  WHERE "error_mensajes_envio" IS NOT NULL;

-- Table 2: control_envios_boletas_procesos
ALTER TABLE "sc_renagro_mag"."control_envios_boletas_procesos"
  ADD COLUMN "error_mensajes_envio" TEXT NULL;

COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."error_mensajes_envio" IS 
  'Mensaje de error específico del envío a la API de terceros. Se almacena cuando envio_datos_procesados = ERROR. Incluye detalles como código HTTP, mensaje de respuesta, número de reintentos, etc.';

CREATE INDEX "idx_control_envios_procesos_error_mensajes" 
  ON "sc_renagro_mag"."control_envios_boletas_procesos" ("error_mensajes_envio")
  WHERE "error_mensajes_envio" IS NOT NULL;

-- Table 3: control_envios_boletas_simplificadas
ALTER TABLE "sc_renagro_mag"."control_envios_boletas_simplificadas"
  ADD COLUMN "error_mensajes_envio" TEXT NULL;

COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."error_mensajes_envio" IS 
  'Mensaje de error específico del envío a la API de terceros. Se almacena cuando envio_datos_procesados = ERROR. Incluye detalles como código HTTP, mensaje de respuesta, número de reintentos, etc.';

CREATE INDEX "idx_control_envios_simplificadas_error_mensajes" 
  ON "sc_renagro_mag"."control_envios_boletas_simplificadas" ("error_mensajes_envio")
  WHERE "error_mensajes_envio" IS NOT NULL;

-- Verification queries:
-- SELECT _id, envio_datos_procesados, error_mensajes_envio FROM "sc_renagro_mag"."control_envios_boletas" WHERE error_mensajes_envio IS NOT NULL;
-- SELECT _id, envio_datos_procesados, error_mensajes_envio FROM "sc_renagro_mag"."control_envios_boletas_procesos" WHERE error_mensajes_envio IS NOT NULL;
-- SELECT _id, envio_datos_procesados, error_mensajes_envio FROM "sc_renagro_mag"."control_envios_boletas_simplificadas" WHERE error_mensajes_envio IS NOT NULL;
