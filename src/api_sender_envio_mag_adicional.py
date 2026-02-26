"""
Cliente HTTP para envío de tablas adicionales a API remota RENAGRO.
Soporta capacitacion, comunicacion y produccion.
"""
import asyncio
import aiohttp
from typing import Dict, Any, Tuple, Optional

from .config import config
from .logger import envio_mag_logger
from .auth_manager_mag import auth_manager_mag


TARGET_ENDPOINT = {
    'capacitacion': config.RENAGRO_ENDPOINT_CAPACITACION,
    'comunicacion': config.RENAGRO_ENDPOINT_COMUNICACION,
    'produccion': config.RENAGRO_ENDPOINT_PRODUCCION
}

TARGET_RESPONSE_ID_FIELD = {
    'capacitacion': 'capacitacionId',
    'comunicacion': 'comunicacionId',
    'produccion': 'produccionId'
}

TARGET_RESPONSE_ID_FALLBACK_FIELDS = {
    'capacitacion': [
        'capacitacionId', 'capacitacion_id', 'idCapacitacion', 'id_capacitacion',
        'idCapacitacionCreada', 'id_capacitacion_creada',
        'id', '_id'
    ],
    'comunicacion': [
        'comunicacionId', 'comunicacion_id', 'idComunicacion', 'id_comunicacion',
        'idComunicacionCreada', 'id_comunicacion_creada',
        'id', '_id'
    ],
    'produccion': [
        'produccionId', 'produccion_id', 'idProduccion', 'id_produccion',
        'idProduccionCreada', 'id_produccion_creada',
        'id', '_id'
    ]
}


