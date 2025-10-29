#!/bin/bash

# Script para executar a extração de dados dos estágios FAMINAS
# Suporta tanto Python quanto Node.js

echo "=== Script de Extração de Dados dos Estágios FAMINAS ==="
echo ""

# Verificar se o arquivo CSV existe
if [ ! -f "public/dados_processados.csv" ]; then
    echo "Erro: Arquivo public/dados_processados.csv não encontrado!"
    exit 1
fi

# Função para executar com Python
run_python() {
    echo "Executando com Python..."
    if command -v python3 &> /dev/null; then
        python3 extract_data.py
    elif command -v python &> /dev/null; then
        python extract_data.py
    else
        echo "Python não encontrado no sistema!"
        return 1
    fi
}

# Função para executar com Node.js
run_node() {
    echo "Executando com Node.js..."
    if command -v node &> /dev/null; then
        node extract_data.js
    else
        echo "Node.js não encontrado no sistema!"
        return 1
    fi
}

# Verificar parâmetros da linha de comando
case "$1" in
    "python"|"py")
        run_python
        ;;
    "node"|"js")
        run_node
        ;;
    *)
        echo "Escolha o runtime para executar o script:"
        echo "1) Python"
        echo "2) Node.js"
        echo ""
        read -p "Digite sua escolha (1 ou 2): " choice
        
        case $choice in
            1)
                run_python
                ;;
            2)
                run_node
                ;;
            *)
                echo "Opção inválida!"
                exit 1
                ;;
        esac
        ;;
esac

# Verificar se os arquivos foram gerados
if [ -f "public/locations_new.json" ] && [ -f "public/filters_new.json" ]; then
    echo ""
    echo "=== Arquivos gerados com sucesso! ==="
    echo ""
    echo "Para fazer backup dos arquivos atuais e usar os novos:"
    echo "  mv public/locations.json public/locations_backup.json"
    echo "  mv public/filters.json public/filters_backup.json"
    echo "  mv public/locations_new.json public/locations.json"
    echo "  mv public/filters_new.json public/filters.json"
    echo ""
    echo "Ou execute o comando de substituição direta:"
    echo "  ./replace_files.sh"
else
    echo ""
    echo "Erro: Nem todos os arquivos foram gerados corretamente!"
    exit 1
fi
