# RENAGRO ETL Process

Sistema de procesamiento ETL para datos de KoboToolbox del proyecto RENAGRO.

## 📋 Descripción

Este proyecto procesa formularios recibidos desde KoboToolbox, almacena los datos en formato JSON, y genera sentencias SQL INSERT para poblar una base de datos PostgreSQL relacional basándose en archivos de mapeo YAML.

### Características principales:

- ✅ Recepción y almacenamiento de JSONs de KoboToolbox
- ✅ Mapeo declarativo mediante archivos YAML
- ✅ Transformación de datos con conversión de tipos
- ✅ Generación de sentencias SQL INSERT optimizadas
- ✅ Manejo de dependencias de claves foráneas
- ✅ Control de estado del procesamiento ETL
- 🚧 Integración con RabbitMQ (futura implementación)
- 🚧 API REST con FastAPI (futura implementación)

## 🏗️ Arquitectura

```
┌─────────────┐
│ KoboToolbox │
└──────┬──────┘
       │ POST JSON
       ▼
┌─────────────────┐
│  API REST       │ (Futuro)
│  (FastAPI)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  RabbitMQ       │◄────►│ Workers          │
│  Message Queue  │      │ - JSON Saver     │
└─────────────────┘      │ - Transformer    │
         │               │ - DB Inserter    │
         ▼               └──────────────────┘
┌─────────────────┐
│  PostgreSQL     │
│  - control_envios_boletas
│  - bovinos, pollos, etc.
└─────────────────┘
```

## 📁 Estructura del Proyecto

```
renagro-etl-process/
├── .env                    # Variables de entorno (crear desde .env.example)
├── .env.example            # Template de variables de entorno
├── .gitignore             # Archivos ignorados por git
├── requirements.txt       # Dependencias Python
├── README.md             # Este archivo
│
├── mapping/              # Archivos YAML de mapeo
│   ├── master.yml       # Archivo maestro con orden de procesamiento
│   ├── bovinos.yaml
│   ├── pollos.yaml
│   ├── porcinos.yaml
│   ├── personas.yaml
│   ├── boletas.yaml
│   ├── miembros_hogar.yaml
│   ├── terrenos.yaml
│   ├── cultivos.yaml
│   ├── forestales.yaml
│   └── pecuarios_otros.yaml
│
├── scripts/             # Scripts SQL y utilidades
│   └── create_control_table.sql
│
└── src/                 # Código fuente Python
    ├── __init__.py
    ├── config.py       # Configuración y variables de entorno
    ├── models.py       # Modelos SQLAlchemy
    ├── database.py     # Manejo de conexión a BD
    ├── mapping_loader.py   # Cargador de archivos YAML
    ├── transformer.py      # Motor de transformación
    └── process_json.py     # Script principal CLI
```

## 🚀 Instalación

### 1. Requisitos previos

- Python 3.8 o superior
- PostgreSQL 12 o superior
- Git

### 2. Clonar el repositorio (si aplica)

```bash
cd /Users/mac/Documents/projects/RENAGRO/CODIGO/renagro-etl-process
```

### 3. Crear ambiente virtual

```bash
# Crear ambiente virtual
python3 -m venv venv

# Activar ambiente virtual
# En macOS/Linux:
source venv/bin/activate

# En Windows:
# venv\Scripts\activate
```

### 4. Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configurar variables de entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones
nano .env  # o usar tu editor favorito
```

Configurar las siguientes variables en `.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=renagro_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_SCHEMA=sc_renagro_mag
```

### 6. Crear la tabla de control en PostgreSQL

```bash
# Conectarse a PostgreSQL
psql -U postgres -d renagro_db

# Ejecutar el script
\i scripts/create_control_table.sql

# o desde la línea de comandos:
psql -U postgres -d renagro_db -f scripts/create_control_table.sql
```

## 📖 Uso

### Procesar un archivo JSON

```bash
# Sintaxis básica
python -m src.process_json <ruta_al_archivo.json>

# Ejemplo
python -m src.process_json data/formulario_001.json

# Omitir guardado en BD (solo generar SQL)
python -m src.process_json --skip-db data/formulario_001.json
```

### Salida del script

El script realiza las siguientes acciones:

1. **Carga el archivo JSON** y muestra información básica
2. **Guarda en `control_envios_boletas`** el JSON completo con:
   - `_id` del formulario
   - `json_data` completo en JSONB
   - `estado_etl` = 'PENDIENTE'
   - `envio_datos_procesados` = 'PENDIENTE'
3. **Procesa las transformaciones** según los archivos YAML en `mapping/`
4. **Genera sentencias INSERT** para cada tabla siguiendo el orden de dependencias
5. **Imprime las sentencias SQL** en consola de forma legible

### Ejemplo de salida

```
================================================================================
RENAGRO ETL PROCESS - Procesador de formularios KoboToolbox
================================================================================

📂 Cargando archivo JSON: data/formulario_001.json
✅ Archivo cargado exitosamente
   Tamaño: 18,432 bytes (18.00 KB)
   Claves principales: 25 campos

💾 Guardando en base de datos...
✅ JSON guardado en control_envios_boletas
   _id: 12345
   estado_etl: PENDIENTE

================================================================================
INICIANDO PROCESO DE TRANSFORMACIÓN
================================================================================

📋 Cargando archivos de mapeo YAML...
✅ Mapeos cargados: 10 entidades

📊 Orden de procesamiento en 4 grupos:
   Grupo 1: bovinos, pecuario_otros, pollos, porcinos, personas
   Grupo 2: boletas
   Grupo 3: miembros_hogar, terrenos
   Grupo 4: cultivos, forestales

================================================================================
PROCESANDO GRUPO 1: bovinos, pecuario_otros, pollos, porcinos, personas
================================================================================

