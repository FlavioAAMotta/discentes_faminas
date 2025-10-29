#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para padronizar coordenadas de locais no arquivo locations.json.

Este script:
1. Identifica locais com múltiplas coordenadas
2. Seleciona a coordenada "padrão" para cada local (mais frequente ou primeira válida)
3. Aplica a padronização em todos os registros do mesmo local
4. Gera backup dos dados originais
5. Cria novo arquivo com coordenadas padronizadas

Executar: python public/standardize_coordinates.py
"""

import json
import math
import shutil
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any, Optional

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula a distância entre duas coordenadas em metros usando a fórmula de Haversine.
    """
    if lat1 == lat2 and lon1 == lon2:
        return 0.0
    
    # Raio da Terra em metros
    R = 6371000
    
    # Converter graus para radianos
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Fórmula de Haversine
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance

def is_valid_coordinate(lat: float, lon: float) -> bool:
    """
    Verifica se uma coordenada é válida (dentro dos limites do Brasil).
    """
    # Limites aproximados do Brasil
    # Latitude: -33.8 (sul) a 5.3 (norte)
    # Longitude: -73.9 (oeste) a -34.8 (leste)
    
    if not (-34 <= lat <= 6):
        return False
    if not (-74 <= lon <= -34):
        return False
    
    return True

def load_locations_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Carrega os dados do arquivo JSON.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        print(f"✓ Carregados {len(data)} registros de {file_path}")
        return data
    except FileNotFoundError:
        print(f"✗ Arquivo {file_path} não encontrado!")
        return []
    except json.JSONDecodeError as e:
        print(f"✗ Erro ao decodificar JSON: {e}")
        return []
    except Exception as e:
        print(f"✗ Erro ao carregar arquivo: {e}")
        return []

def analyze_coordinates_by_location(locations: List[Dict[str, Any]]) -> Dict[str, Dict]:
    """
    Analisa coordenadas por local e determina a coordenada padrão para cada um.
    """
    locations_analysis = defaultdict(lambda: {
        'coordinates': [],
        'records': [],
        'coordinate_counts': Counter(),
        'valid_coordinates': [],
        'invalid_coordinates': []
    })
    
    # Agrupar registros por local
    for record in locations:
        local_name = record.get('local', '').strip()
        if not local_name:
            continue
            
        lat = record.get('latitude')
        lon = record.get('longitude')
        
        if lat is not None and lon is not None:
            coord_tuple = (round(lat, 5), round(lon, 5))
            
            locations_analysis[local_name]['coordinates'].append(coord_tuple)
            locations_analysis[local_name]['records'].append(record)
            locations_analysis[local_name]['coordinate_counts'][coord_tuple] += 1
            
            # Verificar se a coordenada é válida
            if is_valid_coordinate(lat, lon):
                locations_analysis[local_name]['valid_coordinates'].append(coord_tuple)
            else:
                locations_analysis[local_name]['invalid_coordinates'].append(coord_tuple)
    
    # Determinar coordenada padrão para cada local
    standardization_plan = {}
    
    for local_name, data in locations_analysis.items():
        unique_coords = list(set(data['coordinates']))
        
        # Se há apenas uma coordenada única, usar ela
        if len(unique_coords) == 1:
            standard_coord = unique_coords[0]
            reason = "única coordenada"
        
        # Se há múltiplas coordenadas
        else:
            # Primeiro, tentar usar coordenadas válidas
            valid_coords = list(set(data['valid_coordinates']))
            
            if valid_coords:
                if len(valid_coords) == 1:
                    standard_coord = valid_coords[0]
                    reason = "única coordenada válida"
                else:
                    # Usar a coordenada válida mais frequente
                    valid_counts = {coord: data['coordinate_counts'][coord] 
                                   for coord in valid_coords}
                    standard_coord = max(valid_counts.keys(), key=valid_counts.get)
                    reason = f"coordenada válida mais frequente ({valid_counts[standard_coord]} ocorrências)"
            else:
                # Se não há coordenadas válidas, usar a mais frequente
                standard_coord = data['coordinate_counts'].most_common(1)[0][0]
                reason = f"coordenada mais frequente ({data['coordinate_counts'][standard_coord]} ocorrências) - TODAS INVÁLIDAS"
        
        standardization_plan[local_name] = {
            'standard_coordinate': standard_coord,
            'reason': reason,
            'total_coordinates': len(unique_coords),
            'total_records': len(data['records']),
            'coordinate_distribution': dict(data['coordinate_counts']),
            'needs_standardization': len(unique_coords) > 1,
            'has_invalid_coordinates': len(data['invalid_coordinates']) > 0,
            'original_coordinates': unique_coords
        }
    
    return standardization_plan

