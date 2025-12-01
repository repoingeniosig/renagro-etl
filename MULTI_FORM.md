# Sistema Multi-Formulario ETL

## 📋 Descripción

Sistema ETL que soporta múltiples tipos de formularios, cada uno con sus propios mapeos YAML y tabla de control independiente.

## 🗂️ Estructura de Archivos

```
renagro-etl-process/
├── forms_config.yml              # Configuración de formularios
├── mappings/                      # Directorio base de mapeos
│   ├── aa/                        # Formulario: boletas
│   │   ├── master.yml
│   │   ├── boletas.yaml
│   │   ├── bovinos.yaml
│   │   ├── miembros_hogar.yaml
│   │   └── ...
│   ├── bb/                        # Formulario: boletas_procesos
│   │   ├── master.yml
│   │   ├── procesos.yaml
│   │   └── ...
│   └── cc/                        # Formulario: boletas_simplificadas
│       ├── master.yml
│       ├── simplificadas.yaml
│       └── ...
└── mapping/                       # (Deprecated) Mapeos legacy
```

## ⚙️ Configuración de Formularios

Edita `forms_config.yml` para registrar formularios:

```yaml
forms:
  - uuid: "aa"                                    # UUID del formulario en KoboToolbox
    name: "boletas"                               # Nombre interno
    description: "Formulario principal"
    control_table: "control_envios_boletas"       # Tabla de control
    mapping_dir: "aa"                             # Carpeta de mapeos
    enabled: true                                 # Activado/Desactivado

  - uuid: "bb"
    name: "boletas_procesos"
    control_table: "control_envios_boletas_procesos"
    mapping_dir: "bb"
    enabled: true

config:
  mappings_base_dir: "mappings"                   # Directorio base
  uuid_field: "formhub/uuid"                      # Campo que identifica el formulario
  reject_unknown_forms: true                      # Rechazar UUIDs no registrados
  log_unknown_forms: true                         # Registrar intentos con UUIDs desconocidos
```

## 🔄 Flujo de Procesamiento

### 1. JSON Llega al Sistema

```json
{
  "_id": 12345,
  "formhub/uuid": "bb",
  "datos": {...}
}
```

### 2. Validación de Formulario

```python
from src.forms_manager import forms_manager

# Extraer UUID del JSON
is_valid, form_config, error = forms_manager.validate_json(json_data)

if not is_valid:
    return HTTPException(400, detail=error)

# form_config contiene:
# - uuid: "bb"
# - name: "boletas_procesos"
# - control_table: "control_envios_boletas_procesos"
# - mapping_dir: "bb"
```

### 3. Carga de Mapeos Dinámicos

```python
# Obtener directorio de mapeos
mapping_path = forms_manager.get_mapping_path(form_config)
# → Path("mappings/bb")

# Cargar mapeos desde ese directorio
mapping_loader.load_master(mapping_path / "master.yml")
mapping_loader.load_all_mappings(mapping_path)
```

### 4. Guardar en Tabla de Control Correcta

```python
# Usar tabla de control específica del formulario
table_name = form_config.control_table
# → "control_envios_boletas_procesos"

# Guardar en tabla correspondiente
session.execute(f"INSERT INTO {table_name} ...")
```

## 📊 Tablas de Control

Cada formulario tiene su tabla de control independiente:

| Formulario | Tabla de Control |
|------------|------------------|
| boletas (aa) | `control_envios_boletas` |
| boletas_procesos (bb) | `control_envios_boletas_procesos` |
| boletas_simplificadas (cc) | `control_envios_boletas_simplificadas` |

### Estructura de Tablas

Todas las tablas tienen la misma estructura:

```sql
CREATE TABLE control_envios_boletas_* (
    id SERIAL PRIMARY KEY,
    _id INTEGER UNIQUE NOT NULL,
    uuid_boleta VARCHAR(255),
    json_data JSONB NOT NULL,
    estado_etl VARCHAR(20) DEFAULT 'PENDIENTE',
    procesado_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    last_error_stage VARCHAR(50)
);
```

## 🚀 Uso

### API REST

