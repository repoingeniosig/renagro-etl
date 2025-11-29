# Guía Rápida - RENAGRO ETL Process

## 🚀 Instalación en 3 pasos

### Opción A: Usando el script de setup automático

```bash
cd /Users/mac/Documents/projects/RENAGRO/CODIGO/renagro-etl-process

# Hacer ejecutable el script
chmod +x setup.sh

# Ejecutar
./setup.sh
```

### Opción B: Instalación manual

```bash
# 1. Crear ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
nano .env  # Editar con tus datos
```

## 📝 Configuración básica

Edita el archivo `.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=renagro_db
DB_USER=postgres
DB_PASSWORD=TU_PASSWORD_AQUI
DB_SCHEMA=sc_renagro_mag
```

## 🗄️ Crear tabla de control

```bash
# Desde la terminal de PostgreSQL
psql -U postgres -d renagro_db -f scripts/create_control_table.sql

# O desde psql interactivo
psql -U postgres -d renagro_db
\i scripts/create_control_table.sql
```

## 🎯 Uso básico

### Procesar un JSON

```bash
# Activar ambiente virtual (si no está activo)
source venv/bin/activate

# Procesar archivo JSON
python -m src.process_json data/formulario.json

# Solo generar SQL (sin guardar en BD)
python -m src.process_json --skip-db data/formulario.json
```

## 📋 Comandos útiles

### Ver ayuda
```bash
python -m src.process_json --help
```

### Activar/Desactivar ambiente virtual
```bash
# Activar
source venv/bin/activate

# Desactivar
deactivate
```

### Verificar estado de la tabla de control
```sql
-- Conectar a PostgreSQL
psql -U postgres -d renagro_db

-- Ver todos los registros
SELECT _id, formhub_uuid, estado_etl, fecha_recepcion 
FROM sc_renagro_mag.control_envios_boletas;

-- Ver solo pendientes
SELECT * FROM sc_renagro_mag.control_envios_boletas 
WHERE estado_etl = 'PENDIENTE';

-- Ver errores
SELECT _id, error_message, fecha_recepcion 
FROM sc_renagro_mag.control_envios_boletas 
WHERE estado_etl = 'ERROR';

-- Contar por estado
SELECT estado_etl, COUNT(*) 
FROM sc_renagro_mag.control_envios_boletas 
GROUP BY estado_etl;
```

## 🗺️ Estructura de archivos YAML

Los archivos en `mapping/` definen cómo transformar el JSON:

```yaml
version: 1.0
entity: nombre_entidad
table: nombre_tabla

fields:
  columna_destino:
    source: "ruta.en.json.usando.puntos"
    type: integer|decimal|boolean|string
    default: valor_por_defecto
    convert:
      nombre_conversion: true

conversions:
  nombre_conversion:
    valor_origen: valor_destino
```

## 🔍 Ejemplo completo

1. **Preparar JSON de prueba** (`data/test.json`):
```json
{
  "_id": 12345,
  "formhub/uuid": "test-uuid-123",
  "capitulo_1": {
    "nombre": "Juan Pérez",
    "tiene_ganado": "Si"
  }
}
```

2. **Procesar**:
```bash
python -m src.process_json data/test.json
```

3. **Verificar en BD**:
```sql
SELECT * FROM sc_renagro_mag.control_envios_boletas 
WHERE _id = 12345;
```

## 🐛 Solución de problemas

### Error: "No module named 'sqlalchemy'"
```bash
# Asegúrate de tener el venv activado
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "could not connect to server"
- Verificar que PostgreSQL esté corriendo
- Verificar credenciales en `.env`
- Verificar que la base de datos existe

### Error: "relation does not exist"
```bash
# Crear la tabla de control
psql -U postgres -d renagro_db -f scripts/create_control_table.sql
```

## 📚 Documentación adicional

- `README.md` - Documentación completa del proyecto
- `docs/json_example.md` - Estructura del JSON de KoboToolbox
- `mapping/personas_example.yaml` - Ejemplo de archivo de mapeo

## 🎓 Próximos pasos

1. ✅ Instalar y configurar
2. ✅ Crear tabla de control
3. ✅ Procesar primer JSON
4. 🔜 Crear archivos YAML para tus entidades
5. 🔜 Implementar procesamiento con RabbitMQ
6. 🔜 Crear API REST para recibir JSONs
