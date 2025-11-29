"""
Script para iniciar el servidor FastAPI
"""
import uvicorn

from .config import config


def main():
    """
    Inicia el servidor uvicorn con la configuración del .env
    """
    print(f"\n🚀 Iniciando servidor RENAGRO ETL API en http://{config.API_HOST}:{config.API_PORT}")
    print(f"📝 Documentación disponible en http://{config.API_HOST}:{config.API_PORT}/docs\n")
    
    uvicorn.run(
        "src.api:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_RELOAD,
        log_level="info"
    )


if __name__ == "__main__":
    main()
