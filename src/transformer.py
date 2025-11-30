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
    def get_value_by_path(data: Dict[str, Any], path: str) -> Any:
        """
        Obtiene un valor del JSON usando notación de punto y soporte para índices de array
        
        Args:
            data: Diccionario con los datos JSON
            path: Ruta en notación de punto con soporte para índices
                  (ej: "capitulo_3.seccion3_1.tieneAnimales" o "_geolocation[0]" o "group[0]")
        
        Returns:
            El valor encontrado o None si no existe
        """
        import re
        
        # Patrón para detectar índices: campo[índice]
        pattern = r'([^\[]+)(\[(\d+)\])?'
        
        keys = path.split('.')
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
                return str(value) if value is not None else field_mapping.default
            
            else:
                return value
        
        except (ValueError, TypeError):
            return field_mapping.default
    
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
            
            # Si source está vacío, usar directamente el default
            if not field_mapping.source or field_mapping.source.strip() == "":
                value = None  # convert_value usará el default
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
            else:
                # Obtener el valor del JSON normalmente
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
                    # El path relativo después de terrenos_repeat
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
