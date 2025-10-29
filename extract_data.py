#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para extrair dados do arquivo CSV dados_processados.csv
e gerar os arquivos JSON na mesma estrutura dos existentes.

Estrutura do CSV:
Semestre,Disciplina,Turma,Período,Grupos,Preceptor,Estudante,Categoria,Dia,Turno,Rodízio,Local,Local/End,Latitude,Longitude,Período_Original

Estrutura do locations.json:
{
  "id": int,
  "local": string,
  "endereco": string,
  "disciplina": string,
  "preceptor": string,
  "estudante": int,
  "periodo_original": string,
  "turma": string,
  "categoria": string,
  "turno": string,
  "latitude": float,
  "longitude": float
}

Estrutura do filters.json:
{
  "disciplinas": [string],
  "periodos": [string],
  "preceptores": [string]
}
"""

import csv
import json
import os
from typing import List, Dict, Set, Any

def validate_coordinates(latitude: float, longitude: float) -> bool:
    """
    Valida se as coordenadas estão dentro dos limites esperados para o Brasil.
    Brasil: Latitude entre -33.75 e 5.27, Longitude entre -73.98 e -28.84
    """
    # Limites aproximados do Brasil com margem de segurança
    if not (-35 <= latitude <= 6):
        return False
    if not (-75 <= longitude <= -25):
        return False
    return True

def format_coordinates(lat_raw: float, lon_raw: float) -> tuple:
    """
    Formata coordenadas do CSV para o formato correto.
    Ex: -1959565 -> -19.59565, -198846 -> -19.8846
    """
    # Se o valor já está no formato correto (entre -100 e 100), não modificar
    if -100 <= lat_raw <= 100 and -100 <= lon_raw <= 100:
        return lat_raw, lon_raw
    
    # Função para formatar uma coordenada individual
    def format_single_coord(coord):
        # Converter para string para analisar os dígitos
        coord_str = str(int(abs(coord)))
        
        # Determinar quantos dígitos devem ser decimais
        if len(coord_str) >= 7:  # -1959565 (7 dígitos) -> -19.59565
            decimal_digits = 5
        elif len(coord_str) == 6:  # -198846 (6 dígitos) -> -19.8846  
            decimal_digits = 4
        elif len(coord_str) >= 4:  # Outros casos
            decimal_digits = len(coord_str) - 2
        else:
            return coord  # Muito pequeno, não modificar
        
        divisor = 10 ** decimal_digits
        return coord / divisor
    
    latitude = format_single_coord(lat_raw)
    longitude = format_single_coord(lon_raw)
    
    return latitude, longitude

def read_csv_data(csv_file_path: str) -> List[Dict[str, Any]]:
    """
    Lê o arquivo CSV e retorna uma lista de dicionários com os dados.
    """
    data = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            # Usar DictReader para mapear automaticamente as colunas
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):  # Começar do 2 porque linha 1 é header
                try:
                    # Validar campos obrigatórios
                    if not row.get('Local') or not row.get('Local/End'):
                        print(f"Linha {row_num}: Local ou endereço vazio, pulando...")
                        continue
                    
                    if not row.get('Latitude') or not row.get('Longitude'):
                        print(f"Linha {row_num}: Coordenadas vazias, pulando...")
                        continue
                    
                    # Converter coordenadas para float com formatação correta
                    try:
                        # As coordenadas no CSV estão sem ponto decimal
                        # Ex: -1959565 deve ser -19.59565
                        lat_raw = float(row['Latitude'])
                        lon_raw = float(row['Longitude'])
                        
                        # Aplicar formatação correta das coordenadas
                        latitude, longitude = format_coordinates(lat_raw, lon_raw)
                        
                        # Validar se as coordenadas estão dentro dos limites do Brasil
                        # Ser mais flexível com a validação
                        if not validate_coordinates(latitude, longitude):
                            print(f"Linha {row_num}: Coordenadas possivelmente inválidas ({latitude}, {longitude}), mas incluindo...")
                            # Não pular, apenas avisar
                        
                    except (ValueError, TypeError):
                        print(f"Linha {row_num}: Erro ao converter coordenadas, pulando...")
                        continue
                    
                    # Converter número de estudantes para int
                    try:
                        estudante = int(row.get('Estudante', 0))
                    except (ValueError, TypeError):
                        print(f"Linha {row_num}: Erro ao converter número de estudantes, usando 0")
                        estudante = 0
                    
                    # Montar registro no formato do locations.json
                    location_data = {
                        "id": row_num - 1,  # ID sequencial começando do 1
                        "local": row['Local'].strip(),
                        "endereco": row['Local/End'].strip(),
                        "disciplina": row.get('Disciplina', '').strip(),
                        "preceptor": row.get('Preceptor', '').strip(),
                        "estudante": estudante,
                        "periodo_original": row.get('Período_Original', '').strip(),
                        "turma": row.get('Turma', '').strip(),
                        "categoria": row.get('Categoria', '').strip(),
                        "turno": row.get('Turno', '').strip(),
                        "latitude": latitude,
                        "longitude": longitude
                    }
                    
                    data.append(location_data)
                    
                except Exception as e:
                    print(f"Erro na linha {row_num}: {e}")
                    continue
    
    except FileNotFoundError:
        print(f"Arquivo {csv_file_path} não encontrado!")
        return []
    except Exception as e:
        print(f"Erro ao ler arquivo CSV: {e}")
        return []
    
    print(f"Total de registros processados: {len(data)}")
    return data

def extract_filters_data(locations_data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Extrai os valores únicos para os filtros a partir dos dados de localização.
    """
    disciplinas: Set[str] = set()
    periodos: Set[str] = set()
    preceptores: Set[str] = set()
    
    for location in locations_data:
        # Disciplinas
        if location.get('disciplina'):
            disciplinas.add(location['disciplina'])
        
        # Períodos
        if location.get('periodo_original'):
            periodos.add(location['periodo_original'])
        
        # Preceptores
        if location.get('preceptor'):
            preceptores.add(location['preceptor'])
    
    # Converter sets para listas ordenadas
    filters_data = {
        "disciplinas": sorted(list(disciplinas)),
        "periodos": sorted(list(periodos)),
        "preceptores": sorted(list(preceptores))
    }
    
    print(f"Filtros extraídos:")
    print(f"  - {len(filters_data['disciplinas'])} disciplinas")
    print(f"  - {len(filters_data['periodos'])} períodos")
    print(f"  - {len(filters_data['preceptores'])} preceptores")
    
    return filters_data

