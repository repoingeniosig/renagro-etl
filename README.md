# RENAGRO ETL Process

Sistema de procesamiento ETL para datos de KoboToolbox del proyecto RENAGRO.

## 📋 Descripción

Este proyecto procesa formularios recibidos desde KoboToolbox, almacena los datos en formato JSON, y genera sentencias SQL INSERT para poblar una base de datos PostgreSQL relacional basándose en archivos de mapeo YAML.

### Características principales:

- ✅ Recepción y almacenamiento de JSONs de KoboToolbox
- ✅ API REST con FastAPI y autenticación básica
- ✅ Pipeline asíncrono con RabbitMQ (3 colas)
- ✅ Mapeo declarativo mediante archivos YAML
- ✅ Cache Redis para mapeos YAML
- ✅ Transformación de datos con conversión de tipos
- ✅ Generación de sentencias SQL INSERT optimizadas
- ✅ Manejo de dependencias de claves foráneas
- ✅ Sistema de reintentos con backoff exponencial
- ✅ Dead Letter Queues para errores permanentes
- ✅ Recuperación automática de mensajes fallidos
- ✅ Control de estado del procesamiento ETL
- ✅ Logging centralizado con rotación semanal

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

## 🚀 Despliegue en Producción

### Recomendación: Usar systemd (NO scripts .sh)

Para producción, **NO uses scripts .sh**. En su lugar, usa servicios systemd para gestión profesional:

✅ **systemd** ofrece:
- Auto-restart si un worker muere
- Logs centralizados con journalctl
- Gestión de dependencias entre servicios
- Control de recursos (CPU, memoria)
- Auto-start en boot del servidor
- Integración con monitoreo

Ver documentación completa: **[systemd/README.md](systemd/README.md)**

### Instalación rápida en servidor

```bash
# 1. Copiar código al servidor
rsync -avz ./ servidor:/opt/renagro-etl-process/

# 2. Ejecutar instalación automatizada
ssh servidor
cd /opt/renagro-etl-process
sudo bash systemd/install.sh

# 3. Configurar .env
sudo nano /opt/renagro-etl-process/.env

# 4. Ejecutar migración SQL
psql -h localhost -U postgres -d renagro_db \
  -f /opt/renagro-etl-process/migrations/001_add_retry_fields.sql

# 5. Iniciar servicios
sudo systemctl start renagro-api.service
sleep 10  # Esperar carga de mapeos
sudo systemctl start renagro-worker-json-save.service
sudo systemctl start renagro-worker-etl-transform.service
sudo systemctl start renagro-worker-db-insert.service

# 6. Verificar
sudo systemctl status renagro-*
sudo journalctl -u renagro-api.service -f
```

### Logs en Producción

**Estrategia dual:**

1. **systemd journal** (principal - RECOMENDADO):
```bash
# Ver logs en tiempo real
sudo journalctl -u renagro-api.service -f
sudo journalctl -u 'renagro-worker-*' -f

# Logs con errores
sudo journalctl -u renagro-api.service -p err

# Exportar logs
sudo journalctl -u renagro-api.service --since today > api-logs.txt
```

