# 🚀 RENAGRO ETL Process - Proyecto Completo

## ✅ TODO LO QUE SE HA CREADO

### 📁 Estructura Completa del Proyecto

```
renagro-etl-process/
│
├── 📄 .gitignore                    # Exclusiones para Git
├── 📄 .env.example                  # Template de variables de entorno
├── 📄 requirements.txt              # Dependencias Python
├── 📄 README.md                     # Documentación completa (principal)
├── 📄 QUICKSTART.md                 # Guía rápida de inicio
├── 📄 PROJECT_SUMMARY.md            # Resumen del proyecto
├── 🔧 setup.sh                      # Script de instalación automática
├── 🔍 verify_setup.py               # Script de verificación de instalación
│
├── 📂 src/                          # Código fuente Python
│   ├── __init__.py                  # Módulo principal
│   ├── __main__.py                  # Punto de entrada del módulo
│   ├── config.py                    # Configuración y variables de entorno
│   ├── models.py                    # Modelos SQLAlchemy (ORM)
│   ├── database.py                  # Manejo de conexiones PostgreSQL
│   ├── mapping_loader.py            # Cargador de archivos YAML
│   ├── transformer.py               # Motor de transformación JSON → SQL
│   └── process_json.py              # Script CLI principal
│
├── 📂 scripts/                      # Scripts SQL y utilidades
│   └── create_control_table.sql     # Creación de tabla de control
│
├── 📂 mapping/                      # Archivos YAML de mapeo
│   ├── master.yml                   # Archivo maestro (ya existía)
│   ├── personas_example.yaml        # Ejemplo de mapeo completo
│   ├── bovinos.yaml                 # (existente)
│   ├── pollos.yaml                  # (existente)
│   ├── porcinos.yaml                # (existente)
│   ├── boletas.yaml                 # (existente)
│   ├── miembros_hogar.yaml          # (existente)
│   ├── terrenos.yaml                # (existente)
│   ├── cultivos.yaml                # (existente)
│   ├── forestales.yaml              # (existente)
│   └── pecuarios_otros.yaml         # (existente)
│
├── 📂 docs/                         # Documentación adicional
│   └── json_example.md              # Estructura del JSON de KoboToolbox
│
└── 📂 data/                         # Datos de prueba
    └── test_example.json            # JSON de ejemplo para testing
```

## 🎯 RESUMEN EJECUTIVO

### ¿Qué hace este sistema?

1. **Recibe** JSONs de formularios de KoboToolbox (~18KB cada uno)
2. **Almacena** el JSON completo en PostgreSQL (tabla `control_envios_boletas`)
3. **Transforma** los datos según archivos de mapeo YAML configurables
4. **Genera** sentencias SQL INSERT optimizadas para múltiples tablas
5. **Respeta** dependencias de Foreign Keys en el orden de inserción
6. **Controla** el estado del procesamiento ETL

### Características Principales

✅ **Almacenamiento seguro** - JSON completo en JSONB  
✅ **Mapeo declarativo** - Archivos YAML fáciles de mantener  
✅ **Conversión de tipos** - Integer, Decimal, Boolean, String  
✅ **Conversiones personalizadas** - Si/No → true/false, etc.  
✅ **SQL optimizado** - INSERT con múltiples VALUES  
✅ **Orden de procesamiento** - 4 grupos según dependencias FK  
✅ **CLI intuitivo** - Script de línea de comandos  
✅ **Logging descriptivo** - Mensajes claros de progreso  
✅ **Control de estados** - PENDIENTE, PROCESADO, ERROR  

## 📋 GUÍA DE INICIO RÁPIDO

### Paso 1: Instalación Automática

```bash
cd /Users/mac/Documents/projects/RENAGRO/CODIGO/renagro-etl-process

# Hacer ejecutable y ejecutar
chmod +x setup.sh
./setup.sh
```

### Paso 2: Configurar Base de Datos

```bash
# Editar credenciales
nano .env

# Crear tabla de control
psql -U postgres -d renagro_db -f scripts/create_control_table.sql
```

### Paso 3: Verificar Instalación

```bash
# Activar ambiente virtual
source venv/bin/activate

# Ejecutar verificación
python verify_setup.py
```

### Paso 4: Procesar Primer JSON

```bash
# Procesar JSON de ejemplo
python -m src.process_json data/test_example.json

# O solo generar SQL sin guardar en BD
python -m src.process_json --skip-db data/test_example.json
```

## 🗄️ TABLA DE CONTROL

La tabla `control_envios_boletas` almacena:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `_id` | INTEGER (PK) | ID del envío desde KoboToolbox |
| `formhub_uuid` | VARCHAR(255) UNIQUE | UUID único del formulario |
| `json_data` | JSONB | JSON completo del envío |
| `fecha_recepcion` | TIMESTAMP | Fecha/hora de recepción |
| `estado_etl` | ENUM | PENDIENTE, PROCESADO, ERROR |
| `envio_datos_procesados` | ENUM | Estado de envío a API externa |
| `created_at` | TIMESTAMP | Fecha de creación |
| `updated_at` | TIMESTAMP | Última actualización |
| `error_message` | TEXT | Mensaje de error (si aplica) |
| `procesado_at` | TIMESTAMP | Fecha de procesamiento exitoso |

## 🗺️ SISTEMA DE MAPEO YAML

### Estructura de un Archivo de Mapeo

