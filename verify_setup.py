#!/usr/bin/env python3
"""
Script de verificación de instalación
Verifica que todas las dependencias y configuraciones estén correctas
"""
import sys
import os
from pathlib import Path

def check_python_version():
    """Verifica la versión de Python"""
    print("🔍 Verificando versión de Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (se requiere 3.8+)")
        return False

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    print("\n🔍 Verificando dependencias...")
    dependencies = [
        ('sqlalchemy', 'SQLAlchemy'),
        ('yaml', 'PyYAML'),
        ('dotenv', 'python-dotenv'),
        ('psycopg2', 'psycopg2-binary'),
    ]
    
    all_ok = True
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            print(f"   ✅ {package_name}")
        except ImportError:
            print(f"   ❌ {package_name} - No instalado")
            all_ok = False
    
    return all_ok

def check_env_file():
    """Verifica que exista el archivo .env"""
    print("\n🔍 Verificando archivo .env...")
    env_path = Path('.env')
    
    if env_path.exists():
        print("   ✅ Archivo .env encontrado")
        
        # Leer y verificar variables clave
        with open(env_path, 'r') as f:
            content = f.read()
            required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_SCHEMA']
            missing = []
            
            for var in required_vars:
                if var not in content:
                    missing.append(var)
            
            if missing:
                print(f"   ⚠️  Variables faltantes: {', '.join(missing)}")
                return False
            else:
                print("   ✅ Variables de entorno configuradas")
                return True
    else:
        print("   ❌ Archivo .env no encontrado")
        print("   💡 Ejecuta: cp .env.example .env")
        return False

def check_directories():
    """Verifica que existan los directorios necesarios"""
    print("\n🔍 Verificando estructura de directorios...")
    required_dirs = [
        'src',
        'mapping',
        'scripts',
        'data',
        'docs'
    ]
    
    all_ok = True
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists() and dir_path.is_dir():
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ❌ {dir_name}/ - No encontrado")
            all_ok = False
    
    return all_ok

def check_source_files():
    """Verifica que existan los archivos fuente principales"""
    print("\n🔍 Verificando archivos de código fuente...")
    required_files = [
        'src/__init__.py',
        'src/config.py',
        'src/models.py',
        'src/database.py',
        'src/mapping_loader.py',
        'src/transformer.py',
        'src/process_json.py',
    ]
    
    all_ok = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - No encontrado")
            all_ok = False
    
    return all_ok

def check_mapping_files():
    """Verifica archivos de mapeo"""
    print("\n🔍 Verificando archivos de mapeo...")
    master_path = Path('mapping/master.yml')
    
    if master_path.exists():
        print(f"   ✅ mapping/master.yml")
        return True
    else:
        print(f"   ❌ mapping/master.yml - No encontrado")
        return False

def test_import():
    """Intenta importar el módulo principal"""
    print("\n🔍 Probando importación del módulo...")
    try:
        # Agregar el directorio actual al path
        sys.path.insert(0, str(Path.cwd()))
        
        # Intentar importar
        from src.config import config
        from src.models import ControlEnviosBoletas
        from src.database import db
        from src.mapping_loader import mapping_loader
        from src.transformer import JSONTransformer, SQLGenerator
        
        print("   ✅ Módulos importados correctamente")
        return True
    except Exception as e:
        print(f"   ❌ Error al importar módulos: {e}")
        return False

def main():
    """Función principal"""
    print("="*70)
    print("RENAGRO ETL Process - Verificación de Instalación")
    print("="*70)
    
    checks = [
        ("Python", check_python_version()),
        ("Dependencias", check_dependencies()),
        ("Archivo .env", check_env_file()),
        ("Directorios", check_directories()),
        ("Archivos fuente", check_source_files()),
        ("Archivos de mapeo", check_mapping_files()),
        ("Importación", test_import()),
    ]
    
    print("\n" + "="*70)
    print("RESUMEN DE VERIFICACIÓN")
    print("="*70)
    
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    print(f"\nResultado: {passed}/{total} verificaciones pasadas")
    
    if passed == total:
        print("\n✅ ¡Todo está configurado correctamente!")
        print("\n📝 Próximos pasos:")
        print("   1. Verifica la conexión a PostgreSQL en .env")
        print("   2. Ejecuta: psql -U postgres -d renagro_db -f scripts/create_control_table.sql")
        print("   3. Prueba con: python -m src.process_json data/test_example.json")
        return 0
    else:
        print(f"\n❌ Hay {total - passed} problema(s) que resolver")
        print("\n💡 Sugerencias:")
        if not checks[1][1]:  # Dependencias
            print("   - Ejecuta: pip install -r requirements.txt")
        if not checks[2][1]:  # .env
            print("   - Ejecuta: cp .env.example .env")
        print("   - Consulta QUICKSTART.md para más ayuda")
        return 1

if __name__ == '__main__':
    sys.exit(main())
