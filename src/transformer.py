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
        Obtiene un valor del JSON usando notación de punto
        
        Args:
            data: Diccionario con los datos JSON
            path: Ruta en notación de punto (ej: "capitulo_3.seccion3_1.tieneAnimales")
        
        Returns:
            El valor encontrado o None si no existe
        """
        keys = path.split('.')
        value = data
        
        try:
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return None
                    
                if value is None:
                    return None
            
            return value
        except (KeyError, TypeError, AttributeError):
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
            for conversion_name, conversion_enabled in field_mapping.convert.items():
                if conversion_enabled and conversion_name in conversions:
                    conversion_map = conversions[conversion_name]
                    if value in conversion_map:
                        value = conversion_map[value]
        
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
            # Obtener el valor del JSON
            value = JSONTransformer.get_value_by_path(json_data, field_mapping.source)
            
            # Convertir el valor
            converted_value = JSONTransformer.convert_value(
                value,
                field_mapping,
                entity_mapping.conversions
            )
            
            row[column_name] = converted_value
        
        return row
    
    @staticmethod
    def transform_entity_with_repeats(
        json_data: Dict[str, Any],
        entity_mapping: EntityMapping,
        repeat_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Transforma datos JSON que pueden tener grupos repetidos
        
        Args:
            json_data: Datos JSON del formulario
            entity_mapping: Mapeo de la entidad
            repeat_path: Ruta al grupo repetido (ej: "capitulo_4.seccion4_1.bovinos_repeat")
        
        Returns:
            Lista de diccionarios con los valores transformados
        """
        if not repeat_path:
            # Si no hay repeat, retornar un solo registro
            return [JSONTransformer.transform_entity(json_data, entity_mapping)]
        
        # Obtener el array de elementos repetidos
        repeat_items = JSONTransformer.get_value_by_path(json_data, repeat_path)
        
        if not repeat_items or not isinstance(repeat_items, list):
            return []
        
        # Transformar cada elemento del repeat
        rows = []
        for item in repeat_items:
            # Crear un contexto temporal que incluye el item actual y el JSON completo
            # para permitir acceso a campos fuera del repeat
            context = {**json_data, **item}
            row = JSONTransformer.transform_entity(context, entity_mapping)
            rows.append(row)
        
        return rows


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
