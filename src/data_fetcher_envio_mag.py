"""
Extractor de datos de la base de datos para envío a MAG
Consulta las tablas de la BD y combina los resultados en memoria
"""
from typing import Dict, Any, List, Optional, Tuple
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
        # Cache SQL: {(table_name, parent_fk_column, tuple(sorted_ids)): [rows]}
        self.sql_cache: Dict[Tuple, List[Dict[str, Any]]] = {}
    
    def _make_cache_key(
        self,
        table_name: str,
        parent_fk_column: str,
        parent_ids: List[int]
    ) -> Tuple:
        """
        Genera una clave única para el cache SQL
        
        Args:
            table_name: Nombre de la tabla
            parent_fk_column: Nombre de la columna FK
            parent_ids: Lista de IDs
        
        Returns:
            Tupla que sirve como clave de cache
        """
        return (table_name, parent_fk_column, tuple(sorted(parent_ids)))
    
    def fetch_table_data(
        self,
        table_name: str,
        parent_ids: List[int],
        parent_fk_column: str,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Obtiene datos de una tabla usando un FK para filtrar (genérico)
        
        Args:
            table_name: Nombre de la tabla a consultar
            parent_ids: Lista de IDs para filtrar
            parent_fk_column: Nombre de la columna FK para filtrar
            use_cache: Si debe usar/guardar en cache SQL
        
        Returns:
            Lista de registros como diccionarios
        """
        if not parent_ids:
            return []
        
        # Verificar cache
        cache_key = self._make_cache_key(table_name, parent_fk_column, parent_ids)
        if use_cache and cache_key in self.sql_cache:
            if config.DEBUG_CLI:
                etl_logger.debug(
                    f"[DataFetcherEnvioMAG] Cache HIT: {table_name} - {parent_fk_column}"
                )
            return self.sql_cache[cache_key]
        
        # Construir query SQL
        placeholders = ','.join([f':id{i}' for i in range(len(parent_ids))])
        query = f"""
            SELECT * FROM "{self.schema}".{table_name}
            WHERE {parent_fk_column} IN ({placeholders})
        """
        
        # Crear parámetros
        params = {f'id{i}': parent_id for i, parent_id in enumerate(parent_ids)}
        
        if config.DEBUG_CLI:
            etl_logger.debug(
                f"[DataFetcherEnvioMAG] Query: {table_name} - FK: {parent_fk_column} - IDs: {len(parent_ids)}"
            )
        
        # Ejecutar query
        result = self.session.execute(text(query), params)
        
        # Convertir resultados a diccionarios
        rows = []
        for row in result:
            rows.append(dict(row._mapping))
        
        if config.DEBUG_CLI:
            etl_logger.debug(f"[DataFetcherEnvioMAG] Obtenidos {len(rows)} registros de {table_name}")
        
        # Guardar en cache
        if use_cache:
            self.sql_cache[cache_key] = rows
        
        return rows
    
    def group_by_parent_id(
        self,
        data: List[Dict[str, Any]],
        parent_fk: str
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
        all_mappings: Dict[str, EntityMappingEnvioMAG],
        root_ids: List[int],
        root_mapping: EntityMappingEnvioMAG,
        root_data: List[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Obtiene todos los datos de todas las tablas definidas en los mapeos de forma recursiva
        
        Args:
            all_mappings: Todos los mapeos cargados {yaml_file: EntityMappingEnvioMAG}
            root_ids: Lista de IDs de la entidad raíz (ej: boleta_ids)
            root_mapping: Mapeo de la entidad raíz (ej: main.yml)
            root_data: Datos de la tabla raíz ya consultados (para extraer FKs de campos con source)
        
        Returns:
            Diccionario {table_name: [registros]}
        """
        all_data = {}
        
        # Analizar campos del root_mapping para detectar relaciones con 'source'
        # Ejemplo: personaProductora: {reference: persona.yaml, source: per_id, type: object}
        source_based_queries: Dict[str, Tuple[str, List[int]]] = {}  # {table_name: (fk_column, [ids])}
        
        if root_data:
            for field_name, field_mapping in root_mapping.fields.items():
                if field_mapping.reference and field_mapping.source and field_mapping.type == 'object':
                    # Cargar mapeo referenciado para obtener tabla y database_id
                    from .mapping_loader_envio_mag import mapping_loader_envio_mag
                    referenced_mapping = mapping_loader_envio_mag.load_yaml_file(field_mapping.reference)
                    
                    if referenced_mapping.table and referenced_mapping.database_id:
                        # Extraer valores únicos de la columna 'source' de root_data
                        source_values = set()
                        for row in root_data:
                            value = row.get(field_mapping.source)
                            if value is not None:
                                source_values.add(value)
                        
                        if source_values:
                            source_based_queries[referenced_mapping.table] = (
                                referenced_mapping.database_id,
                                list(source_values)
                            )
                            
                            if config.DEBUG_CLI:
                                etl_logger.debug(
                                    f"[DataFetcherEnvioMAG] Detectada relación con source: "
                                    f"{field_name} → {referenced_mapping.table}.{referenced_mapping.database_id} "
                                    f"({len(source_values)} valores únicos)"
                                )
        
        # Obtener tablas únicas de todos los mapeos (excepto la raíz)
        # Agrupar por tabla para identificar duplicados
        table_to_mappings: Dict[str, List[Tuple[str, EntityMappingEnvioMAG]]] = {}
        
        for yaml_file, entity_mapping in all_mappings.items():
            if entity_mapping.table and entity_mapping.table != root_mapping.table:
                if entity_mapping.table not in table_to_mappings:
                    table_to_mappings[entity_mapping.table] = []
                table_to_mappings[entity_mapping.table].append((yaml_file, entity_mapping))
        
        if config.DEBUG_CLI:
            etl_logger.debug(
                f"[DataFetcherEnvioMAG] Tablas únicas a consultar: {list(table_to_mappings.keys())}"
            )
            for table_name, mappings in table_to_mappings.items():
                if len(mappings) > 1:
                    yaml_files = [m[0] for m in mappings]
                    etl_logger.debug(
                        f"[DataFetcherEnvioMAG] ⚠️  Tabla '{table_name}' usada por múltiples YAMLs: {yaml_files}"
                    )
        
        # Nivel 1: Consultar tablas directamente relacionadas con la raíz
        for table_name, mappings_list in table_to_mappings.items():
            # Verificar si esta tabla tiene una consulta basada en 'source'
            if table_name in source_based_queries:
                fk_column, ids_to_query = source_based_queries[table_name]
                
                try:
                    data = self.fetch_table_data(
                        table_name,
                        ids_to_query,
                        fk_column,
                        use_cache=True
                    )
                    all_data[table_name] = data
                    
                    if config.DEBUG_CLI:
                        etl_logger.debug(
                            f"[DataFetcherEnvioMAG] Tabla {table_name}: {len(data)} registros (por source - FK: {fk_column})"
                        )
                except Exception as e:
                    etl_logger.warning(
                        f"[DataFetcherEnvioMAG] Error consultando tabla {table_name}: {e}"
                    )
                    all_data[table_name] = []
                
                continue  # Ya consultada, skip normal flow
            
            # Usar el primer mapping para obtener parent_id
            yaml_file, entity_mapping = mappings_list[0]
            
            # Si no tiene parent_id, asumir que usa el database_id de la raíz
            parent_fk_column = entity_mapping.parent_id or root_mapping.database_id
            
            if not parent_fk_column:
                etl_logger.warning(
                    f"[DataFetcherEnvioMAG] Tabla {table_name} no tiene parent_id definido"
                )
                continue
            
            try:
                # Intentar primero como hijo directo de la raíz
                data = self.fetch_table_data(
                    table_name,
                    root_ids,
                    parent_fk_column,
                    use_cache=True  # Usar cache para evitar duplicados
                )
                all_data[table_name] = data
                
                if config.DEBUG_CLI:
                    etl_logger.debug(
                        f"[DataFetcherEnvioMAG] Tabla {table_name}: {len(data)} registros (FK: {parent_fk_column})"
                    )
            except Exception as e:
                etl_logger.warning(
                    f"[DataFetcherEnvioMAG] Error consultando tabla {table_name}: {e}"
                )
                all_data[table_name] = []
        
        # Nivel 2+: Consultar tablas de niveles más profundos (ej: cultivos bajo terrenos)
        for yaml_file, entity_mapping in all_mappings.items():
            # Ver si tiene referencias (tablas hijas)
            for field_name, field_mapping in entity_mapping.fields.items():
                if field_mapping.reference and field_mapping.type == 'array':
                    from .mapping_loader_envio_mag import mapping_loader_envio_mag
                    
                    child_mapping = mapping_loader_envio_mag.load_yaml_file(field_mapping.reference)
                    child_table = child_mapping.table
                    
                    if not child_table or child_table in all_data:
                        # Ya consultada o no tiene tabla
                        continue
                    
                    # Obtener IDs de los padres de esta tabla
                    parent_table = entity_mapping.table
                    parent_data = all_data.get(parent_table, [])
                    
                    if not parent_data:
                        continue
                    
                    # Usar database_id del padre para extraer IDs
                    parent_db_id = entity_mapping.database_id
                    if not parent_db_id:
                        etl_logger.warning(
                            f"[DataFetcherEnvioMAG] Tabla padre {parent_table} no tiene database_id"
                        )
                        continue
                    
                    parent_ids = [row[parent_db_id] for row in parent_data if parent_db_id in row]
                    
                    if not parent_ids:
                        continue
                    
                    # Usar parent_id del hijo
                    child_fk_column = child_mapping.parent_id
                    if not child_fk_column:
                        etl_logger.warning(
                            f"[DataFetcherEnvioMAG] Tabla hija {child_table} no tiene parent_id"
                        )
                        continue
                    
                    try:
                        child_data = self.fetch_table_data(
                            child_table,
                            parent_ids,
                            child_fk_column,
                            use_cache=True
                        )
                        all_data[child_table] = child_data
                        
                        if config.DEBUG_CLI:
                            etl_logger.debug(
                                f"[DataFetcherEnvioMAG] Tabla hija {child_table}: {len(child_data)} registros (FK: {child_fk_column})"
                            )
                    except Exception as e:
                        etl_logger.warning(
                            f"[DataFetcherEnvioMAG] Error consultando tabla hija {child_table}: {e}"
                        )
                        all_data[child_table] = []
        
        return all_data
