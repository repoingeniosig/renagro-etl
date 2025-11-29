# Ejemplo de estructura JSON de KoboToolbox

Este archivo muestra un ejemplo simplificado de la estructura JSON que se recibe desde KoboToolbox.

```json
{
  "_id": 12345,
  "formhub/uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "_submission_time": "2025-01-15T10:30:00",
  
  "capitulo_1": {
    "datos_productor": {
      "cedula": "1234567890",
      "nombres": "Juan",
      "apellidos": "Pérez González",
      "sexo": "Hombre",
      "fecha_nacimiento": "1980-05-15",
      "edad": 44,
      "estado_civil": "Casado",
      "nivel_educacion": "Secundaria",
      "sabe_leer_escribir": "Si"
    },
    "contacto": {
      "celular": "0987654321",
      "telefono": "022345678",
      "email": "juan.perez@example.com"
    },
    "ubicacion": {
      "provincia": "Pichincha",
      "canton": "Quito",
      "parroquia": "Calderón"
    }
  },
  
  "capitulo_2": {
    "terrenos": [
      {
        "numero_terreno": 1,
        "area_ha": 5.5,
        "tipo_propiedad": "Propia",
        "tiene_riego": "Si",
        "latitud": -0.123456,
        "longitud": -78.654321
      },
      {
        "numero_terreno": 2,
        "area_ha": 2.3,
        "tipo_propiedad": "Arrendada",
        "tiene_riego": "No",
        "latitud": -0.234567,
        "longitud": -78.765432
      }
    ]
  },
  
  "capitulo_3": {
    "seccion3_1": {
      "tieneAnimales": "Si",
      "tieneBovinos": "Si",
      "numeroBovinos": 12,
      "lecheLitrosDia": 35.5,
      "tienePorcinos": "No",
      "tienePollos": "Si",
      "numeroPollos": 50
    },
    "bovinos_detail": [
      {
        "tipo": "Vaca lechera",
        "cantidad": 8,
        "raza": "Holstein"
      },
      {
        "tipo": "Terneros",
        "cantidad": 4,
        "raza": "Holstein"
      }
    ]
  },
  
  "capitulo_4": {
    "cultivos": [
      {
        "nombre_cultivo": "Maíz",
        "area_cultivada": 2.0,
        "produccion_total": 4000,
        "unidad": "kg",
        "destino": "Venta"
      },
      {
        "nombre_cultivo": "Papa",
        "area_cultivada": 1.5,
        "produccion_total": 3000,
        "unidad": "kg",
        "destino": "Autoconsumo y venta"
      }
    ]
  }
}
```

## Notas importantes:

1. **_id**: Campo único que identifica el envío (usado como PK en control_envios_boletas)
2. **formhub/uuid**: UUID único del formulario (puede venir como "formhub/uuid" o anidado)
3. **Grupos repetidos**: Arrays como `terrenos`, `bovinos_detail`, `cultivos` que generan múltiples registros
4. **Valores Si/No**: Se convierten a booleanos true/false según el mapeo
5. **Rutas con punto**: En los archivos YAML se usa notación de punto (ej: "capitulo_1.datos_productor.cedula")

## Tamaño aproximado:
- Un formulario completo pesa entre 15-20 KB en disco
- Formato JSON compacto, sin espacios adicionales
