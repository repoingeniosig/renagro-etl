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
from .process_json import save_to_control_table, process_transformations, execute_transaction, update_control_status

# Inicializar FastAPI
app = FastAPI(
    title="RENAGRO ETL API",
    description="API para procesar formularios KoboToolbox y ejecutar transformaciones ETL",
    version="1.0.0"
)

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


class ProcessResponse(BaseModel):
    """Modelo de respuesta del procesamiento"""
    success: bool
    message: str
    _id: int
    formhub_uuid: str
    estado_etl: str
    entities_processed: int
    total_rows_inserted: int
    execution_time: float
    errors: list = []


@app.get("/")
async def root():
    """Endpoint raíz - información de la API"""
    return {
        "service": "RENAGRO ETL API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "POST /boletas": "Procesar formulario KoboToolbox"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/boletas", response_model=ProcessResponse, status_code=status.HTTP_200_OK)
async def process_boleta(
    json_data: Dict[str, Any],
    username: str = Depends(verify_credentials)
):
    """
    Procesa un JSON de KoboToolbox
    
    Flujo:
    1. Guarda JSON en control_envios_boletas
    2. Realiza transformaciones según mapeos YAML
    3. Ejecuta transacción en PostgreSQL
    4. Retorna resultado del procesamiento
    
    Args:
        json_data: JSON completo del formulario KoboToolbox
        
    Returns:
        ProcessResponse con el resultado del procesamiento
        
    Raises:
        HTTPException 400: Si el JSON es inválido
        HTTPException 500: Si falla el procesamiento
    """
    _id = None
    
    try:
        # Validar campos requeridos
        _id = json_data.get('_id')
        formhub_uuid = json_data.get('formhub/uuid') or json_data.get('formhub', {}).get('uuid')
        
        if not _id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El JSON no contiene el campo '_id'"
            )
        
        if not formhub_uuid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El JSON no contiene el campo 'formhub/uuid'"
            )
        
        # PASO 1: Guardar en tabla de control
        try:
            _id = save_to_control_table(json_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error guardando en base de datos: {str(e)}"
            )
        
        # PASO 2: Procesar transformaciones
        try:
            transformation_result = process_transformations(json_data)
            transformations = transformation_result['transformations']
            processing_order = transformation_result['processing_order']
        except Exception as e:
            error_msg = f"Error en transformaciones: {str(e)}"
            update_control_status(_id, success=False, error_message=error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
        
        # PASO 3 y 4: Ejecutar transacción
        if not transformations:
            update_control_status(_id, success=True)
            return ProcessResponse(
                success=True,
                message="Procesamiento completado (sin datos para insertar)",
                _id=_id,
                formhub_uuid=formhub_uuid,
                estado_etl=EstadoETLEnum.PROCESADO.value,
                entities_processed=0,
                total_rows_inserted=0,
                execution_time=0.0,
                errors=[]
            )
        
        try:
            results = execute_transaction(
                transformations=transformations,
                processing_order=processing_order,
                debug=config.DEBUG
            )
            
            if results['success']:
                # Actualizar estado a PROCESADO
                update_control_status(_id, success=True)
                
                return ProcessResponse(
                    success=True,
                    message="Procesamiento completado exitosamente",
                    _id=_id,
                    formhub_uuid=formhub_uuid,
                    estado_etl=EstadoETLEnum.PROCESADO.value,
                    entities_processed=results['entities_processed'],
                    total_rows_inserted=results['total_rows_inserted'],
                    execution_time=results['execution_time'],
                    errors=[]
                )
            else:
                # Hubo errores en la transacción
                error_msg = '; '.join(results['errors']) if results['errors'] else 'Error desconocido'
                update_control_status(_id, success=False, error_message=error_msg)
                
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error ejecutando transacción: {error_msg}"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"Error ejecutando transacción: {str(e)}"
            update_control_status(_id, success=False, error_message=error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
    
    except HTTPException:
        raise
    except Exception as e:
        # Error inesperado
        error_msg = f"Error inesperado: {str(e)}"
        if _id:
            update_control_status(_id, success=False, error_message=error_msg)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones"""
    return {
        "success": False,
        "message": f"Error interno del servidor: {str(exc)}",
        "timestamp": datetime.now().isoformat()
    }
