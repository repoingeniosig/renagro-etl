"""
Configuración de la aplicación
Carga variables de entorno desde .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Configuración de la aplicación"""
    
    # PostgreSQL
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_NAME = os.getenv('DB_NAME', 'renagro_db')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    DB_SCHEMA = os.getenv('DB_SCHEMA', 'sc_renagro_mag')
    
    @property
    def database_url(self) -> str:
        """Construye la URL de conexión a PostgreSQL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    REDIS_TTL = int(os.getenv('REDIS_TTL', 3600))  # 1 hora por defecto
    REDIS_ENABLED = os.getenv('REDIS_ENABLED', 'true').lower() in ('true', '1', 'yes')
    
    # RabbitMQ
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
    RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
    RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
    RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
    RABBITMQ_VHOST = os.getenv('RABBITMQ_VHOST', '/')
    
    # Colas
    QUEUE_JSON_SAVE = os.getenv('QUEUE_JSON_SAVE', 'renagro.json.save')
    QUEUE_ETL_TRANSFORM = os.getenv('QUEUE_ETL_TRANSFORM', 'renagro.etl.transform')
    QUEUE_DB_INSERT = os.getenv('QUEUE_DB_INSERT', 'renagro.db.insert')
    
    # Colas de reintentos (con TTL)
    QUEUE_JSON_SAVE_RETRY = os.getenv('QUEUE_JSON_SAVE_RETRY', 'renagro.json.save.retry')
    QUEUE_ETL_TRANSFORM_RETRY = os.getenv('QUEUE_ETL_TRANSFORM_RETRY', 'renagro.etl.transform.retry')
    QUEUE_DB_INSERT_RETRY = os.getenv('QUEUE_DB_INSERT_RETRY', 'renagro.db.insert.retry')
    
    # Dead Letter Queues (errores permanentes)
    QUEUE_JSON_SAVE_DLQ = os.getenv('QUEUE_JSON_SAVE_DLQ', 'renagro.json.save.dlq')
    QUEUE_ETL_TRANSFORM_DLQ = os.getenv('QUEUE_ETL_TRANSFORM_DLQ', 'renagro.etl.transform.dlq')
    QUEUE_DB_INSERT_DLQ = os.getenv('QUEUE_DB_INSERT_DLQ', 'renagro.db.insert.dlq')
    
    # Configuraci\u00f3n de reintentos
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    
    # API Externa
    API_EXTERNAL_URL = os.getenv('API_EXTERNAL_URL', 'https://api.example.com')
    API_EXTERNAL_KEY = os.getenv('API_EXTERNAL_KEY', '')
    
    # API REST (FastAPI)
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 8000))
    API_RELOAD = os.getenv('API_RELOAD', 'true').lower() in ('true', '1', 'yes')
    API_BASIC_USER = os.getenv('API_BASIC_USER', 'admin')
    API_BASIC_PASSWORD = os.getenv('API_BASIC_PASSWORD', 'admin123')
    
    # Aplicación
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DEBUG = os.getenv('DEBUG', 'false').lower() in ('true', '1', 'yes')
    DEBUG_CLI = os.getenv('DEBUG_CLI', 'false').lower() in ('true', '1', 'yes')
    
    # Rutas del proyecto
    BASE_DIR = Path(__file__).parent.parent
    MAPPINGS_BASE_DIR = BASE_DIR / 'mappings'  # Base para multi-form
    MAPPING_ENVIO_MAG_DIR = BASE_DIR / 'mappings-envio-mag'
    LOG_DIR = BASE_DIR / os.getenv('LOG_DIR', 'logs')
    
    # MAG Envio Configuration
    BATCH_SIZE_SEND_MAG = int(os.getenv('BATCH_SIZE_SEND_MAG', 1000))
    DEBUG_JSON_OUTPUT = os.getenv('DEBUG_JSON_OUTPUT', 'false').lower() in ('true', '1', 'yes')
    
    # Intervalos de revisión (solo para desarrollo)
    ENVIO_MAG_CHECK_INTERVAL = int(os.getenv('ENVIO_MAG_CHECK_INTERVAL', 300))  # 5 minutos
    ENVIO_MAG_SENDER_CHECK_INTERVAL = int(os.getenv('ENVIO_MAG_SENDER_CHECK_INTERVAL', 120))  # 2 minutos
    
    # API Remota RENAGRO (envío de JSONs)
    RENAGRO_ENDPOINT = os.getenv('RENAGRO_ENDPOINT', '')
    PARALLEL_REQUESTS_SEND_MAG = int(os.getenv('PARALLEL_REQUESTS_SEND_MAG', 10))
    MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', 3))
    
    # MAG RENAGRO Authentication
    MAG_RENAGRO_AUTH_URL = os.getenv('MAG_RENAGRO_AUTH_URL', '')
    MAG_RENAGRO_ID = int(os.getenv('MAG_RENAGRO_ID', 87))
    MAG_RENAGRO_USER = os.getenv('MAG_RENAGRO_USER', '')
    MAG_RENAGRO_PASSWORD = os.getenv('MAG_RENAGRO_PASSWORD', '')
    MAG_RENAGRO_IP_LAN = os.getenv('MAG_RENAGRO_IP_LAN', '')
    MAG_RENAGRO_IP_WAN = os.getenv('MAG_RENAGRO_IP_WAN', '')
    
    # Colas de envío MAG
    QUEUE_ENVIO_MAG_SEND = os.getenv('QUEUE_ENVIO_MAG_SEND', 'renagro.envio.mag.send')
    QUEUE_ENVIO_MAG_SEND_RETRY = os.getenv('QUEUE_ENVIO_MAG_SEND_RETRY', 'renagro.envio.mag.send.retry')
    QUEUE_ENVIO_MAG_SEND_DLQ = os.getenv('QUEUE_ENVIO_MAG_SEND_DLQ', 'renagro.envio.mag.send.dlq')
    

# Instancia global de configuración
config = Config()