def apply_standardization(locations: List[Dict[str, Any]], 
                         standardization_plan: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """
    Aplica a padronização de coordenadas aos registros.
    """
    standardized_locations = []
    changes_count = 0
    
    for record in locations:
        local_name = record.get('local', '').strip()
        
        if local_name in standardization_plan:
            plan = standardization_plan[local_name]
            standard_lat, standard_lon = plan['standard_coordinate']
            
            # Verificar se precisa de mudança
            current_lat = record.get('latitude')
            current_lon = record.get('longitude')
            
            if (current_lat != standard_lat or current_lon != standard_lon):
                # Criar nova cópia do registro com coordenadas padronizadas
                new_record = record.copy()
                new_record['latitude'] = standard_lat
                new_record['longitude'] = standard_lon
                standardized_locations.append(new_record)
                changes_count += 1
            else:
                # Coordenadas já estão corretas
                standardized_locations.append(record.copy())
        else:
            # Local não encontrado no plano (não deveria acontecer)
            standardized_locations.append(record.copy())
    
    print(f"✓ Aplicada padronização em {changes_count} registros")
    return standardized_locations

def create_backup(file_path: str) -> str:
    """
    Cria backup do arquivo original.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    
    try:
        shutil.copy2(file_path, backup_path)
        print(f"✓ Backup criado: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"✗ Erro ao criar backup: {e}")
        return ""

def save_standardized_data(data: List[Dict[str, Any]], output_path: str) -> bool:
    """
    Salva os dados padronizados em arquivo.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        print(f"✓ Dados padronizados salvos em: {output_path}")
        return True
    except Exception as e:
        print(f"✗ Erro ao salvar dados padronizados: {e}")
        return False

def generate_standardization_report(standardization_plan: Dict[str, Dict]) -> None:
    """
    Gera relatório detalhado da padronização.
    """
    print("\n" + "="*80)
    print("RELATÓRIO DE PADRONIZAÇÃO DE COORDENADAS")
    print("="*80)
    
    # Estatísticas gerais
    total_locations = len(standardization_plan)
    locations_needing_standardization = sum(1 for plan in standardization_plan.values() 
                                           if plan['needs_standardization'])
    locations_with_invalid = sum(1 for plan in standardization_plan.values() 
                                if plan['has_invalid_coordinates'])
    
    print(f"\n📊 RESUMO GERAL:")
    print(f"   • Total de locais: {total_locations}")
    print(f"   • Locais que precisam padronização: {locations_needing_standardization}")
    print(f"   • Locais com coordenadas inválidas: {locations_with_invalid}")
    
    if locations_needing_standardization == 0:
        print("\n✅ Nenhuma padronização necessária!")
        return
    
    print(f"\n" + "-"*80)
    print("DETALHES DA PADRONIZAÇÃO:")
    
    # Ordenar por prioridade (locais com mais problemas primeiro)
    sorted_locations = sorted(
        [(name, plan) for name, plan in standardization_plan.items() 
         if plan['needs_standardization']],
        key=lambda x: (x[1]['has_invalid_coordinates'], x[1]['total_coordinates']),
        reverse=True
    )
    
    for i, (local_name, plan) in enumerate(sorted_locations, 1):
        print(f"\n{i}. 🏥 {local_name}")
        print(f"   📍 {plan['total_coordinates']} coordenadas diferentes → 1 coordenada padrão")
        print(f"   📊 {plan['total_records']} registros afetados")
        
        # Mostrar coordenada selecionada
        standard_lat, standard_lon = plan['standard_coordinate']
        print(f"   ✅ Coordenada padrão: ({standard_lat}, {standard_lon})")
        print(f"   📋 Critério: {plan['reason']}")
        
        # Mostrar distribuição das coordenadas
        if len(plan['coordinate_distribution']) > 1:
            print(f"   📈 Distribuição original:")
            for coord, count in plan['coordinate_distribution'].items():
                marker = " ← PADRÃO" if coord == plan['standard_coordinate'] else ""
                print(f"      • {coord}: {count} registro(s){marker}")
        
        # Alertas para coordenadas inválidas
        if plan['has_invalid_coordinates']:
            print(f"   ⚠️  Este local continha coordenadas inválidas!")
        
        print("-" * 60)

def save_standardization_report(standardization_plan: Dict[str, Dict], 
                               output_file: str) -> None:
    """
    Salva relatório de padronização em JSON.
    """
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_locations': len(standardization_plan),
            'locations_needing_standardization': sum(1 for plan in standardization_plan.values() 
                                                    if plan['needs_standardization']),
            'locations_with_invalid_coordinates': sum(1 for plan in standardization_plan.values() 
                                                     if plan['has_invalid_coordinates'])
        },
        'standardization_details': standardization_plan
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(report_data, file, ensure_ascii=False, indent=2)
        print(f"\n💾 Relatório de padronização salvo em: {output_file}")
    except Exception as e:
        print(f"\n❌ Erro ao salvar relatório: {e}")

