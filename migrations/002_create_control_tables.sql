-- Script para crear las tablas de control de envíos multi-formulario
-- Schema: sc_renagro_mag

-- Crear tipos ENUM para los campos de control
DROP TYPE IF EXISTS "sc_renagro_mag"."estado_etl_enum" CASCADE;
CREATE TYPE "sc_renagro_mag"."estado_etl_enum" AS ENUM ('ERROR', 'PENDIENTE', 'PROCESADO');

DROP TYPE IF EXISTS "sc_renagro_mag"."estado_envio_enum" CASCADE;
CREATE TYPE "sc_renagro_mag"."estado_envio_enum" AS ENUM ('ERROR', 'PENDIENTE', 'PROCESADO');

-- Trigger para actualizar automáticamente el campo updated_at
CREATE OR REPLACE FUNCTION "sc_renagro_mag"."update_updated_at_column"()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 1. CONTROL_ENVIOS_BOLETAS (Formulario Principal)
-- ============================================================================
DROP TABLE IF EXISTS "sc_renagro_mag"."control_envios_boletas" CASCADE;
CREATE TABLE "sc_renagro_mag"."control_envios_boletas" (
  "_id" INTEGER NOT NULL,
  "uuid_boleta" VARCHAR(36),
  "json_data" JSONB NOT NULL,
  "fecha_recepcion" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "estado_etl" "sc_renagro_mag"."estado_etl_enum" NOT NULL DEFAULT 'PENDIENTE',
  "envio_datos_procesados" "sc_renagro_mag"."estado_envio_enum" NOT NULL DEFAULT 'PENDIENTE',
  "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "error_message" TEXT,
  "procesado_at" TIMESTAMP WITH TIME ZONE,
  "retry_count" INTEGER NOT NULL DEFAULT 0,
  "last_error_stage" VARCHAR(50),
  CONSTRAINT "pk_control_envios_boletas" PRIMARY KEY ("_id")
);

CREATE INDEX "idx_control_boletas_estado_etl" ON "sc_renagro_mag"."control_envios_boletas" ("estado_etl");
CREATE INDEX "idx_control_boletas_estado_procesados" ON "sc_renagro_mag"."control_envios_boletas" ("envio_datos_procesados");
CREATE INDEX "idx_control_boletas_fecha_recepcion" ON "sc_renagro_mag"."control_envios_boletas" ("fecha_recepcion");
CREATE INDEX "idx_control_boletas_json_data" ON "sc_renagro_mag"."control_envios_boletas" USING GIN ("json_data");
CREATE INDEX "idx_control_boletas_uuid" ON "sc_renagro_mag"."control_envios_boletas" ("uuid_boleta");

COMMENT ON TABLE "sc_renagro_mag"."control_envios_boletas" IS 'Tabla de control para almacenar los JSONs del formulario principal de boletas';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."_id" IS 'ID único del envío proveniente del campo _id del JSON de KoboToolbox (Primary Key)';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."uuid_boleta" IS 'UUID del submission (_uuid del JSON)';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."json_data" IS 'JSON completo del envío de KoboToolbox almacenado en formato JSONB';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."fecha_recepcion" IS 'Fecha y hora exacta de recepción del JSON en el servidor externo';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."estado_etl" IS 'Estado del procesamiento ETL: PENDIENTE, PROCESADO, ERROR';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."envio_datos_procesados" IS 'Estado del envío a API de terceros: PENDIENTE, PROCESADO, ERROR';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."created_at" IS 'Fecha de creación del registro';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."updated_at" IS 'Fecha de última actualización del registro';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."error_message" IS 'Mensaje de error en caso de que el procesamiento falle';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."procesado_at" IS 'Fecha y hora cuando se completó el procesamiento exitosamente';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."retry_count" IS 'Número de reintentos de procesamiento realizados';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."last_error_stage" IS 'Última etapa donde ocurrió el error: json_save, etl_transform, db_insert';

CREATE TRIGGER "trigger_update_control_envios_boletas_updated_at"
    BEFORE UPDATE ON "sc_renagro_mag"."control_envios_boletas"
    FOR EACH ROW
    EXECUTE FUNCTION "sc_renagro_mag"."update_updated_at_column"();


-- ============================================================================
-- 2. CONTROL_ENVIOS_BOLETAS_PROCESOS (Formulario de Procesos)
-- ============================================================================
DROP TABLE IF EXISTS "sc_renagro_mag"."control_envios_boletas_procesos" CASCADE;
CREATE TABLE "sc_renagro_mag"."control_envios_boletas_procesos" (
  "_id" INTEGER NOT NULL,
  "uuid_boleta" VARCHAR(36),
  "json_data" JSONB NOT NULL,
  "fecha_recepcion" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "estado_etl" "sc_renagro_mag"."estado_etl_enum" NOT NULL DEFAULT 'PENDIENTE',
  "envio_datos_procesados" "sc_renagro_mag"."estado_envio_enum" NOT NULL DEFAULT 'PENDIENTE',
  "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "error_message" TEXT,
  "procesado_at" TIMESTAMP WITH TIME ZONE,
  "retry_count" INTEGER NOT NULL DEFAULT 0,
  "last_error_stage" VARCHAR(50),
  CONSTRAINT "pk_control_envios_boletas_procesos" PRIMARY KEY ("_id")
);

