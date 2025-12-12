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
from .rabbitmq_client import rabbitmq_client


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
    
    def get_pending_boletas_ids(self) -> List[Tuple[int, Any]]:
        """
        Obtiene los IDs pendientes desde la tabla de control configurada en structure.yaml
        
        Returns:
            Lista de tuplas (pk, reference_id) donde:
            - pk: Valor de control_table_primary_key (ej: _id) para UPDATEs
            - reference_id: Valor de control_table_id (ej: uuid_boleta) para SELECTs
        """
        # Construir condiciones WHERE dinámicamente
        where_conditions = []
        params = {'batch_size': self.batch_size}
        
        for filter_obj in self.target_config.control_table_filters:
            where_conditions.append(f"{filter_obj.column} = :{filter_obj.column}")
            params[filter_obj.column] = filter_obj.value
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = f"""
            SELECT {self.target_config.control_table_primary_key}, {self.target_config.control_table_id}
            FROM "{config.DB_SCHEMA}".{self.target_config.control_table}
            WHERE {where_clause}
            ORDER BY {self.target_config.control_table_primary_key} ASC
            LIMIT :batch_size
        """
        
        if config.DEBUG_CLI:
            envio_mag_logger.debug(
                f"[BatchProcessorEnvioMAG] Query control: "
                f"SELECT {self.target_config.control_table_primary_key}, {self.target_config.control_table_id} "
                f"FROM {self.target_config.control_table} WHERE {where_clause} LIMIT {self.batch_size}"
            )
        
        with db.get_session() as session:
            result = session.execute(text(query), params)
            # Retornar tuplas (pk, reference_id)
            ids = [(row[0], row[1]) for row in result]
        
        if config.DEBUG_CLI:
            envio_mag_logger.debug(f"[BatchProcessorEnvioMAG] Encontrados {len(ids)} registros pendientes")
        
        return ids
    
    def fetch_all_data_for_batch(
        self,
        reference_ids: List[Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
        """
        Obtiene todos los datos necesarios para un lote
        
        Flujo:
        1. Usar reference_ids (valores de control_table_id como uuid_boleta)
        2. Consultar tabla principal por source_reference_field (ej: bol_id_levanta)
        3. Extraer database_id (ej: bol_id) para consultar tablas relacionadas
        
        Args:
            reference_ids: Lista de valores de control_table_id para buscar datos
                          Ejemplo: ['uuid1', 'uuid2'] de control_envios_boletas.uuid_boleta
        
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
            # Los reference_ids (valores de control_table_id) deben coincidir con
            # los valores en main_table.source_reference_field
            # Ejemplo: control_envios_boletas.uuid_boleta == boletas.bol_id_levanta
            main_table_data = fetcher.fetch_table_data(
                main_table,
                reference_ids,
                reference_field,  # Usar source_reference_field en lugar de database_id
                use_cache=True
            )
            
            if config.DEBUG_CLI:
                envio_mag_logger.debug(
                    f"[BatchProcessorEnvioMAG] Obtenidos {len(main_table_data)} registros de {main_table}"
                )
            
            # Extraer bol_id (source_database_id) de los datos de boletas
            # Estos son los IDs que usan las tablas relacionadas como FK
            database_ids = [record.get(self.target_config.source_database_id) for record in main_table_data]
            database_ids = [db_id for db_id in database_ids if db_id is not None]
            
            envio_mag_logger.info(
                f"[BatchProcessorEnvioMAG] Extraídos {len(database_ids)} {self.target_config.source_database_id} "
                f"de {main_table}: {database_ids[:3]}..." if len(database_ids) > 3 else f": {database_ids}"
            )
            
            envio_mag_logger.info(
                f"[BatchProcessorEnvioMAG] Consultando tablas relacionadas con {self.target_config.source_database_id} IN ({database_ids[:3]}...)"
            )
            
            # Usar mappings precargados en lugar de cargarlos nuevamente
            # Los mappings ya fueron cargados en API startup y están en memoria
            all_mappings = mapping_loader_envio_mag.loaded_mappings
            
            if not all_mappings:
                # Fallback: cargar si no están precargados (no debería ocurrir)
                envio_mag_logger.warning("[BatchProcessorEnvioMAG] Mappings no precargados, cargando ahora...")
                all_mappings = mapping_loader_envio_mag.load_all_mappings_recursive('main.yml')
            
            # Obtener todos los datos de tablas relacionadas
            # Usar database_ids (bol_id) para consultar tablas relacionadas
            all_related_data = fetcher.fetch_all_related_tables(
                all_mappings,
                database_ids,  # ← CORRECCIÓN: Usar bol_id extraídos de boletas
                main_mapping,
                root_data=main_table_data,
                source_reference_field=None  # No usar, ya pasamos los bol_id correctos
            )
            
            envio_mag_logger.info(
                f"[BatchProcessorEnvioMAG] Tablas relacionadas obtenidas: "
                f"{', '.join([f'{k}({len(v)})' for k, v in all_related_data.items()])}"
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
    
    def _mark_as_processing(self, control_id: int):
        """
        Marca un registro como PROCESANDO para evitar duplicados en timer
        
        Args:
            control_id: ID del registro en control_table (valor de la PK)
        """
        try:
            with db.get_session() as session:
                update_query = f"""
                    UPDATE "{config.DB_SCHEMA}".{self.target_config.control_table}
                    SET envio_datos_procesados = 'PROCESANDO',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE {self.target_config.control_table_primary_key} = :control_id
                """
                
                session.execute(text(update_query), {"control_id": control_id})
                session.commit()
                
                if config.DEBUG_CLI:
                    envio_mag_logger.debug(
                        f"[BatchProcessorEnvioMAG] Marcado como PROCESANDO: {control_id}"
                    )
        
        except Exception as e:
            envio_mag_logger.error(
                f"[BatchProcessorEnvioMAG] Error marcando como PROCESANDO ({control_id}): {e}",
                exc_info=True
            )
            raise
    
    def _mark_as_error(self, control_id: int, error_message: str):
        """
        Marca un registro como ERROR (sin reencolar)
        Usado para errores de construcción de JSON (equivalente a 4xx)
        
        Args:
            control_id: ID del registro en control_table (valor de la PK)
            error_message: Descripción del error
        """
        try:
            with db.get_session() as session:
                # Truncar mensaje si es muy largo
                error_message_truncated = error_message[:500] if len(error_message) > 500 else error_message
                
                update_query = f"""
                    UPDATE "{config.DB_SCHEMA}".{self.target_config.control_table}
                    SET envio_datos_procesados = 'ERROR',
                        error_mensajes_envio = :error_message,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE {self.target_config.control_table_primary_key} = :control_id
                """
                
                session.execute(text(update_query), {
                    "control_id": control_id,
                    "error_message": error_message_truncated
                })
                session.commit()
                
                envio_mag_logger.error(
                    f"[BatchProcessorEnvioMAG] Marcado como ERROR ({control_id}): {error_message_truncated}"
                )
        
        except Exception as e:
            envio_mag_logger.error(
                f"[BatchProcessorEnvioMAG] Error marcando como ERROR ({control_id}): {e}",
                exc_info=True
            )
    
    def mark_batch_as_completed(self, control_ids: List[str]):
        """
        Marca los registros procesados como completados en control_table
        
        NOTA: Este método ya NO se usa después de procesar batch
        Los registros se marcan como ENVIADO solo después del envío exitoso HTTP
        Ver: EnvioMagSenderWorker.update_control_status()
        
        Args:
            control_ids: Lista de IDs (uuid_boleta) procesados exitosamente
        """
        if not control_ids:
            return
        
        try:
            # Construir UPDATE dinámico
            # UPDATE control_table SET envio_datos_procesados = 'COMPLETADO' WHERE uuid_boleta IN (...)
            placeholders = ', '.join([f":id_{i}" for i in range(len(control_ids))])
            params = {f"id_{i}": control_id for i, control_id in enumerate(control_ids)}
            
            update_query = f"""
                UPDATE "{config.DB_SCHEMA}".{self.target_config.control_table}
                SET envio_datos_procesados = 'ENVIADO'
                WHERE {self.target_config.control_table_id} IN ({placeholders})
            """
            
            with db.get_session() as session:
                session.execute(text(update_query), params)
                session.commit()
            
            envio_mag_logger.info(
                f"[BatchProcessorEnvioMAG] ✅ {len(control_ids)} registros marcados como ENVIADO"
            )
        
        except Exception as e:
            envio_mag_logger.error(
                f"[BatchProcessorEnvioMAG] Error marcando registros como completados: {e}",
                exc_info=True
            )
    
    def process_batch(self) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Procesa un lote de registros pendientes
        
        Returns:
            Tupla (total_procesados, json_list)
            - total_procesados: Cantidad de JSONs construidos exitosamente
            - json_list: Lista de JSONs construidos con sus IDs
        """
        envio_mag_logger.info("[BatchProcessorEnvioMAG] Iniciando procesamiento de lote")
        
        # Obtener IDs pendientes desde tabla de control (tuplas de pk, reference_id)
        control_records = self.get_pending_boletas_ids()
        
        if not control_records:
            envio_mag_logger.info("[BatchProcessorEnvioMAG] No hay registros pendientes")
            return 0, []
        
        # Separar PKs y reference_ids
        pk_list = [pk for pk, _ in control_records]
        reference_ids = [ref_id for _, ref_id in control_records]
        
        # Crear mapping de reference_id -> pk para uso posterior
        ref_to_pk = {ref_id: pk for pk, ref_id in control_records}
        
        envio_mag_logger.info(
            f"[BatchProcessorEnvioMAG] Procesando {len(control_records)} registros "
            f"desde {self.target_config.control_table}"
        )
        
        try:
            # Cargar mapeo principal para obtener database_id
            main_mapping = mapping_loader_envio_mag.load_main_mapping()
            db_id_field = main_mapping.database_id
            
            if not db_id_field:
                raise ValueError("El archivo main.yml no tiene database_id definido")
            
            # Obtener todos los datos necesarios usando reference_ids
            main_table_data, all_related_data = self.fetch_all_data_for_batch(reference_ids)
            
            # Construir JSONs para cada registro
            json_list = []
            successful_count = 0
            
            for main_row in main_table_data:
                record_id = main_row.get(db_id_field)
                reference_value = main_row.get(self.target_config.source_reference_field)
                
                # Obtener PK de control_table para UPDATEs
                control_pk = ref_to_pk.get(reference_value)
                
                if not control_pk:
                    envio_mag_logger.warning(
                        f"[BatchProcessorEnvioMAG] No se encontró PK para reference_value={reference_value}, saltando"
                    )
                    continue
                
                try:
                    # ✅ PASO 1: Marcar como PROCESANDO inmediatamente (evita duplicados)
                    # Usar control_pk (_id) para el UPDATE
                    self._mark_as_processing(control_pk)
                    
                    # ✅ PASO 2: Construir JSON
                    json_data = self.build_json_for_record(main_row, all_related_data)
                    
                    # Validar que el JSON no esté vacío
                    if not json_data:
                        raise ValueError("JSON vacío o inválido")
                    
                    # Guardar para debug si está habilitado
                    self.save_debug_json(record_id, json_data)
                    
                    # Agregar a la lista con metadata
                    json_list.append({
                        'control_id': control_pk,  # PK de control_table (_id) para UPDATEs
                        'record_id': record_id,  # ID del registro en tabla principal (bol_id)
                        'json_data': json_data
                    })
                    
                    successful_count += 1
                    
                    if config.DEBUG_CLI:
                        envio_mag_logger.debug(
                            f"[BatchProcessorEnvioMAG] JSON construido para {db_id_field}={record_id}"
                        )
                
                except Exception as e:
                    # ❌ ERROR en construcción de JSON (equivalente a 4xx: SIN reencolar)
                    error_msg = f"Error construyendo JSON: {str(e)}"
                    envio_mag_logger.error(
                        f"[BatchProcessorEnvioMAG] {error_msg} para {db_id_field}={record_id}",
                        exc_info=True
                    )
                    
                    # Marcar como ERROR usando control_pk (_id)
                    self._mark_as_error(control_pk, error_msg)
                    
                    # Continuar con el siguiente registro
                    continue
            
            envio_mag_logger.info(
                f"[BatchProcessorEnvioMAG] Lote procesado: {successful_count}/{len(control_records)} exitosos"
            )
            
            # CAMBIO: No actualizar a ENVIADO aquí
            # Los registros se actualizan después del envío HTTP exitoso
            # Ver: EnvioMagSenderWorker.update_control_status()
            
            return successful_count, json_list
        
        except Exception as e:
            envio_mag_logger.error(
                f"[BatchProcessorEnvioMAG] Error procesando lote: {e}",
                exc_info=True
            )
            return 0, []
    
    async def process_all_pending(self) -> int:
        """
        Procesa todos los registros pendientes en lotes
        Publica cada JSON a RabbitMQ para envío posterior
        
        Returns:
            Total de registros publicados exitosamente
        """
        envio_mag_logger.info("[BatchProcessorEnvioMAG] Iniciando procesamiento de todos los pendientes")
        
        total_published = 0
        batch_number = 1
        
        while True:
            envio_mag_logger.info(f"[BatchProcessorEnvioMAG] Procesando lote #{batch_number}")
            
            # Procesar un lote (construir JSONs)
            count, json_list = self.process_batch()
            
            if count == 0:
                # No hay más registros pendientes
                break
            
            # Publicar cada JSON a la cola de envío
            published_count = 0
            for json_item in json_list:
                try:
                    # Construir mensaje para la cola
                    message = {
                        'control_id': json_item['control_id'],  # PK de control_table (_id)
                        'record_id': json_item['record_id'],
                        'json_data': json_item['json_data'],
                        'control_table': self.target_config.control_table,
                        'control_id_column': self.target_config.control_table_primary_key  # Usar PK para UPDATEs
                    }
                    
                    # Publicar a cola de envío
                    success = await rabbitmq_client.publish_message(
                        queue_name=config.QUEUE_ENVIO_MAG_SEND,
                        message=message,
                        priority=5
                    )
                    
                    if success:
                        published_count += 1
                        
                        if config.DEBUG_CLI:
                            envio_mag_logger.debug(
                                f"[BatchProcessorEnvioMAG] JSON publicado a cola: control_id={json_item['control_id']}"
                            )
                    else:
                        # Error publicando a RabbitMQ
                        # NOTA: El registro queda en PROCESANDO, puede reprocesarse después
                        envio_mag_logger.error(
                            f"[BatchProcessorEnvioMAG] Error publicando JSON para control_id={json_item['control_id']}"
                        )
                
                except Exception as e:
                    envio_mag_logger.error(
                        f"[BatchProcessorEnvioMAG] Excepción publicando mensaje: {e}",
                        exc_info=True
                    )
            
            total_published += published_count
            batch_number += 1
            
            envio_mag_logger.info(
                f"[BatchProcessorEnvioMAG] Lote #{batch_number - 1} publicado: "
                f"{published_count}/{count} JSONs. Total acumulado: {total_published}"
            )
        
        envio_mag_logger.info(
            f"[BatchProcessorEnvioMAG] Procesamiento completo. "
            f"Total publicado: {total_published} JSONs a cola {config.QUEUE_ENVIO_MAG_SEND}"
        )
        
        return total_published


# Instancia global
batch_processor_envio_mag = BatchProcessorEnvioMAG()