def main():
    """
    Função principal do script.
    """
    print("🔧 PADRONIZADOR DE COORDENADAS POR LOCAL")
    print("=" * 60)
    
    # Configurações
    input_file = "locations.json"
    output_file = "locations_standardized.json"
    report_file = "standardization_report.json"
    
    # Carregar dados
    print(f"\n📂 Carregando dados de {input_file}...")
    locations_data = load_locations_data(input_file)
    
    if not locations_data:
        print("❌ Não foi possível carregar os dados!")
        return
    
    # Analisar coordenadas por local
    print(f"\n🔍 Analisando coordenadas por local...")
    standardization_plan = analyze_coordinates_by_location(locations_data)
    
    # Gerar relatório
    generate_standardization_report(standardization_plan)
    
    # Verificar se há padronização necessária
    locations_needing_standardization = sum(1 for plan in standardization_plan.values() 
                                           if plan['needs_standardization'])
    
    if locations_needing_standardization == 0:
        print(f"\n" + "="*80)
        print("✅ PADRONIZAÇÃO CONCLUÍDA!")
        print("📝 Nenhuma mudança necessária - todas as coordenadas já estão padronizadas.")
        print("="*80)
        return
    
    # Criar backup do arquivo original
    print(f"\n💾 Criando backup do arquivo original...")
    backup_path = create_backup(input_file)
    
    if not backup_path:
        print("❌ Falha ao criar backup! Abortando padronização por segurança.")
        return
    
    # Aplicar padronização
    print(f"\n🔧 Aplicando padronização...")
    standardized_data = apply_standardization(locations_data, standardization_plan)
    
    # Salvar dados padronizados
    print(f"\n💾 Salvando dados padronizados...")
    if save_standardized_data(standardized_data, output_file):
        print(f"✅ Dados padronizados salvos com sucesso!")
    else:
        print(f"❌ Falha ao salvar dados padronizados!")
        return
    
    # Salvar relatório
    save_standardization_report(standardization_plan, report_file)
    
    print(f"\n" + "="*80)
    print("✅ PADRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
    print(f"📂 Arquivo original: {input_file} (backup: {backup_path})")
    print(f"📂 Arquivo padronizado: {output_file}")
    print(f"📂 Relatório: {report_file}")
    print(f"\n📋 PRÓXIMOS PASSOS:")
    print(f"   1. Revisar o arquivo padronizado: {output_file}")
    print(f"   2. Se estiver satisfeito, substituir o original:")
    print(f"      mv {output_file} {input_file}")
    print(f"   3. Ou usar o script de substituição automática")
    print("="*80)

if __name__ == "__main__":
    main()

