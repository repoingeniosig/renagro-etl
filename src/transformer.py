"""
Motor de transformación de JSON a SQL
Extrae datos del JSON según los mapeos YAML y genera sentencias INSERT
"""
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal
import json

from .mapping_loader import EntityMapping, FieldMapping


class JSONTransformer:
    """Transformador de JSON a estructuras relacionales"""
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """
        Sanitiza un string siguiendo estas reglas:
        1. Reemplaza vocales con tilde por su equivalente sin tilde (á→a, é→e, í→i, ó→o, ú→u)
        2. Reemplaza ñ por n (tanto minúscula como mayúscula)
        3. Elimina caracteres especiales, preservando solo: letras (a-z, A-Z), números (0-9) y espacios
        4. Elimina saltos de línea y tabulaciones
        
        Args:
            value: String a sanitizar
        
        Returns:
            String sanitizado
        """
        import re
        if not isinstance(value, str):
            return value
        
        # PASO 1: Reemplazar vocales con tilde por equivalente sin tilde
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
            'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
            'À': 'A', 'È': 'E', 'Ì': 'I', 'Ò': 'O', 'Ù': 'U',
            'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u',
            'Ä': 'A', 'Ë': 'E', 'Ï': 'I', 'Ö': 'O', 'Ü': 'U',
            'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u',
            'Â': 'A', 'Ê': 'E', 'Î': 'I', 'Ô': 'O', 'Û': 'U',
            'ñ': 'n', 'Ñ': 'N'
        }
        
        for old_char, new_char in replacements.items():
            value = value.replace(old_char, new_char)
        
        # PASO 2: Eliminar saltos de línea y tabulaciones
        value = value.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # PASO 3: Eliminar caracteres especiales (solo permitir letras a-z, A-Z, números 0-9 y espacios)
        sanitized = re.sub(r'[^a-zA-Z0-9 ]', '', value)
        
        # PASO 4: Normalizar espacios múltiples a un solo espacio
        sanitized = re.sub(r' +', ' ', sanitized)
        
        # PASO 5: Eliminar espacios al inicio y final
        sanitized = sanitized.strip()
        
        return sanitized
    
    @staticmethod
    def evaluate_condition(
        json_data: Dict[str, Any],
        condition: Dict[str, Any],
        conversions: Dict = None
    ) -> bool:
        """
        Evalúa una condición 'when' para determinar si se debe extraer un valor
        
        Args:
            json_data: Datos JSON del formulario
            condition: Diccionario con la condición (field, convert, equals)
            conversions: Diccionario de conversiones disponibles
        
        Returns:
            True si la condición se cumple, False en caso contrario
        
        Ejemplo condition:
            {
                'field': 'capitulos_1_10_wrapper/productos_pecuarios_group/ganado_bovino_group/existe_ganado_bovino',
                'convert': 'yes_no_to_bool',
                'equals': True
            }
        """
        if not condition or 'field' not in condition:
            return True  # Sin condición, siempre verdadero
        
        # Obtener el valor del campo de condición
        condition_field = condition['field']
        condition_value = JSONTransformer.get_value_by_path(json_data, condition_field)
        
        # Aplicar conversión si está especificada
        if 'convert' in condition and condition_value is not None:
            convert_name = condition['convert']
            
            # Aplicar conversión yes_no_to_bool
            if convert_name == 'yes_no_to_bool':
                if isinstance(condition_value, str):
                    value_lower = condition_value.lower().strip()
                    if value_lower in ('si', 'sí', 'yes', 'true', '1'):
                        condition_value = True
                    elif value_lower in ('no', 'false', '0'):
                        condition_value = False
            
            # Aplicar otras conversiones desde el diccionario
            elif conversions and convert_name in conversions:
                conversion_map = conversions[convert_name]
                if condition_value in conversion_map:
                    condition_value = conversion_map[condition_value]
        
        # Comparar con el valor esperado
        if 'equals' in condition:
            expected_value = condition['equals']
            return condition_value == expected_value
        
        # Si no hay 'equals', considerar verdadero si el valor no es None/False
        return bool(condition_value)
    
    @staticmethod
    def get_value_by_path(data: Dict[str, Any], path: str) -> Any:
        """
        Obtiene un valor del JSON usando notación de punto y soporte para índices de array
        Soporta claves directas de Kobo con slash (ej: "group/field")
        
        Args:
            data: Diccionario con los datos JSON
            path: Ruta en notación de punto o slash con soporte para índices
                  (ej: "capitulo_3.seccion3_1.tieneAnimales" o "group/field" o "_geolocation[0]")
        
        Returns:
            El valor encontrado o None si no existe
        """
        import re
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Primero intentar acceso directo (para claves de Kobo con /)
        if path in data:
            value = data[path]
            logger.debug(f"✓ Acceso directo exitoso: {path} = {value}")
            return value
        
        logger.debug(f"✗ Clave '{path}' NO encontrada como acceso directo. Keys disponibles: {list(data.keys())[:10]}...")
        #logger.info(f"Intentando navegación por niveles para: {path}")
        
        # Si no existe como clave directa, intentar navegación por niveles
        # Normalizar separadores: convertir / a . para compatibilidad
        normalized_path = path.replace('/', '.')
        
        # Patrón para detectar índices: campo[índice]
        pattern = r'([^\[]+)(\[(\d+)\])?'
        
        keys = normalized_path.split('.')
        value = data
        
        try:
            for key in keys:
                # Verificar si la clave tiene un índice de array
                match = re.match(pattern, key)
                if match:
                    field_name = match.group(1)
                    array_index = match.group(3)
                    
                    # Obtener el valor del campo
                    if isinstance(value, dict):
                        value = value.get(field_name)
                    else:
                        return None
                    
                    if value is None:
                        return None
                    
                    # Si hay índice y el valor es una lista, acceder al elemento
                    if array_index is not None:
                        if isinstance(value, list):
                            idx = int(array_index)
                            if 0 <= idx < len(value):
                                value = value[idx]
                            else:
                                return None
                        else:
                            return None
                else:
                    # Clave sin índice
                    if isinstance(value, dict):
                        value = value.get(key)
                    else:
                        return None
                    
                    if value is None:
                        return None
            
            return value
        except (KeyError, TypeError, AttributeError, ValueError):
            return None
    
    @staticmethod
    def convert_value(value: Any, field_mapping: FieldMapping, conversions: Dict = None) -> Any:
        """
        Convierte un valor según el tipo y las reglas de conversión especificadas
        
        Args:
            value: Valor a convertir
            field_mapping: Mapeo del campo con información de tipo y conversión
            conversions: Diccionario de conversiones disponibles
        
        Returns:
            Valor convertido
        """
        # Si el valor es None, usar el default
        if value is None:
            return field_mapping.default
        
        # Aplicar conversión personalizada si existe
        if field_mapping.convert and conversions:
            for conversion_name, conversion_param in field_mapping.convert.items():
                if conversion_name in conversions:
                    conversion_map = conversions[conversion_name]
                    if value in conversion_map:
                        value = conversion_map[value]
                # Conversión especial: contains_option
                elif conversion_name == 'contains_option':
                    option_to_check = conversion_param
                    if isinstance(value, str):
                        # Verificar si la opción está en el string (puede ser espacio o multi-select)
                        return option_to_check in value.split()
                    return False
                # Conversión especial: yes_no_to_bool
                elif conversion_name == 'yes_no_to_bool' and conversion_param:
                    if isinstance(value, str):
                        value_lower = value.lower().strip()
                        if value_lower in ('si', 'sí', 'yes', 'true', '1'):
                            value = True
                        elif value_lower in ('no', 'false', '0'):
                            value = False
        
        # Convertir según el tipo
        try:
            if field_mapping.type == 'integer':
                if isinstance(value, str):
                    value = value.strip()
                    if value == '':
                        return field_mapping.default
                return int(value) if value is not None else field_mapping.default
            
            elif field_mapping.type == 'decimal':
                if isinstance(value, str):
                    value = value.strip()
                    if value == '':
                        return field_mapping.default
                return float(value) if value is not None else field_mapping.default
            
            elif field_mapping.type == 'boolean':
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    value_lower = value.lower().strip()
                    if value_lower in ('si', 'sí', 'yes', 'true', '1'):
                        return True
                    elif value_lower in ('no', 'false', '0'):
                        return False
                return bool(value) if value is not None else field_mapping.default
            
            elif field_mapping.type == 'datetime':
                # Mantener como string para PostgreSQL, el motor lo parseará
                if value is not None:
                    return str(value)
                return field_mapping.default
            
            elif field_mapping.type == 'string':
                if value is not None:
                    str_value = str(value)
                    # Aplicar sanitización si sanitize es True (default)
                    if field_mapping.sanitize:
                        str_value = JSONTransformer.sanitize_string(str_value)
                    # Aplicar uppercase solo si apply_uppercase es True (default)
                    if field_mapping.apply_uppercase:
                        str_value = str_value.upper()
                    return str_value
                return field_mapping.default
            
            elif field_mapping.type == 'email':
                # Emails se tratan como strings pero NO se convierten a mayúsculas
                if value is not None:
                    str_value = str(value)
                    # Aplicar sanitización si sanitize es True (default)
                    # NOTA: Para emails, sanitize debería ser False en el YAML
                    if field_mapping.sanitize:
                        str_value = JSONTransformer.sanitize_string(str_value)
                    return str_value
                return field_mapping.default
            
            elif field_mapping.type == 'uuid':
                if value is not None:
                    return str(value)
                return field_mapping.default
            
            else:
                return value
        
        except (ValueError, TypeError):
            return field_mapping.default
    
    @staticmethod
    def extract_and_concatenate_sources(json_data: Dict[str, Any], sources) -> Optional[str]:
        """
        Extrae valores de múltiples fuentes y los concatena
        
        Args:
            json_data: Datos JSON del formulario
            sources: Lista de rutas a extraer (list de strings)
        
        Returns:
            String concatenado de todos los valores (sin separador) o None si todos son None
        """
        if not isinstance(sources, list):
            return None
        
        values = []
        for source_path in sources:
            # get_value_by_path maneja internamente la normalización de separadores
            value = JSONTransformer.get_value_by_path(json_data, source_path)
            if value is not None:
                values.append(str(value))
            else:
                values.append('')  # Agregar string vacío si es None para mantener orden
        
        # Si todos los valores son vacíos, retornar None
        concatenated = ''.join(values)
        return concatenated if concatenated else None
    
    @staticmethod
    def apply_function(value: Any, func_name: str) -> Any:
        """
        Aplica una función de transformación al valor
        
        Args:
            value: Valor a transformar
            func_name: Nombre de la función (upper, lower, etc.)
        
        Returns:
            Valor transformado
        """
        if value is None:
            return None
        
        value_str = str(value)
        
        if func_name == 'upper':
            return value_str.upper()
        elif func_name == 'lower':
            return value_str.lower()
        elif func_name == 'strip':
            return value_str.strip()
        elif func_name == 'capitalize':
            return value_str.capitalize()
        elif func_name == 'title':
            return value_str.title()
        else:
            return value
    
    @staticmethod
    def transform_entity(json_data: Dict[str, Any], entity_mapping: EntityMapping) -> Dict[str, Any]:
        """
        Transforma los datos JSON para una entidad según su mapeo
        
        Args:
            json_data: Datos JSON del formulario
            entity_mapping: Mapeo de la entidad
        
        Returns:
            Diccionario con los valores transformados listos para INSERT
        """
        row = {}
        
        for column_name, field_mapping in entity_mapping.fields.items():
            value = None
            
            # Si source está vacío o es string vacío, usar directamente el default
            if field_mapping.source is None or \
               (isinstance(field_mapping.source, str) and field_mapping.source.strip() == ""):
                value = None  # convert_value usará el default
            # Si source es un dict con condicional 'when'
            elif isinstance(field_mapping.source, dict) and 'when' in field_mapping.source:
                # Evaluar condición
                condition_met = JSONTransformer.evaluate_condition(
                    json_data,
                    field_mapping.source['when'],
                    entity_mapping.conversions
                )
                
                if condition_met:
                    # Extraer el valor del campo especificado
                    source_field = field_mapping.source.get('field')
                    if source_field:
                        value = JSONTransformer.get_value_by_path(json_data, source_field)
                else:
                    # Condición no cumplida, usar default
                    value = None
            # Si source es una lista, concatenar todos los valores
            elif isinstance(field_mapping.source, list):
                value = JSONTransformer.extract_and_concatenate_sources(json_data, field_mapping.source)
            # Manejar repeat_filter
            elif field_mapping.repeat_filter and field_mapping.extract:
                # Obtener el array de elementos
                repeat_items = JSONTransformer.get_value_by_path(json_data, field_mapping.source)
                
                if repeat_items and isinstance(repeat_items, list):
                    # Aplicar filtro
                    where_conditions = field_mapping.repeat_filter.get('where', {})
                    
                    for item in repeat_items:
                        # Verificar si el item cumple todas las condiciones
                        match = True
                        for field_path, expected_value in where_conditions.items():
                            item_value = JSONTransformer.get_value_by_path(item, field_path)
                            if str(item_value) != str(expected_value):
                                match = False
                                break
                        
                        if match:
                            # Extraer el valor del campo especificado
                            value = JSONTransformer.get_value_by_path(item, field_mapping.extract)
                            break
            # Source es un string normal
            else:
                # get_value_by_path maneja internamente la normalización de separadores
                value = JSONTransformer.get_value_by_path(json_data, field_mapping.source)
                
                # Si hay un extract sin repeat_filter, extraer el subcampo del valor obtenido
                # Caso: source="group[0]" obtiene un objeto, extract="campo" obtiene el valor del campo
                if field_mapping.extract and value is not None:
                    if isinstance(value, dict):
                        # El valor es un objeto, extraer el campo especificado
                        value = value.get(field_mapping.extract)
                    elif isinstance(value, list) and len(value) > 0:
                        # Si es una lista, intentar extraer del primer elemento
                        first_item = value[0]
                        if isinstance(first_item, dict):
                            value = first_item.get(field_mapping.extract)
            
            # Aplicar función si está definida
            if field_mapping.func and value is not None:
                value = JSONTransformer.apply_function(value, field_mapping.func)
            
            # Convertir el valor (siempre se agrega al row, incluso si es None/default)
            converted_value = JSONTransformer.convert_value(
                value,
                field_mapping,
                entity_mapping.conversions
            )
            
            # IMPORTANTE: Siempre agregar el campo, incluso si el valor es None o default
            row[column_name] = converted_value
        
        return row
    
    @staticmethod
    def transform_entity_with_repeats(
        json_data: Dict[str, Any],
        entity_mapping: EntityMapping,
        parent_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Transforma datos JSON que pueden tener grupos repetidos
        
        Args:
            json_data: Datos JSON del formulario
            entity_mapping: Mapeo de la entidad
            parent_id: ID del registro padre (para FK)
        
        Returns:
            Lista de diccionarios con los valores transformados, 
            cada uno con metadato __parent_index__ si es repeat anidado
        """
        # Si la entidad tiene repeat configurado
        if entity_mapping.repeat:
            # Obtener la ruta del repeat
            if isinstance(entity_mapping.repeat, dict):
                repeat_path = entity_mapping.repeat.get('source')
            else:
                repeat_path = entity_mapping.repeat
            
            # Detectar si es un repeat anidado (contiene otro repeat en el path)
            is_nested_repeat = '/terrenos_repeat/' in repeat_path
            
            if is_nested_repeat:
                # CASO ESPECIAL: Repeat anidado (ej: cultivos dentro de terrenos)
                # Necesitamos procesar cada terreno por separado y mantener el índice
                
                # Extraer el path del padre (terrenos)
                parent_repeat_path = repeat_path.split('/terrenos_repeat/')[0] + '/terrenos_repeat'
                terrenos = JSONTransformer.get_value_by_path(json_data, parent_repeat_path)
                
                if not terrenos or not isinstance(terrenos, list):
                    return []
                
                rows = []
                for terreno_index, terreno in enumerate(terrenos):
                    # Obtener cultivos/forestales de este terreno específico
                    # KoboToolbox guarda la ruta completa como clave, no como estructura anidada
                    # Intentar primero con el path completo (clave directa)
                    child_items = terreno.get(repeat_path)
                    
                    # Si no existe, intentar con path relativo (estructura anidada)
                    if child_items is None:
                        child_relative_path = repeat_path.split('/terrenos_repeat/')[1]
                        child_items = JSONTransformer.get_value_by_path(terreno, child_relative_path)
                    
                    if child_items and isinstance(child_items, list):
                        for item in child_items:
                            # Combinar contexto global + terreno + item
                            context = {**json_data, **terreno, **item}
                            row = JSONTransformer.transform_entity(context, entity_mapping)
                            
                            # IMPORTANTE: Agregar índice del terreno padre como metadato
                            row['__parent_index__'] = terreno_index
                            
                            rows.append(row)
                
                return rows
            
            else:
                # CASO NORMAL: Repeat simple (ej: miembros_hogar, terrenos)
                repeat_items = JSONTransformer.get_value_by_path(json_data, repeat_path)
                
                if not repeat_items or not isinstance(repeat_items, list):
                    return []
                
                rows = []
                for item in repeat_items:
                    # Combinar el contexto global con el item actual
                    context = {**json_data, **item}
                    row = JSONTransformer.transform_entity(context, entity_mapping)
                    
                    # Agregar parent_id si existe
                    if parent_id is not None and entity_mapping.parent_key:
                        if isinstance(entity_mapping.parent_key, dict):
                            parent_field = entity_mapping.parent_key.get('field')
                        else:
                            parent_field = entity_mapping.parent_key
                        
                        if parent_field:
                            row[parent_field] = parent_id
                    
                    rows.append(row)
                
                return rows
        else:
            # Sin repeat, generar un solo registro
            row = JSONTransformer.transform_entity(json_data, entity_mapping)
            
            # Agregar parent_id si existe
            if parent_id is not None and entity_mapping.parent_key:
                if isinstance(entity_mapping.parent_key, dict):
                    parent_field = entity_mapping.parent_key.get('field')
                else:
                    parent_field = entity_mapping.parent_key
                
                if parent_field:
                    row[parent_field] = parent_id
            
            return [row] if row else []
            
            rows.append(row)
        
        return rows
    
    @staticmethod
    def _merge_item_to_context(context: Dict[str, Any], repeat_path: str, item: Dict[str, Any]):
        """
        Fusiona un item del repeat en el contexto para que sus campos sean accesibles
        """
        # Navegar hasta el repeat y reemplazar con el item
        keys = repeat_path.split('/')
        current = context
        
        for i, key in enumerate(keys[:-1]):
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Reemplazar el último nivel con el item
        if keys:
            current[keys[-1]] = item


class SQLGenerator:
    """Generador de sentencias SQL INSERT"""
    
    @staticmethod
    def format_value_for_sql(value: Any) -> str:
        """
        Formatea un valor para ser usado en SQL
        
        Args:
            value: Valor a formatear
        
        Returns:
            String con el valor formateado para SQL
        """
        if value is None:
            return 'NULL'
        elif isinstance(value, bool):
            return 'TRUE' if value else 'FALSE'
        elif isinstance(value, (int, float, Decimal)):
            return str(value)
        elif isinstance(value, str):
            # Escapar comillas simples
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        else:
            # Para otros tipos, convertir a string y escapar
            escaped = str(value).replace("'", "''")
            return f"'{escaped}'"
    
    @staticmethod
    def generate_insert(
        table_name: str,
        rows: List[Dict[str, Any]],
        schema: str = 'sc_renagro_mag'
    ) -> Optional[str]:
        """
        Genera una sentencia INSERT con múltiples VALUES
        
        Args:
            table_name: Nombre de la tabla
            rows: Lista de diccionarios con los datos a insertar
            schema: Schema de la base de datos
        
        Returns:
            String con la sentencia INSERT completa o None si no hay datos
        """
        if not rows:
            return None
        
        # Obtener las columnas del primer registro (asumimos que todos tienen las mismas)
        columns = list(rows[0].keys())
        columns_str = ', '.join([f'"{col}"' for col in columns])
        
        # Generar los VALUES para cada fila
        values_list = []
        for row in rows:
            values = [SQLGenerator.format_value_for_sql(row[col]) for col in columns]
            values_str = ', '.join(values)
            values_list.append(f"({values_str})")
        
        # Unir todos los VALUES
        all_values = ',\n    '.join(values_list)
        
        # Construir la sentencia INSERT completa
        insert_statement = f"""INSERT INTO "{schema}"."{table_name}" ({columns_str})
VALUES
    {all_values};"""
        
        return insert_statement
    
    @staticmethod
    def generate_batch_insert(
        table_name: str,
        rows: List[Dict[str, Any]],
        schema: str = 'sc_renagro_mag',
        batch_size: int = 100
    ) -> List[str]:
        """
        Genera múltiples sentencias INSERT si hay muchos registros
        
        Args:
            table_name: Nombre de la tabla
            rows: Lista de diccionarios con los datos
            schema: Schema de la base de datos
            batch_size: Número máximo de registros por INSERT
        
        Returns:
            Lista de sentencias INSERT
        """
        if not rows:
            return []
        
        statements = []
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            stmt = SQLGenerator.generate_insert(table_name, batch, schema)
            if stmt:
                statements.append(stmt)
        
        return statements