```bash
# El endpoint /boletas detecta automáticamente el formulario
curl -X POST http://localhost:8000/boletas \
  -u admin:admin123 \
  -H "Content-Type: application/json" \
  -d @formulario_bb.json
```

El sistema:
1. Extrae `formhub/uuid` del JSON
2. Busca configuración en `forms_config.yml`
3. Carga mapeos desde `mappings/{uuid}/`
4. Guarda en tabla de control correspondiente
5. Procesa con el pipeline ETL

### Batch Processor

```bash
# Procesar lote de formularios (pueden ser de diferentes tipos)
python -m src.batch_processor lote_formularios.json
```

El script procesa cada formulario según su UUID automáticamente.

## ➕ Agregar Nuevo Formulario

### Paso 1: Crear Tabla de Control

```sql
-- scripts/create_control_tables.sql
CREATE TABLE control_envios_mi_nuevo_form (
    -- ... misma estructura que las otras
);
```

### Paso 2: Crear Carpeta de Mapeos

```bash
mkdir -p mappings/nuevo_uuid
```

### Paso 3: Copiar YAMLs Base

```bash
# Copiar desde un formulario existente
cp mappings/aa/*.yaml mappings/nuevo_uuid/
```

### Paso 4: Editar YAMLs

Modificar los archivos YAML según la estructura del nuevo formulario.

### Paso 5: Registrar en Configuración

```yaml
# forms_config.yml
forms:
  - uuid: "nuevo_uuid"
    name: "mi_nuevo_formulario"
    control_table: "control_envios_mi_nuevo_form"
    mapping_dir: "nuevo_uuid"
    enabled: true
```

### Paso 6: Reiniciar Servicios

```bash
# Reiniciar API y workers
sudo systemctl restart renagro-api
sudo systemctl restart renagro-worker-*
```

¡Listo! El sistema ahora procesa el nuevo formulario.

## 🔍 Monitoreo

### Ver Todos los Formularios Activos

```python
from src.forms_manager import forms_manager

for form in forms_manager.list_active_forms():
    print(f"{form.uuid}: {form.name} → {form.control_table}")
```

### Vista Unificada de Control

```sql
-- Ver todos los formularios en una sola consulta
SELECT * FROM v_control_envios_todos
ORDER BY created_at DESC
LIMIT 100;
```

### Estadísticas por Formulario

```sql
-- Estadísticas de un formulario específico
SELECT * FROM get_stats_by_form_type('boletas');
SELECT * FROM get_stats_by_form_type('boletas_procesos');
SELECT * FROM get_stats_by_form_type('boletas_simplificadas');
```

## ⚠️ Consideraciones

### Escalabilidad

- ✅ Agregar formularios no requiere cambios de código
- ✅ Cada formulario tiene tabla de control independiente
- ✅ Procesamiento paralelo de diferentes formularios
- ✅ Fácil mantenimiento y versionamiento

### Retrocompatibilidad

Si `forms_config.yml` no existe o un JSON no tiene `formhub/uuid`:
- Sistema usa configuración **por defecto**
- Carga mapeos desde `mapping/` (directorio original)
- Guarda en `control_envios_boletas`

### Performance

- Configuración se carga **una vez** al iniciar
- Mapeos se cachean en **Redis**
- Tablas independientes evitan bloqueos
- Índices optimizados por tabla

## 🛠️ Troubleshooting

### Error: "Formulario no reconocido"

**Causa:** UUID no está en `forms_config.yml`

**Solución:**
```yaml
# Agregar formulario a forms_config.yml
forms:
  - uuid: "el_uuid_del_error"
    ...
```

### Error: "Mapeos no encontrados"

**Causa:** Carpeta `mappings/{uuid}/` no existe

**Solución:**
```bash
mkdir -p mappings/{uuid}
# Copiar YAMLs necesarios
```

### Error: "Tabla de control no existe"

**Causa:** Tabla no creada en BD

**Solución:**
```bash
psql -d renagro_db -f scripts/create_control_tables.sql
```

## 📈 Futuro

Para agregar más formularios en el futuro:
1. Crear tabla de control
2. Crear carpeta de mapeos
3. Editar `forms_config.yml`
4. Reiniciar servicios

**No se requieren cambios de código** ✅