class APISenderEnvioMAGAdicional:
    """Cliente HTTP para envío de tablas adicionales con reintentos"""

    def __init__(self):
        self.max_retries = config.MAX_RETRY_ATTEMPTS

    @staticmethod
    def _coerce_int(value: Any) -> Optional[int]:
        if value is None:
            return None

        if isinstance(value, bool):
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _extract_remote_id(self, target_type: str, response_data: Any) -> Optional[int]:
        """
        Extrae ID remoto desde múltiples esquemas de respuesta.
        Soporta:
        - Campo directo en raíz
        - Campo dentro de data/result/payload
        - Variaciones de nombre del ID
        """
        if not isinstance(response_data, dict):
            return None

        primary_field = TARGET_RESPONSE_ID_FIELD.get(target_type)
        if primary_field:
            primary_value = self._coerce_int(response_data.get(primary_field))
            if primary_value is not None:
                return primary_value

        candidate_fields = TARGET_RESPONSE_ID_FALLBACK_FIELDS.get(target_type, [])
        containers = [response_data]

        for container_key in ('data', 'result', 'payload', 'response'):
            container = response_data.get(container_key)
            if isinstance(container, dict):
                containers.append(container)

        for container in containers:
            for field_name in candidate_fields:
                value = self._coerce_int(container.get(field_name))
                if value is not None:
                    return value

        return None

    async def _get_headers(self) -> Optional[Dict[str, str]]:
        token = await auth_manager_mag.get_token()
        if not token:
            envio_mag_logger.error("[APISenderEnvioMAGAdicional] No se pudo obtener token")
            return None
        return {
            'Content-Type': 'application/json',
            'Authorization': token
        }

    async def send_json(
        self,
        target_type: str,
        json_data: Dict[str, Any],
        control_id: int,
        record_id: int
    ) -> Tuple[bool, Optional[int], Optional[str], Optional[int]]:
        if auth_manager_mag.is_auth_failed():
            error_msg = "Proceso detenido por fallo de autenticación"
            envio_mag_logger.error(
                f"[APISenderEnvioMAGAdicional] ❌ {error_msg} - "
                f"target={target_type}, control_id={control_id}"
            )
            return False, None, error_msg, None

        endpoint = TARGET_ENDPOINT.get(target_type)
        if not endpoint:
            error_msg = f"Endpoint no configurado para target={target_type}"
            envio_mag_logger.error(f"[APISenderEnvioMAGAdicional] {error_msg}")
            return False, None, error_msg, None

        headers = await self._get_headers()
        if not headers:
            error_msg = "No se pudo obtener token de autenticación"
            envio_mag_logger.error(f"[APISenderEnvioMAGAdicional] {error_msg}")
            return False, None, error_msg, None

        attempt = 0
        last_error = None
        last_status = None

        connector = None
        if not config.VERIFY_SSL:
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)

        async with aiohttp.ClientSession(connector=connector) as session:
            while attempt < self.max_retries:
                attempt += 1

                try:
                    if config.DEBUG_CLI:
                        envio_mag_logger.debug(
                            f"[APISenderEnvioMAGAdicional] Intento {attempt}/{self.max_retries} "
                            f"target={target_type}, control_id={control_id}, record_id={record_id}"
                        )

                    async with session.post(
                        endpoint,
                        json=json_data,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        last_status = response.status

                        if response.status == 200:
                            response_data = await response.json()
                            remote_id = self._extract_remote_id(target_type, response_data)

                            if remote_id is None:
                                envio_mag_logger.warning(
                                    f"[APISenderEnvioMAGAdicional] ⚠️ Respuesta 200 sin ID remoto detectable: "
                                    f"target={target_type}, control_id={control_id}, "
                                    f"keys={list(response_data.keys())}"
                                )

                            envio_mag_logger.info(
                                f"[APISenderEnvioMAGAdicional] ✅ Enviado exitosamente: "
                                f"target={target_type}, control_id={control_id}, status=200, remote_id={remote_id}"
                            )

                            return True, 200, None, remote_id

                        if response.status == 401:
                            error_text = await response.text()
                            envio_mag_logger.error(
                                f"[APISenderEnvioMAGAdicional] ❌ Error 401 Unauthorized: "
                                f"target={target_type}, control_id={control_id}, body={error_text}"
                            )
                            await auth_manager_mag.handle_unauthorized()
                            return False, 401, f"HTTP 401 Unauthorized: {error_text}", None

                        if 400 <= response.status < 500:
                            error_text = await response.text()
                            envio_mag_logger.error(
                                f"[APISenderEnvioMAGAdicional] ❌ Error 4xx (no reintentable): "
                                f"target={target_type}, control_id={control_id}, status={response.status}, "
                                f"body={error_text[:500] if len(error_text) > 500 else error_text}"
                            )
                            return False, response.status, f"HTTP {response.status}: {error_text}", None

                        if response.status >= 500:
                            error_text = await response.text()
                            last_error = f"HTTP {response.status}: {error_text}"

                            envio_mag_logger.warning(
                                f"[APISenderEnvioMAGAdicional] ⚠️ Error 5xx (reintentable): "
                                f"target={target_type}, control_id={control_id}, status={response.status}, "
                                f"intento={attempt}/{self.max_retries}, "
                                f"body={error_text[:500] if len(error_text) > 500 else error_text}"
                            )

                            if attempt < self.max_retries:
                                wait_time = 5 * (2 ** (attempt - 1))
                                envio_mag_logger.info(
                                    f"[APISenderEnvioMAGAdicional] Reintentando en {wait_time}s..."
                                )
                                await asyncio.sleep(wait_time)

                            continue

                        error_text = await response.text()
                        last_error = f"HTTP {response.status}: {error_text}"

                        envio_mag_logger.warning(
                            f"[APISenderEnvioMAGAdicional] Código inesperado: "
                            f"target={target_type}, control_id={control_id}, status={response.status}"
                        )

                        if attempt < self.max_retries:
                            wait_time = 5 * (2 ** (attempt - 1))
                            await asyncio.sleep(wait_time)

                        continue

                except aiohttp.ClientError as e:
                    last_error = f"Error de conexión: {str(e)}"

                    envio_mag_logger.error(
                        f"[APISenderEnvioMAGAdicional] Error de red: "
                        f"target={target_type}, control_id={control_id}, error={str(e)}, "
                        f"intento={attempt}/{self.max_retries}"
                    )

                    if attempt < self.max_retries:
                        wait_time = 5 * (2 ** (attempt - 1))
                        envio_mag_logger.info(
                            f"[APISenderEnvioMAGAdicional] Reintentando en {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)

                    continue

                except Exception as e:
                    last_error = f"Error inesperado: {str(e)}"
                    envio_mag_logger.error(
                        f"[APISenderEnvioMAGAdicional] Error inesperado: "
                        f"target={target_type}, control_id={control_id}, error={str(e)}",
                        exc_info=True
                    )
                    return False, None, last_error, None

        final_error = last_error or "Reintentos agotados"
        envio_mag_logger.error(
            f"[APISenderEnvioMAGAdicional] ❌ Reintentos agotados: "
            f"target={target_type}, control_id={control_id}, last_status={last_status}, error={final_error}"
        )

        return False, last_status, final_error, None


api_sender_envio_mag_adicional = APISenderEnvioMAGAdicional()
