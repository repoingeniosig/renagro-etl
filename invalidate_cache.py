#!/usr/bin/env python3
"""
Script para invalidar el cache de Redis
Útil cuando se actualizan los archivos YAML de mappings
"""

import sys
import os
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))
os.chdir(Path(__file__).parent)

from src.redis_client import redis_client
from rich.console import Console

console = Console()

def main():
    """Invalida todos los caches de mapeos en Redis"""
    console.print("🗑️  Invalidando cache de mapeos en Redis...")
    
    try:
        # Invalidar cache para todos los formularios
        prefixes = ['etl:boletas', 'etl:boletas-procesos', 'etl:boletas-simplificadas']
        
        total_deleted = 0
        for prefix in prefixes:
            deleted = redis_client.invalidate_cache(cache_prefix=prefix)
            if deleted:
                console.print(f"✅ Cache invalidado: {prefix}")
                total_deleted += 1
            else:
                console.print(f"ℹ️  No había cache para: {prefix}")
        
        if total_deleted > 0:
            console.print(f"\n✅ {total_deleted} caches invalidados correctamente")
            console.print("Los workers cargarán los mapeos desde disco en la próxima ejecución")
        else:
            console.print("\nℹ️  No había caches para invalidar")
            
    except Exception as e:
        console.print(f"❌ Error invalidando cache: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
