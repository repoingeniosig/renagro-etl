"""
Worker para envío de geometrías a API remota RENAGRO.
Consume cola QUEUE_ENVIO_MAG_GEOMETRIA_SEND y actualiza estado en tablas de control.
"""
import asyncio
from typing import Dict, Any
from sqlalchemy import text

from .config import config
from .logger import envio_mag_logger
from .database import db
from .api_sender_envio_mag_geometria import api_sender_envio_mag_geometria


class EnvioMagSenderWorkerGeometria:
    """Worker de envío paralelo para geometrías"""

    def __init__(self):
        self.semaphore = asyncio.Semaphore(config.PARALLEL_REQUESTS_SEND_MAG)
        self.stats = {
            'total_processed': 0,
            'success': 0,
            'error_4xx': 0,
            'error_5xx': 0,
            'error_network': 0
        }

    async def update_control_status(
        self,
        control_table: str,
        control_id_column: str,
        control_id: int,
        status: str,
        remote_id_column: str = None,
        remote_id: int = None,
        error_message: str = None
    ):
        try:
            if status == 'ERROR' and error_message:
                reintentable = True

                if error_message.startswith('HTTP '):
                    try:
                        http_code_str = error_message.split(':')[0].replace('HTTP ', '').strip()
                        http_code = int(http_code_str)
                        reintentable = http_code >= 500
                    except (ValueError, IndexError):
                        reintentable = True

                update_query = f"""
                    UPDATE "{config.DB_SCHEMA}".{control_table}
                    SET envio_datos_procesados = :status,
                        error_mensajes_envio = :error_message,
                        reintentable = :reintentable,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE {control_id_column} = :control_id
                """
                params = {
                    'status': status,
                    'error_message': error_message,
                    'reintentable': reintentable,
                    'control_id': control_id
                }
            elif status == 'ENVIADO' and remote_id_column:
                update_query = f"""
                    UPDATE "{config.DB_SCHEMA}".{control_table}
                    SET envio_datos_procesados = :status,
                        reintentable = FALSE,
                        error_mensajes_envio = NULL,
                        {remote_id_column} = :remote_id,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE {control_id_column} = :control_id
                """
                params = {
                    'status': status,
                    'remote_id': remote_id,
                    'control_id': control_id
                }
            else:
                update_query = f"""
                    UPDATE "{config.DB_SCHEMA}".{control_table}
                    SET envio_datos_procesados = :status,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE {control_id_column} = :control_id
                """
                params = {
                    'status': status,
                    'control_id': control_id
                }

            with db.get_session() as session:
                result = session.execute(text(update_query), params)
                session.commit()

                if result.rowcount == 0:
                    envio_mag_logger.warning(
                        f"[EnvioMagSenderWorkerGeometria] UPDATE sin filas afectadas: "
                        f"tabla={control_table}, columna={control_id_column}, id={control_id}, status={status}"
                    )
                elif config.DEBUG_CLI:
                    envio_mag_logger.debug(
                        f"[EnvioMagSenderWorkerGeometria] Estado actualizado: "
                        f"{control_table}.{control_id_column}={control_id} -> {status}"
                    )
        except Exception as e:
            envio_mag_logger.error(
                f"[EnvioMagSenderWorkerGeometria] Error actualizando estado: {e}",
                exc_info=True
            )

    async def send_json_task(self, message: Dict[str, Any]):
        async with self.semaphore:
            control_id = message.get('control_id')
            record_id = message.get('record_id')
            target_type = message.get('target_type')
            json_data = message.get('json_data')
            control_table = message.get('control_table')
            control_id_column = message.get('control_id_column')
            remote_id_column = message.get('remote_id_column')

            try:
                await self.update_control_status(
                    control_table=control_table,
                    control_id_column=control_id_column,
                    control_id=control_id,
                    status='ENTREGANDO'
                )

                success, status_code, error_msg, remote_id = await api_sender_envio_mag_geometria.send_json(
                    target_type=target_type,
                    json_data=json_data,
                    control_id=control_id,
                    record_id=record_id
                )

                if success:
                    await self.update_control_status(
                        control_table=control_table,
                        control_id_column=control_id_column,
                        control_id=control_id,
                        status='ENVIADO',
                        remote_id_column=remote_id_column,
                        remote_id=remote_id
                    )
                    self.stats['success'] += 1

                    envio_mag_logger.info(
                        f"[EnvioMagSenderWorkerGeometria] ✅ Enviado: "
                        f"target={target_type}, control_id={control_id}, remote_id={remote_id}"
                    )
                else:
                    await self.update_control_status(
                        control_table=control_table,
                        control_id_column=control_id_column,
                        control_id=control_id,
                        status='ERROR',
                        error_message=error_msg
                    )

                    if status_code and 400 <= status_code < 500:
                        self.stats['error_4xx'] += 1
                    elif status_code and status_code >= 500:
                        self.stats['error_5xx'] += 1
                    else:
                        self.stats['error_network'] += 1

                    envio_mag_logger.error(
                        f"[EnvioMagSenderWorkerGeometria] ❌ Error enviando: "
                        f"target={target_type}, control_id={control_id}, status={status_code}, error={error_msg}"
                    )

            except Exception as e:
                envio_mag_logger.error(
                    f"[EnvioMagSenderWorkerGeometria] Error inesperado: control_id={control_id}, {e}",
                    exc_info=True
                )
                await self.update_control_status(
                    control_table=control_table,
                    control_id_column=control_id_column,
                    control_id=control_id,
                    status='ERROR',
                    error_message=f"Error inesperado: {str(e)[:200]}"
                )
                self.stats['error_network'] += 1
            finally:
                self.stats['total_processed'] += 1

    async def process_message(self, data: Dict[str, Any]):
        await self.send_json_task(data)

    def print_stats(self):
        envio_mag_logger.info("=" * 80)
        envio_mag_logger.info("ESTADÍSTICAS DE ENVÍO GEOMETRÍA")
        envio_mag_logger.info("=" * 80)
        envio_mag_logger.info(f"Total procesado: {self.stats['total_processed']}")
        envio_mag_logger.info(f"✅ Enviados exitosamente: {self.stats['success']}")
        envio_mag_logger.info(f"❌ Errores 4xx (cliente): {self.stats['error_4xx']}")
        envio_mag_logger.info(f"❌ Errores 5xx (servidor): {self.stats['error_5xx']}")
        envio_mag_logger.info(f"❌ Errores de red: {self.stats['error_network']}")
        envio_mag_logger.info("=" * 80)


envio_mag_sender_worker_geometria = EnvioMagSenderWorkerGeometria()