🔄 Procesando entidad: bovinos
   Tabla destino: bovinos
   Campos a mapear: 15
   ✅ Registros generados: 1
   ✅ Sentencia SQL generada (1,234 caracteres)

[... más entidades ...]

================================================================================
SENTENCIAS SQL GENERADAS
================================================================================

✅ Total de sentencias generadas: 10

────────────────────────────────────────────────────────────────────────────────
ENTIDAD: BOVINOS
────────────────────────────────────────────────────────────────────────────────
INSERT INTO "sc_renagro_mag"."bovinos" ("tieneBovinos", "cantidadBovinos", ...)
VALUES
    (TRUE, 12, 35.5, 'Pichincha', 'Quito');

[... más sentencias ...]

✅ Proceso completado exitosamente
```

## 🗺️ Archivos de Mapeo YAML

Los archivos YAML definen cómo transformar los campos del JSON a columnas de la base de datos.

### Estructura de un archivo de mapeo

```yaml
version: 1.0
entity: bovinos
table: bovinos

fields:
  tieneBovinos:
    source: "capitulo_3.seccion3_1.tieneAnimales"
    type: boolean
    convert:
      yes_no_to_bool: true
    default: false

  cantidadBovinos:
    source: "capitulo_3.seccion3_1.numeroBovinos"
    type: integer
    default: 0

  litrosLeche:
    source: "capitulo_3.seccion3_1.lecheLitrosDia"
    type: decimal
    default: 0.0

  provincia:
    source: "capitulo_1.direccion.provincia"
    type: string

conversions:
  yes_no_to_bool:
    Si: true
    Sí: true
    No: false
```

### Tipos de datos soportados

- `integer`: Números enteros
- `decimal`: Números decimales (float)
- `boolean`: Valores booleanos (true/false)
- `string`: Cadenas de texto

### Conversiones personalizadas

```yaml
conversions:
  yes_no_to_bool:
    Si: true
    Sí: true
    No: false
  
  estado_civil:
    SOLTERO: 1
    CASADO: 2
    DIVORCIADO: 3
    VIUDO: 4
```

### Archivo master.yml

Define el orden de procesamiento de las entidades:

```yaml
# Grupo 1: Sin dependencias
bovinos: "mapping/bovinos.yaml"
pecuario_otros: "mapping/pecuarios_otros.yaml"
pollos: "mapping/pollos.yaml"
porcinos: "mapping/porcinos.yaml"
personas: "mapping/personas.yaml"

# Grupo 2: Depende de IDs del grupo 1
boletas: "mapping/boletas.yaml"

# Grupo 3: Depende de boletas
miembros_hogar: "mapping/miembros_hogar.yaml"
terrenos: "mapping/terrenos.yaml"

# Grupo 4: Depende de terrenos
cultivos: "mapping/cultivos.yaml"
forestales: "mapping/forestales.yaml"
```

## 🗄️ Base de Datos

### Tabla de Control

La tabla `control_envios_boletas` almacena:

```sql
CREATE TABLE "sc_renagro_mag"."control_envios_boletas" (
  "_id" INTEGER PRIMARY KEY,
  "json_data" JSONB NOT NULL,
  "fecha_recepcion" TIMESTAMP WITH TIME ZONE NOT NULL,
  "estado_etl" estado_etl_enum NOT NULL DEFAULT 'PENDIENTE',
  "envio_datos_procesados" estado_envio_enum NOT NULL DEFAULT 'PENDIENTE',
  "created_at" TIMESTAMP WITH TIME ZONE NOT NULL,
  "updated_at" TIMESTAMP WITH TIME ZONE NOT NULL,
  "error_message" TEXT,
  "procesado_at" TIMESTAMP WITH TIME ZONE
);
```

### Estados del procesamiento

**estado_etl:**
- `PENDIENTE`: JSON recibido, pendiente de transformar
- `PROCESADO`: Transformación completada exitosamente
- `ERROR`: Error durante la transformación

**envio_datos_procesados:**
- `PENDIENTE`: Pendiente de enviar a API externa
- `PROCESADO`: Enviado exitosamente
- `ERROR`: Error durante el envío

## 🔧 Desarrollo

### Estructura del código

- **config.py**: Maneja variables de entorno y configuración
- **models.py**: Define modelos SQLAlchemy (ORM)
- **database.py**: Maneja conexiones a PostgreSQL
- **mapping_loader.py**: Carga y valida archivos YAML
- **transformer.py**: Motor de transformación JSON → SQL
- **process_json.py**: Script CLI principal

### Agregar una nueva entidad

1. Crear archivo YAML en `mapping/nueva_entidad.yaml`
2. Agregar referencia en `mapping/master.yml`
3. Ejecutar el script para procesar un JSON

### Ejecutar tests (futuro)

```bash
pytest tests/
```

## 📝 Próximos pasos

- [ ] Implementar soporte para campos `repeat` (grupos repetidos)
- [ ] Agregar API REST con FastAPI para recibir JSONs
- [ ] Integrar RabbitMQ para procesamiento asíncrono
- [ ] Implementar workers para cada cola de mensajes
- [ ] Agregar manejo de errores y reintentos
- [ ] Implementar transacciones SQL con SQLAlchemy
- [ ] Agregar envío a API de terceros
- [ ] Tests unitarios y de integración
- [ ] Logging estructurado
- [ ] Monitoreo y métricas

## 🤝 Contribución

1. Crear una rama para tu feature
2. Hacer commit de los cambios
3. Push a la rama
4. Crear Pull Request

## 📄 Licencia

Proyecto interno RENAGRO - Ministerio de Agricultura y Ganadería del Ecuador

## 👥 Contacto

Proyecto RENAGRO - Sistema de Tableros
