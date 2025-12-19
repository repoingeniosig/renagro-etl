#!/usr/bin/env python3
"""
Test para verificar el funcionamiento de condicionales 'when' en transformaciones
"""
import sys
from pathlib import Path

# Agregar raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.transformer import JSONTransformer
from src.mapping_loader import mapping_loader

def test_conditional_transformation():
    """
    Prueba la transformación condicional con 'when'
    """
    print("="*80)
    print("TEST: Transformación Condicional 'when'")
    print("="*80)
    
    # Cargar mappings de boletas
    mapping_dir = Path(__file__).parent.parent / 'mappings' / 'boletas'
    mapping_loader.set_mapping_dir(mapping_dir)
    mapping_loader.load_all_mappings()
    
    # Obtener mapping de bovinos
    bovinos_mapping = mapping_loader.entity_mappings.get('bovinos')
    
    if not bovinos_mapping:
        print("❌ No se encontró mapping de bovinos")
        return False
    
    # Caso 1: existe_ganado_bovino = "yes" (debe extraer valores)
    print("\n📋 Caso 1: existe_ganado_bovino = 'yes'")
    print("-" * 80)
    
    json_data_yes = {
        "capitulos_1_10_wrapper/productos_pecuarios_group/ganado_bovino_group/existe_ganado_bovino": "yes",
        "capitulos_1_10_wrapper/productos_pecuarios_group/ganado_bovino_group/total_bovino": 150,
        "capitulos_1_10_wrapper/productos_pecuarios_group/ganado_bovino_group/total_tenencia_bovino": 120,
    }
    
    # Verificar condición
    bov_total_ganado_field = bovinos_mapping.fields.get('bov_total_ganado')
    condition = bov_total_ganado_field.source['when']
    
    condition_met = JSONTransformer.evaluate_condition(
        json_data_yes,
        condition,
        bovinos_mapping.conversions
    )
    
    print(f"Condición evaluada: {condition_met}")
    print(f"  Campo condición: {condition['field']}")
    print(f"  Valor en JSON: 'yes'")
    print(f"  Conversión: yes_no_to_bool -> True")
    print(f"  Esperado: {condition['equals']}")
    
    if condition_met:
        print("✅ Condición CUMPLIDA")
    else:
        print("❌ Condición NO CUMPLIDA")
        return False
    
    # Transformar entidad completa
    row_yes = JSONTransformer.transform_entity(json_data_yes, bovinos_mapping)
    
    print(f"\nResultados transformación:")
    print(f"  bov_total_ganado: {row_yes.get('bov_total_ganado')} (esperado: 150)")
    print(f"  bov_total_ganado_prop: {row_yes.get('bov_total_ganado_prop')} (esperado: 120)")
    
    if row_yes.get('bov_total_ganado') == 150 and row_yes.get('bov_total_ganado_prop') == 120:
        print("✅ Valores extraídos correctamente")
    else:
        print("❌ Valores incorrectos")
        return False
    
    # Caso 2: existe_ganado_bovino = "no" (debe retornar null)
    print("\n📋 Caso 2: existe_ganado_bovino = 'no'")
    print("-" * 80)
    
    json_data_no = {
        "capitulos_1_10_wrapper/productos_pecuarios_group/ganado_bovino_group/existe_ganado_bovino": "no",
        "capitulos_1_10_wrapper/productos_pecuarios_group/ganado_bovino_group/total_bovino": 150,
        "capitulos_1_10_wrapper/productos_pecuarios_group/ganado_bovino_group/total_tenencia_bovino": 120,
    }
    
    condition_met_no = JSONTransformer.evaluate_condition(
        json_data_no,
        condition,
        bovinos_mapping.conversions
    )
    
    print(f"Condición evaluada: {condition_met_no}")
    print(f"  Campo condición: {condition['field']}")
    print(f"  Valor en JSON: 'no'")
    print(f"  Conversión: yes_no_to_bool -> False")
    print(f"  Esperado: {condition['equals']}")
    
    if not condition_met_no:
        print("✅ Condición NO CUMPLIDA (esperado)")
    else:
        print("❌ Condición CUMPLIDA (inesperado)")
        return False
    
    # Transformar entidad completa
    row_no = JSONTransformer.transform_entity(json_data_no, bovinos_mapping)
    
    print(f"\nResultados transformación:")
    print(f"  bov_total_ganado: {row_no.get('bov_total_ganado')} (esperado: None)")
    print(f"  bov_total_ganado_prop: {row_no.get('bov_total_ganado_prop')} (esperado: None)")
    
    if row_no.get('bov_total_ganado') is None and row_no.get('bov_total_ganado_prop') is None:
        print("✅ Valores null correctos (default)")
    else:
        print("❌ Valores incorrectos, deberían ser None")
        return False
    
    # Caso 3: campo no existe (debe retornar null)
    print("\n📋 Caso 3: existe_ganado_bovino NO existe en JSON")
    print("-" * 80)
    
    json_data_missing = {
        "capitulos_1_10_wrapper/productos_pecuarios_group/ganado_bovino_group/total_bovino": 150,
        "capitulos_1_10_wrapper/productos_pecuarios_group/ganado_bovino_group/total_tenencia_bovino": 120,
    }
    
    condition_met_missing = JSONTransformer.evaluate_condition(
        json_data_missing,
        condition,
        bovinos_mapping.conversions
    )
    
    print(f"Condición evaluada: {condition_met_missing}")
    print(f"  Campo condición: {condition['field']}")
    print(f"  Valor en JSON: None (no existe)")
    print(f"  Esperado: {condition['equals']}")
    
    if not condition_met_missing:
        print("✅ Condición NO CUMPLIDA (esperado)")
    else:
        print("❌ Condición CUMPLIDA (inesperado)")
        return False
    
    row_missing = JSONTransformer.transform_entity(json_data_missing, bovinos_mapping)
    
    print(f"\nResultados transformación:")
    print(f"  bov_total_ganado: {row_missing.get('bov_total_ganado')} (esperado: None)")
    print(f"  bov_total_ganado_prop: {row_missing.get('bov_total_ganado_prop')} (esperado: None)")
    
    if row_missing.get('bov_total_ganado') is None and row_missing.get('bov_total_ganado_prop') is None:
        print("✅ Valores null correctos (default)")
    else:
        print("❌ Valores incorrectos, deberían ser None")
        return False
    
    print("\n" + "="*80)
    print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
    print("="*80)
    
    return True


if __name__ == '__main__':
    try:
        success = test_conditional_transformation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
