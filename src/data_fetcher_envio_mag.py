"""
Extractor de datos de la base de datos para envío a MAG
Consulta las tablas de la BD y combina los resultados en memoria
"""
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import config
from .logger import etl_logger
from .database import db
from .mapping_loader_envio_mag import EntityMappingEnvioMAG


class DataFetcherEnvioMAG:
    """Extractor de datos de BD para envío a MAG"""
    
    def __init__(self, session: Session):
        self.session = session
        self.schema = config.DB_SCHEMA
    
    def fetch_table_data(self, table_name: str, boleta_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Obtiene datos de una tabla para un conjunto de boleta_ids
        
        Args:
            table_name: Nombre de la tabla a consultar
            boleta_ids: Lista de IDs de boletas a consultar
        
        Returns:
            Lista de registros como diccionarios
        """
        if not boleta_ids:
            return []
        
        # Construir query SQL
        placeholders = ','.join([f':id{i}' for i in range(len(boleta_ids))])
        query = f"""
            SELECT * FROM "{self.schema}".{table_name}
            WHERE boleta_id IN ({placeholders})
        """
        
        # Crear parámetros
        params = {f'id{i}': boleta_id for i, boleta_id in enumerate(boleta_ids)}
        
        if config.DEBUG:
            etl_logger.debug(f"[DataFetcherEnvioMAG] Query: {table_name} - IDs: {len(boleta_ids)}")
        
        # Ejecutar query
        result = self.session.execute(text(query), params)
        
        # Convertir resultados a diccionarios
        rows = []
        for row in result:
            rows.append(dict(row._mapping))
        
        if config.DEBUG_CLI:
            etl_logger.debug(f"[DataFetcherEnvioMAG] Obtenidos {len(rows)} registros de {table_name}")
        
        return rows
    
    def fetch_related_data(
        self,
        table_name: str,
        parent_ids: List[int],
        parent_fk_column: str = 'boleta_id'
    ) -> List[Dict[str, Any]]:
        """
        Obtiene datos de una tabla relacionada usando una FK
        
        Args:
            table_name: Nombre de la tabla a consultar
            parent_ids: Lista de IDs del padre
            parent_fk_column: Nombre de la columna FK en la tabla hija
        
        Returns:
            Lista de registros como diccionarios
        """
        if not parent_ids:
            return []
        
        # Construir query SQL
        placeholders = ','.join([f':id{i}' for i in range(len(parent_ids))])
        query = f"""
            SELECT * FROM "{self.schema}".{table_name}
            WHERE {parent_fk_column} IN ({placeholders})
        """
        
        # Crear parámetros
        params = {f'id{i}': parent_id for i, parent_id in enumerate(parent_ids)}
        
        if config.DEBUG:
            etl_logger.debug(f"[DataFetcherEnvioMAG] Related query: {table_name} - FK: {parent_fk_column}")
        
        # Ejecutar query
        result = self.session.execute(text(query), params)
        
        # Convertir resultados a diccionarios
        rows = []
        for row in result:
            rows.append(dict(row._mapping))
        
        if config.DEBUG_CLI:
            etl_logger.debug(f"[DataFetcherEnvioMAG] Obtenidos {len(rows)} registros de {table_name}")
        
        return rows
    
    def fetch_boletas_data(self, boleta_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Obtiene los datos principales de las boletas
        
        Args:
            boleta_ids: Lista de IDs de boletas
        
        Returns:
            Lista de registros de boletas
        """
        return self.fetch_table_data('boletas', boleta_ids)
    
    def group_by_parent_id(
        self,
        data: List[Dict[str, Any]],
        parent_fk: str = 'boleta_id'
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Agrupa registros por su ID padre
        
        Args:
            data: Lista de registros
            parent_fk: Nombre de la columna FK del padre
        
        Returns:
            Diccionario {parent_id: [registros]}
        """
        grouped = {}
        for record in data:
            parent_id = record.get(parent_fk)
            if parent_id:
                if parent_id not in grouped:
                    grouped[parent_id] = []
                grouped[parent_id].append(record)
        return grouped
    
    def fetch_all_related_tables(
        self,
        all_mappings: Dict[str, Any],
        boleta_ids: List[int]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Obtiene todos los datos de todas las tablas definidas en los mapeos
        
        Args:
            all_mappings: Todos los mapeos cargados {yaml_file: EntityMappingEnvioMAG}
            boleta_ids: Lista de IDs de boletas
        
        Returns:
            Diccionario {table_name: [registros]}
        """
        all_data = {}
        
        # Obtener tablas únicas de todos los mapeos
        tables_info = {}
        for yaml_file, entity_mapping in all_mappings.items():
            if entity_mapping.table and entity_mapping.table not in ('boletas',):
                tables_info[entity_mapping.table] = {
                    'yaml_file': yaml_file,
                    'entity': entity_mapping.entity
                }
        
        if config.DEBUG_CLI:
            etl_logger.debug(
                f"[DataFetcherEnvioMAG] Tablas a consultar: {list(tables_info.keys())}"
            )
        
        # Consultar cada tabla
        for table_name, info in tables_info.items():
            try:
                data = self.fetch_related_data(table_name, boleta_ids, 'boleta_id')
                all_data[table_name] = data
                
                if config.DEBUG:
                    etl_logger.debug(
                        f"[DataFetcherEnvioMAG] Tabla {table_name}: {len(data)} registros"
                    )
            except Exception as e:
                etl_logger.warning(
                    f"[DataFetcherEnvioMAG] Error consultando tabla {table_name}: {e}"
                )
                all_data[table_name] = []
        
        # Ahora consultar tablas de segundo nivel (ej: cultivos bajo terrenos)
        # Necesitamos IDs de las tablas padres (ej: terreno_ids)
        for table_name, info in tables_info.items():
            # Obtener el mapeo de esta tabla
            mapping = all_mappings.get(info['yaml_file'])
            if not mapping:
                continue
            
            # Ver si tiene referencias (tablas hijas)
            for field_name, field_mapping in mapping.fields.items():
                if field_mapping.reference and field_mapping.type == 'array':
                    from .mapping_loader_envio_mag import mapping_loader_envio_mag
                    
                    child_mapping = mapping_loader_envio_mag.load_yaml_file(field_mapping.reference)
                    child_table = child_mapping.table
                    
                    if child_table and child_table not in all_data:
                        # Obtener IDs de los padres de esta tabla
                        parent_data = all_data.get(table_name, [])
                        if parent_data:
                            parent_ids = [row['id'] for row in parent_data if 'id' in row]
                            
                            # Determinar FK column
                            fk_column = f"{table_name.rstrip('s')}_id"
                            
                            try:
                                child_data = self.fetch_related_data(
                                    child_table,
                                    parent_ids,
                                    fk_column
                                )
                                all_data[child_table] = child_data
                                
                                if config.DEBUG:
                                    etl_logger.debug(
                                        f"[DataFetcherEnvioMAG] Tabla hija {child_table}: {len(child_data)} registros"
                                    )
                            except Exception as e:
                                etl_logger.warning(
                                    f"[DataFetcherEnvioMAG] Error consultando tabla hija {child_table}: {e}"
                                )
                                all_data[child_table] = []
        
        return all_data
