-- Migración: Agregar índice en boletas.bol_id_levanta
-- Fecha: 2025-12-16
-- Propósito: Mejorar performance de búsqueda al comparar control_envios_boletas._id con boletas.bol_id_levanta

-- Verificar si el índice ya existe
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_indexes 
        WHERE schemaname = 'sc_renagro_mag' 
        AND tablename = 'boletas' 
        AND indexname = 'idx_boletas_bol_id_levanta'
    ) THEN
        -- Crear índice en bol_id_levanta para acelerar búsquedas
        CREATE INDEX idx_boletas_bol_id_levanta ON "sc_renagro_mag".boletas (bol_id_levanta);
        
        RAISE NOTICE 'Índice idx_boletas_bol_id_levanta creado exitosamente';
    ELSE
        RAISE NOTICE 'Índice idx_boletas_bol_id_levanta ya existe';
    END IF;
END $$;

-- Comentario sobre el índice
COMMENT ON INDEX "sc_renagro_mag".idx_boletas_bol_id_levanta IS 
'Índice para mejorar performance al buscar registros por bol_id_levanta (comparación con control_envios_boletas._id)';
