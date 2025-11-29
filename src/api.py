"""
API REST con FastAPI para procesar JSONs de KoboToolbox
"""
import secrets
from typing import Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from .config import config
from .models import EstadoETLEnum
from .logger import etl_logger
from .mapping_loader import mapping_loader
from .rabbitmq_client import rabbitmq_client

# Inicializar FastAPI
app = FastAPI(
    title="RENAGRO ETL API",
    description="API para procesar formularios KoboToolbox y ejecutar transformaciones ETL",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """
    Evento de inicio: Cargar mapeos YAML a Redis cache
    Se ejecuta una sola vez al iniciar el servidor
    """
    etl_logger.info("Iniciando servidor RENAGRO ETL API...")
    
    try:
        # Cargar mapeos master y YAML
        etl_logger.info("Cargando mapeos YAML...")
        mapping_loader.load_master()
        mapping_loader.load_all_mappings(force_reload=False)
        
        etl_logger.info(f"Mapeos cargados: {len(mapping_loader.entity_mappings)} entidades")
        
        if config.DEBUG_CLI:
            from rich.console import Console
            console = Console()
            console.print(f"\n[green]✅ Servidor iniciado - {len(mapping_loader.entity_mappings)} mapeos YAML cargados[/green]")
            console.print(f"[cyan]Redis cache: {'Habilitado' if config.REDIS_ENABLED else 'Deshabilitado'}[/cyan]\n")
    
    except Exception as e:
        etl_logger.error(f"Error cargando mapeos en startup: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre del servidor"""
    etl_logger.info("Cerrando servidor RENAGRO ETL API...")


# Seguridad HTTP Basic
security = HTTPBasic()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Verifica las credenciales de autenticación básica
    """
    correct_username = secrets.compare_digest(credentials.username, config.API_BASIC_USER)
    correct_password = secrets.compare_digest(credentials.password, config.API_BASIC_PASSWORD)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


class AcceptedResponse(BaseModel):
    """Modelo de respuesta para procesamiento asíncrono"""
    success: bool
    message: str
    _id: int
    status: str


@app.get("/")
async def root():
    """Endpoint raíz - información de la API"""
    return {
        "service": "RENAGRO ETL API",
        "version": "1.0.0",
        "status": "running",
        "mode": "async",
        "endpoints": {
            "POST /boletas": "Recibir formulario KoboToolbox (procesamiento asíncrono)",
            "GET /boletas/{_id}": "Consultar estado de procesamiento"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/boletas", response_model=AcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def process_boleta(
    json_data: Dict[str, Any],
    username: str = Depends(verify_credentials)
):
    """
    Recibe un JSON de KoboToolbox para procesamiento asíncrono
    
    Flujo asíncrono (pipeline de colas RabbitMQ):
    1. API valida JSON y publica a cola json_save
    2. Worker json_save guarda en BD y publica a etl_transform
    3. Worker etl_transform procesa transformaciones y publica a db_insert
    4. Worker db_insert ejecuta transacción y actualiza estado final
    
    Args:
        json_data: JSON completo del formulario KoboToolbox
        
    Returns:
        AcceptedResponse con confirmación de recepción (202 Accepted)
        
    Raises:
        HTTPException 400: Si el JSON es inválido
        HTTPException 503: Si RabbitMQ no está disponible
    """
    _id = None
    
    try:
        # Validar campos requeridos
        _id = json_data.get('_id')
        
        if not _id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El JSON no contiene el campo '_id'"
            )
        
        etl_logger.info(f"API - _id={_id} recibido desde {username}")
        
        # Publicar a cola json_save
        success = await rabbitmq_client.publish_message(
            queue_name=config.QUEUE_JSON_SAVE,
            message=json_data,
            priority=5
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No se pudo publicar mensaje a cola de procesamiento"
            )
        
        etl_logger.info(f"API - _id={_id} publicado a cola {config.QUEUE_JSON_SAVE}")
        
        # Retornar inmediatamente (procesamiento asíncrono)
        return AcceptedResponse(
            success=True,
            message="JSON recibido y enviado a procesamiento asíncrono",
            _id=_id,
            status="ENCOLADO"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        etl_logger.error(f"API - _id={_id} - {error_msg}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@app.get("/boletas/{_id}")
async def get_boleta_status(
    _id: int,
    username: str = Depends(verify_credentials)
):
    """
    Consulta el estado de procesamiento de un JSON
    
    Args:
        _id: ID del formulario
        
    Returns:
        Estado actual del procesamiento
    """
    try:
        from .database import db
        from .models import ControlEnviosBoletas
        
        with db.get_session() as session:
            control = session.query(ControlEnviosBoletas).filter_by(_id=_id).first()
            
            if not control:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No se encontró registro con _id={_id}"
                )
            
            return {
                "_id": control._id,
                "estado_etl": control.estado_etl.value,
                "envio_datos_procesados": control.envio_datos_procesados.value,
                "fecha_recepcion": control.fecha_recepcion.isoformat(),
                "procesado_at": control.procesado_at.isoformat() if control.procesado_at else None,
                "error_message": control.error_message
            }
    
    except HTTPException:
        raise
    except Exception as e:
        etl_logger.error(f"Error consultando estado _id={_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones"""
    etl_logger.error(f"API - Excepción global: {str(exc)}", exc_info=True)
    
    return {
        "success": False,
        "message": f"Error interno del servidor: {str(exc)}",
        "timestamp": datetime.now().isoformat()
    }
