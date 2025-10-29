#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar locais que aparecem com múltiplas coordenadas diferentes.

Este script analisa o arquivo locations.json e identifica:
1. Locais que aparecem mais de uma vez com coordenadas diferentes
2. Calcula a distância entre as coordenadas diferentes
3. Gera relatório detalhado das inconsistências

Executar: python public/check_duplicate_locations.py
"""

import json
import math
from collections import defaultdict
from typing import Dict, List, Tuple, Any

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula a distância entre duas coordenadas em metros usando a fórmula de Haversine.
    """
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

def analyze_duplicate_locations(locations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Analisa locais que aparecem com coordenadas diferentes.
    """
    # Agrupar por nome do local
    locations_by_name = defaultdict(list)
    
    for location in locations:
        local_name = location.get('local', '').strip()
        if local_name:
            locations_by_name[local_name].append(location)
    
    # Filtrar locais com múltiplas ocorrências
    duplicates = {}
    
    for local_name, occurrences in locations_by_name.items():
        if len(occurrences) > 1:
            # Verificar se há coordenadas diferentes
            unique_coords = set()
            for occurrence in occurrences:
                lat = occurrence.get('latitude')
                lon = occurrence.get('longitude')
                if lat is not None and lon is not None:
                    # Arredondar para 5 casas decimais para evitar diferenças mínimas
                    unique_coords.add((round(lat, 5), round(lon, 5)))
            
            # Se há mais de uma coordenada única, é um local com coordenadas diferentes
            if len(unique_coords) > 1:
                duplicates[local_name] = occurrences
    
    return duplicates

def generate_detailed_report(duplicates: Dict[str, List[Dict[str, Any]]]) -> None:
    """
    Gera relatório detalhado das inconsistências encontradas.
    """
    print("\n" + "="*80)
    print("RELATÓRIO DE LOCAIS COM COORDENADAS DIFERENTES")
    print("="*80)
    
    if not duplicates:
        print("\n✓ Nenhum local encontrado com coordenadas diferentes!")
        print("  Todos os locais têm coordenadas consistentes.")
        return
    
    total_locations = len(duplicates)
    total_occurrences = sum(len(occurrences) for occurrences in duplicates.values())
    
    print(f"\n📊 RESUMO:")
    print(f"   • {total_locations} locais com coordenadas diferentes")
    print(f"   • {total_occurrences} registros afetados")
    print(f"\n" + "-"*80)
    
    # Ordenar por número de ocorrências (mais problemáticos primeiro)
    sorted_duplicates = sorted(duplicates.items(), 
                              key=lambda x: len(x[1]), 
                              reverse=True)
    
    for i, (local_name, occurrences) in enumerate(sorted_duplicates, 1):
        print(f"\n{i}. 🏥 {local_name}")
        print(f"   📍 {len(occurrences)} registros com coordenadas diferentes")
        
        # Extrair coordenadas únicas
        coord_groups = defaultdict(list)
        for occurrence in occurrences:
            lat = occurrence.get('latitude')
            lon = occurrence.get('longitude')
            if lat is not None and lon is not None:
                coord_key = (round(lat, 5), round(lon, 5))
                coord_groups[coord_key].append(occurrence)
        
        print(f"   🗺️  {len(coord_groups)} coordenadas diferentes:")
        
        coords_list = list(coord_groups.keys())
        
        for j, (lat, lon) in enumerate(coords_list, 1):
            records = coord_groups[(lat, lon)]
            disciplinas = set(r.get('disciplina', 'N/A') for r in records)
            enderecos = set(r.get('endereco', 'N/A') for r in records)
            
            print(f"     Coordenada {j}: ({lat}, {lon})")
            print(f"       • {len(records)} registro(s)")
            print(f"       • Disciplinas: {', '.join(sorted(disciplinas))}")
            
            # Mostrar endereços se forem diferentes
            if len(enderecos) > 1:
                print(f"       ⚠️  Endereços diferentes:")
                for endereco in sorted(enderecos):
                    print(f"          - {endereco}")
            else:
                print(f"       • Endereço: {list(enderecos)[0]}")
        
        # Calcular distâncias entre coordenadas
        if len(coords_list) > 1:
            print(f"   📏 Distâncias entre coordenadas:")
            for j in range(len(coords_list)):
                for k in range(j + 1, len(coords_list)):
                    lat1, lon1 = coords_list[j]
                    lat2, lon2 = coords_list[k]
                    distance = calculate_distance(lat1, lon1, lat2, lon2)
                    
                    if distance < 1000:
                        dist_str = f"{distance:.1f}m"
                    else:
                        dist_str = f"{distance/1000:.2f}km"
                    
                    # Classificar a distância
                    if distance < 100:
                        status = "✓ Pequena"
                    elif distance < 1000:
                        status = "⚠️ Moderada"
                    else:
                        status = "❌ Grande"
                    
                    print(f"     Coord {j+1} ↔ Coord {k+1}: {dist_str} ({status})")
        
        print("-" * 60)

def generate_summary_statistics(duplicates: Dict[str, List[Dict[str, Any]]]) -> None:
    """
    Gera estatísticas resumidas.
    """
    if not duplicates:
        return
    
    print(f"\n📈 ESTATÍSTICAS DETALHADAS:")
    
    # Estatísticas de distância
    all_distances = []
    locations_by_distance_category = {'pequena': 0, 'moderada': 0, 'grande': 0}
    
    for local_name, occurrences in duplicates.items():
        coord_groups = defaultdict(list)
        for occurrence in occurrences:
            lat = occurrence.get('latitude')
            lon = occurrence.get('longitude')
            if lat is not None and lon is not None:
                coord_key = (round(lat, 5), round(lon, 5))
                coord_groups[coord_key].append(occurrence)
        
        coords_list = list(coord_groups.keys())
        max_distance = 0
        
        if len(coords_list) > 1:
            for j in range(len(coords_list)):
                for k in range(j + 1, len(coords_list)):
                    lat1, lon1 = coords_list[j]
                    lat2, lon2 = coords_list[k]
                    distance = calculate_distance(lat1, lon1, lat2, lon2)
                    all_distances.append(distance)
                    max_distance = max(max_distance, distance)
        
        # Categorizar por maior distância
        if max_distance < 100:
            locations_by_distance_category['pequena'] += 1
        elif max_distance < 1000:
            locations_by_distance_category['moderada'] += 1
        else:
            locations_by_distance_category['grande'] += 1
    
    if all_distances:
        avg_distance = sum(all_distances) / len(all_distances)
        max_distance = max(all_distances)
        min_distance = min(all_distances)
        
        print(f"   • Distância média entre coordenadas: {avg_distance:.1f}m")
        print(f"   • Distância máxima: {max_distance:.1f}m")
        print(f"   • Distância mínima: {min_distance:.1f}m")
    
    print(f"\n📊 CLASSIFICAÇÃO POR DISTÂNCIA:")
    print(f"   • Diferenças pequenas (<100m): {locations_by_distance_category['pequena']} locais")
    print(f"   • Diferenças moderadas (100m-1km): {locations_by_distance_category['moderada']} locais")
    print(f"   • Diferenças grandes (>1km): {locations_by_distance_category['grande']} locais")

def export_results_to_json(duplicates: Dict[str, List[Dict[str, Any]]], output_file: str) -> None:
    """
    Exporta os resultados para um arquivo JSON para análise posterior.
    """
    if not duplicates:
        return
    
    export_data = {}
    
    for local_name, occurrences in duplicates.items():
        coord_groups = defaultdict(list)
        for occurrence in occurrences:
            lat = occurrence.get('latitude')
            lon = occurrence.get('longitude')
            if lat is not None and lon is not None:
                coord_key = (round(lat, 5), round(lon, 5))
                coord_groups[coord_key].append(occurrence)
        
        coords_list = list(coord_groups.keys())
        coord_details = []
        
        for lat, lon in coords_list:
            records = coord_groups[(lat, lon)]
            coord_details.append({
                'latitude': lat,
                'longitude': lon,
                'record_count': len(records),
                'disciplinas': list(set(r.get('disciplina', 'N/A') for r in records)),
                'enderecos': list(set(r.get('endereco', 'N/A') for r in records)),
                'registros': records
            })
        
        # Calcular distâncias
        distances = []
        if len(coords_list) > 1:
            for j in range(len(coords_list)):
                for k in range(j + 1, len(coords_list)):
                    lat1, lon1 = coords_list[j]
                    lat2, lon2 = coords_list[k]
                    distance = calculate_distance(lat1, lon1, lat2, lon2)
                    distances.append({
                        'coord1': {'latitude': lat1, 'longitude': lon1},
                        'coord2': {'latitude': lat2, 'longitude': lon2},
                        'distance_meters': round(distance, 1)
                    })
        
        export_data[local_name] = {
            'total_records': len(occurrences),
            'unique_coordinates': len(coords_list),
            'coordinates': coord_details,
            'distances': distances
        }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(export_data, file, ensure_ascii=False, indent=2)
        print(f"\n💾 Resultados exportados para: {output_file}")
    except Exception as e:
        print(f"\n❌ Erro ao exportar resultados: {e}")

def main():
    """
    Função principal do script.
    """
    print("🔍 VERIFICADOR DE LOCAIS COM COORDENADAS DIFERENTES")
    print("=" * 60)
    
    # Carregar dados
    locations_file = "locations.json"
    locations_data = load_locations_data(locations_file)
    
    if not locations_data:
        print("❌ Não foi possível carregar os dados!")
        return
    
    # Analisar duplicatas
    print(f"\n🔎 Analisando {len(locations_data)} registros...")
    duplicates = analyze_duplicate_locations(locations_data)
    
    # Gerar relatório
    generate_detailed_report(duplicates)
    
    # Gerar estatísticas
    generate_summary_statistics(duplicates)
    
    # Exportar resultados
    if duplicates:
        export_results_to_json(duplicates, "duplicate_coordinates_report.json")
    
    print(f"\n" + "="*80)
    print("✅ ANÁLISE CONCLUÍDA!")
    
    if duplicates:
        print("⚠️  Foram encontradas inconsistências de coordenadas.")
        print("📋 Recomendações:")
        print("   1. Revisar locais com diferenças grandes (>1km)")
        print("   2. Verificar se são realmente locais diferentes")
        print("   3. Padronizar coordenadas quando necessário")
        print("   4. Considerar usar endereços como critério de desambiguação")
    else:
        print("✅ Nenhuma inconsistência encontrada!")
    
    print("="*80)

if __name__ == "__main__":
    main()
