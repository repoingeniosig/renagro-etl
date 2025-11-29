"""
Modelos SQLAlchemy para la base de datos
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class EstadoETLEnum(str, enum.Enum):
    """Estados posibles para el procesamiento ETL"""
    ERROR = "ERROR"
    PENDIENTE = "PENDIENTE"
    PROCESADO = "PROCESADO"


class EstadoEnvioEnum(str, enum.Enum):
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
    
    _id = Column(Integer, primary_key=True, nullable=False, comment='ID único del envío proveniente del campo _id del JSON de KoboToolbox')
    formhub_uuid = Column(String(255), unique=True, nullable=False, comment='UUID único del formulario proveniente del campo formhub/uuid del JSON')
    json_data = Column(JSONB, nullable=False, comment='JSON completo del envío de KoboToolbox almacenado en formato JSONB')
    fecha_recepcion = Column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        comment='Fecha y hora exacta de recepción del JSON en el servidor externo'
    )
    estado_etl = Column(
        Enum(EstadoETLEnum, name='estado_etl_enum', schema='sc_renagro_mag'),
        nullable=False,
        default=EstadoETLEnum.PENDIENTE,
        server_default='PENDIENTE',
        comment='Estado del procesamiento ETL: PENDIENTE, PROCESADO, ERROR'
    )
    envio_datos_procesados = Column(
        Enum(EstadoEnvioEnum, name='estado_envio_enum', schema='sc_renagro_mag'),
        nullable=False,
        default=EstadoEnvioEnum.PENDIENTE,
        server_default='PENDIENTE',
        comment='Estado del envío a API de terceros: PENDIENTE, PROCESADO, ERROR'
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment='Fecha de creación del registro'
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment='Fecha de última actualización del registro'
    )
    error_message = Column(Text, nullable=True, comment='Mensaje de error en caso de que el procesamiento falle')
    procesado_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment='Fecha y hora cuando se completó el procesamiento exitosamente'
    )
    
    def __repr__(self):
        return f"<ControlEnviosBoletas(_id={self._id}, formhub_uuid={self.formhub_uuid}, estado_etl={self.estado_etl})>"
