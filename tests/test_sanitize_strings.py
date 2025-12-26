#!/usr/bin/env python3
"""
Test para verificar el funcionamiento de sanitización de caracteres especiales
"""
import sys
from pathlib import Path

# Agregar raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.transformer import JSONTransformer
from src.mapping_loader import FieldMapping

def test_sanitize_string():
    """
    Prueba la función de sanitización de strings
    """
    print("="*80)
    print("TEST: Sanitización de Caracteres Especiales")
    print("="*80)
    
    test_cases = [
        {
            "input": "Juan Pérez @ Gmail.com",
            "expected": "Juan Pérez  Gmailcom",
            "description": "Email con @ y punto"
        },
        {
            "input": "Teléfono: +593-099-123-4567",
            "expected": "Teléfono 5930991234567",
            "description": "Teléfono con símbolos"
        },
        {
            "input": "Precio: $100.50 USD",
            "expected": "Precio 10050 USD",
            "description": "Precio con símbolos monetarios"
        },
        {
            "input": "Dirección: Calle #25, Av. Principal",
            "expected": "Dirección Calle 25 Av Principal",
            "description": "Dirección con #, comas"
        },
        {
            "input": "Comentario:\nLínea 1\nLínea 2\nLínea 3",
            "expected": "Comentario\nLínea 1\nLínea 2\nLínea 3",
            "description": "Texto con saltos de línea (deben preservarse)"
        },
        {
            "input": "Código: ABC-123_XYZ",
            "expected": "Código ABC123XYZ",
            "description": "Código con guiones y guión bajo (eliminados)"
        },
        {
            "input": "50%",
            "expected": "50",
            "description": "Porcentaje"
        },
        {
            "input": "Normal text 123",
            "expected": "Normal text 123",
            "description": "Texto sin caracteres especiales"
        },
        {
            "input": "Áéíóú ÁÉÍÓÚ ñÑ",
            "expected": "Áéíóú ÁÉÍÓÚ ñÑ",
            "description": "Acentos y eñes (deben mantenerse)"
        },
        {
            "input": "!@#$%^&*()[]{}|\\/<>?",
            "expected": "",
            "description": "Solo símbolos especiales (resultado vacío)"
        }
    ]
    
    print("\n🧪 Casos de prueba:")
    print("-" * 80)
    
    all_passed = True
    for idx, test in enumerate(test_cases, 1):
        result = JSONTransformer.sanitize_string(test["input"])
        passed = result == test["expected"]
        
        status = "✅" if passed else "❌"
        print(f"\n{status} Test {idx}: {test['description']}")
        print(f"   Input:    '{test['input']}'")
        print(f"   Expected: '{test['expected']}'")
        print(f"   Got:      '{result}'")
        
        if not passed:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ TODOS LOS TESTS DE SANITIZACIÓN PASARON")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
    print("="*80)
    
    return all_passed


def test_sanitize_in_transform():
    """
    Prueba la sanitización dentro del proceso de transformación
    """
    print("\n" + "="*80)
    print("TEST: Sanitización en Transformación de Campos")
    print("="*80)
    
    # Caso 1: Campo con sanitize=True (default)
    print("\n📋 Caso 1: Campo con sanitize=True (default)")
    print("-" * 80)
    
    field_mapping_sanitize = FieldMapping(
        source="nombre",
        type="string",
        default=None,
        apply_uppercase=True,
        sanitize=True  # Default
    )
    
    value = "Juan Pérez @ #123"
    result = JSONTransformer.convert_value(value, field_mapping_sanitize, None)
    expected = "JUAN PÉREZ  123"  # Sanitizado + uppercase (mantiene acentos)
    
    print(f"Input:    '{value}'")
    print(f"Expected: '{expected}'")
    print(f"Got:      '{result}'")
    
    if result == expected:
        print("✅ Sanitización + Uppercase funciona correctamente")
        case1_passed = True
    else:
        print("❌ Resultado incorrecto")
        case1_passed = False
    
    # Caso 2: Campo con sanitize=False
    print("\n📋 Caso 2: Campo con sanitize=False")
    print("-" * 80)
    
    field_mapping_no_sanitize = FieldMapping(
        source="email",
        type="string",
        default=None,
        apply_uppercase=False,
        sanitize=False  # No sanitizar
    )
    
    value = "usuario@example.com"
    result = JSONTransformer.convert_value(value, field_mapping_no_sanitize, None)
    expected = "usuario@example.com"  # Sin cambios
    
    print(f"Input:    '{value}'")
    print(f"Expected: '{expected}'")
    print(f"Got:      '{result}'")
    
    if result == expected:
        print("✅ sanitize=False preserva caracteres especiales")
        case2_passed = True
    else:
        print("❌ Resultado incorrecto")
        case2_passed = False
    
    # Caso 3: Campo con sanitize=True pero sin uppercase
    print("\n📋 Caso 3: Campo con sanitize=True, apply_uppercase=False")
    print("-" * 80)
    
    field_mapping_sanitize_no_upper = FieldMapping(
        source="descripcion",
        type="string",
        default=None,
        apply_uppercase=False,
        sanitize=True
    )
    
    value = "Texto con símbolos: $100 & más"
    result = JSONTransformer.convert_value(value, field_mapping_sanitize_no_upper, None)
    expected = "Texto con símbolos 100  más"  # Sanitizado sin uppercase (mantiene acentos)
    
    print(f"Input:    '{value}'")
    print(f"Expected: '{expected}'")
    print(f"Got:      '{result}'")
    
    if result == expected:
        print("✅ Sanitización sin uppercase funciona correctamente")
        case3_passed = True
    else:
        print("❌ Resultado incorrecto")
        case3_passed = False
    
    # Caso 4: Campo tipo email con sanitize=True
    print("\n📋 Caso 4: Campo tipo 'email' con sanitize=True")
    print("-" * 80)
    
    field_mapping_email = FieldMapping(
        source="correo",
        type="email",
        default=None,
        sanitize=True  # Para emails debería ser False en YAMLs reales
    )
    
    value = "test@example.com"
    result = JSONTransformer.convert_value(value, field_mapping_email, None)
    expected = "testexamplecom"  # Sanitizado (@ y . eliminados)
    
    print(f"Input:    '{value}'")
    print(f"Expected: '{expected}'")
    print(f"Got:      '{result}'")
    
    if result == expected:
        print("✅ Email sanitizado (RECORDATORIO: usar sanitize=False en YAMLs para emails)")
        case4_passed = True
    else:
        print("❌ Resultado incorrecto")
        case4_passed = False
    
    print("\n" + "="*80)
    all_cases = all([case1_passed, case2_passed, case3_passed, case4_passed])
    if all_cases:
        print("✅ TODOS LOS TESTS DE TRANSFORMACIÓN PASARON")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
    print("="*80)
    
    return all_cases


def main():
    """Ejecuta todos los tests"""
    print("\n" + "🧪" * 40)
    print(" " * 15 + "SUITE DE TESTS: SANITIZACIÓN")
    print("🧪" * 40 + "\n")
    
    test1_passed = test_sanitize_string()
    test2_passed = test_sanitize_in_transform()
    
    print("\n" + "="*80)
    print("RESUMEN FINAL")
    print("="*80)
    print(f"Test 1 (sanitize_string): {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Test 2 (transform):       {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print("="*80)
    
    if test1_passed and test2_passed:
        print("\n🎉 TODOS LOS TESTS PASARON EXITOSAMENTE 🎉\n")
        return True
    else:
        print("\n❌ ALGUNOS TESTS FALLARON\n")
        return False


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
