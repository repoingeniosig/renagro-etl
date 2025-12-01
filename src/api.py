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
from .recovery import recover_failed_messages

# Inicializar FastAPI
app = FastAPI(
    title="RENAGRO ETL API",
    description="API para procesar formularios KoboToolbox y ejecutar transformaciones ETL",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """
    Evento de inicio: 
    1. Cargar configuración de formularios
    2. Cargar mapeos YAML de todos los formularios
    3. Recuperar mensajes con ERROR
    """
    etl_logger.info("Iniciando servidor RENAGRO ETL API...")
    
    try:
        # 1. Cargar configuración de formularios
        from .forms_manager import forms_manager
        from pathlib import Path
        
        etl_logger.info("Cargando configuración de formularios...")
        forms = forms_manager.list_active_forms()
        etl_logger.info(f"{len(forms)} formularios activos")
        
        # 2. Cargar mapeos YAML para cada formulario
        for form in forms:
            mapping_path = forms_manager.get_mapping_path(form)
            
            if not mapping_path.exists():
                etl_logger.warning(f"Directorio de mapeos no existe: {mapping_path}")
                continue
            
            try:
                mapping_loader.load_form_mappings(form.uuid, mapping_path)
            except Exception as e:
                etl_logger.error(f"Error cargando mapeos para {form.uuid}: {e}")
        
        # 3. Recuperar mensajes fallidos de la BD
        etl_logger.info("Recuperando mensajes con estado ERROR...")
        recovered = await recover_failed_messages()
        etl_logger.info(f"Recuperación completada: {recovered} mensajes republicados")
        
        if config.DEBUG_CLI:
            from rich.console import Console
            console = Console()
            console.print(f"\n[green]✅ Servidor iniciado - {len(forms)} formularios configurados[/green]")
            for form in forms:
                mappings_count = len(mapping_loader.get_form_mappings(form.uuid))
                console.print(f"   {form.uuid}: {mappings_count} entidades")
            console.print(f"[yellow]Mensajes recuperados: {recovered}[/yellow]\n")
    
    except Exception as e:
        etl_logger.error(f"Error en startup: {e}", exc_info=True)
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
        
        # VALIDAR FORMULARIO POR UUID
        from .forms_manager import forms_manager
        from .database import db
        from sqlalchemy import text
        
        is_valid, form_config, error = forms_manager.validate_json(json_data)
        
        if not is_valid:
            etl_logger.error(f"API - _id={_id} rechazado: {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        etl_logger.info(f"API - _id={_id} identificado como formulario '{form_config.name}' (UUID: {form_config.uuid})")
        
        # VALIDAR DUPLICADOS EN TABLA DE CONTROL CORRESPONDIENTE
        from .models import get_control_table_model
        
        ControlModel = get_control_table_model(form_config.control_table, db.engine)
        
        with db.get_session() as session:
            existing = session.query(ControlModel).filter_by(_id=_id).first()
            
            if existing:
                etl_logger.warning(f"API - _id={_id} duplicado rechazado en {form_config.control_table}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Registro duplicado: _id={_id} ya existe en {form_config.control_table}"
                )
        
        # Agregar metadato del formulario al mensaje
        json_data['__form_uuid__'] = form_config.uuid
        
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
