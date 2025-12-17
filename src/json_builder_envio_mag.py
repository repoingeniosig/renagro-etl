"""
Transformador de datos de BD a JSON para envío a MAG
Construye la estructura JSON según los mapeos YAML
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal

from .config import config
from .logger import etl_logger
from .mapping_loader_envio_mag import EntityMappingEnvioMAG, FieldMappingEnvioMAG, mapping_loader_envio_mag


class JSONBuilderEnvioMAG:
    """Constructor de JSON para envío a MAG"""
    
    @staticmethod
    def convert_value(value: Any, field_mapping: FieldMappingEnvioMAG) -> Any:
        """
        Convierte un valor de BD al tipo esperado en el JSON
        
        Args:
            value: Valor de la base de datos
            field_mapping: Mapeo del campo con información de tipo y conversión
        
        Returns:
            Valor convertido
        """
        if value is None:
            return field_mapping.default
        
        # Aplicar conversión personalizada si existe
        if field_mapping.convert:
            for conversion_type, conversion_param in field_mapping.convert.items():
                if conversion_type == 'contains_option':
                    # Verificar si la opción está presente en el valor
                    if isinstance(value, str):
                        # El valor puede ser multi-select separado por espacios
                        return conversion_param in value.split()
                    return False
        
        # Convertir según el tipo
        try:
            if field_mapping.type == 'integer':
                if isinstance(value, str):
                    value = value.strip()
                    if value == '':
                        return field_mapping.default
                return int(value) if value is not None else field_mapping.default
            elif field_mapping.type == 'float':
                if isinstance(value, Decimal):
                    return float(value)
                if isinstance(value, str):
                    value = value.strip()
                    if value == '':
                        return field_mapping.default
                return float(value) if value is not None else field_mapping.default
            elif field_mapping.type == 'boolean':
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'si', 'sí', 't')
                return bool(value) if value is not None else field_mapping.default
            elif field_mapping.type == 'string':
                if value is not None:
                    str_value = str(value)
                    # Convertir a mayúsculas si UPPERCASE_JSON_MAG está habilitado
                    if config.UPPERCASE_JSON_MAG:
                        return str_value.upper()
                    return str_value
                return field_mapping.default
            elif field_mapping.type == 'email':
                # Emails NO se convierten a mayúsculas (incluso con UPPERCASE_JSON_MAG=true)
                if value is not None:
                    return str(value)
                return field_mapping.default
            else:
                return value
        except (ValueError, TypeError):
            return field_mapping.default
    
    @staticmethod
    def build_object_from_mapping(
        data_row: Dict[str, Any],
        entity_mapping: EntityMappingEnvioMAG,
        related_data: Dict[str, List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Construye un objeto JSON a partir de un registro de BD y su mapeo
        
        Args:
            data_row: Registro de la base de datos
            entity_mapping: Mapeo de la entidad
            related_data: Datos relacionados ya consultados {field_name: [registros]}
        
        Returns:
            Objeto JSON construido
        """
        result = {}
        
        for json_field_name, field_mapping in entity_mapping.fields.items():
            # Si tiene reference, es un objeto o array anidado
            if field_mapping.reference:
                # Cargar el mapeo referenciado
                referenced_mapping = mapping_loader_envio_mag.load_yaml_file(field_mapping.reference)
                
                if field_mapping.type == 'array':
                    # Es un array de objetos
                    result[json_field_name] = JSONBuilderEnvioMAG._build_array_field(
                        data_row,
                        json_field_name,
                        referenced_mapping,
                        related_data
                    )
                else:
                    # Es un objeto único
                    result[json_field_name] = JSONBuilderEnvioMAG._build_object_field(
                        data_row,
                        json_field_name,
                        referenced_mapping,
                        related_data
                    )
            else:
                # Es un campo simple
                db_column = field_mapping.source
                value = data_row.get(db_column)
                result[json_field_name] = JSONBuilderEnvioMAG.convert_value(
                    value,
                    field_mapping.type,
                    field_mapping.default
                )
        
        return result
    
    @staticmethod
    def _build_array_field(
        parent_row: Dict[str, Any],
        field_name: str,
        referenced_mapping: EntityMappingEnvioMAG,
        related_data: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Construye un campo de tipo array
        
        Args:
            parent_row: Registro padre
            field_name: Nombre del campo en el JSON
            referenced_mapping: Mapeo de la entidad referenciada
            related_data: Datos relacionados
        
        Returns:
            Lista de objetos JSON
        """
        if not related_data or field_name not in related_data:
            return []
        
        # Obtener los registros relacionados con este padre
        parent_id = parent_row.get('id')  # Asumimos que el padre tiene un campo 'id'
        related_rows = related_data.get(field_name, [])
        
        # Filtrar los que pertenecen a este padre
        # Buscar la FK apropiada (puede ser boleta_id, terreno_id, etc.)
        fk_column = None
        for col in related_rows[0].keys() if related_rows else []:
            if col.endswith('_id') and col != 'id':
                # Podría ser la FK, verificar si coincide con el ID del padre
                # Por ahora, asumimos que es boleta_id para el primer nivel
                # y terreno_id, etc., para niveles anidados
                fk_column = col
                break
        
        if not fk_column:
            fk_column = 'boleta_id'  # Default
        
        filtered_rows = [row for row in related_rows if row.get(fk_column) == parent_id]
        
        # Construir cada objeto del array
        array_result = []
        for row in filtered_rows:
            obj = JSONBuilderEnvioMAG.build_object_from_mapping(
                row,
                referenced_mapping,
                related_data
            )
            array_result.append(obj)
        
        return array_result
    
    @staticmethod
    def _build_object_field(
        parent_row: Dict[str, Any],
        field_name: str,
        referenced_mapping: EntityMappingEnvioMAG,
        related_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Construye un campo de tipo objeto
        
        Args:
            parent_row: Registro padre
            field_name: Nombre del campo en el JSON
            referenced_mapping: Mapeo de la entidad referenciada
            related_data: Datos relacionados
        
        Returns:
            Objeto JSON
        """
        # Para objetos únicos (no arrays), los datos pueden estar en la misma fila
        # o en una tabla relacionada con relación 1:1
        
        # Primero intentar construir desde la misma fila (campos embebidos)
        obj = JSONBuilderEnvioMAG.build_object_from_mapping(
            parent_row,
            referenced_mapping,
            related_data
        )
        
        return obj
    
    @staticmethod
    def build_json_for_boleta(
        boleta_row: Dict[str, Any],
        main_mapping: EntityMappingEnvioMAG,
        all_related_data: Dict[str, Dict[int, List[Dict[str, Any]]]]
    ) -> Dict[str, Any]:
        """
        Construye el JSON completo para una boleta
        
        Args:
            boleta_row: Registro de la boleta
            main_mapping: Mapeo principal (main.yml)
            all_related_data: Todos los datos relacionados agrupados
                {field_name: {boleta_id: [registros]}}
        
        Returns:
            JSON completo de la boleta
        """
        boleta_id = boleta_row.get('id')
        
        # Preparar related_data para esta boleta específica
        related_data_for_boleta = {}
        for field_name, grouped_data in all_related_data.items():
            related_data_for_boleta[field_name] = grouped_data.get(boleta_id, [])
        
        # Construir el JSON principal
        json_result = JSONBuilderEnvioMAG.build_object_from_mapping(
            boleta_row,
            main_mapping,
            related_data_for_boleta
        )
        
        return json_result
    
    @staticmethod
    def build_nested_structure(
        parent_row: Dict[str, Any],
        entity_mapping: EntityMappingEnvioMAG,
        all_fetched_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Construye una estructura anidada recursivamente usando database_id y parent_id de los mapeos
        
        Args:
            parent_row: Registro padre
            entity_mapping: Mapeo de la entidad
            all_fetched_data: Todos los datos fetched de BD {table_name: [rows]}
        
        Returns:
            Estructura JSON completa con todos los niveles anidados
        """
        result = {}
        
        # Obtener el ID del padre usando database_id del mapping
        parent_id_field = entity_mapping.database_id or 'id'
        parent_id = parent_row.get(parent_id_field)
        
        for json_field_name, field_mapping in entity_mapping.fields.items():
            if field_mapping.reference:
                # Cargar mapeo referenciado
                referenced_mapping = mapping_loader_envio_mag.load_yaml_file(field_mapping.reference)
                table_name = referenced_mapping.table
                
                # Obtener datos de esta tabla
                table_data = all_fetched_data.get(table_name, [])
                
                if field_mapping.type == 'array':
                    # Es un array de objetos - filtrar por parent_id del mapeo referenciado
                    fk_column = referenced_mapping.parent_id
                    
                    if not fk_column:
                        if config.DEBUG_CLI:
                            etl_logger.warning(
                                f"[JSONBuilderEnvioMAG] Tabla {table_name} no tiene parent_id definido"
                            )
                        result[json_field_name] = field_mapping.default if field_mapping.default is not None else []
                        continue
                    
                    # DEBUG: Log para diagnóstico de arrays vacíos
                    if config.DEBUG_CLI:
                        etl_logger.debug(
                            f"[JSONBuilderEnvioMAG] Procesando array '{json_field_name}' de tabla '{table_name}': "
                            f"parent_id_field='{parent_id_field}', parent_id={parent_id} (type={type(parent_id).__name__}), "
                            f"fk_column='{fk_column}', table_data_count={len(table_data)}"
                        )
                        if len(table_data) > 0 and len(table_data) <= 3:
                            # Mostrar todos los rows si son pocos
                            for idx, row in enumerate(table_data):
                                fk_value = row.get(fk_column)
                                etl_logger.debug(
                                    f"[JSONBuilderEnvioMAG]   Row {idx}: {fk_column}={fk_value} (type={type(fk_value).__name__}), match={fk_value == parent_id}"
                                )
                        elif len(table_data) > 0:
                            # Mostrar solo el primer row si hay muchos
                            sample_row = table_data[0]
                            sample_fk = sample_row.get(fk_column)
                            etl_logger.debug(
                                f"[JSONBuilderEnvioMAG]   Sample row: {fk_column}={sample_fk} (type={type(sample_fk).__name__})"
                            )
                    
                    # Filtrar registros que pertenecen a este padre
                    filtered_rows = []
                    for row in table_data:
                        if row.get(fk_column) == parent_id:
                            filtered_rows.append(row)
                    
                    # DEBUG: Log resultado del filtrado
                    if config.DEBUG_CLI and len(filtered_rows) == 0 and len(table_data) > 0:
                        etl_logger.warning(
                            f"[JSONBuilderEnvioMAG] ⚠️  Array '{json_field_name}' vacío: "
                            f"No se encontró {fk_column}=={parent_id} en {len(table_data)} registros de '{table_name}'"
                        )
                    
                    # Construir cada elemento del array recursivamente
                    array_result = []
                    for row in filtered_rows:
                        nested_obj = JSONBuilderEnvioMAG.build_nested_structure(
                            row,
                            referenced_mapping,
                            all_fetched_data
                        )
                        array_result.append(nested_obj)
                    
                    result[json_field_name] = array_result
                    
                else:
                    # Es un objeto único (no array)
                    # Verificar si tiene 'source' definido
                    if field_mapping.source:
                        # Caso: Relación por FK en parent_row
                        # Ejemplo: boletas.per_id → personas.per_id (database_id)
                        # source = per_id (columna en tabla actual)
                        # database_id de referenced_mapping = per_id (PK en tabla referenciada)
                        
                        fk_value = parent_row.get(field_mapping.source)
                        
                        if not fk_value:
                            # No hay FK, usar default
                            result[json_field_name] = field_mapping.default if field_mapping.default is not None else {}
                            continue
                        
                        # Buscar registro en tabla referenciada por database_id
                        db_id_column = referenced_mapping.database_id
                        
                        if not db_id_column:
                            if config.DEBUG_CLI:
                                etl_logger.warning(
                                    f"[JSONBuilderEnvioMAG] Tabla {table_name} no tiene database_id definido"
                                )
                            result[json_field_name] = field_mapping.default if field_mapping.default is not None else {}
                            continue
                        
                        # Buscar el registro donde database_id == fk_value
                        related_row = None
                        for row in table_data:
                            if row.get(db_id_column) == fk_value:
                                related_row = row
                                break
                        
                        if related_row:
                            nested_obj = JSONBuilderEnvioMAG.build_nested_structure(
                                related_row,
                                referenced_mapping,
                                all_fetched_data
                            )
                        else:
                            # No hay registro relacionado, usar default
                            nested_obj = field_mapping.default if field_mapping.default is not None else {}
                    
                    elif table_name != entity_mapping.table:
                        # Caso: Sin source, tabla diferente, usar parent_id
                        # Es una tabla diferente, buscar el registro relacionado por parent_id
                        fk_column = referenced_mapping.parent_id
                        
                        if not fk_column:
                            if config.DEBUG_CLI:
                                etl_logger.warning(
                                    f"[JSONBuilderEnvioMAG] Objeto {table_name} no tiene parent_id definido ni source"
                                )
                            result[json_field_name] = field_mapping.default if field_mapping.default is not None else {}
                            continue
                        
                        # Buscar el registro relacionado
                        related_row = None
                        for row in table_data:
                            if row.get(fk_column) == parent_id:
                                related_row = row
                                break
                        
                        if related_row:
                            nested_obj = JSONBuilderEnvioMAG.build_nested_structure(
                                related_row,
                                referenced_mapping,
                                all_fetched_data
                            )
                        else:
                            # No hay registro relacionado, usar default
                            nested_obj = field_mapping.default if field_mapping.default is not None else {}
                    else:
                        # Es la misma tabla (campos embebidos), construir desde parent_row
                        nested_obj = JSONBuilderEnvioMAG.build_nested_structure(
                            parent_row,
                            referenced_mapping,
                            all_fetched_data
                        )
                    
                    result[json_field_name] = nested_obj
            else:
                # Campo simple
                db_column = field_mapping.source
                value = parent_row.get(db_column)
                result[json_field_name] = JSONBuilderEnvioMAG.convert_value(
                    value,
                    field_mapping
                )
        
        return result