```yaml
version: 1.0
entity: nombre_entidad      # Nombre lógico de la entidad
table: nombre_tabla_bd      # Nombre de la tabla en PostgreSQL

fields:
  columna_bd:               # Nombre de columna en la BD
    source: "ruta.campo.json"  # Ruta en el JSON (dot notation)
    type: integer           # Tipo: integer, decimal, boolean, string
    default: 0              # Valor por defecto si no existe
    convert:                # Conversiones a aplicar (opcional)
      nombre_conversion: true

conversions:
  nombre_conversion:        # Definición de conversión personalizada
    valor_en_json: valor_en_bd
    Si: true
    No: false
```

### Ejemplo Real

```yaml
version: 1.0
entity: personas
table: personas

fields:
  per_sexo:
    source: "capitulo_1.datos_productor.sexo"
    type: integer
    convert:
      sexo_to_int: true
    default: null

  per_sabe_leer_escribir:
    source: "capitulo_1.datos_productor.sabe_leer_escribir"
    type: boolean
    convert:
      yes_no_to_bool: true
    default: false

conversions:
  sexo_to_int:
    Hombre: 1
    Mujer: 2
  
  yes_no_to_bool:
    Si: true
    No: false
```

## 🔄 ORDEN DE PROCESAMIENTO

El sistema procesa las entidades en **4 grupos** según dependencias:

### Grupo 1: Sin dependencias
- bovinos
- pecuario_otros
- pollos
- porcinos
- personas

### Grupo 2: Depende de IDs del Grupo 1
- boletas (necesita IDs de bovinos, porcinos, pollos, personas)

### Grupo 3: Depende de boletas
- miembros_hogar (necesita ID de boleta)
- terrenos (necesita ID de boleta)

### Grupo 4: Depende de terrenos
- cultivos (necesita ID de terreno)
- forestales (necesita ID de terreno)

## 💻 COMANDOS PRINCIPALES

### Instalación y Setup

```bash
# Instalación automática
./setup.sh

# Instalación manual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Procesamiento de JSONs

```bash
# Activar ambiente virtual
source venv/bin/activate

# Procesar JSON y guardar en BD
python -m src.process_json ruta/al/archivo.json

# Solo generar SQL (sin guardar)
python -m src.process_json --skip-db ruta/al/archivo.json

# Ver ayuda
python -m src.process_json --help
```

### Verificación

```bash
# Verificar instalación
python verify_setup.py

# Verificar conexión a BD
psql -U postgres -d renagro_db -c "SELECT version();"
```

### Consultas SQL Útiles

```sql
-- Ver todos los envíos
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

-- Ver JSON de un envío específico
SELECT json_data 
FROM sc_renagro_mag.control_envios_boletas 
WHERE _id = 12345;
```

## 📚 DOCUMENTACIÓN

| Archivo | Contenido |
|---------|-----------|
| `README.md` | Documentación completa del proyecto |
| `QUICKSTART.md` | Guía rápida de inicio |
| `PROJECT_SUMMARY.md` | Resumen técnico del proyecto |
| `docs/json_example.md` | Estructura del JSON de KoboToolbox |
| `mapping/personas_example.yaml` | Ejemplo completo de mapeo YAML |

## 🔧 TECNOLOGÍAS

- **Python 3.8+** - Lenguaje principal
- **SQLAlchemy 2.0** - ORM para PostgreSQL
- **PyYAML** - Procesamiento de archivos YAML
- **python-dotenv** - Manejo de variables de entorno
- **psycopg2-binary** - Driver PostgreSQL

## 🎓 PRÓXIMOS PASOS (Futuro)

### Fase 2: API REST
- [ ] Implementar API con FastAPI
- [ ] Endpoint POST para recibir JSONs de KoboToolbox
- [ ] Validación de JSONs entrantes

### Fase 3: Procesamiento Asíncrono
- [ ] Integrar RabbitMQ
- [ ] Crear workers para cada cola
- [ ] Implementar reintentos automáticos

### Fase 4: Ejecución de Transacciones
- [ ] Ejecutar INSERT statements en PostgreSQL
- [ ] Manejo de transacciones con SQLAlchemy
- [ ] Actualización de estados en control_envios_boletas

### Fase 5: Grupos Repetidos
- [ ] Detección automática de repeat groups en JSON
- [ ] Generación de múltiples registros por entidad

### Fase 6: Monitoreo
- [ ] Sistema de logging estructurado
- [ ] Dashboard de monitoreo
- [ ] Alertas de errores

## ✅ CHECKLIST DE INSTALACIÓN

- [ ] Python 3.8+ instalado
- [ ] PostgreSQL 12+ instalado y corriendo
- [ ] Ambiente virtual creado (`venv/`)
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Archivo `.env` configurado
- [ ] Tabla `control_envios_boletas` creada
- [ ] Verificación exitosa (`python verify_setup.py`)
- [ ] JSON de prueba procesado exitosamente

## 🐛 SOLUCIÓN DE PROBLEMAS

### Error: "No module named 'sqlalchemy'"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "could not connect to server"
- Verificar que PostgreSQL esté corriendo: `pg_isready`
- Verificar credenciales en `.env`
- Verificar que la base de datos existe

### Error: "relation does not exist"
```bash
psql -U postgres -d renagro_db -f scripts/create_control_table.sql
```

### Error: "No such file or directory: .env"
```bash
cp .env.example .env
nano .env  # Editar con tus configuraciones
```

## 📞 RECURSOS

- **Documentación SQLAlchemy**: https://docs.sqlalchemy.org/
- **PyYAML Docs**: https://pyyaml.org/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/

---

**Estado**: ✅ Fase 1 Completada  
**Versión**: 0.1.0  
**Fecha**: Noviembre 2025  
**Proyecto**: RENAGRO - Ministerio de Agricultura y Ganadería del Ecuador