2. **Archivos logs/** (secundario - debugging):
- `etl_process.log` - Logs generales
- `etl_errors.log` - Solo errores
- Rotación automática semanal (12 semanas)
- Configurar logrotate (ver `systemd/logrotate-renagro`)

**¿Por qué NO usar logs de workers individuales?**
- systemd journal centraliza TODO
- No necesitas logs/worker_json_save.log separados
- journalctl filtra por servicio automáticamente
- Rotación automática sin configuración

### Nginx como reverse proxy

Ver configuración completa en: **[systemd/README.md](systemd/README.md#configuración-nginx)**

```bash
# Instalar certificado SSL
sudo certbot --nginx -d etl.renagro.gob.ec

# Configurar proxy
sudo nano /etc/nginx/sites-available/renagro-etl
sudo ln -s /etc/nginx/sites-available/renagro-etl /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 📊 Monitoreo y Manejo de Errores

### Sistema de Reintentos

El sistema implementa **reintentos automáticos con backoff exponencial**:

- Intento 1: delay 2 segundos
- Intento 2: delay 4 segundos
- Intento 3: delay 8 segundos
- Después de 3 intentos → Dead Letter Queue (DLQ)

Ver documentación completa: **[ERROR_HANDLING.md](ERROR_HANDLING.md)**

### Consultar mensajes con error

```sql
-- Errores permanentes (requieren corrección de código)
SELECT _id, retry_count, last_error_stage, error_message
FROM sc_renagro_mag.control_envios_boletas
WHERE estado_etl = 'ERROR' AND retry_count >= 3
ORDER BY fecha_recepcion DESC;

-- Mensajes en reintentos
SELECT _id, retry_count, last_error_stage, error_message
FROM sc_renagro_mag.control_envios_boletas
WHERE estado_etl = 'PENDIENTE' AND retry_count > 0;
```

### Recuperación automática

Al reiniciar el servidor API, el sistema:
1. Busca registros con `estado_etl='ERROR'` y `retry_count < 3`
2. Obtiene el JSON completo de la BD
3. Republica a la cola correspondiente según `last_error_stage`
4. Continúa el pipeline desde donde falló

### Ejecutar tests (futuro)

```bash
pytest tests/
```

## 📝 Documentación Adicional

- **[ERROR_HANDLING.md](ERROR_HANDLING.md)** - Sistema de reintentos y DLQ
- **[REDIS_CACHE.md](REDIS_CACHE.md)** - Cache de mapeos YAML
- **[ENVIO_MAG.md](ENVIO_MAG.md)** - Envío de datos a API remota MAG
- **[DUPLICATE_PROTECTION.md](DUPLICATE_PROTECTION.md)** - Protección contra duplicados en timer
- **[systemd/PRODUCTION_DEPLOYMENT.md](systemd/PRODUCTION_DEPLOYMENT.md)** - Despliegue completo en producción
- **[systemd/README.md](systemd/README.md)** - Configuración systemd services
- **[COMMIT_TYPES.md](COMMIT_TYPES.md)** - Convenciones de commits

## ✅ Estado del Proyecto

- [x] API REST con FastAPI
- [x] Pipeline asíncrono con RabbitMQ
- [x] Workers para cada cola de mensajes
- [x] Manejo de errores y reintentos
- [x] Dead Letter Queues (DLQ)
- [x] Recuperación automática de mensajes
- [x] Transacciones SQL con SQLAlchemy
- [x] Cache Redis para mapeos YAML
- [x] Logging con rotación semanal
- [x] Servicios systemd para producción
- [x] Construcción de JSONs para envío a MAG
- [x] Envío paralelo a API remota con reintentos
- [ ] Tests unitarios y de integración
- [ ] Métricas con Prometheus

## 🚀 Envío de Datos a API Remota (MAG)

El sistema incluye workers **asíncronos e independientes** para envío de datos procesados a API remota.

### Arquitectura Asíncrona

```
Worker envio_mag (construcción)          Worker envio_mag_sender (envío)
        │                                          │
        ▼                                          ▼
   Consulta BD ────► Construye JSON ────► RabbitMQ ────► Consume ────► HTTP POST
   (PENDIENTE)       (publica a cola)     (queue)        (paralelo)     (API remota)
        │                                                                     │
        │                                                                     ▼
        └─── NO espera ───┐                                            UPDATE estado
                          │                                            ENVIADO/ERROR
                          ▼
                   Siguiente lote
```

**Funcionamiento independiente:**
- Worker `envio_mag`: Consulta BD, construye JSONs, publica a RabbitMQ
- Worker `envio_mag_sender`: Consume cola, envía HTTP, actualiza estados
- **NO se bloquean entre sí**: Construcción y envío en paralelo

### Configuración

Agregar en `.env`:

```bash
# API Remota RENAGRO
RENAGRO_ENDPOINT=https://api.renagro.gob.ec/v1/boletas
RENAGRO_TOKEN=Bearer tu_token_aqui

# Colas (auto-configuradas)
QUEUE_ENVIO_MAG_SEND=renagro.envio.mag.send
QUEUE_ENVIO_MAG_SEND_RETRY=renagro.envio.mag.send.retry
QUEUE_ENVIO_MAG_SEND_DLQ=renagro.envio.mag.send.dlq

# Configuración de envío
PARALLEL_REQUESTS_SEND_MAG=10    # Solicitudes simultáneas
MAX_RETRY_ATTEMPTS=3              # Reintentos para errores 5xx
BATCH_SIZE_SEND_MAG=1000          # Registros por lote
DEBUG_JSON_OUTPUT=false           # true para guardar JSONs localmente
```

### Ejecutar Workers

**Ejecutar en terminales separadas (desarrollo):**

```bash
# Terminal 1: Construir JSONs desde BD
python -m src.workers envio_mag

# Terminal 2: Enviar JSONs a API remota (en paralelo)
python -m src.workers envio_mag_sender
```

**Producción con systemd:**

```bash
# Iniciar ambos workers (se ejecutan continuamente)
sudo systemctl start renagro-envio-mag.service
sudo systemctl start renagro-envio-mag-sender.service

# Ver logs
sudo journalctl -u renagro-envio-mag.service -f
sudo journalctl -u renagro-envio-mag-sender.service -f
```

### Estados de Envío

| Estado | Descripción | Cuándo se establece |
|--------|-------------|---------------------|
| `PENDIENTE` | JSON construido, en cola | Después de publicar a RabbitMQ |
| `ENTREGANDO` | Enviando a API | Antes de HTTP POST |
| `ENVIADO` | Enviado exitosamente | **Después de HTTP 201** |
| `ERROR` | Error permanente | Después de reintentos agotados o 4xx |

### Reintentos

- **Error 4xx** (cliente): NO reintenta, marca ERROR inmediatamente
- **Error 5xx** (servidor): Reintenta con backoff (5s → 10s → 20s)
- **Error de red**: Reintenta hasta MAX_RETRY_ATTEMPTS

### Consultas Útiles

```sql
-- Pendientes de envío
SELECT COUNT(*) FROM control_envios_boletas
WHERE estado_etl='PROCESADO' AND envio_datos_procesados='PENDIENTE';

-- Estadísticas de envío
SELECT envio_datos_procesados, COUNT(*) 
FROM control_envios_boletas 
WHERE estado_etl='PROCESADO'
GROUP BY envio_datos_procesados;

-- Errores de envío
SELECT _id, error_envio_datos 
FROM control_envios_boletas 
WHERE envio_datos_procesados='ERROR'
LIMIT 10;
```

**Para más detalles:** Ver [ENVIO_MAG.md](ENVIO_MAG.md)

## 🤝 Contribución

1. Crear una rama para tu feature
2. Hacer commit de los cambios
3. Push a la rama
4. Crear Pull Request

## 📄 Licencia

Proyecto interno RENAGRO - Ministerio de Agricultura y Ganadería del Ecuador

## 👥 Contacto

Proyecto RENAGRO - Sistema de Tableros
