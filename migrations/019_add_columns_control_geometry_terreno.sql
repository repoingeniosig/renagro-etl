ALTER TABLE "sc_renagro_mag"."terrenos_geometria_mag"
ADD COLUMN "tege_geojson" jsonb,
ADD COLUMN "ter_id_mag" int8,
ADD COLUMN "estado_geom" "sc_renagro_mag"."estado_geom_enum" NOT NULL DEFAULT 'PENDIENTE',
ADD COLUMN "envio_datos_procesados" "sc_renagro_mag"."estado_envio_enum" NOT NULL DEFAULT 'PENDIENTE',
ADD COLUMN "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN "error_message" TEXT,
ADD COLUMN "procesado_at" TIMESTAMP WITH TIME ZONE,
ADD COLUMN "retry_count" INTEGER NOT NULL DEFAULT 0,
ADD COLUMN "last_error_stage" VARCHAR(50),
ADD COLUMN "error_mensajes_envio" TEXT NULL,
ADD COLUMN "reintentable" BOOLEAN DEFAULT FALSE,
ADD COLUMN "id_terreno_geometria_creada" INTEGER NULL;


COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."tege_geojson" IS 'Representación GeoJSON de la geometría del terreno.';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."ter_id_mag" IS 'Identificador del terreno asociado a esta geometría en el sistema MAG.';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."estado_geom" IS 'Estado de la geometría del terreno: PENDIENTE, APROBADO';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."envio_datos_procesados" IS 'Estado del envío a API de terceros: PENDIENTE (no enviado aún), ENTREGANDO (en proceso de envío), ENVIADO (enviado exitosamente), ERROR (falló el envío)';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."created_at" IS 'Fecha de creación del registro';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."updated_at" IS 'Fecha de última actualización del registro';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."error_message" IS 'Mensaje de error en caso de que el procesamiento falle';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."procesado_at" IS 'Fecha y hora cuando se completó el procesamiento exitosamente';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."retry_count" IS 'Número de reintentos de procesamiento realizados';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."last_error_stage" IS 'Última etapa donde ocurrió el error: json_save, etl_transform, db_insert, envio';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."error_mensajes_envio" IS 'Mensaje de error específico del envío a la API de terceros. Se almacena cuando envio_datos_procesados = ERROR. Incluye detalles como código HTTP, mensaje de respuesta, número de reintentos, etc.';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."reintentable" IS 
	'Indica si el registro con ERROR debe reintentarse automáticamente:
- FALSE (default): Registro exitoso o error 4xx que requiere corrección manual
- TRUE: Error 5xx (servidor) que se reintenta automáticamente, o registro corregido manualmente
- Solo relevante cuando envio_datos_procesados = ERROR';
COMMENT ON COLUMN "sc_renagro_mag"."terrenos_geometria_mag"."id_terreno_geometria_creada" IS 'ID de la geometría del terreno creada en el sistema remoto RENAGRO (campo terrenoId o id de la respuesta HTTP 200)';

CREATE TRIGGER "trigger_update_control_envios_terrenos_geometria_updated_at"
		BEFORE UPDATE ON "sc_renagro_mag"."terrenos_geometria_mag"
		FOR EACH ROW
		EXECUTE FUNCTION "sc_renagro_mag"."update_updated_at_column"();

CREATE INDEX "idx_control_terrenos_geometria_estado_geom" ON "sc_renagro_mag"."terrenos_geometria_mag" ("estado_geom");
CREATE INDEX "idx_control_terrenos_geometria_envio_procesados" ON "sc_renagro_mag"."terrenos_geometria_mag" ("envio_datos_procesados");
CREATE INDEX "idx_control_terrenos_geometria_error_mensajes" ON "sc_renagro_mag"."terrenos_geometria_mag" ("error_mensajes_envio");
CREATE INDEX "idx_control_envios_terrenos_geometria_reintentable" ON "sc_renagro_mag"."terrenos_geometria_mag" ("envio_datos_procesados", "reintentable");
