# Conversión Automática a Mayúsculas en ETL

## 📋 Descripción del Cambio

Se ha implementado la conversión automática a **MAYÚSCULAS** para **TODOS** los campos de tipo `string` en el proceso ETL. Esta conversión se aplica durante la transformación de JSON a sentencias SQL, garantizando que todos los datos textuales se almacenen en mayúsculas en la base de datos.

## 🎯 Objetivo

Estandarizar el formato de todos los textos almacenados en la base de datos para:
- Facilitar búsquedas y comparaciones
- Mantener consistencia en los datos
- Evitar problemas de mayúsculas/minúsculas en consultas

## ⚙️ Implementación

### Archivo Modificado

**`src/transformer.py`** - Método `convert_value()`

```python
elif field_mapping.type == 'string':
    if value is not None:
        str_value = str(value)
        # Convertir a mayúsculas por defecto para todos los strings
        return str_value.upper()
    return field_mapping.default
```

### Comportamiento por Tipo de Campo

| Tipo de Campo | Conversión | Ejemplo |
|--------------|------------|---------|
| `string` | **→ MAYÚSCULAS** | `"pichincha"` → `"PICHINCHA"` |
| `email` | Sin cambios | `"usuario@ejemplo.com"` → `"usuario@ejemplo.com"` |
| `integer` | Sin cambios | `42` → `42` |
| `float` / `decimal` | Sin cambios | `3.14` → `3.14` |
| `boolean` | Sin cambios | `true` → `true` |
| `datetime` | Sin cambios | `"2023-12-15"` → `"2023-12-15"` |
| `uuid` | Sin cambios | `"550e8400-..."` → `"550e8400-..."` |

## 📊 Ejemplos de Conversión

### Campos de Ubicación
```yaml
# Input JSON
{
  "provincia": "pichincha",
  "canton": "quito",
  "parroquia": "el inca"
}

# Output SQL
provincia = 'PICHINCHA'
canton = 'QUITO'
parroquia = 'EL INCA'
```

### Códigos y Referencias
```yaml
# Input JSON
{
  "codigo_encuestador": "enc123",
  "sector": "rural"
}

# Output SQL
codigo_encuestador = 'ENC123'
sector = 'RURAL'
```

### Nombres y Observaciones
```yaml
# Input JSON
{
  "nombre": "Juan Pérez",
  "observacion": "Texto con MAYÚSCULAS y minúsculas"
}

# Output SQL
nombre = 'JUAN PÉREZ'
observacion = 'TEXTO CON MAYÚSCULAS Y MINÚSCULAS'
```

### Emails
```yaml
# Input JSON
{
  "email": "productor@ejemplo.com"
}

# Output SQL con type: email
email = 'productor@ejemplo.com'

# Output SQL con type: string
email = 'PRODUCTOR@EJEMPLO.COM'
```

**Nota:** Los emails deben definirse como `type: email` en el mapping YAML para preservar su formato original. Si se definen como `type: string`, se convertirán a mayúsculas.

### Concatenación de Campos
```yaml
# Campo con concatenación (bol_codigo_UPA)
source:
  - "poligono_pre"      # "001"
  - "numero_upa"        # "042"
  - "codigo_encuestador" # "enc123"
  - "numero_boleta"     # "789"

# Output SQL
bol_codigo_UPA = '001042ENC123789'
```

**Nota:** La concatenación ocurre primero, luego se aplica `.upper()` al resultado final.

## 🔧 Configuración en YAML

### Campos Afectados

Todos los campos definidos como `type: string` en los archivos YAML de mapping se convertirán automáticamente:

```yaml
# mappings/boletas/boletas.yaml
bol_provincia:
  source: "pre_datos_upa_group/provincia_pre"
  type: string  # ← Se convierte a MAYÚSCULAS
  default: null

bol_direccion_email:
  source: "capitulos_1_10_wrapper/datos_pp_group/comunicacion_group/correo_electronico_direccion"
  type: email  # ← NO se convierte a mayúsculas
  default: null

bol_numero_boleta:
  source: "pre_datos_upa_group/numero_boleta"
  type: integer  # ← NO se convierte
  default: null
```

### Sin Configuración Adicional Necesaria

