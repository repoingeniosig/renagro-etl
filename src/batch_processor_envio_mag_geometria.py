"""
Procesador de lotes para envío de geometrías a MAG
Soporta boleta_geometria y terreno_geometria con configuración por target.
"""
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


TARGET_REMOTE_ID_COLUMN = {
    'boleta_geometria': 'id_boleta_geometria_creada',
    'terreno_geometria': 'id_terreno_geometria_creada'
}


class BatchProcessorEnvioMAGGeometria:
    """Procesador de lotes para geometría por target"""

    def __init__(self, target_name: str):
        self.target_name = target_name
        self.batch_size = config.BATCH_SIZE_SEND_MAG
        self.target_config = structure_loader.get_target_data_to_send(target_name)

    def _configure_mapping_context(self):
        mapping_loader_envio_mag.configure_mapping_context(
            mapping_path=self.target_config.mapping,
            main_mapping_file=self.target_config.source_reference_file
        )

    def get_pending_ids(self) -> List[Tuple[Any, Any]]:
        where_conditions = []
        params = {'batch_size': self.batch_size}

        for filter_obj in self.target_config.control_table_filters:
            where_conditions.append(f"{filter_obj.column} = :{filter_obj.column}")
            params[filter_obj.column] = filter_obj.value

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        where_clause_with_retry = (
            f"({where_clause}) OR (envio_datos_procesados = 'ERROR' AND reintentable = TRUE)"
        )

        same_column = self.target_config.control_table_id == self.target_config.control_table_primary_key

        if same_column:
            query = f"""
                SELECT {self.target_config.control_table_primary_key}
                FROM "{config.DB_SCHEMA}".{self.target_config.control_table}
                WHERE {where_clause_with_retry}
                ORDER BY {self.target_config.control_table_primary_key} ASC
                LIMIT :batch_size
            """
        else:
            query = f"""
                SELECT {self.target_config.control_table_primary_key}, {self.target_config.control_table_id}
                FROM "{config.DB_SCHEMA}".{self.target_config.control_table}
                WHERE {where_clause_with_retry}
                ORDER BY {self.target_config.control_table_primary_key} ASC
                LIMIT :batch_size
            """

        with db.get_session() as session:
            result = session.execute(text(query), params)
            if same_column:
                ids = [(row[0], str(row[0])) for row in result]
            else:
                ids = [(row[0], str(row[1]) if row[1] is not None else None) for row in result]

        return ids

    def fetch_all_data_for_batch(
        self,
        reference_ids: List[Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
        self._configure_mapping_context()

        with db.get_session() as session:
            fetcher = DataFetcherEnvioMAG(session)

            main_mapping = mapping_loader_envio_mag.load_main_mapping()
            main_table = main_mapping.table
            reference_field = self.target_config.source_reference_field

            main_table_data = fetcher.fetch_table_data(
                main_table,
                reference_ids,
                reference_field,
                use_cache=True
            )

            database_ids = [record.get(self.target_config.source_database_id) for record in main_table_data]
            database_ids = [db_id for db_id in database_ids if db_id is not None]

            all_mappings = mapping_loader_envio_mag.load_all_mappings_recursive(
                self.target_config.source_reference_file,
                use_redis_cache=True
            )

            all_related_data = fetcher.fetch_all_related_tables(
                all_mappings,
                database_ids,
                main_mapping,
                root_data=main_table_data,
                source_reference_field=None
            )

        return main_table_data, all_related_data

    def build_json_for_record(
        self,
        main_row: Dict[str, Any],
        all_related_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        self._configure_mapping_context()
        main_mapping = mapping_loader_envio_mag.load_main_mapping()

        return JSONBuilderEnvioMAG.build_nested_structure(
            main_row,
            main_mapping,
            all_related_data
        )

    def _mark_as_processing(self, control_id: Any):
        with db.get_session() as session:
            update_query = f"""
                UPDATE "{config.DB_SCHEMA}".{self.target_config.control_table}
                SET envio_datos_procesados = 'PROCESANDO',
                    updated_at = CURRENT_TIMESTAMP
                WHERE {self.target_config.control_table_primary_key} = :control_id
            """
            session.execute(text(update_query), {"control_id": control_id})
            session.commit()

    def _mark_as_error(self, control_id: Any, error_message: str):
        error_message_truncated = error_message[:500] if len(error_message) > 500 else error_message

        with db.get_session() as session:
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

    def process_batch(self) -> Tuple[int, List[Dict[str, Any]]]:
        control_records = self.get_pending_ids()

        if not control_records:
            return 0, []

        reference_ids = [ref_id for _, ref_id in control_records]
        ref_to_pk = {ref_id: pk for pk, ref_id in control_records}

        main_table_data, all_related_data = self.fetch_all_data_for_batch(reference_ids)

        self._configure_mapping_context()
        main_mapping = mapping_loader_envio_mag.load_main_mapping()
        db_id_field = main_mapping.database_id

        json_list = []
        successful_count = 0

        for main_row in main_table_data:
            record_id = main_row.get(db_id_field)
            reference_value = main_row.get(self.target_config.source_reference_field)
            control_pk = ref_to_pk.get(str(reference_value))

            if not control_pk:
                envio_mag_logger.warning(
                    f"[BatchProcessorEnvioMAGGeometria:{self.target_name}] "
                    f"No se encontró PK para reference_value={reference_value}"
                )
                continue

            try:
                self._mark_as_processing(control_pk)
                json_data = self.build_json_for_record(main_row, all_related_data)

                if not json_data:
                    raise ValueError("JSON vacío o inválido")

                json_list.append({
                    'target_type': self.target_name,
                    'control_id': control_pk,
                    'record_id': record_id,
                    'json_data': json_data,
                    'control_table': self.target_config.control_table,
                    'control_id_column': self.target_config.control_table_primary_key,
                    'remote_id_column': TARGET_REMOTE_ID_COLUMN[self.target_name]
                })
                successful_count += 1
            except Exception as e:
                error_msg = f"Error construyendo JSON: {str(e)}"
                envio_mag_logger.error(
                    f"[BatchProcessorEnvioMAGGeometria:{self.target_name}] {error_msg}",
                    exc_info=True
                )
                self._mark_as_error(control_pk, error_msg)

        envio_mag_logger.info(
            f"[BatchProcessorEnvioMAGGeometria:{self.target_name}] "
            f"Lote procesado: {successful_count}/{len(control_records)}"
        )

        return successful_count, json_list

    async def process_all_pending(self) -> int:
        total_published = 0
        batch_number = 1

        while True:
            count, json_list = self.process_batch()
            if count == 0:
                break

            published_count = 0
            for message in json_list:
                try:
                    success = await rabbitmq_client.publish_message(
                        queue_name=config.QUEUE_ENVIO_MAG_GEOMETRIA_SEND,
                        message=message,
                        priority=5
                    )
                    if success:
                        published_count += 1
                    else:
                        envio_mag_logger.error(
                            f"[BatchProcessorEnvioMAGGeometria:{self.target_name}] "
                            f"Error publicando JSON para control_id={message['control_id']}"
                        )
                except Exception as e:
                    envio_mag_logger.error(
                        f"[BatchProcessorEnvioMAGGeometria:{self.target_name}] "
                        f"Excepción publicando mensaje: {e}",
                        exc_info=True
                    )

            total_published += published_count
            envio_mag_logger.info(
                f"[BatchProcessorEnvioMAGGeometria:{self.target_name}] "
                f"Lote #{batch_number} publicado: {published_count}/{count}. "
                f"Total acumulado: {total_published}"
            )
            batch_number += 1

        return total_published


batch_processor_boleta_geometria = BatchProcessorEnvioMAGGeometria('boleta_geometria')
batch_processor_terreno_geometria = BatchProcessorEnvioMAGGeometria('terreno_geometria')


async def process_all_geometry_targets() -> int:
    envio_mag_logger.info("[BatchProcessorEnvioMAGGeometria] Iniciando procesamiento de geometrías")

    total_boleta = await batch_processor_boleta_geometria.process_all_pending()
    total_terreno = await batch_processor_terreno_geometria.process_all_pending()

    total = total_boleta + total_terreno
    envio_mag_logger.info(
        f"[BatchProcessorEnvioMAGGeometria] Procesamiento completo. "
        f"boleta={total_boleta}, terreno={total_terreno}, total={total}"
    )

    return total


async def process_geometry_target(target_name: str) -> int:
    """
    Procesa un único target de geometría.

    Args:
        target_name: 'boleta_geometria' o 'terreno_geometria'

    Returns:
        Total publicado para el target
    """
    if target_name == 'boleta_geometria':
        return await batch_processor_boleta_geometria.process_all_pending()

    if target_name == 'terreno_geometria':
        return await batch_processor_terreno_geometria.process_all_pending()

    raise ValueError(f"Target de geometría no soportado: {target_name}")
