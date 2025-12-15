-- Migration: Update estado_envio_enum
-- Description: Remove 'PROCESADO' and add new states 'ENTREGANDO', 'ENVIADO' for Phase 2 API sending
-- Schema: sc_renagro_mag
-- Date: 2025-12-05

-- Step 1: Create new enum with updated values
CREATE TYPE "sc_renagro_mag"."estado_envio_enum_new" AS ENUM ('PENDIENTE', 'ENTREGANDO', 'ENVIADO', 'ERROR');

-- Step 2: Update all tables that use this enum
-- Table 1: control_envios_boletas
ALTER TABLE "sc_renagro_mag"."control_envios_boletas"
  ALTER COLUMN "envio_datos_procesados" DROP DEFAULT;

ALTER TABLE "sc_renagro_mag"."control_envios_boletas"
  ALTER COLUMN "envio_datos_procesados" TYPE "sc_renagro_mag"."estado_envio_enum_new"
  USING (
    CASE "envio_datos_procesados"::TEXT
      WHEN 'PROCESADO' THEN 'ENVIADO'::sc_renagro_mag.estado_envio_enum_new
      WHEN 'PENDIENTE' THEN 'PENDIENTE'::sc_renagro_mag.estado_envio_enum_new
      WHEN 'ERROR' THEN 'ERROR'::sc_renagro_mag.estado_envio_enum_new
      ELSE 'PENDIENTE'::sc_renagro_mag.estado_envio_enum_new
    END
  );

ALTER TABLE "sc_renagro_mag"."control_envios_boletas"
  ALTER COLUMN "envio_datos_procesados" SET DEFAULT 'PENDIENTE'::sc_renagro_mag.estado_envio_enum_new;

-- Table 2: control_envios_boletas_procesos
ALTER TABLE "sc_renagro_mag"."control_envios_boletas_procesos"
  ALTER COLUMN "envio_datos_procesados" DROP DEFAULT;

ALTER TABLE "sc_renagro_mag"."control_envios_boletas_procesos"
  ALTER COLUMN "envio_datos_procesados" TYPE "sc_renagro_mag"."estado_envio_enum_new"
  USING (
    CASE "envio_datos_procesados"::TEXT
      WHEN 'PROCESADO' THEN 'ENVIADO'::sc_renagro_mag.estado_envio_enum_new
      WHEN 'PENDIENTE' THEN 'PENDIENTE'::sc_renagro_mag.estado_envio_enum_new
      WHEN 'ERROR' THEN 'ERROR'::sc_renagro_mag.estado_envio_enum_new
      ELSE 'PENDIENTE'::sc_renagro_mag.estado_envio_enum_new
    END
  );

ALTER TABLE "sc_renagro_mag"."control_envios_boletas_procesos"
  ALTER COLUMN "envio_datos_procesados" SET DEFAULT 'PENDIENTE'::sc_renagro_mag.estado_envio_enum_new;

-- Table 3: control_envios_boletas_simplificadas
ALTER TABLE "sc_renagro_mag"."control_envios_boletas_simplificadas"
  ALTER COLUMN "envio_datos_procesados" DROP DEFAULT;

ALTER TABLE "sc_renagro_mag"."control_envios_boletas_simplificadas"
  ALTER COLUMN "envio_datos_procesados" TYPE "sc_renagro_mag"."estado_envio_enum_new"
  USING (
    CASE "envio_datos_procesados"::TEXT
      WHEN 'PROCESADO' THEN 'ENVIADO'::sc_renagro_mag.estado_envio_enum_new
      WHEN 'PENDIENTE' THEN 'PENDIENTE'::sc_renagro_mag.estado_envio_enum_new
      WHEN 'ERROR' THEN 'ERROR'::sc_renagro_mag.estado_envio_enum_new
      ELSE 'PENDIENTE'::sc_renagro_mag.estado_envio_enum_new
    END
  );

ALTER TABLE "sc_renagro_mag"."control_envios_boletas_simplificadas"
  ALTER COLUMN "envio_datos_procesados" SET DEFAULT 'PENDIENTE'::sc_renagro_mag.estado_envio_enum_new;

-- Step 3: Drop old enum
DROP TYPE "sc_renagro_mag"."estado_envio_enum";

-- Step 4: Rename new enum to original name
ALTER TYPE "sc_renagro_mag"."estado_envio_enum_new" RENAME TO "estado_envio_enum";

-- Step 5: Update comments to reflect new states
COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas"."envio_datos_procesados" IS 
  'Estado del envío a API de terceros: PENDIENTE (no enviado aún), ENTREGANDO (en proceso de envío), ENVIADO (enviado exitosamente), ERROR (falló el envío)';

COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_procesos"."envio_datos_procesados" IS 
  'Estado del envío a API de terceros: PENDIENTE (no enviado aún), ENTREGANDO (en proceso de envío), ENVIADO (enviado exitosamente), ERROR (falló el envío)';

COMMENT ON COLUMN "sc_renagro_mag"."control_envios_boletas_simplificadas"."envio_datos_procesados" IS 
  'Estado del envío a API de terceros: PENDIENTE (no enviado aún), ENTREGANDO (en proceso de envío), ENVIADO (enviado exitosamente), ERROR (falló el envío)';

-- Verification queries:
-- SELECT DISTINCT envio_datos_procesados FROM "sc_renagro_mag"."control_envios_boletas";
-- SELECT COUNT(*), envio_datos_procesados FROM "sc_renagro_mag"."control_envios_boletas" GROUP BY envio_datos_procesados;
