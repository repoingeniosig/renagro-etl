-- ============================================================================
-- Tablas de Control para Sistema ETL Multi-Formulario
-- Versión: 2.0
-- ============================================================================

-- ============================================================================
-- 1. CONTROL_ENVIOS_BOLETAS (Formulario Principal)
-- ============================================================================
CREATE TABLE IF NOT EXISTS control_envios_boletas (
    id SERIAL PRIMARY KEY,
    _id INTEGER UNIQUE NOT NULL,
    uuid_boleta VARCHAR(255),
    json_data JSONB NOT NULL,
    estado_etl VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    envio_datos_procesados VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    procesado_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    
    -- Campos para sistema de reintentos (migración 001)
    retry_count INTEGER DEFAULT 0,
    last_error_stage VARCHAR(50),
    
    CONSTRAINT chk_estado_etl CHECK (estado_etl IN ('PENDIENTE', 'PROCESANDO', 'PROCESADO', 'ERROR')),
    CONSTRAINT chk_envio_datos CHECK (envio_datos_procesados IN ('PENDIENTE', 'ENVIADO', 'ERROR'))
);

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_control_boletas_estado_etl ON control_envios_boletas(estado_etl);
CREATE INDEX IF NOT EXISTS idx_control_boletas_uuid ON control_envios_boletas(uuid_boleta);
CREATE INDEX IF NOT EXISTS idx_control_boletas_created_at ON control_envios_boletas(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_control_boletas_error ON control_envios_boletas(estado_etl) WHERE estado_etl = 'ERROR';

COMMENT ON TABLE control_envios_boletas IS 'Control de procesamiento ETL para formulario principal de boletas';
COMMENT ON COLUMN control_envios_boletas._id IS 'ID del formulario de KoboToolbox (único)';
COMMENT ON COLUMN control_envios_boletas.uuid_boleta IS 'UUID del submission (_uuid del JSON)';
COMMENT ON COLUMN control_envios_boletas.json_data IS 'JSON completo del formulario';
COMMENT ON COLUMN control_envios_boletas.estado_etl IS 'Estado del procesamiento ETL: PENDIENTE, PROCESANDO, PROCESADO, ERROR';
COMMENT ON COLUMN control_envios_boletas.retry_count IS 'Número de reintentos realizados';
COMMENT ON COLUMN control_envios_boletas.last_error_stage IS 'Última etapa donde falló: json_save, etl_transform, db_insert';


-- ============================================================================
-- 2. CONTROL_ENVIOS_BOLETAS_PROCESOS (Formulario de Procesos)
-- ============================================================================
CREATE TABLE IF NOT EXISTS control_envios_boletas_procesos (
    id SERIAL PRIMARY KEY,
    _id INTEGER UNIQUE NOT NULL,
    uuid_boleta VARCHAR(255),
    json_data JSONB NOT NULL,
    estado_etl VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    envio_datos_procesados VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    procesado_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    
    -- Campos para sistema de reintentos
    retry_count INTEGER DEFAULT 0,
    last_error_stage VARCHAR(50),
    
    CONSTRAINT chk_estado_etl_procesos CHECK (estado_etl IN ('PENDIENTE', 'PROCESANDO', 'PROCESADO', 'ERROR')),
    CONSTRAINT chk_envio_datos_procesos CHECK (envio_datos_procesados IN ('PENDIENTE', 'ENVIADO', 'ERROR'))
);

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_control_procesos_estado_etl ON control_envios_boletas_procesos(estado_etl);
CREATE INDEX IF NOT EXISTS idx_control_procesos_uuid ON control_envios_boletas_procesos(uuid_boleta);
CREATE INDEX IF NOT EXISTS idx_control_procesos_created_at ON control_envios_boletas_procesos(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_control_procesos_error ON control_envios_boletas_procesos(estado_etl) WHERE estado_etl = 'ERROR';

COMMENT ON TABLE control_envios_boletas_procesos IS 'Control de procesamiento ETL para formulario de procesos productivos';
COMMENT ON COLUMN control_envios_boletas_procesos._id IS 'ID del formulario de KoboToolbox (único)';
COMMENT ON COLUMN control_envios_boletas_procesos.uuid_boleta IS 'UUID del submission (_uuid del JSON)';
COMMENT ON COLUMN control_envios_boletas_procesos.json_data IS 'JSON completo del formulario';
COMMENT ON COLUMN control_envios_boletas_procesos.estado_etl IS 'Estado del procesamiento ETL: PENDIENTE, PROCESANDO, PROCESADO, ERROR';
COMMENT ON COLUMN control_envios_boletas_procesos.retry_count IS 'Número de reintentos realizados';
COMMENT ON COLUMN control_envios_boletas_procesos.last_error_stage IS 'Última etapa donde falló: json_save, etl_transform, db_insert';


-- ============================================================================
-- 3. CONTROL_ENVIOS_BOLETAS_SIMPLIFICADAS (Formulario Simplificado)
-- ============================================================================
CREATE TABLE IF NOT EXISTS control_envios_boletas_simplificadas (
    id SERIAL PRIMARY KEY,
    _id INTEGER UNIQUE NOT NULL,
    uuid_boleta VARCHAR(255),
    json_data JSONB NOT NULL,
    estado_etl VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    envio_datos_procesados VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    procesado_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    
    -- Campos para sistema de reintentos
    retry_count INTEGER DEFAULT 0,
    last_error_stage VARCHAR(50),
    
    CONSTRAINT chk_estado_etl_simplificadas CHECK (estado_etl IN ('PENDIENTE', 'PROCESANDO', 'PROCESADO', 'ERROR')),
    CONSTRAINT chk_envio_datos_simplificadas CHECK (envio_datos_procesados IN ('PENDIENTE', 'ENVIADO', 'ERROR'))
);

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_control_simplificadas_estado_etl ON control_envios_boletas_simplificadas(estado_etl);
CREATE INDEX IF NOT EXISTS idx_control_simplificadas_uuid ON control_envios_boletas_simplificadas(uuid_boleta);
CREATE INDEX IF NOT EXISTS idx_control_simplificadas_created_at ON control_envios_boletas_simplificadas(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_control_simplificadas_error ON control_envios_boletas_simplificadas(estado_etl) WHERE estado_etl = 'ERROR';

COMMENT ON TABLE control_envios_boletas_simplificadas IS 'Control de procesamiento ETL para formulario simplificado de boletas';
COMMENT ON COLUMN control_envios_boletas_simplificadas._id IS 'ID del formulario de KoboToolbox (único)';
COMMENT ON COLUMN control_envios_boletas_simplificadas.uuid_boleta IS 'UUID del submission (_uuid del JSON)';
COMMENT ON COLUMN control_envios_boletas_simplificadas.json_data IS 'JSON completo del formulario';
COMMENT ON COLUMN control_envios_boletas_simplificadas.estado_etl IS 'Estado del procesamiento ETL: PENDIENTE, PROCESANDO, PROCESADO, ERROR';
COMMENT ON COLUMN control_envios_boletas_simplificadas.retry_count IS 'Número de reintentos realizados';
COMMENT ON COLUMN control_envios_boletas_simplificadas.last_error_stage IS 'Última etapa donde falló: json_save, etl_transform, db_insert';


-- ============================================================================
-- 4. VISTA UNIFICADA DE CONTROL (Opcional - para monitoreo)
-- ============================================================================
CREATE OR REPLACE VIEW v_control_envios_todos AS
SELECT 
    'boletas' AS tipo_formulario,
    _id,
    uuid_boleta,
    estado_etl,
    envio_datos_procesados,
    procesado_at,
    created_at,
    updated_at,
    error_message,
    retry_count,
    last_error_stage
FROM control_envios_boletas

UNION ALL

SELECT 
    'boletas_procesos' AS tipo_formulario,
    _id,
    uuid_boleta,
    estado_etl,
    envio_datos_procesados,
    procesado_at,
    created_at,
    updated_at,
    error_message,
    retry_count,
    last_error_stage
FROM control_envios_boletas_procesos

UNION ALL

SELECT 
    'boletas_simplificadas' AS tipo_formulario,
    _id,
    uuid_boleta,
    estado_etl,
    envio_datos_procesados,
    procesado_at,
    created_at,
    updated_at,
    error_message,
    retry_count,
    last_error_stage
FROM control_envios_boletas_simplificadas;

COMMENT ON VIEW v_control_envios_todos IS 'Vista unificada de todos los formularios para monitoreo';


-- ============================================================================
-- 5. FUNCIONES AUXILIARES
-- ============================================================================

-- Función para obtener estadísticas por tipo de formulario
CREATE OR REPLACE FUNCTION get_stats_by_form_type(form_type TEXT)
RETURNS TABLE(
    estado VARCHAR(20),
    total BIGINT
) AS $$
BEGIN
    RETURN QUERY EXECUTE format('
        SELECT estado_etl::VARCHAR(20), COUNT(*)::BIGINT
        FROM control_envios_%s
        GROUP BY estado_etl
        ORDER BY estado_etl
    ', form_type);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_stats_by_form_type IS 'Obtiene estadísticas de procesamiento por tipo de formulario';

-- Ejemplo de uso:
-- SELECT * FROM get_stats_by_form_type('boletas');
-- SELECT * FROM get_stats_by_form_type('boletas_procesos');
-- SELECT * FROM get_stats_by_form_type('boletas_simplificadas');


-- ============================================================================
-- PERMISOS (Ajustar según usuario de la aplicación)
-- ============================================================================
-- GRANT SELECT, INSERT, UPDATE ON control_envios_boletas TO renagro_app;
-- GRANT SELECT, INSERT, UPDATE ON control_envios_boletas_procesos TO renagro_app;
-- GRANT SELECT, INSERT, UPDATE ON control_envios_boletas_simplificadas TO renagro_app;
-- GRANT SELECT ON v_control_envios_todos TO renagro_app;