CREATE INDEX "idx_control_procesos_estado_etl" ON "sc_renagro_mag"."control_envios_boletas_procesos" ("estado_etl");
CREATE INDEX "idx_control_procesos_estado_procesados" ON "sc_renagro_mag"."control_envios_boletas_procesos" ("envio_datos_procesados");
CREATE INDEX "idx_control_procesos_fecha_recepcion" ON "sc_renagro_mag"."control_envios_boletas_procesos" ("fecha_recepcion");
CREATE INDEX "idx_control_procesos_json_data" ON "sc_renagro_mag"."control_envios_boletas_procesos" USING GIN ("json_data");
CREATE INDEX "idx_control_procesos_uuid" ON "sc_renagro_mag"."control_envios_boletas_procesos" ("uuid_boleta");

COMMENT ON TABLE "sc_renagro_mag"."control_envios_boletas_procesos" IS 'Tabla de control para almacenar los JSONs del formulario de procesos productivos';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."_id" IS 'ID único del envío proveniente del campo _id del JSON de KoboToolbox (Primary Key)';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."uuid_boleta" IS 'UUID del submission (_uuid del JSON)';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."json_data" IS 'JSON completo del envío de KoboToolbox almacenado en formato JSONB';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."fecha_recepcion" IS 'Fecha y hora exacta de recepción del JSON en el servidor externo';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."estado_etl" IS 'Estado del procesamiento ETL: PENDIENTE, PROCESADO, ERROR';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."envio_datos_procesados" IS 'Estado del envío a API de terceros: PENDIENTE, PROCESADO, ERROR';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."created_at" IS 'Fecha de creación del registro';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."updated_at" IS 'Fecha de última actualización del registro';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."error_message" IS 'Mensaje de error en caso de que el procesamiento falle';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."procesado_at" IS 'Fecha y hora cuando se completó el procesamiento exitosamente';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."retry_count" IS 'Número de reintentos de procesamiento realizados';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."last_error_stage" IS 'Última etapa donde ocurrió el error: json_save, etl_transform, db_insert';

CREATE TRIGGER "trigger_update_control_envios_boletas_procesos_updated_at"
    BEFORE UPDATE ON "sc_renagro_mag"."control_envios_boletas_procesos"
    FOR EACH ROW
    EXECUTE FUNCTION "sc_renagro_mag"."update_updated_at_column"();


-- ============================================================================
-- 3. CONTROL_ENVIOS_BOLETAS_SIMPLIFICADAS (Formulario Simplificado)
-- ============================================================================
DROP TABLE IF EXISTS "sc_renagro_mag"."control_envios_boletas_simplificadas" CASCADE;
CREATE TABLE "sc_renagro_mag"."control_envios_boletas_simplificadas" (
  "_id" INTEGER NOT NULL,
  "uuid_boleta" VARCHAR(36),
  "json_data" JSONB NOT NULL,
  "fecha_recepcion" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "estado_etl" "sc_renagro_mag"."estado_etl_enum" NOT NULL DEFAULT 'PENDIENTE',
  "envio_datos_procesados" "sc_renagro_mag"."estado_envio_enum" NOT NULL DEFAULT 'PENDIENTE',
  "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "error_message" TEXT,
  "procesado_at" TIMESTAMP WITH TIME ZONE,
  "retry_count" INTEGER NOT NULL DEFAULT 0,
  "last_error_stage" VARCHAR(50),
  CONSTRAINT "pk_control_envios_boletas_simplificadas" PRIMARY KEY ("_id")
);

CREATE INDEX "idx_control_simplificadas_estado_etl" ON "sc_renagro_mag"."control_envios_boletas_simplificadas" ("estado_etl");
CREATE INDEX "idx_control_simplificadas_estado_procesados" ON "sc_renagro_mag"."control_envios_boletas_simplificadas" ("envio_datos_procesados");
CREATE INDEX "idx_control_simplificadas_fecha_recepcion" ON "sc_renagro_mag"."control_envios_boletas_simplificadas" ("fecha_recepcion");
CREATE INDEX "idx_control_simplificadas_json_data" ON "sc_renagro_mag"."control_envios_boletas_simplificadas" USING GIN ("json_data");
CREATE INDEX "idx_control_simplificadas_uuid" ON "sc_renagro_mag"."control_envios_boletas_simplificadas" ("uuid_boleta");

COMMENT ON TABLE "sc_renagro_mag"."control_envios_boletas_simplificadas" IS 'Tabla de control para almacenar los JSONs del formulario simplificado de boletas';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."_id" IS 'ID único del envío proveniente del campo _id del JSON de KoboToolbox (Primary Key)';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."uuid_boleta" IS 'UUID del submission (_uuid del JSON)';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."json_data" IS 'JSON completo del envío de KoboToolbox almacenado en formato JSONB';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."fecha_recepcion" IS 'Fecha y hora exacta de recepción del JSON en el servidor externo';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."estado_etl" IS 'Estado del procesamiento ETL: PENDIENTE, PROCESADO, ERROR';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."envio_datos_procesados" IS 'Estado del envío a API de terceros: PENDIENTE, PROCESADO, ERROR';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."created_at" IS 'Fecha de creación del registro';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."updated_at" IS 'Fecha de última actualización del registro';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."error_message" IS 'Mensaje de error en caso de que el procesamiento falle';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."procesado_at" IS 'Fecha y hora cuando se completó el procesamiento exitosamente';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."retry_count" IS 'Número de reintentos de procesamiento realizados';
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."last_error_stage" IS 'Última etapa donde ocurrió el error: json_save, etl_transform, db_insert';

CREATE TRIGGER "trigger_update_control_envios_boletas_simplificadas_updated_at"
    BEFORE UPDATE ON "sc_renagro_mag"."control_envios_boletas_simplificadas"
    FOR EACH ROW
    EXECUTE FUNCTION "sc_renagro_mag"."update_updated_at_column"();
