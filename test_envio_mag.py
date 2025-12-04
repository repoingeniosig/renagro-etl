#!/usr/bin/env python3
"""
Script de prueba para el procesador de envío a MAG
Permite probar la generación de JSON para un ID específico
"""
import sys
import json
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import config
from src.logger import envio_mag_logger
from src.batch_processor_envio_mag import batch_processor_envio_mag
from src.mapping_loader_envio_mag import mapping_loader_envio_mag


def test_single_boleta(boleta_id: int):
    """
    Prueba la generación de JSON para un ID de boleta específico
    
    Args:
        boleta_id: ID de la boleta a procesar
    """
    envio_mag_logger.info(f"Probando generación de JSON para boleta_id={boleta_id}")
    
    # Forzar debug output
    config.DEBUG_JSON_OUTPUT = True
    batch_processor_envio_mag.debug_json_output = True
    
    # Crear directorio temporal si no existe
    batch_processor_envio_mag.temp_output_dir.mkdir(exist_ok=True, parents=True)
    
    # Obtener datos para un solo registro
    boletas_data, all_related_data = batch_processor_envio_mag.fetch_all_data_for_batch([boleta_id])
    
    if not boletas_data:
        envio_mag_logger.error(f"No se encontró boleta con ID {boleta_id}")
        return
    
    boleta_row = boletas_data[0]
    
    # Construir JSON
    json_data = batch_processor_envio_mag.build_json_for_boleta(boleta_row, all_related_data)
    
    # Guardar para debug
    batch_processor_envio_mag.save_debug_json(boleta_id, json_data)
    
    # Mostrar en consola
    print("\n" + "=" * 80)
    print(f"JSON generado para boleta_id={boleta_id}")
    print("=" * 80)
    print(json.dumps(json_data, indent=2, ensure_ascii=False))
    print("=" * 80)
    
    envio_mag_logger.info(f"JSON guardado en: {batch_processor_envio_mag.temp_output_dir / f'boleta_{boleta_id}.json'}")


def test_mappings():
    """Prueba la carga de mapeos YAML"""
    print("\n" + "=" * 80)
    print("Probando carga de mapeos YAML")
    print("=" * 80)
    
    # Cargar todos los mapeos
    all_mappings = mapping_loader_envio_mag.load_all_mappings_recursive('main.yml')
    
    print(f"\nTotal de archivos YAML cargados: {len(all_mappings)}")
    print("\nArchivos cargados:")
    for yaml_file, entity_mapping in all_mappings.items():
        print(f"  - {yaml_file}")
        print(f"    Entity: {entity_mapping.entity}")
        print(f"    Table: {entity_mapping.table}")
        print(f"    Fields: {len(entity_mapping.fields)}")
        
        # Mostrar referencias
        references = []
        for field_name, field_mapping in entity_mapping.fields.items():
            if field_mapping.reference:
                references.append(f"{field_name} -> {field_mapping.reference}")
        
        if references:
            print(f"    References:")
            for ref in references:
                print(f"      - {ref}")
        print()
    
    print("=" * 80)


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Prueba el procesador de envío a MAG')
    parser.add_argument(
        'command',
        choices=['test-json', 'test-mappings', 'process-batch'],
        help='Comando a ejecutar'
    )
    parser.add_argument(
        '--id',
        type=int,
        help='ID de boleta para test-json'
    )
    
    args = parser.parse_args()
    
    if args.command == 'test-json':
        if not args.id:
            parser.error('--id es requerido para test-json')
        test_single_boleta(args.id)
    
    elif args.command == 'test-mappings':
        test_mappings()
    
    elif args.command == 'process-batch':
        # Procesar un lote completo
        count, json_list = batch_processor_envio_mag.process_batch()
        print(f"\nProcesados {count} registros")
        print(f"JSONs generados: {len(json_list)}")


if __name__ == "__main__":
    main()
