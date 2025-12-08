""" 
Modelos SQLAlchemy para la base de datos
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class EstadoETLEnum(enum.Enum):
    """Estados posibles para el procesamiento ETL"""
    ERROR = "ERROR"
    PENDIENTE = "PENDIENTE"
    PROCESADO = "PROCESADO"


class EstadoEnvioEnum(enum.Enum):
    """Estados posibles para el envío de datos procesados"""
    ERROR = "ERROR"
    PENDIENTE = "PENDIENTE"
    PROCESADO = "PROCESADO"


def create_control_table_model(table_name: str, schema: str = 'sc_renagro_mag'):
    """
    Crea dinámicamente un modelo SQLAlchemy para una tabla de control
    
    Args:
        table_name: Nombre de la tabla (ej: 'control_envios_boletas', 'control_envios_boletas_procesos')
        schema: Esquema de la base de datos
    
    Returns:
        Clase del modelo SQLAlchemy
    """
    class_name = ''.join(word.capitalize() for word in table_name.split('_'))
    
    attrs = {
        '__tablename__': table_name,
        '__table_args__': {'schema': schema, 'extend_existing': True},
        '_id': Column('_id', Integer, primary_key=True, nullable=False, comment='ID único del envío proveniente del campo _id del JSON de KoboToolbox'),
        'uuid_boleta': Column('uuid_boleta', String(36), nullable=True, unique=True, comment='UUID de la boleta extraído del campo _uuid del JSON de KoboToolbox'),
        'json_data': Column('json_data', JSONB, nullable=False, comment='JSON completo del envío de KoboToolbox almacenado en formato JSONB'),
        'fecha_recepcion': Column(
            'fecha_recepcion',
            DateTime(timezone=True), 
            nullable=False, 
            server_default=func.current_timestamp(),
            comment='Fecha y hora exacta de recepción del JSON en el servidor externo'
        ),
        'estado_etl': Column(
            'estado_etl',
            SQLEnum(
                EstadoETLEnum,
                name='estado_etl_enum',
                schema=schema,
                create_type=False
            ),
            nullable=False,
            server_default='PENDIENTE',
            comment='Estado del procesamiento ETL: PENDIENTE, PROCESADO, ERROR'
        ),
        'envio_datos_procesados': Column(
            'envio_datos_procesados',
            SQLEnum(
                EstadoEnvioEnum,
                name='estado_envio_enum',
                schema=schema,
                create_type=False
            ),
            nullable=False,
            server_default='PENDIENTE',
            comment='Estado del envío a API de terceros: PENDIENTE, PROCESADO, ERROR'
        ),
        'created_at': Column(
            'created_at',
            DateTime(timezone=True),
            nullable=False,
            server_default=func.current_timestamp(),
            comment='Fecha de creación del registro'
        ),
        'updated_at': Column(
            'updated_at',
            DateTime(timezone=True),
            nullable=False,
            server_default=func.current_timestamp(),
            onupdate=func.current_timestamp(),
            comment='Fecha de última actualización del registro'
        ),
        'error_message': Column('error_message', Text, nullable=True, comment='Mensaje de error en caso de que el procesamiento falle'),
        'error_mensajes_envio': Column('error_mensajes_envio', JSONB, nullable=True, comment='Detalles de errores en el envío a API de terceros'),
        'retry_count': Column('retry_count', Integer, nullable=False, server_default='0', comment='Número de reintentos de procesamiento realizados'),
        'last_error_stage': Column('last_error_stage', String(50), nullable=True, comment='Última etapa donde ocurrió el error: json_save, etl_transform, db_insert'),
        'procesado_at': Column(
            'procesado_at',
            DateTime(timezone=True),
            nullable=True,
            comment='Fecha y hora cuando se completó el procesamiento exitosamente'
        ),
        '__repr__': lambda self: f"<{class_name}(_id={self._id}, uuid_boleta={self.uuid_boleta}, estado_etl={self.estado_etl})>"
    }
    
    return type(class_name, (Base,), attrs)


# Cache de modelos dinámicos
_control_table_models = {}


def get_control_table_model(table_name: str, schema: str = 'sc_renagro_mag'):
    """
    Obtiene o crea un modelo de tabla de control
    
    Args:
        table_name: Nombre de la tabla
        schema: Esquema de la base de datos
    
    Returns:
        Clase del modelo SQLAlchemy
    """
    cache_key = f"{schema}.{table_name}"
    if cache_key not in _control_table_models:
        _control_table_models[cache_key] = create_control_table_model(table_name, schema)
    return _control_table_models[cache_key]


class ControlEnviosBoletas(Base):
    """
    Tabla de control para almacenar los JSONs recibidos de KoboToolbox
    y controlar su procesamiento ETL
    """
    __tablename__ = 'control_envios_boletas'
    __table_args__ = {'schema': 'sc_renagro_mag'}
    
    _id = Column('_id', Integer, primary_key=True, nullable=False, comment='ID único del envío proveniente del campo _id del JSON de KoboToolbox')
    uuid_boleta = Column('uuid_boleta', String(36), nullable=True, unique=True, comment='UUID de la boleta extraído del campo _uuid del JSON de KoboToolbox')
    json_data = Column('json_data', JSONB, nullable=False, comment='JSON completo del envío de KoboToolbox almacenado en formato JSONB')
    fecha_recepcion = Column(
        'fecha_recepcion',
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp(),
        comment='Fecha y hora exacta de recepción del JSON en el servidor externo'
    )
    estado_etl = Column(
        'estado_etl',
        SQLEnum(
            EstadoETLEnum,
            name='estado_etl_enum',
            schema='sc_renagro_mag',
            create_type=False
        ),
        nullable=False,
        server_default='PENDIENTE',
        comment='Estado del procesamiento ETL: PENDIENTE, PROCESADO, ERROR'
    )
    envio_datos_procesados = Column(
        'envio_datos_procesados',
        SQLEnum(
            EstadoEnvioEnum,
            name='estado_envio_enum',
            schema='sc_renagro_mag',
            create_type=False
        ),
        nullable=False,
        server_default='PENDIENTE',
        comment='Estado del envío a API de terceros: PENDIENTE, PROCESADO, ERROR'
    )
    created_at = Column(
        'created_at',
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        comment='Fecha de creación del registro'
    )
    updated_at = Column(
        'updated_at',
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment='Fecha de última actualización del registro'
    )
    error_message = Column('error_message', Text, nullable=True, comment='Mensaje de error en caso de que el procesamiento falle')
    retry_count = Column('retry_count', Integer, nullable=False, server_default='0', comment='Número de reintentos de procesamiento realizados')
    last_error_stage = Column('last_error_stage', String(50), nullable=True, comment='Última etapa donde ocurrió el error: json_save, etl_transform, db_insert')
    procesado_at = Column(
        'procesado_at',
        DateTime(timezone=True),
        nullable=True,
        comment='Fecha y hora cuando se completó el procesamiento exitosamente'
    )
    
    def __repr__(self):
        return f"<ControlEnviosBoletas(_id={self._id}, formhub_uuid={self.formhub_uuid}, estado_etl={self.estado_etl})>"