def save_json_file(data: Any, file_path: str, indent: int = 2) -> bool:
    """
    Salva dados em um arquivo JSON.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=indent)
        print(f"Arquivo {file_path} salvo com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao salvar {file_path}: {e}")
        return False

def compare_with_existing(new_data: List[Dict], existing_file: str) -> None:
    """
    Compara os novos dados com o arquivo existente para identificar diferenças.
    """
    if not os.path.exists(existing_file):
        print(f"Arquivo {existing_file} não existe para comparação.")
        return
    
    try:
        with open(existing_file, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
        
        print(f"\nComparação com {existing_file}:")
        print(f"  - Registros existentes: {len(existing_data)}")
        print(f"  - Novos registros: {len(new_data)}")
        print(f"  - Diferença: {len(new_data) - len(existing_data)}")
        
        # Verificar alguns campos específicos para identificar discrepâncias
        if len(existing_data) > 0 and len(new_data) > 0:
            print(f"\nPrimeiro registro existente vs novo:")
            print(f"  Local: '{existing_data[0].get('local')}' vs '{new_data[0].get('local')}'")
            print(f"  Disciplina: '{existing_data[0].get('disciplina')}' vs '{new_data[0].get('disciplina')}'")
            
    except Exception as e:
        print(f"Erro ao comparar com arquivo existente: {e}")

def test_coordinate_conversion():
    """
    Testa a conversão de coordenadas com exemplos conhecidos.
    """
    print("=== Teste de Conversão de Coordenadas ===")
    
    test_cases = [
        (-1959565, -4390824, "CAS Norte - Policlínica Regional Norte (7 dígitos)"),
        (-1986977, -4389453, "UBS Novo Alvorada (7 dígitos)"),
        (-198846, -437984, "UBS Siderúrgica (6 dígitos)"),
        (-1988232, -4389812, "UBS Nova Vista (7 dígitos)"),
        (-1978835, -439401, "UBS Catumbi (6 dígitos)"),
        (-1975626, -4384725, "UBS Bom Jesus (7 dígitos)")
    ]
    
    for lat_raw, lon_raw, local in test_cases:
        lat_formatted, lon_formatted = format_coordinates(lat_raw, lon_raw)
        is_valid = validate_coordinates(lat_formatted, lon_formatted)
        
        print(f"Local: {local}")
        print(f"  Original: ({lat_raw}, {lon_raw})")
        print(f"  Formatado: ({lat_formatted}, {lon_formatted})")
        print(f"  Válido: {'✓' if is_valid else '✗'}")
        print()

def main():
    """
    Função principal do script.
    """
    print("=== Script de Extração de Dados dos Estágios FAMINAS ===\n")
    
    # Executar teste de coordenadas
    test_coordinate_conversion()
    
    # Caminhos dos arquivos
    csv_file = "public/dados_processados.csv"
    locations_output = "public/locations_new.json"
    filters_output = "public/filters_new.json"
    
    # Verificar se o arquivo CSV existe
    if not os.path.exists(csv_file):
        print(f"Erro: Arquivo {csv_file} não encontrado!")
        return
    
    # Ler dados do CSV
    print("1. Lendo dados do arquivo CSV...")
    locations_data = read_csv_data(csv_file)
    
    if not locations_data:
        print("Nenhum dado válido encontrado no CSV!")
        return
    
    # Extrair dados de filtros
    print("\n2. Extraindo dados para filtros...")
    filters_data = extract_filters_data(locations_data)
    
    # Salvar arquivos JSON
    print("\n3. Salvando arquivos JSON...")
    
    # Salvar locations
    if save_json_file(locations_data, locations_output):
        # Comparar com arquivo existente
        compare_with_existing(locations_data, "public/locations.json")
    
    # Salvar filters
    if save_json_file(filters_data, filters_output):
        # Comparar com arquivo existente
        compare_with_existing(filters_data, "public/filters.json")
    
    print(f"\n=== Processamento concluído ===")
    print(f"Novos arquivos gerados:")
    print(f"  - {locations_output}")
    print(f"  - {filters_output}")
    print(f"\nPara substituir os arquivos atuais, renomeie:")
    print(f"  mv {locations_output} public/locations.json")
    print(f"  mv {filters_output} public/filters.json")

if __name__ == "__main__":
    main()
