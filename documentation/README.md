# Documentación RENAGRO ETL

Documentación completa del sistema de procesamiento ETL para datos de KoboToolbox.

## 📚 Índice de Documentación

### Guías Generales

- **[README Principal](../README.md)** - Descripción general del proyecto, instalación y uso básico

### Arquitectura y Configuración

- **[DOCKER.md](DOCKER.md)** - Comandos Docker, configuración de contenedores y migraciones
- **[SERVER_SPECS.md](SERVER_SPECS.md)** - Especificaciones del servidor y requisitos de hardware

### Procesamiento ETL

- **[ERROR_HANDLING.md](ERROR_HANDLING.md)** - Sistema de reintentos, DLQ y manejo de errores
- **[REDIS_CACHE.md](REDIS_CACHE.md)** - Configuración y uso del cache Redis para mappings YAML
- **[BATCH_PROCESSOR.md](BATCH_PROCESSOR.md)** - Procesamiento por lotes de formularios JSON
- **[FIELD_CONCATENATION.md](FIELD_CONCATENATION.md)** - Concatenación de múltiples campos en mappings
- **[UPPERCASE_CONVERSION.md](UPPERCASE_CONVERSION.md)** - Conversión automática a mayúsculas en strings
- **[DUPLICATE_PROTECTION.md](DUPLICATE_PROTECTION.md)** - Protección contra duplicados en timer

### Envío a API Remota

- **[ENVIO_MAG.md](ENVIO_MAG.md)** - Sistema de envío de datos procesados a API remota MAG
- **[API_EXAMPLES.md](API_EXAMPLES.md)** - Ejemplos de uso de la API REST

## 🗂️ Documentación por Tema

### Instalación y Configuración Inicial

1. [README Principal](../README.md) - Instalación base
2. [DOCKER.md](DOCKER.md) - Configuración con Docker
3. [SERVER_SPECS.md](SERVER_SPECS.md) - Requisitos del servidor

### Desarrollo Local

1. [Scripts de Desarrollo](../scripts-dev/README.md) - Scripts para desarrollo local
2. [API_EXAMPLES.md](API_EXAMPLES.md) - Ejemplos de uso de la API

### Procesamiento de Datos

1. [BATCH_PROCESSOR.md](BATCH_PROCESSOR.md) - Cómo procesar lotes de datos
2. [FIELD_CONCATENATION.md](FIELD_CONCATENATION.md) - Concatenar campos múltiples
3. [UPPERCASE_CONVERSION.md](UPPERCASE_CONVERSION.md) - Conversión automática de texto

### Manejo de Errores

1. [ERROR_HANDLING.md](ERROR_HANDLING.md) - Sistema completo de errores y reintentos
2. [DUPLICATE_PROTECTION.md](DUPLICATE_PROTECTION.md) - Evitar procesamiento duplicado

### Optimización

1. [REDIS_CACHE.md](REDIS_CACHE.md) - Cache para mejorar rendimiento

### Integración Externa

1. [ENVIO_MAG.md](ENVIO_MAG.md) - Envío de datos a API remota

## 🚀 Guías Rápidas

### Para Desarrolladores Nuevos

1. Leer [README Principal](../README.md)
2. Configurar entorno con [Scripts de Desarrollo](../scripts-dev/README.md)
3. Revisar [API_EXAMPLES.md](API_EXAMPLES.md) para ejemplos prácticos

### Para Administradores de Sistema

1. Revisar [SERVER_SPECS.md](SERVER_SPECS.md)
2. Configurar con [DOCKER.md](DOCKER.md)
3. Implementar monitoreo con [ERROR_HANDLING.md](ERROR_HANDLING.md)

### Para Operadores

1. Usar [BATCH_PROCESSOR.md](BATCH_PROCESSOR.md) para procesar datos
2. Consultar [ERROR_HANDLING.md](ERROR_HANDLING.md) para resolver errores
3. Verificar [ENVIO_MAG.md](ENVIO_MAG.md) para estado de envíos

## 📖 Cómo Usar Esta Documentación

### Buscar por Palabra Clave

- **Docker**: Ver [DOCKER.md](DOCKER.md)
- **Errores**: Ver [ERROR_HANDLING.md](ERROR_HANDLING.md)
- **API**: Ver [API_EXAMPLES.md](API_EXAMPLES.md)
- **Cache**: Ver [REDIS_CACHE.md](REDIS_CACHE.md)
- **Envío**: Ver [ENVIO_MAG.md](ENVIO_MAG.md)
- **Mayúsculas**: Ver [UPPERCASE_CONVERSION.md](UPPERCASE_CONVERSION.md)
- **Concatenación**: Ver [FIELD_CONCATENATION.md](FIELD_CONCATENATION.md)
- **Lotes**: Ver [BATCH_PROCESSOR.md](BATCH_PROCESSOR.md)
- **Duplicados**: Ver [DUPLICATE_PROTECTION.md](DUPLICATE_PROTECTION.md)

### Flujo de Lectura Recomendado

#### Primera Vez
1. README Principal → Instalación básica
2. Scripts de Desarrollo → Ejecutar localmente
3. API Examples → Probar endpoints
4. Error Handling → Entender flujo de errores

#### Desarrollo de Features
1. Field Concatenation → Si necesitas concatenar campos
2. Uppercase Conversion → Si necesitas conversión de texto
3. Batch Processor → Si procesas muchos registros
4. Redis Cache → Si optimizas rendimiento

#### Troubleshooting
1. Error Handling → Sistema de errores
2. Duplicate Protection → Problemas de duplicados
3. Envío MAG → Errores de envío externo

## 🔗 Enlaces Externos

- **Repositorio**: (Agregar URL del repositorio)
- **Wiki del Proyecto**: (Agregar URL de wiki)
- **Issue Tracker**: (Agregar URL de issues)

## 📝 Convenciones

- `código` - Código inline o comandos
- **Negrita** - Conceptos importantes
- > Citas - Notas importantes o advertencias
- ✅ - Feature implementado
- ⚠️ - Advertencia
- 🚀 - Producción
- 🔧 - Desarrollo

## 🤝 Contribuir a la Documentación

Si encuentras errores o quieres mejorar la documentación:

1. Edita el archivo Markdown correspondiente
2. Usa el formato establecido
3. Agrega ejemplos cuando sea posible
4. Actualiza este índice si es necesario

## 📅 Última Actualización

**Fecha**: 15 de diciembre de 2025  
**Versión del Sistema**: 1.0