La conversión es **automática** y **no requiere** ninguna configuración adicional en los archivos YAML. Simplemente funciona para todos los campos `string`.

## ✅ Tests Realizados

Se ejecutaron tests exhaustivos que verificaron:

1. ✅ Conversión de strings en minúsculas → MAYÚSCULAS
2. ✅ Conversión de strings con mayúsculas/minúsculas mezcladas → MAYÚSCULAS
3. ✅ Conversión de códigos alfanuméricos → MAYÚSCULAS
4. ✅ Preservación de campos numéricos (integer) sin cambios
5. ✅ Preservación de campos booleanos sin cambios
6. ✅ Preservación de UUIDs sin cambios
7. ✅ Conversión de emails → MAYÚSCULAS
8. ✅ Conversión en campos concatenados
9. ✅ Integración con mapping real de boletas
10. ✅ Manejo de caracteres especiales (tildes, espacios, etc.)

## 🚀 Alcance del Cambio

### Archivos Afectados

- ✅ `src/transformer.py` - Modificado
- ℹ️  Todos los mappings YAML - Sin cambios necesarios

### Proceso ETL Completo

La conversión se aplica en:

1. **API REST** (`src/api.py`)
   - Endpoint POST `/etl/process`
   - Recibe JSON → Transforma → Inserta en BD

2. **CLI** (`src/__main__.py`)
   - Comando: `python -m src process`
   - Lee JSON desde archivo/stdin → Transforma → Inserta en BD

3. **Workers RabbitMQ** (`src/workers.py`)
   - Worker: `etl_transform`
   - Consume cola → Transforma → Publica a siguiente cola

### Formularios Soportados

- ✅ Boletas principales
- ✅ Boletas simplificadas
- ✅ Boletas de procesos
- ✅ Todos los sub-formularios (cultivos, terrenos, personas, etc.)

## 📝 Consideraciones

### Ventajas

- ✅ **Consistencia:** Todos los datos textuales en formato uniforme
- ✅ **Búsquedas:** Facilita consultas SQL sin preocuparse por case-sensitivity
- ✅ **Comparaciones:** Simplifica comparaciones de strings
- ✅ **Estandarización:** Elimina inconsistencias en la entrada de datos

### Limitaciones

- ⚠️  **URLs:** Si se almacenan como `type: string`, se convertirán a mayúsculas
- ⚠️  **JSON/XML:** Datos estructurados como string se convertirán a mayúsculas

### Recomendaciones

1. **Para emails:** Usa `type: email` en el mapping YAML para preservar el formato original
   ```yaml
   bol_direccion_email:
     source: "ruta/al/campo"
     type: email  # ← Correcto para emails
     default: null
   ```

2. **Para preservar mayúsculas/minúsculas en otros campos:**
   - Usa `type: email` (para emails)
   - Usa `type: uuid` (para UUIDs)
   - Crea nuevos tipos específicos si es necesario

3. **Para campos que requieren formato específico (URLs, JSON):**
   - Considera almacenarlos en un tipo diferente a `string`
   - O procésalos antes de enviar al ETL

## 🔍 Verificación

Puedes verificar que los datos se guardan correctamente en mayúsculas:

```sql
SELECT 
    bol_provincia,
    bol_canton,
    bol_parroquia,
    bol_codigo_encuestador
FROM sc_renagro_mag.boletas
LIMIT 5;

-- Resultado esperado:
-- PICHINCHA | QUITO | EL INCA | ENC123
-- AZUAY     | CUENCA | SAN SEBASTIÁN | ENC456
```

## 🆘 Soporte y Rollback

Si por alguna razón necesitas desactivar esta funcionalidad:

1. **Modificar** `src/transformer.py`:
   ```python
   elif field_mapping.type == 'string':
       if value is not None:
           # return str(value).upper()  # ← Comentar esta línea
           return str(value)  # ← Descomentar esta línea
       return field_mapping.default
   ```

2. **Reiniciar** servicios:
   ```bash
   sudo systemctl restart renagro-worker-etl-transform
   sudo systemctl restart renagro-api
   ```

## 📅 Historial de Cambios

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2025-12-15 | 1.0 | Implementación inicial de conversión automática a mayúsculas |

---

**Autor:** Sistema ETL RENAGRO  
**Fecha:** 15 de diciembre de 2025
