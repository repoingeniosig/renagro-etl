# PostgREST API - Boletas Aprobadas

API REST para consultar boletas del RENAGRO que han sido aprobadas y enviadas exitosamente.

## Arquitectura

```
Cliente (curl/app) → PostgREST (:3000) → PostgreSQL (schema api) → sc_renagro_mag.*
                         ↑
                    Valida JWT
```

PostgREST expone funciones SQL del schema `api` como endpoints REST. La autenticación se realiza mediante tokens JWT.

## Requisitos

- Docker y Docker Compose
- Python 3.x con `PyJWT` (`pip install PyJWT`) para generar tokens

## Levantar el servicio

```bash
docker-compose up -d renagro-etl-db renagro-etl-postgrest
```

## Ejecutar migración

Antes del primer uso, ejecutar la migración que crea el schema `api`, los roles y las funciones:

```bash
# Desde el host (PostgreSQL debe estar corriendo)
psql -h localhost -U postgres -d renagro -f migrations/023_create_postgrest_api.sql
```

O desde dentro del contenedor:

```bash
docker exec -i renagro-etl-db psql -U postgres -d renagro < migrations/023_create_postgrest_api.sql
```

## Generar token JWT

```bash
# Token con valores por defecto (rol=api_user, expira en 24h)
python scripts/generate_jwt_token.py

# Token personalizado
python scripts/generate_jwt_token.py --role api_user --exp 48 --secret "your-super-secret-jwt-key-min-32-chars!"

# Verificar un token existente
python scripts/generate_jwt_token.py --verify "eyJhbGciOiJIUzI1NiIs..."
```

> **Importante:** El `--secret` debe coincidir con `PGRST_JWT_SECRET` configurado en `docker-compose.yml` y/o la variable de entorno `POSTGREST_JWT_SECRET`.

## Endpoints

### GET `/rpc/get_boletas_aprobadas`

Retorna boletas con `estado_etl = 'APROBADO'` y `envio_datos_procesados = 'ENVIADO'`.

**Autenticación requerida:** Sí (JWT con `role: api_user`)

**Parámetros:**

| Parámetro    | Tipo   | Default | Descripción                                      |
|-------------|--------|---------|--------------------------------------------------|
| `p_after_id` | BIGINT | 0       | Cursor keyset: último `id` recibido en la página anterior |
| `p_limit`    | INT    | 100     | Registros por página (máximo 100)                |

**Ejemplo — Primera página:**

```bash
curl -s \
  -H "Authorization: Bearer <TOKEN>" \
  "http://localhost:3000/rpc/get_boletas_aprobadas?p_limit=10"
```

**Ejemplo — Siguiente página (cursor):**

```bash
# Si el último objeto de la respuesta anterior tenía "id": 847
curl -s \
  -H "Authorization: Bearer <TOKEN>" \
  "http://localhost:3000/rpc/get_boletas_aprobadas?p_after_id=847&p_limit=10"
```

**Respuesta:**

```json
[
  {
    "id": 1,
    "boletaIdLevanta": "abc-123",
    "estadoBoleta": "RECALIFICADO",
    "provincia": "10",
    "canton": "101",
    "personaProductora": {
      "primerNombre": "JUAN",
      "segundoNombre": "CARLOS",
      "primerApellido": "PÉREZ",
      "segundoApellido": "GONZÁLEZ",
      "identificacion": "0923456789",
      "tipoIdentificacion": "1",
      "isPersonaJuridica": false,
      "isPersonaNatural": true,
      "razonSocial": null
    },
    "terrenos": [
      {
        "terrenoNo": 1,
        "superficie": 5.5,
        "cultivos": [...],
        "cultivosForestales": [...]
      }
    ],
    "miembroHogar": [...],
    "bovino": { ... },
    "porcino": { ... },
    "pollo": { ... },
    "pecuarioOtro": { ... },
    "..."
  }
]
```

Cuando no hay más registros, retorna `[]` (array vacío).

---

### GET `/rpc/get_boletas_aprobadas_count`

Retorna el conteo de boletas disponibles y el máximo por página.

**Autenticación requerida:** Sí (JWT con `role: api_user`)

**Ejemplo:**

```bash
curl -s \
  -H "Authorization: Bearer <TOKEN>" \
  "http://localhost:3000/rpc/get_boletas_aprobadas_count"
```

**Respuesta:**

```json
{
  "estimatedTotal": 487523,
  "maxPerPage": 100
}
```

## Flujo de paginación completo

```python
import requests

TOKEN = "eyJhbGciOiJIUzI1NiIs..."
BASE = "http://localhost:3000"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# 1. Obtener total estimado
r = requests.get(f"{BASE}/rpc/get_boletas_aprobadas_count", headers=HEADERS)
print(f"Total estimado: {r.json()['estimatedTotal']}")

# 2. Paginar con keyset
after_id = 0
page = 1
while True:
    r = requests.get(
        f"{BASE}/rpc/get_boletas_aprobadas",
        params={"p_after_id": after_id, "p_limit": 100},
        headers=HEADERS,
    )
    data = r.json()
    if not data:
        break
    print(f"Página {page}: {len(data)} registros (ids {data[0]['id']}..{data[-1]['id']})")
    after_id = data[-1]["id"]
    page += 1
```

## Errores comunes

| Código | Causa | Solución |
|--------|-------|----------|
| 401    | Token JWT faltante o inválido | Verificar header `Authorization: Bearer <token>` |
| 403    | Rol sin permisos | El token debe tener `"role": "api_user"` |
| 404    | Función no encontrada | Verificar que la migración 023 se ejecutó correctamente |

## Configuración

Variables en `.env` / `docker-compose.yml`:

| Variable | Descripción | Default |
|----------|-------------|---------|
| `POSTGREST_JWT_SECRET` | Secreto compartido para firmar/validar JWT (mínimo 32 caracteres) | `your-super-secret-jwt-key-min-32-chars!` |
| `POSTGREST_PORT` | Puerto de PostgREST | `3000` |
| `POSTGREST_DB_MAX_ROWS` | Máximo de filas por request (safety net) | `100` |

## Seguridad

- **Solo lectura**: El rol `api_user` tiene únicamente permisos `SELECT` sobre `sc_renagro_mag`
- **Sin acceso anónimo**: El rol `web_anon` no tiene permisos sobre las funciones de datos
- **SECURITY DEFINER**: Las funciones se ejecutan con los permisos del owner, no del caller
- **JWT obligatorio**: Toda petición sin token válido recibe `401 Unauthorized`
- **En producción**: cambiar `POSTGREST_JWT_SECRET` y la contraseña del rol `authenticator`
