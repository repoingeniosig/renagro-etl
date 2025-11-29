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
    
    # API Externa
    API_EXTERNAL_URL = os.getenv('API_EXTERNAL_URL', 'https://api.example.com')
    API_EXTERNAL_KEY = os.getenv('API_EXTERNAL_KEY', '')
    
    # Aplicación
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DEBUG = os.getenv('DEBUG', 'false').lower() in ('true', '1', 'yes')
    
    # Rutas del proyecto
    BASE_DIR = Path(__file__).parent.parent
    MAPPING_DIR = BASE_DIR / 'mapping'
    

# Instancia global de configuración
config = Config()
