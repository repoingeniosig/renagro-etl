-- Migration: Add reintentable column
-- Description: Add column to control automatic retry behavior for ERROR records
-- Schema: sc_renagro_mag
-- Date: 2025-12-12

-- Table 1: control_envios_boletas
ALTER TABLE "sc_renagro_mag"."control_envios_boletas"
  ADD COLUMN "reintentable" BOOLEAN DEFAULT TRUE;

COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."reintentable" IS 
  'Indica si el registro debe reintentarse automáticamente en caso de ERROR:
- TRUE: Error 5xx (servidor) o error construcción JSON, se reintenta automáticamente
- FALSE: Error 4xx (validación de negocio), requiere corrección manual de datos
- Usuario cambia manualmente a TRUE después de corregir datos para reprocesar';

-- Índice para mejorar performance del query de registros reintenables
CREATE INDEX "idx_control_envios_boletas_reintentable" 
  ON "sc_renagro_mag"."control_envios_boletas" ("envio_datos_procesados", "reintentable")
  WHERE "envio_datos_procesados" = 'ERROR';

-- Table 2: control_envios_boletas_procesos
ALTER TABLE "sc_renagro_mag"."control_envios_boletas_procesos"
  ADD COLUMN "reintentable" BOOLEAN DEFAULT TRUE;

COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."reintentable" IS 
  'Indica si el registro debe reintentarse automáticamente en caso de ERROR:
- TRUE: Error 5xx (servidor) o error construcción JSON, se reintenta automáticamente
- FALSE: Error 4xx (validación de negocio), requiere corrección manual de datos
- Usuario cambia manualmente a TRUE después de corregir datos para reprocesar';

CREATE INDEX "idx_control_envios_boletas_procesos_reintentable" 
  ON "sc_renagro_mag"."control_envios_boletas_procesos" ("envio_datos_procesados", "reintentable")
  WHERE "envio_datos_procesados" = 'ERROR';

-- Table 3: control_envios_boletas_simplificadas
ALTER TABLE "sc_renagro_mag"."control_envios_boletas_simplificadas"
  ADD COLUMN "reintentable" BOOLEAN DEFAULT TRUE;

COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."reintentable" IS 
  'Indica si el registro debe reintentarse automáticamente en caso de ERROR:
- TRUE: Error 5xx (servidor) o error construcción JSON, se reintenta automáticamente
- FALSE: Error 4xx (validación de negocio), requiere corrección manual de datos
- Usuario cambia manualmente a TRUE después de corregir datos para reprocesar';

CREATE INDEX "idx_control_envios_boletas_simplificadas_reintentable" 
  ON "sc_renagro_mag"."control_envios_boletas_simplificadas" ("envio_datos_procesados", "reintentable")
  WHERE "envio_datos_procesados" = 'ERROR';

-- Queries de verificación
-- SELECT _id, envio_datos_procesados, reintentable, error_mensajes_envio FROM "sc_renagro_mag"."control_envios_boletas" WHERE envio_datos_procesados = 'ERROR';
-- SELECT _id, envio_datos_procesados, reintentable, error_mensajes_envio FROM "sc_renagro_mag"."control_envios_boletas_procesos" WHERE envio_datos_procesados = 'ERROR';
-- SELECT _id, envio_datos_procesados, reintentable, error_mensajes_envio FROM "sc_renagro_mag"."control_envios_boletas_simplificadas" WHERE envio_datos_procesados = 'ERROR';
