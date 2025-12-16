# Redis Cache para Mapeos YAML

## 🚀 Descripción

El sistema ahora utiliza Redis como cache para los mapeos YAML, optimizando el rendimiento al procesar múltiples JSONs.

### Ventajas

- **10-100x más rápido**: Primera ejecución normal, siguientes usan cache
- **Escalable**: Miles de JSONs comparten el mismo cache
- **Resiliente**: Si Redis falla, automáticamente usa lectura desde disco
- **Fácil invalidación**: Un comando actualiza el cache

## 🔧 Configuración

### 1. Variables de entorno (.env)

```env
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_TTL=3600          # 1 hora (tiempo de vida del cache)
REDIS_ENABLED=true      # false para deshabilitar el cache
```

### 2. Iniciar Redis con Docker

```bash
# Opción 1: Con docker-compose (incluye PostgreSQL y RabbitMQ)
docker-compose up -d

# Opción 2: Solo Redis
docker run -d -p 6379:6379 --name renagro-redis redis:7-alpine

# Verificar que Redis esté corriendo
docker ps | grep redis
redis-cli ping  # Debe responder: PONG
```

## 📖 Uso

### Procesamiento Normal

El cache se usa automáticamente:

```bash
# Primera ejecución: Lee YAML desde disco + Guarda en Redis
python -m src.process_json archivo.json

# Siguientes ejecuciones: Lee desde Redis (mucho más rápido)
python -m src.process_json otro_archivo.json
```

### Invalidar Cache (después de actualizar YAMLs)

Cuando modificas archivos YAML de mapeo:

```bash
# Opción 1: Script Python
python -m src.invalidate_cache

# Opción 2: Directamente con redis-cli
redis-cli DEL renagro:mappings

# Opción 3: Forzar recarga en el código
# En mapping_loader:
mapping_loader.load_all_mappings(force_reload=True)
mapping_loader.invalidate_cache()
```

### Deshabilitar Cache

Si no quieres usar Redis:

```env
# En .env
REDIS_ENABLED=false
```

O detener Redis:

```bash
docker stop renagro-redis
```

El sistema automáticamente detectará que Redis no está disponible y usará disco.

## 🔍 Monitoreo

### Ver estadísticas del cache

```python
from src.redis_client import redis_client

stats = redis_client.get_stats()
print(stats)
# {
#   'enabled': True,
#   'connected': True,
#   'has_cache': True,
#   'ttl': 3245  # segundos restantes
# }
```

### Conectarse a Redis

```bash
# CLI de Redis
redis-cli

# Ver todas las claves
127.0.0.1:6379> KEYS *

# Ver el cache de mapeos
127.0.0.1:6379> EXISTS renagro:mappings

# Ver TTL restante
127.0.0.1:6379> TTL renagro:mappings

# Borrar cache
127.0.0.1:6379> DEL renagro:mappings
```

## 🎯 Flujo de Ejecución

```
┌─────────────────────────────────────────────────┐
│ 1. Intentar cargar desde Redis                  │
│    ↓                                             │
│    Cache hit? → SÍ → Usar mapeos cacheados     │
│              → NO → Continuar al paso 2         │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 2. Redis no disponible o sin cache              │
│    → Leer YAMLs desde disco (fallback)          │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 3. Intentar guardar en Redis para próxima vez   │
│    → Éxito: Próximas ejecuciones serán rápidas │
│    → Falla: Log warning, continúa normalmente   │
└─────────────────────────────────────────────────┘
```

## 📊 Logs del Sistema

```
# Cache hit (rápido)
✅ Mapeos cargados desde Redis cache (10 entidades)

# Cache miss (primera vez)
ℹ️  No hay mapeos en cache, se cargarán desde disco
📂 Cargando mapeos desde archivos YAML...
✅ 10 mapeos cargados desde disco
✅ Mapeos guardados en Redis cache

# Redis no disponible (fallback)
⚠️  No se pudo conectar a Redis: Connection refused
Se usará lectura directa desde disco como fallback
📂 Cargando mapeos desde archivos YAML...
✅ 10 mapeos cargados desde disco
⚠️  No se pudo guardar en cache: Connection refused
El proceso continuará normalmente
```

## 🛠️ Troubleshooting

### Redis no se conecta

```bash
# Verificar que Redis esté corriendo
docker ps | grep redis

# Ver logs de Redis
docker logs renagro-redis

# Reiniciar Redis
docker restart renagro-redis
```

### Cache desactualizado

```bash
# Invalidar cache
python -m src.invalidate_cache

# O forzar recarga
python -m src.process_json --force-reload archivo.json
```

### Verificar que el cache funciona

```bash
# Primera ejecución (debe decir "cargados desde disco")
time python -m src.process_json test.json

# Segunda ejecución (debe decir "desde Redis cache" y ser más rápida)
time python -m src.process_json test2.json
```

## 🔐 Seguridad

Si Redis requiere contraseña:

```env
REDIS_PASSWORD=tu_password_seguro
```

El cliente Redis usará automáticamente la contraseña configurada.
