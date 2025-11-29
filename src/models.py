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
class ControlEnviosBoletas(Base):
    """
    Tabla de control para almacenar los JSONs recibidos de KoboToolbox
    y controlar su procesamiento ETL
    """
    __tablename__ = 'control_envios_boletas'
    __table_args__ = {'schema': 'sc_renagro_mag'}
    
    _id = Column('_id', Integer, primary_key=True, nullable=False, comment='ID único del envío proveniente del campo _id del JSON de KoboToolbox')
    formhub_uuid = Column('formhub_uuid', String(255), unique=True, nullable=False, comment='UUID único del formulario proveniente del campo formhub/uuid del JSON')
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
    procesado_at = Column(
        'procesado_at',
        DateTime(timezone=True),
        nullable=True,
        comment='Fecha y hora cuando se completó el procesamiento exitosamente'
    )
    
    def __repr__(self):
        return f"<ControlEnviosBoletas(_id={self._id}, formhub_uuid={self.formhub_uuid}, estado_etl={self.estado_etl})>"
