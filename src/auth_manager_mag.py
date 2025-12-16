"""
Gestor de autenticación para API remota MAG RENAGRO
Maneja obtención y renovación de tokens de acceso
"""
import asyncio
import aiohttp
from typing import Optional
from datetime import datetime

from .config import config
from .logger import envio_mag_logger


class AuthManagerMAG:
    """
    Gestor de autenticación para API MAG RENAGRO
    
    Funcionalidades:
    - Obtiene token de acceso mediante autenticación POST
    - Mantiene token en memoria
    - Detecta errores 401 y detiene el proceso
    - Proporciona token actualizado para peticiones
    """
    
    def __init__(self):
        self.auth_url = config.MAG_RENAGRO_AUTH_URL
        self.apli_id = config.MAG_RENAGRO_ID
        self.user = config.MAG_RENAGRO_USER
        self.password = config.MAG_RENAGRO_PASSWORD
        self.ip_lan = config.MAG_RENAGRO_IP_LAN
        self.ip_wan = config.MAG_RENAGRO_IP_WAN
        
        self._access_token: Optional[str] = None
        self._token_lock = asyncio.Lock()
        self._auth_failed = False  # Flag para detener proceso si falla autenticación
        
        # Validar configuración
        if not all([self.auth_url, self.user, self.password, self.ip_lan, self.ip_wan]):
            envio_mag_logger.warning(
                "[AuthManagerMAG] Variables de autenticación MAG no configuradas completamente"
            )
    
    def _build_auth_payload(self) -> dict:
        """Construye el payload para autenticación"""
        return {
            "apliId": self.apli_id,
            "user": self.user,
            "password": self.password,
            "ipLan": self.ip_lan,
            "ipWan": self.ip_wan
        }
    
    async def authenticate(self) -> bool:
        """
        Realiza autenticación y obtiene token de acceso
        
        Returns:
            bool: True si autenticación exitosa, False si falla
        """
        async with self._token_lock:
            if self._auth_failed:
                envio_mag_logger.error(
                    "[AuthManagerMAG] ❌ Autenticación previamente fallida, "
                    "proceso detenido"
                )
                return False
            
            if not self.auth_url:
                envio_mag_logger.error(
                    "[AuthManagerMAG] ❌ MAG_RENAGRO_AUTH_URL no configurado"
                )
                self._auth_failed = True
                return False
            
            try:
                envio_mag_logger.info(
                    f"[AuthManagerMAG] 🔐 Iniciando autenticación en {self.auth_url}"
                )
                
                payload = self._build_auth_payload()
                
                # Construir headers con Basic Auth si está configurado
                headers = {'Content-Type': 'application/json'}
                
                # Agregar Basic Auth si está configurado
                if config.MAG_USERNAME and config.MAG_PASSWORD:
                    import base64
                    credentials = f"{config.MAG_USERNAME}:{config.MAG_PASSWORD}"
                    encoded_credentials = base64.b64encode(credentials.encode()).decode()
                    headers['Authorization'] = f'Basic {encoded_credentials}'
                    
                    if config.DEBUG_CLI:
                        envio_mag_logger.debug(
                            f"[AuthManagerMAG] Usando Basic Auth con usuario: {config.MAG_USERNAME}"
                        )
                
                # Configurar SSL verification
                connector = None
                if not config.VERIFY_SSL:
                    import ssl
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    connector = aiohttp.TCPConnector(ssl=ssl_context)
                    
                    if config.DEBUG_CLI:
                        envio_mag_logger.debug(
                            "[AuthManagerMAG] SSL verification deshabilitada"
                        )
                
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.post(
                        self.auth_url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            access_token = data.get('accessToken')
                            
                            if not access_token:
                                envio_mag_logger.error(
                                    "[AuthManagerMAG] ❌ Respuesta sin accessToken"
                                )
                                self._auth_failed = True
                                return False
                            
                            self._access_token = access_token
                            self._auth_failed = False
                            
                            envio_mag_logger.info(
                                "[AuthManagerMAG] ✅ Autenticación exitosa, token obtenido"
                            )
                            
                            if config.DEBUG_CLI:
                                envio_mag_logger.debug(
                                    f"[AuthManagerMAG] Token: {access_token[:50]}..."
                                )
                            
                            return True
                        
                        elif response.status == 401:
                            error_text = await response.text()
                            envio_mag_logger.error(
                                f"[AuthManagerMAG] ❌ Autenticación fallida (401 Unauthorized): "
                                f"{error_text}"
                            )
                            envio_mag_logger.error(
                                "[AuthManagerMAG] 🛑 PROCESO DETENIDO - Credenciales inválidas"
                            )
                            self._auth_failed = True
                            return False
                        
                        else:
                            error_text = await response.text()
                            envio_mag_logger.error(
                                f"[AuthManagerMAG] ❌ Error de autenticación HTTP {response.status}: "
                                f"{error_text}"
                            )
                            self._auth_failed = True
                            return False
            
            except aiohttp.ClientError as e:
                envio_mag_logger.error(
                    f"[AuthManagerMAG] ❌ Error de conexión durante autenticación: {e}"
                )
                self._auth_failed = True
                return False
            
            except Exception as e:
                envio_mag_logger.error(
                    f"[AuthManagerMAG] ❌ Error inesperado durante autenticación: {e}",
                    exc_info=True
                )
                self._auth_failed = True
                return False
    
    async def get_token(self) -> Optional[str]:
        """
        Obtiene el token de acceso actual (autenticándose si es necesario)
        
        Returns:
            str: Token de acceso con formato "Bearer <token>"
            None: Si autenticación falla o proceso está detenido
        """
        # Verificar si proceso está detenido por fallo de autenticación
        if self._auth_failed:
            envio_mag_logger.error(
                "[AuthManagerMAG] ❌ No se puede obtener token, "
                "autenticación previamente fallida"
            )
            return None
        
        # Si no hay token, autenticar
        if not self._access_token:
            success = await self.authenticate()
            if not success:
                return None
        
        return f"Bearer {self._access_token}"
    
    async def handle_unauthorized(self):
        """
        Maneja error 401 Unauthorized
        Marca autenticación como fallida y detiene proceso
        """
        async with self._token_lock:
            envio_mag_logger.error(
                "[AuthManagerMAG] ❌ Token rechazado (401 Unauthorized) durante envío"
            )
            envio_mag_logger.error(
                "[AuthManagerMAG] 🛑 PROCESO DETENIDO - Token inválido o expirado"
            )
            self._auth_failed = True
            self._access_token = None
    
    def is_auth_failed(self) -> bool:
        """
        Verifica si la autenticación ha fallado y el proceso debe detenerse
        
        Returns:
            bool: True si autenticación falló y proceso debe detenerse
        """
        return self._auth_failed
    
    async def reset_auth_state(self):
        """
        Resetea el estado de autenticación (para testing/recuperación manual)
        """
        async with self._token_lock:
            self._access_token = None
            self._auth_failed = False
            envio_mag_logger.info(
                "[AuthManagerMAG] Estado de autenticación reseteado"
            )


# Instancia global
auth_manager_mag = AuthManagerMAG()
