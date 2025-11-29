"""
Manejo de conexión a la base de datos con SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from .config import config
from .models import Base


class Database:
    """Clase para manejar la conexión a PostgreSQL"""
    
    def __init__(self):
        self.engine = create_engine(
            config.database_url,
            pool_pre_ping=True,
            echo=False  # Cambiar a True para ver las queries SQL en consola
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self):
        """Crea todas las tablas definidas en los modelos"""
        Base.metadata.create_all(bind=self.engine)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager para obtener una sesión de base de datos
        Uso:
            with db.get_session() as session:
                # usar session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_db_session(self) -> Session:
        """Obtiene una nueva sesión de base de datos"""
        return self.SessionLocal()


# Instancia global de la base de datos
db = Database()
