# Ejemplos de uso del API

## 1. Health Check
```bash
curl http://localhost:8000/health
```

## 2. POST /boletas con autenticación básica

### Usando curl:
```bash
curl -X POST http://localhost:8000/boletas \
  -u admin:admin123 \
  -H "Content-Type: application/json" \
  -d @json-examples/results/220.json
```

### Usando Python requests:
```python
import requests
from requests.auth import HTTPBasicAuth
import json

# Leer JSON
with open('json-examples/results/220.json', 'r') as f:
    data = json.load(f)

# Enviar a API
response = requests.post(
    'http://localhost:8000/boletas',
    auth=HTTPBasicAuth('admin', 'admin123'),
    json=data
)

print(response.status_code)
print(response.json())
```

## 3. Acceder a documentación interactiva

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

## 4. Respuestas

### Éxito (200):
```json
{
  "success": true,
  "message": "Procesamiento completado exitosamente",
  "_id": 220,
  "estado_etl": "PROCESADO",
  "entities_processed": 8,
  "total_rows_inserted": 42,
  "execution_time": 0.123,
  "errors": []
}
```

### Error autenticación (401):
```json
{
  "detail": "Credenciales inválidas"
}
```

### Error validación (400):
```json
{
  "detail": "El JSON no contiene el campo '_id'"
}
```

### Error procesamiento (500):
```json
{
  "detail": "Error ejecutando transacción: ..."
}
```
