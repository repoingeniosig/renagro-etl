-- Script para crear la tabla de control de envíos de boletas
-- Schema: sc_renagro_mag
-- Descripción: Almacena el JSON completo de cada envío y controla el estado del procesamiento ETL

-- Crear tipos ENUM para los campos de control
DROP TYPE IF EXISTS "sc_renagro_mag"."estado_etl_enum" CASCADE;
CREATE TYPE "sc_renagro_mag"."estado_etl_enum" AS ENUM ('ERROR', 'PENDIENTE', 'PROCESADO');

DROP TYPE IF EXISTS "sc_renagro_mag"."estado_envio_enum" CASCADE;
CREATE TYPE "sc_renagro_mag"."estado_envio_enum" AS ENUM ('ERROR', 'PENDIENTE', 'PROCESADO');

-- Crear la tabla control_envios_boletas
DROP TABLE IF EXISTS "sc_renagro_mag"."control_envios_boletas" CASCADE;
CREATE TABLE "sc_renagro_mag"."control_envios_boletas" (
  "_id" INTEGER NOT NULL,
  "json_data" JSONB NOT NULL,
  "fecha_recepcion" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "estado_etl" "sc_renagro_mag"."estado_etl_enum" NOT NULL DEFAULT 'PENDIENTE',
  "envio_datos_procesados" "sc_renagro_mag"."estado_envio_enum" NOT NULL DEFAULT 'PENDIENTE',
  "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "error_message" TEXT,
  "procesado_at" TIMESTAMP WITH TIME ZONE,
  CONSTRAINT "pk_control_envios_boletas" PRIMARY KEY ("_id")
);

-- Crear índices para mejorar el rendimiento
CREATE INDEX "idx_control_envios_estado_etl" ON "sc_renagro_mag"."control_envios_boletas" ("estado_etl");
CREATE INDEX "idx_control_envios_estado_procesados" ON "sc_renagro_mag"."control_envios_boletas" ("envio_datos_procesados");
CREATE INDEX "idx_control_envios_fecha_recepcion" ON "sc_renagro_mag"."control_envios_boletas" ("fecha_recepcion");
CREATE INDEX "idx_control_envios_json_data" ON "sc_renagro_mag"."control_envios_boletas" USING GIN ("json_data");

-- Comentarios para documentación
COMMENT ON TABLE "sc_renagro_mag"."control_envios_boletas" IS 'Tabla de control para almacenar los JSONs recibidos de KoboToolbox y controlar su procesamiento ETL';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."_id" IS 'ID único del envío proveniente del campo _id del JSON de KoboToolbox (Primary Key)';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."json_data" IS 'JSON completo del envío de KoboToolbox almacenado en formato JSONB';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."fecha_recepcion" IS 'Fecha y hora exacta de recepción del JSON en el servidor externo';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."estado_etl" IS 'Estado del procesamiento ETL: PENDIENTE, PROCESADO, ERROR';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."envio_datos_procesados" IS 'Estado del envío a API de terceros: PENDIENTE, PROCESADO, ERROR';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."created_at" IS 'Fecha de creación del registro';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."updated_at" IS 'Fecha de última actualización del registro';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."error_message" IS 'Mensaje de error en caso de que el procesamiento falle';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."procesado_at" IS 'Fecha y hora cuando se completó el procesamiento exitosamente';

-- Trigger para actualizar automáticamente el campo updated_at
CREATE OR REPLACE FUNCTION "sc_renagro_mag"."update_updated_at_column"()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER "trigger_update_control_envios_updated_at"
    BEFORE UPDATE ON "sc_renagro_mag"."control_envios_boletas"
    FOR EACH ROW
    EXECUTE FUNCTION "sc_renagro_mag"."update_updated_at_column"();

-- Ejemplo de consultas útiles:
-- 
-- Ver todos los envíos pendientes de procesar:
-- SELECT * FROM "sc_renagro_mag"."control_envios_boletas" WHERE estado_etl = 'PENDIENTE';
--
-- Ver todos los errores:
-- SELECT _id, estado_etl, error_message, fecha_recepcion 
-- FROM "sc_renagro_mag"."control_envios_boletas" WHERE estado_etl = 'ERROR';
--
-- Contar envíos por estado:
-- SELECT estado_etl, COUNT(*) FROM "sc_renagro_mag"."control_envios_boletas" GROUP BY estado_etl;
