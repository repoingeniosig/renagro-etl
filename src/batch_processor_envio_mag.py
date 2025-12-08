"""
Procesador de lotes para envío de datos a MAG
Consulta registros pendientes, construye JSON y prepara para envío
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from sqlalchemy import text

from .config import config
from .logger import envio_mag_logger
from .database import db
from .mapping_loader_envio_mag import mapping_loader_envio_mag
from .data_fetcher_envio_mag import DataFetcherEnvioMAG
from .json_builder_envio_mag import JSONBuilderEnvioMAG
from .structure_loader import structure_loader


class BatchProcessorEnvioMAG:
    """Procesador de lotes para envío a MAG"""
    
    def __init__(self):
        self.batch_size = config.BATCH_SIZE_SEND_MAG
        self.debug_json_output = config.DEBUG_JSON_OUTPUT
        self.temp_output_dir = config.BASE_DIR / 'temp_json_output'
        
        # Cargar configuración desde structure.yaml
        self.target_config = structure_loader.get_target_data_to_send()
        
        # Crear directorio temporal si DEBUG_JSON_OUTPUT está activo
        if self.debug_json_output:
            self.temp_output_dir.mkdir(exist_ok=True, parents=True)
            if config.DEBUG_CLI:
                envio_mag_logger.debug(f"[BatchProcessorEnvioMAG] Directorio debug creado: {self.temp_output_dir}")
    
    def get_pending_boletas_ids(self) -> List[int]:
        """
        Obtiene los IDs pendientes desde la tabla de control configurada en structure.yaml
        
        Returns:
            Lista de IDs (según id_column) pendientes
        """
        # Construir condiciones WHERE dinámicamente
        where_conditions = []
        params = {'batch_size': self.batch_size}
        
        for filter_obj in self.target_config.control_table_filters:
            where_conditions.append(f"{filter_obj.column} = :{filter_obj.column}")
            params[filter_obj.column] = filter_obj.value
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = f"""
            SELECT {self.target_config.control_table_id}
            FROM "{config.DB_SCHEMA}".{self.target_config.control_table}
            WHERE {where_clause}
            ORDER BY {self.target_config.control_table_id} ASC
            LIMIT :batch_size
        """
        
        if config.DEBUG_CLI:
            envio_mag_logger.debug(
                f"[BatchProcessorEnvioMAG] Query control: "
                f"SELECT {self.target_config.control_table_id} FROM {self.target_config.control_table} "
                f"WHERE {where_clause} LIMIT {self.batch_size}"
            )
        
        with db.get_session() as session:
            result = session.execute(text(query), params)
            ids = [row[0] for row in result]
        
        if config.DEBUG_CLI:
            envio_mag_logger.debug(f"[BatchProcessorEnvioMAG] Encontrados {len(ids)} registros pendientes")
        
        return ids
    
    def fetch_all_data_for_batch(
        self,
        control_ids: List[int]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
        """
        Obtiene todos los datos necesarios para un lote
        
        Flujo:
        1. Extraer IDs desde control_table usando id_column (ej: _id de control_envios_boletas)
        2. Usar esos IDs para consultar la tabla principal del main.yml
        3. La consulta se hace por database_id del main.yml (ej: bol_id de boletas)
        4. Los valores de id_column deben coincidir con database_id (ej: _id == bol_id)
        
        Args:
            control_ids: Lista de IDs extraídos de control_table.id_column
                        Estos valores coinciden con main_table.database_id
                        Ejemplo: [237, 238, 240] de control_envios_boletas._id
                                == boletas.bol_id
        
        Returns:
            Tupla (main_table_data, all_related_data)
            - main_table_data: Lista de registros de la tabla principal (ej: boletas)
            - all_related_data: Dict {table_name: [registros]}
        """
        with db.get_session() as session:
            fetcher = DataFetcherEnvioMAG(session)
            
            # Cargar mapeo principal para obtener tabla
            main_mapping = mapping_loader_envio_mag.load_main_mapping()
            main_table = main_mapping.table
            
            # Usar source_reference_field de structure.yaml en lugar de database_id
            # Esto permite hacer match entre control_table_id y el campo correcto en la tabla principal
            # Ejemplo: control_envios_boletas.uuid_boleta -> boletas.bol_id_levanta
            reference_field = self.target_config.source_reference_field
            
            if config.DEBUG_CLI:
                envio_mag_logger.debug(
                    f"[BatchProcessorEnvioMAG] Usando IDs de {self.target_config.control_table}.{self.target_config.control_table_id} "
                    f"para consultar {main_table}.{reference_field}"
                )
            
            # Consultar tabla principal usando source_reference_field
            # Los control_ids (de control_table.control_table_id) deben coincidir con
            # los valores en main_table.source_reference_field
            # Ejemplo: control_envios_boletas.uuid_boleta == boletas.bol_id_levanta
            main_table_data = fetcher.fetch_table_data(
                main_table,
                control_ids,
                reference_field,  # Usar source_reference_field en lugar de database_id
                use_cache=True
            )
            
            if config.DEBUG_CLI:
                envio_mag_logger.debug(
                    f"[BatchProcessorEnvioMAG] Obtenidos {len(main_table_data)} registros de {main_table}"
                )
            
            # Cargar mapeos recursivamente
            all_mappings = mapping_loader_envio_mag.load_all_mappings_recursive('main.yml')
            
            # Obtener todos los datos de tablas relacionadas
            # Pasar main_table_data para que pueda extraer FKs de campos con 'source'
            # Pasar source_reference_field para que las tablas relacionadas usen el mismo FK
            all_related_data = fetcher.fetch_all_related_tables(
                all_mappings,
                control_ids,  # Usar los mismos IDs para consultar tablas relacionadas
                main_mapping,
                root_data=main_table_data,  # Pasar datos de tabla principal
                source_reference_field=reference_field  # ← NUEVO: Usar bol_id_levanta en lugar de bol_id
            )
        
        return main_table_data, all_related_data
    
    def build_json_for_record(
        self,
        main_row: Dict[str, Any],
        all_related_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Construye el JSON completo para un registro
        
        Args:
            main_row: Registro de la tabla principal (ej: boleta de BD)
            all_related_data: Todos los datos relacionados {table_name: [registros]}
        
        Returns:
            JSON construido según main.yml
        """
        # Cargar mapeo principal
        main_mapping = mapping_loader_envio_mag.load_main_mapping()
        
        # Construir JSON usando el builder (ahora sin parámetros hardcodeados)
        json_result = JSONBuilderEnvioMAG.build_nested_structure(
            main_row,
            main_mapping,
            all_related_data
        )
        
        return json_result
    
    def save_debug_json(self, record_id: int, json_data: Dict[str, Any]):
        """
        Guarda el JSON en archivo para debugging
        
        Args:
            record_id: ID del registro (ej: boleta_id, solicitud_id, etc.)
            json_data: JSON construido
        """
        if not self.debug_json_output:
            return
        
        # Usar nombre genérico basado en la tabla principal
        main_mapping = mapping_loader_envio_mag.load_main_mapping()
        entity_name = main_mapping.entity.replace('Dto', '').replace('Create', '').lower()
        
        output_file = self.temp_output_dir / f"{entity_name}_{record_id}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            if config.DEBUG_CLI:
                envio_mag_logger.debug(f"[BatchProcessorEnvioMAG] JSON guardado: {output_file}")
        except Exception as e:
            envio_mag_logger.error(f"[BatchProcessorEnvioMAG] Error guardando JSON debug: {e}")
    
    def process_batch(self) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Procesa un lote de registros pendientes
        
        Returns:
            Tupla (total_procesados, json_list)
            - total_procesados: Cantidad de JSONs construidos exitosamente
            - json_list: Lista de JSONs construidos con sus IDs
        """
        envio_mag_logger.info("[BatchProcessorEnvioMAG] Iniciando procesamiento de lote")
        
        # Obtener IDs pendientes desde tabla de control
        control_ids = self.get_pending_boletas_ids()
        
        if not control_ids:
            envio_mag_logger.info("[BatchProcessorEnvioMAG] No hay registros pendientes")
            return 0, []
        
        envio_mag_logger.info(
            f"[BatchProcessorEnvioMAG] Procesando {len(control_ids)} registros "
            f"desde {self.target_config.control_table}"
        )
        
        try:
            # Cargar mapeo principal para obtener database_id
            main_mapping = mapping_loader_envio_mag.load_main_mapping()
            db_id_field = main_mapping.database_id
            
            if not db_id_field:
                raise ValueError("El archivo main.yml no tiene database_id definido")
            
            # Obtener todos los datos necesarios
            main_table_data, all_related_data = self.fetch_all_data_for_batch(control_ids)
            
            # Construir JSONs para cada registro
            json_list = []
            successful_count = 0
            
            for main_row in main_table_data:
                try:
                    # Usar database_id del mapping en lugar de 'id' hardcodeado
                    record_id = main_row.get(db_id_field)
                    
                    # Construir JSON
                    json_data = self.build_json_for_record(main_row, all_related_data)
                    
                    # Guardar para debug si está habilitado
                    self.save_debug_json(record_id, json_data)
                    
                    # Agregar a la lista con metadata
                    json_list.append({
                        'control_id': record_id,  # ID de la tabla de control
                        'record_id': record_id,  # ID del registro en tabla principal
                        'json_data': json_data
                    })
                    
                    successful_count += 1
                    
                    if config.DEBUG_CLI:
                        envio_mag_logger.debug(
                            f"[BatchProcessorEnvioMAG] JSON construido para {db_id_field}={record_id}"
                        )
                
                except Exception as e:
                    record_id = main_row.get(db_id_field, 'unknown')
                    envio_mag_logger.error(
                        f"[BatchProcessorEnvioMAG] Error construyendo JSON para {db_id_field}={record_id}: {e}",
                        exc_info=True
                    )
                    # Continuar con el siguiente registro
                    continue
            
            envio_mag_logger.info(
                f"[BatchProcessorEnvioMAG] Lote procesado: {successful_count}/{len(control_ids)} exitosos"
            )
            
            return successful_count, json_list
        
        except Exception as e:
            envio_mag_logger.error(
                f"[BatchProcessorEnvioMAG] Error procesando lote: {e}",
                exc_info=True
            )
            return 0, []
    
    def process_all_pending(self) -> int:
        """
        Procesa todos los registros pendientes en lotes
        
        Returns:
            Total de registros procesados exitosamente
        """
        envio_mag_logger.info("[BatchProcessorEnvioMAG] Iniciando procesamiento de todos los pendientes")
        
        total_processed = 0
        batch_number = 1
        
        while True:
            envio_mag_logger.info(f"[BatchProcessorEnvioMAG] Procesando lote #{batch_number}")
            
            # Procesar un lote
            count, json_list = self.process_batch()
            
            if count == 0:
                # No hay más registros pendientes
                break
            
            total_processed += count
            batch_number += 1
            
            envio_mag_logger.info(
                f"[BatchProcessorEnvioMAG] Lote #{batch_number - 1} completado. "
                f"Total acumulado: {total_processed}"
            )
        
        envio_mag_logger.info(
            f"[BatchProcessorEnvioMAG] Procesamiento completo. Total procesado: {total_processed}"
        )
        
        return total_processed


# Instancia global
batch_processor_envio_mag = BatchProcessorEnvioMAG()
