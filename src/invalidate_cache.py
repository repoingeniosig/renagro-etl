#!/usr/bin/env python
"""
Script para invalidar el cache de Redis
Útil cuando se actualizan los archivos YAML de mapeo

Uso:
    python -m src.invalidate_cache
"""
import sys
from rich.console import Console
from rich.panel import Panel

console = Console()


def main():
    """Invalida el cache de mapeos en Redis"""
    try:
        console.print(Panel.fit(
            "[bold cyan]Invalidar Cache de Mapeos[/bold cyan]\n"
            "Este script elimina los mapeos cacheados en Redis",
            border_style="cyan"
        ))
        
        from .redis_client import redis_client
        
        # Obtener estadísticas antes
        stats_before = redis_client.get_stats()
        
        console.print(f"\n📊 Estado actual del cache:")
        console.print(f"   Redis habilitado: {stats_before['enabled']}")
        console.print(f"   Redis conectado: {stats_before['connected']}")
        
        if stats_before.get('caches'):
            for prefix, cache_info in stats_before['caches'].items():
                console.print(f"\n   Cache '{prefix}':")
                console.print(f"      Tiene cache: {cache_info['has_cache']}")
                if cache_info['has_cache']:
                    console.print(f"      TTL restante: {cache_info['ttl']}s")
        
        if not stats_before['enabled']:
            console.print("\n[yellow]⚠️  Redis no está habilitado en la configuración[/yellow]")
            console.print("   Configure REDIS_ENABLED=true en .env")
            return
        
        if not stats_before['connected']:
            console.print("\n[yellow]⚠️  No se pudo conectar a Redis[/yellow]")
            console.print(f"   Verifique que Redis esté corriendo en {redis_client._redis_client}")
            return
        
        # Verificar si hay algún cache
        has_any_cache = any(
            cache_info['has_cache'] 
            for cache_info in stats_before.get('caches', {}).values()
        )
        
        if not has_any_cache:
            console.print("\n[yellow]ℹ️  No hay cache para invalidar[/yellow]")
            return
        
        # Invalidar cache
        console.print("\n🗑️  Invalidando cache...")
        success = redis_client.invalidate_cache()
        
        if success:
            console.print("[green]✅ Cache invalidado exitosamente[/green]")
            console.print("\n[dim]La próxima ejecución cargará los mapeos desde disco[/dim]")
        else:
            console.print("[yellow]⚠️  No se pudo invalidar el cache[/yellow]")
    
    except ImportError:
        console.print("\n[red]❌ Error: Redis client no disponible[/red]")
        console.print("   Instale las dependencias: pip install -r requirements.txt")
        sys.exit(1)
    
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
