#!/bin/bash

# Script para substituir os arquivos JSON existentes pelos novos
# Faz backup automático dos arquivos antigos

echo "=== Substituindo arquivos JSON ==="
echo ""

# Verificar se os novos arquivos existem
if [ ! -f "public/locations_new.json" ] || [ ! -f "public/filters_new.json" ]; then
    echo "Erro: Arquivos novos não encontrados!"
    echo "Execute primeiro o script extract_data.sh"
    exit 1
fi

# Criar diretório de backup se não existir
backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"

echo "Criando backup em: $backup_dir"

# Fazer backup dos arquivos existentes
if [ -f "public/locations.json" ]; then
    cp "public/locations.json" "$backup_dir/locations.json"
    echo "  ✓ Backup de locations.json criado"
fi

if [ -f "public/filters.json" ]; then
    cp "public/filters.json" "$backup_dir/filters.json"
    echo "  ✓ Backup de filters.json criado"
fi

echo ""
echo "Substituindo arquivos..."

# Substituir os arquivos
mv "public/locations_new.json" "public/locations.json"
mv "public/filters_new.json" "public/filters.json"

echo "  ✓ locations.json atualizado"
echo "  ✓ filters.json atualizado"

echo ""
echo "=== Substituição concluída! ==="
echo "Backup dos arquivos antigos em: $backup_dir"
echo ""
echo "Para testar a aplicação:"
echo "  npm run dev"
