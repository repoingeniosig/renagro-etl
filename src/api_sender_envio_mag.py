"""
Cliente HTTP para envío de JSONs a API remota RENAGRO
Maneja reintentos con backoff exponencial y autenticación dinámica
"""
import asyncio
import aiohttp
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

from .config import config
from .logger import envio_mag_logger
from .auth_manager_mag import auth_manager_mag


class APISenderEnvioMAG:
    """Cliente HTTP para envío de JSONs con reintentos y autenticación dinámica"""
    
    def __init__(self):
        self.endpoint = config.RENAGRO_ENDPOINT
        self.max_retries = config.MAX_RETRY_ATTEMPTS
        
        if not self.endpoint:
            envio_mag_logger.warning("[APISenderEnvioMAG] RENAGRO_ENDPOINT no configurado")
    
    async def _get_headers(self) -> Optional[Dict[str, str]]:
        """
        Construye headers para petición HTTP con token dinámico
        
        Returns:
            Dict con headers si token disponible, None si autenticación falla
        """
        token = await auth_manager_mag.get_token()
        
        if not token:
            envio_mag_logger.error(
                "[APISenderEnvioMAG] No se pudo obtener token de autenticación"
            )
            return None
        
        return {
            'Content-Type': 'application/json',
            'Authorization': token
        }
    
    async def send_json(
        self,
        json_data: Dict[str, Any],
        control_id: int,
        record_id: int
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Envía un JSON a la API remota con reintentos
        
        Args:
            json_data: Datos JSON a enviar
            control_id: ID del registro en tabla de control
            record_id: ID del registro en tabla principal
        
        Returns:
            Tupla (success, status_code, error_message)
            - success: True si envío exitoso (201)
            - status_code: Código HTTP de respuesta (None si error de red)
            - error_message: Mensaje de error (None si exitoso)
        """
        # Verificar si autenticación ha fallado previamente
        if auth_manager_mag.is_auth_failed():
            error_msg = "Proceso detenido por fallo de autenticación"
            envio_mag_logger.error(
                f"[APISenderEnvioMAG] ❌ {error_msg} - control_id={control_id}"
            )
            return False, None, error_msg
        
        if not self.endpoint:
            error_msg = "API endpoint no configurado"
            envio_mag_logger.error(f"[APISenderEnvioMAG] {error_msg}")
            return False, None, error_msg
        
        # Obtener headers con token dinámico
        headers = await self._get_headers()
        if not headers:
            error_msg = "No se pudo obtener token de autenticación"
            envio_mag_logger.error(f"[APISenderEnvioMAG] {error_msg}")
            return False, None, error_msg
        
        attempt = 0
        last_error = None
        last_status = None
        
        # Configurar SSL verification
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
                            f"[APISenderEnvioMAG] Intento {attempt}/{self.max_retries} "
                            f"para control_id={control_id}, record_id={record_id}"
                        )
                    
                    async with session.post(
                        self.endpoint,
                        json=json_data,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        last_status = response.status
                        
                        # Éxito: 200 OK
                        if response.status == 200:
                            # Extraer boletaId del body
                            response_data = await response.json()
                            boleta_id = response_data.get('boletaId')
                            
                            envio_mag_logger.info(
                                f"[APISenderEnvioMAG] ✅ Enviado exitosamente: "
                                f"control_id={control_id}, status=200, boletaId={boleta_id}"
                            )
                            return True, 200, None, boleta_id
                        
                        # Error 401: Token inválido o expirado - DETENER TODO
                        if response.status == 401:
                            error_text = await response.text()
                            error_msg = f"HTTP 401 Unauthorized: {error_text}"
                            
                            envio_mag_logger.error(
                                f"[APISenderEnvioMAG] ❌ Error 401 Unauthorized: "
                                f"control_id={control_id}, body={error_text}"
                            )
                            
                            # Notificar al auth manager y detener proceso
                            await auth_manager_mag.handle_unauthorized()
                            
                            return False, 401, error_msg, None
                        
                        # Error 4xx (excepto 401): No reintentar (error del cliente)
                        if 400 <= response.status < 500:
                            error_text = await response.text()
                            error_msg = f"HTTP {response.status}: {error_text}"  # SIN truncar
                            
                            envio_mag_logger.error(
                                f"[APISenderEnvioMAG] ❌ Error 4xx (no reintentable): "
                                f"control_id={control_id}, status={response.status}, "
                                f"body={error_text[:500] if len(error_text) > 500 else error_text}"
                            )
                            
                            return False, response.status, error_msg, None
                        
                        # Error 5xx: Reintentar (error del servidor)
                        if response.status >= 500:
                            error_text = await response.text()
                            last_error = f"HTTP {response.status}: {error_text}"  # SIN truncar
                            
                            envio_mag_logger.warning(
                                f"[APISenderEnvioMAG] ⚠️ Error 5xx (reintentable): "
                                f"control_id={control_id}, status={response.status}, "
                                f"intento={attempt}/{self.max_retries}, "
                                f"body={error_text[:500] if len(error_text) > 500 else error_text}"
                            )
                            
                            # Backoff exponencial: 5s, 10s, 20s
                            if attempt < self.max_retries:
                                wait_time = 5 * (2 ** (attempt - 1))
                                envio_mag_logger.info(
                                    f"[APISenderEnvioMAG] Reintentando en {wait_time}s..."
                                )
                                await asyncio.sleep(wait_time)
                            
                            continue
                        
                        # Otros códigos inesperados
                        error_text = await response.text()
                        last_error = f"HTTP {response.status}: {error_text}"  # SIN truncar
                        
                        envio_mag_logger.warning(
                            f"[APISenderEnvioMAG] Código inesperado: "
                            f"control_id={control_id}, status={response.status}"
                        )
                        
                        # Reintentar en caso de respuestas inesperadas
                        if attempt < self.max_retries:
                            wait_time = 5 * (2 ** (attempt - 1))
                            await asyncio.sleep(wait_time)
                        
                        continue
                
                except aiohttp.ClientError as e:
                    last_error = f"Error de conexión: {str(e)}"
                    
                    envio_mag_logger.error(
                        f"[APISenderEnvioMAG] Error de red: control_id={control_id}, "
                        f"error={str(e)}, intento={attempt}/{self.max_retries}"
                    )
                    
                    # Reintentar errores de red
                    if attempt < self.max_retries:
                        wait_time = 5 * (2 ** (attempt - 1))
                        envio_mag_logger.info(
                            f"[APISenderEnvioMAG] Reintentando en {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                    
                    continue
                
                except Exception as e:
                    last_error = f"Error inesperado: {str(e)}"
                    
                    envio_mag_logger.error(
                        f"[APISenderEnvioMAG] Error inesperado: control_id={control_id}, "
                        f"error={str(e)}",
                        exc_info=True
                    )
                    
                    # No reintentar errores inesperados
                    return False, None, last_error, None
        
        # Agotados todos los reintentos
        final_error = last_error or "Reintentos agotados sin respuesta"
        
        envio_mag_logger.error(
            f"[APISenderEnvioMAG] ❌ Reintentos agotados: control_id={control_id}, "
            f"last_status={last_status}, error_completo={final_error}"
        )
        
        return False, last_status, final_error, None


# Instancia global
api_sender_envio_mag = APISenderEnvioMAG()
