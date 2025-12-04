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


class BatchProcessorEnvioMAG:
    """Procesador de lotes para envío a MAG"""
    
    def __init__(self):
        self.batch_size = config.BATCH_SIZE_SEND_MAG
        self.debug_json_output = config.DEBUG_JSON_OUTPUT
        self.temp_output_dir = config.BASE_DIR / 'temp_json_output'
        
        # Crear directorio temporal si DEBUG_JSON_OUTPUT está activo
        if self.debug_json_output:
            self.temp_output_dir.mkdir(exist_ok=True, parents=True)
            if config.DEBUG_CLI:
                envio_mag_logger.debug(f"[BatchProcessorEnvioMAG] Directorio debug creado: {self.temp_output_dir}")
    
    def get_pending_boletas_ids(self) -> List[int]:
        """
        Obtiene los IDs de boletas pendientes de enviar a MAG
        
        Returns:
            Lista de IDs (_id de control_envios_boletas) pendientes
        """
        query = f"""
            SELECT _id
            FROM "{config.DB_SCHEMA}".control_envios_boletas
            WHERE estado_etl = 'PROCESADO'
              AND envio_datos_procesados = 'PENDIENTE'
            ORDER BY _id ASC
            LIMIT :batch_size
        """
        
        with db.get_session() as session:
            result = session.execute(text(query), {'batch_size': self.batch_size})
            ids = [row[0] for row in result]
        
        if config.DEBUG_CLI:
            envio_mag_logger.debug(f"[BatchProcessorEnvioMAG] Encontrados {len(ids)} registros pendientes")
        
        return ids
    
    def fetch_all_data_for_batch(
        self,
        boleta_ids: List[int]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
        """
        Obtiene todos los datos necesarios para un lote de boletas
        
        Args:
            boleta_ids: Lista de IDs de boletas
        
        Returns:
            Tupla (boletas_data, all_related_data)
            - boletas_data: Lista de registros de boletas
            - all_related_data: Dict {table_name: [registros]}
        """
        with db.get_session() as session:
            fetcher = DataFetcherEnvioMAG(session)
            
            # Obtener datos principales de boletas
            boletas_data = fetcher.fetch_boletas_data(boleta_ids)
            
            if config.DEBUG_CLI:
                envio_mag_logger.debug(f"[BatchProcessorEnvioMAG] Obtenidas {len(boletas_data)} boletas")
            
            # Cargar mapeos recursivamente
            all_mappings = mapping_loader_envio_mag.load_all_mappings_recursive('main.yml')
            
            # Obtener todos los datos de tablas relacionadas
            all_related_data = fetcher.fetch_all_related_tables(all_mappings, boleta_ids)
        
        return boletas_data, all_related_data
    
    def build_json_for_boleta(
        self,
        boleta_row: Dict[str, Any],
        all_related_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Construye el JSON completo para una boleta
        
        Args:
            boleta_row: Registro de boleta de BD
            all_related_data: Todos los datos relacionados {table_name: [registros]}
        
        Returns:
            JSON construido según main.yml
        """
        # Cargar mapeo principal
        main_mapping = mapping_loader_envio_mag.load_main_mapping()
        
        # Construir JSON usando el builder
        json_result = JSONBuilderEnvioMAG.build_nested_structure(
            boleta_row,
            main_mapping,
            all_related_data,
            'id',
            'boletas'
        )
        
        return json_result
    
    def save_debug_json(self, boleta_id: int, json_data: Dict[str, Any]):
        """
        Guarda el JSON en archivo para debugging
        
        Args:
            boleta_id: ID de la boleta
            json_data: JSON construido
        """
        if not self.debug_json_output:
            return
        
        output_file = self.temp_output_dir / f"boleta_{boleta_id}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            if config.DEBUG_CLI:
                envio_mag_logger.debug(f"[BatchProcessorEnvioMAG] JSON guardado: {output_file}")
        except Exception as e:
            envio_mag_logger.error(f"[BatchProcessorEnvioMAG] Error guardando JSON debug: {e}")
    
    def process_batch(self) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Procesa un lote de boletas pendientes
        
        Returns:
            Tupla (total_procesados, json_list)
            - total_procesados: Cantidad de JSONs construidos exitosamente
            - json_list: Lista de JSONs construidos con sus IDs
        """
        envio_mag_logger.info("[BatchProcessorEnvioMAG] Iniciando procesamiento de lote")
        
        # Obtener IDs pendientes
        boleta_ids = self.get_pending_boletas_ids()
        
        if not boleta_ids:
            envio_mag_logger.info("[BatchProcessorEnvioMAG] No hay registros pendientes")
            return 0, []
        
        envio_mag_logger.info(f"[BatchProcessorEnvioMAG] Procesando {len(boleta_ids)} boletas")
        
        try:
            # Obtener todos los datos necesarios
            boletas_data, all_related_data = self.fetch_all_data_for_batch(boleta_ids)
            
            # Construir JSONs para cada boleta
            json_list = []
            successful_count = 0
            
            for boleta_row in boletas_data:
                try:
                    boleta_id = boleta_row.get('id')
                    
                    # Construir JSON
                    json_data = self.build_json_for_boleta(boleta_row, all_related_data)
                    
                    # Guardar para debug si está habilitado
                    self.save_debug_json(boleta_id, json_data)
                    
                    # Agregar a la lista con metadata
                    json_list.append({
                        '_id': boleta_row.get('id'),  # ID de control_envios_boletas
                        'boleta_id': boleta_id,  # ID de la boleta en tabla boletas
                        'json_data': json_data
                    })
                    
                    successful_count += 1
                    
                    if config.DEBUG_CLI:
                        envio_mag_logger.debug(
                            f"[BatchProcessorEnvioMAG] JSON construido para boleta_id={boleta_id}"
                        )
                
                except Exception as e:
                    boleta_id = boleta_row.get('id', 'unknown')
                    envio_mag_logger.error(
                        f"[BatchProcessorEnvioMAG] Error construyendo JSON para boleta_id={boleta_id}: {e}",
                        exc_info=True
                    )
                    # Continuar con la siguiente boleta
                    continue
            
            envio_mag_logger.info(
                f"[BatchProcessorEnvioMAG] Lote procesado: {successful_count}/{len(boleta_ids)} exitosos"
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
