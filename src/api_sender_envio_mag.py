"""
Cliente HTTP para envío de JSONs a API remota RENAGRO
Maneja reintentos con backoff exponencial
"""
import asyncio
import aiohttp
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

from .config import config
from .logger import envio_mag_logger


class APISenderEnvioMAG:
    """Cliente HTTP para envío de JSONs con reintentos"""
    
    def __init__(self):
        self.endpoint = config.RENAGRO_ENDPOINT
        self.token = config.RENAGRO_TOKEN
        self.max_retries = config.MAX_RETRY_ATTEMPTS
        
        if not self.endpoint:
            envio_mag_logger.warning("[APISenderEnvioMAG] RENAGRO_ENDPOINT no configurado")
        
        if not self.token:
            envio_mag_logger.warning("[APISenderEnvioMAG] RENAGRO_TOKEN no configurado")
    
    def _get_headers(self) -> Dict[str, str]:
        """Construye headers para petición HTTP"""
        return {
            'Content-Type': 'application/json',
            'Authorization': self.token
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
        if not self.endpoint or not self.token:
            error_msg = "API endpoint o token no configurados"
            envio_mag_logger.error(f"[APISenderEnvioMAG] {error_msg}")
            return False, None, error_msg
        
        attempt = 0
        last_error = None
        last_status = None
        
        async with aiohttp.ClientSession() as session:
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
                        headers=self._get_headers(),
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        last_status = response.status
                        
                        # Éxito: 201 Created
                        if response.status == 201:
                            envio_mag_logger.info(
                                f"[APISenderEnvioMAG] ✅ Enviado exitosamente: "
                                f"control_id={control_id}, status=201"
                            )
                            return True, 201, None
                        
                        # Error 4xx: No reintentar (error del cliente)
                        if 400 <= response.status < 500:
                            error_text = await response.text()
                            error_msg = f"HTTP {response.status}: {error_text[:200]}"
                            
                            envio_mag_logger.error(
                                f"[APISenderEnvioMAG] ❌ Error 4xx (no reintentable): "
                                f"control_id={control_id}, status={response.status}, "
                                f"error={error_text[:100]}"
                            )
                            
                            return False, response.status, error_msg
                        
                        # Error 5xx: Reintentar (error del servidor)
                        if response.status >= 500:
                            error_text = await response.text()
                            last_error = f"HTTP {response.status}: {error_text[:200]}"
                            
                            envio_mag_logger.warning(
                                f"[APISenderEnvioMAG] ⚠️ Error 5xx (reintentable): "
                                f"control_id={control_id}, status={response.status}, "
                                f"intento={attempt}/{self.max_retries}"
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
                        last_error = f"HTTP {response.status}: {error_text[:200]}"
                        
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
                    return False, None, last_error
        
        # Agotados todos los reintentos
        envio_mag_logger.error(
            f"[APISenderEnvioMAG] ❌ Reintentos agotados: control_id={control_id}, "
            f"last_status={last_status}, last_error={last_error}"
        )
        
        return False, last_status, last_error or "Reintentos agotados"


# Instancia global
api_sender_envio_mag = APISenderEnvioMAG()
