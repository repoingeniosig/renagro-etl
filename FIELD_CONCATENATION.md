# Concatenación de Múltiples Campos - Documentación

## Descripción

Se ha implementado soporte para concatenar valores de múltiples campos del JSON en un solo campo de destino. Esta funcionalidad es útil cuando necesitas crear códigos compuestos o identificadores que combinan varios valores.

## Uso

### 1. Source como String Simple (Comportamiento Tradicional)

```yaml
bol_provincia:
  source: "pre_datos_upa_group/provincia_pre"
  type: string
  default: null
```

**Resultado:** Extrae el valor de un solo campo del JSON.

---

### 2. Source como Array (Concatenación)

```yaml
bol_codigo_UPA:
  source: 
    - "pre_datos_upa_group/poligono_pre"
    - "pre_datos_upa_group/numero_upa"
    - "pre_datos_upa_group/codigo_encuestador"
    - "pre_datos_upa_group/numero_boleta"
  type: string
  default: null
```

**Comportamiento:**
- Extrae el valor de cada campo en el orden especificado
- Concatena todos los valores **sin separador**
- Si un valor es `None`, se reemplaza por string vacío

**Ejemplo:**
```json
{
  "pre_datos_upa_group": {
    "poligono_pre": "001",
    "numero_upa": "042",
    "codigo_encuestador": "ENC123",
    "numero_boleta": "789"
  }
}
```

**Resultado:** `"001042ENC123789"`

---

### 3. Aplicación de Funciones de Transformación

Puedes aplicar funciones de transformación al valor extraído usando el campo `func`:

```yaml
bol_sector_muestreo:
  source: 
    field: "pre_datos_upa_group/sector_muestreo"
    func: upper
  type: string
  default: null
```

**Funciones disponibles:**
- `upper` - Convierte a mayúsculas
- `lower` - Convierte a minúsculas
- `strip` - Elimina espacios al inicio y final
- `capitalize` - Primera letra mayúscula
- `title` - Primera letra de cada palabra en mayúscula

**Ejemplo:**
```json
{
  "pre_datos_upa_group": {
    "sector_muestreo": "rural"
  }
}
```

**Resultado:** `"RURAL"`

---

## Casos de Uso

### Código UPA Compuesto

```yaml
bol_codigo_UPA:
  source: 
    - "pre_datos_upa_group/poligono_pre"
    - "pre_datos_upa_group/numero_upa"
    - "pre_datos_upa_group/codigo_encuestador"
    - "pre_datos_upa_group/numero_boleta"
  type: string
  default: null
```

**Input:** `["001", "042", "ENC123", "789"]`  
**Output:** `"001042ENC123789"`

---

### Código DPA (División Político-Administrativa)

```yaml
codigo_dpa:
  source: 
    - "ubicacion/provincia"
    - "ubicacion/canton"
    - "ubicacion/parroquia"
  type: string
  default: null
```

**Input:** `["17", "01", "05"]`  
**Output:** `"170105"`

---

### Identificador con Fecha

```yaml
identificador_boleta:
  source: 
    - "fecha_encuesta"
    - "codigo_encuestador"
    - "numero_boleta"
  type: string
  default: null
```

**Input:** `["20231215", "ENC001", "042"]`  
**Output:** `"20231215ENC001042"`

---

## Manejo de Valores None

Si alguno de los campos a concatenar tiene valor `None`:

```yaml
codigo_compuesto:
  source: 
    - "campo1"  # = "A"
    - "campo2"  # = None
    - "campo3"  # = "C"
  type: string
  default: null
```

**Resultado:** `"AC"` (el None se convierte en string vacío)

Si **todos** los campos son `None`:

**Resultado:** `None` (se respeta el default del campo)

---

## Implementación Técnica

### Archivos Modificados

1. **`src/mapping_loader.py`**
   - `FieldMapping.source` ahora acepta `str` o `List[str]`
   - Agregado campo `func` para transformaciones

2. **`src/transformer.py`**
   - Nuevo método `extract_and_concatenate_sources()` para concatenación
   - Nuevo método `apply_function()` para transformaciones
   - Modificado `transform_entity()` para manejar arrays en source

### Flujo de Procesamiento

```
source: List[str]
    ↓
extract_and_concatenate_sources()
    ↓
Para cada path en la lista:
    - Normalizar path (/ → .)
    - Extraer valor con get_value_by_path()
    - Convertir a string (None → '')
    ↓
Concatenar todos los valores
    ↓
Si resultado vacío → None
Sino → String concatenado
    ↓
Aplicar func si está definido
    ↓
convert_value() (conversión de tipo)
    ↓
Valor final en la fila
```

---

## Ejemplos Adicionales

### Concatenación con Separador Personalizado

Si necesitas un separador, puedes crear campos intermedios:

```yaml
# Opción 1: Concatenar sin separador (como está ahora)
codigo_sin_separador:
  source: 
    - "campo1"
    - "campo2"
  type: string

# Opción 2: Para separadores, usa el campo directamente en SQL
# o implementa una función personalizada
```

### Transformación y Concatenación Juntas

```yaml
codigo_normalizado:
  source: 
    field:
      - "grupo/campo1"
      - "grupo/campo2"
    func: upper
  type: string
  default: null
```

**Nota:** Actualmente `func` se aplica **después** de la concatenación. Si necesitas aplicar transformaciones a campos individuales antes de concatenar, deberás crear campos intermedios.

---

## Testing

Ejecuta el test de validación:

```bash
cd /path/to/renagro-etl-process
source venv/bin/activate
python3 test_concatenation.py
```

**Tests incluidos:**
1. ✅ Concatenación de múltiples campos
2. ✅ Source como string simple (comportamiento tradicional)
3. ✅ Aplicación de funciones (upper, lower, etc.)
4. ✅ Manejo de valores None parciales
5. ✅ Manejo de todos los valores None

---

## Notas Importantes

1. **Separador de paths:** Los YAML usan `/` como separador, pero internamente se convierten a `.` para compatibilidad con `get_value_by_path()`

2. **Orden de concatenación:** Los valores se concatenan en el mismo orden en que aparecen en el array

3. **Sin separador automático:** Los valores se concatenan directamente sin espacios ni guiones

4. **Compatibilidad:** La funcionalidad es retrocompatible - los campos con `source` como string siguen funcionando igual

5. **Performance:** No hay impacto significativo en performance - solo se ejecuta cuando `source` es un array
