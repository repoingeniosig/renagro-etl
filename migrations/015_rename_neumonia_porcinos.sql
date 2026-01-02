-- Migración: Renombrar campo por_is_neumonía_por_enzootica a por_is_neumonia_por_enzootica
-- Fecha: 2026-01-02
-- Descripción: Se cambia el nombre del campo para eliminar el carácter con tilde (í -> i)
--              preservando todos los datos existentes

-- Renombrar la columna preservando los datos
ALTER TABLE "sc_renagro_mag"."porcinos"
RENAME COLUMN "por_is_neumonía_por_enzootica" TO "por_is_neumonia_por_enzootica";

-- Actualizar el comentario de la columna
COMMENT ON COLUMN "sc_renagro_mag"."porcinos"."por_is_neumonia_por_enzootica" IS 'Vacuno contra Neumonía Porcina Enzootica (tos)';
