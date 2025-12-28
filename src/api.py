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
    1. Cargar configuración multi-formulario
    2. Cargar mapeos YAML por defecto (boletas) a Redis cache
    3. Recuperar mensajes con ERROR de la BD y republicarlos
    """
    etl_logger.info("Iniciando servidor RENAGRO ETL API...")
    
    try:
        # 1. Cargar configuración multi-formulario
        etl_logger.info("Cargando configuración multi-formulario...")
        from .multi_form_loader import multi_form_loader
        multi_form_loader.load_config()
        etl_logger.info(f"✅ Configuración multi-formulario cargada: {len(multi_form_loader.config.forms)} formularios")
        
        # 2. Cargar todos los mappings de todos los formularios a Redis cache
        etl_logger.info("Precargando mappings de todos los formularios en Redis...")
        form_stats = []  # Lista para trackear stats por formulario
        for form_config in multi_form_loader.config.forms:
            try:
                mapping_dir = config.MAPPINGS_BASE_DIR / form_config.mapping_dir
                etl_logger.info(f"  - Cargando mappings para formulario '{form_config.name}' desde {mapping_dir}")
                
                mapping_loader.load_master(mapping_dir=mapping_dir)
                mapping_loader.load_all_mappings(force_reload=False, mapping_dir=mapping_dir)
                
                num_entities = len(mapping_loader.entity_mappings)
                form_stats.append({'name': form_config.name, 'entities': num_entities})
                etl_logger.info(f"    ✅ {num_entities} entidades cargadas para '{form_config.name}'")
            except Exception as e:
                etl_logger.error(f"    ❌ Error cargando mappings para '{form_config.name}': {e}")
        
        total_mappings = sum(f['entities'] for f in form_stats)
        etl_logger.info(f"✅ Total de mappings precargados en Redis: {total_mappings} entidades de {len(form_stats)} formularios")
        
        # 2.5. Cargar mappings de envio_mag a Redis
        etl_logger.info("Precargando mappings de envio_mag en Redis...")
        try:
            from .mapping_loader_envio_mag import mapping_loader_envio_mag
            num_envio_mappings = mapping_loader_envio_mag.preload_all_mappings_to_redis()
            etl_logger.info(f"✅ Mappings de envio_mag precargados: {num_envio_mappings} entidades")
        except Exception as e:
            etl_logger.error(f"❌ Error precargando mappings envio_mag: {e}")
        
        # 3. Recuperar mensajes fallidos de la BD
        etl_logger.info("Recuperando mensajes con estado ERROR...")
        recovered = await recover_failed_messages()
        etl_logger.info(f"Recuperación completada: {recovered} mensajes republicados")
        
        if config.DEBUG_CLI:
            from rich.console import Console
            console = Console()
            console.print(f"\n[green]✅ Servidor iniciado - {len(form_stats)} formularios cargados ({total_mappings} entidades totales)[/green]")
            for stat in form_stats:
                console.print(f"  • {stat['name']}: {stat['entities']} entidades")
            console.print(f"[cyan]Redis cache: {'Habilitado' if config.REDIS_ENABLED else 'Deshabilitado'}[/cyan]")
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
        
        # VALIDAR DUPLICADOS ANTES DE ENCOLAR
        from .database import db
        from .models import ControlEnviosBoletas
        
        with db.get_session() as session:
            existing = session.query(ControlEnviosBoletas).filter_by(_id=_id).first()
            
            if existing:
                etl_logger.warning(f"API - _id={_id} duplicado rechazado (ya existe en BD)")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Registro duplicado: _id={_id} ya existe en la base de datos"
                )
        
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
