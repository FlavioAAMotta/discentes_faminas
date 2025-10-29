# Scripts de Extração de Dados - Estágios FAMINAS

Este conjunto de scripts foi criado para extrair dados do arquivo CSV `dados_processados.csv` e gerar os arquivos JSON na mesma estrutura dos existentes, garantindo que todos os dados estejam completos.

## 📁 Arquivos Incluídos

- **`extract_data.py`** - Script em Python para extração dos dados
- **`extract_data.js`** - Script em Node.js para extração dos dados  
- **`extract_data.sh`** - Script Bash para execução facilitada
- **`replace_files.sh`** - Script para substituir os arquivos existentes

## 🎯 Objetivo

O problema identificado é que os arquivos JSON atuais (`locations.json` e `filters.json`) podem ter dados faltantes em relação ao arquivo CSV completo. Estes scripts:

1. Leem o arquivo `public/dados_processados.csv`
2. Processam e validam os dados
3. Geram novos arquivos JSON com estrutura idêntica aos existentes
4. Permitem comparação para identificar dados ausentes

## 📊 Estruturas de Dados

### CSV de Entrada (`dados_processados.csv`)
```
Semestre,Disciplina,Turma,Período,Grupos,Preceptor,Estudante,Categoria,Dia,Turno,Rodízio,Local,Local/End,Latitude,Longitude,Período_Original
```

### JSON de Localizações (`locations.json`)
```json
{
  "id": number,
  "local": string,
  "endereco": string,
  "disciplina": string,
  "preceptor": string,
  "estudante": number,
  "periodo_original": string,
  "turma": string,
  "categoria": string,
  "turno": string,
  "latitude": number,
  "longitude": number
}
```

### JSON de Filtros (`filters.json`)
```json
{
  "disciplinas": [string],
  "periodos": [string],
  "preceptores": [string]
}
```

## 🚀 Como Usar

### Opção 1: Script Bash (Recomendado)
```bash
# Execução interativa (escolhe Python ou Node.js)
./extract_data.sh

# Execução direta com Python
./extract_data.sh python

# Execução direta com Node.js  
./extract_data.sh node
```

### Opção 2: Python Direto
```bash
python3 extract_data.py
```

### Opção 3: Node.js Direto
```bash
node extract_data.js
```

## 📋 Processo de Extração

1. **Leitura do CSV**: O script lê `public/dados_processados.csv`
2. **Validação**: Verifica campos obrigatórios (local, endereço, coordenadas)
3. **Conversão**: Converte tipos de dados (int, float) apropriadamente
4. **Mapeamento**: Mapeia colunas do CSV para estrutura JSON
5. **Filtros**: Extrai valores únicos para disciplinas, períodos e preceptores
6. **Comparação**: Compara com arquivos existentes
7. **Geração**: Cria `locations_new.json` e `filters_new.json`

## 🔄 Substituição dos Arquivos

Após a extração, para usar os novos dados:

### Opção 1: Script Automático (Recomendado)
```bash
./replace_files.sh
```
- Cria backup automático com timestamp
- Substitui os arquivos existentes
- Mantém segurança dos dados originais

### Opção 2: Manual
```bash
# Fazer backup manual
cp public/locations.json public/locations_backup.json
cp public/filters.json public/filters_backup.json

# Substituir arquivos
mv public/locations_new.json public/locations.json
mv public/filters_new.json public/filters.json
```

## 🔍 Validações Realizadas

### Dados Obrigatórios
- ✅ Nome do local não pode estar vazio
- ✅ Endereço não pode estar vazio  
- ✅ Latitude e longitude devem existir e ser válidas
- ✅ Coordenadas devem ser números válidos

### Conversões de Tipo
- ✅ Latitude/Longitude → `float`
- ✅ Número de estudantes → `int`
- ✅ ID → sequencial começando em 1

### Limpeza de Dados
- ✅ Remove espaços em branco extras
- ✅ Trata campos vazios apropriadamente
- ✅ Ignora linhas com dados inválidos

## 📊 Relatórios Gerados

Durante a execução, o script fornece:

- **Contagem de registros**: Processados vs pulados
- **Erros detalhados**: Linha por linha com motivo
- **Comparação**: Diferenças com arquivos existentes
- **Estatísticas de filtros**: Quantidade de itens únicos

## ⚠️ Tratamento de Erros

### Erros Comuns e Soluções

1. **CSV não encontrado**
   - Verificar se `public/dados_processados.csv` existe
   - Verificar caminho relativo do script

2. **Coordenadas inválidas**
   - Linhas com coordenadas vazias/inválidas são puladas
   - Relatório mostra quais linhas foram ignoradas

3. **Encoding de caracteres**
   - Scripts configurados para UTF-8
   - Suporte a caracteres especiais portugueses

## 🧪 Testando os Novos Dados

Após substituir os arquivos:

```bash
# Iniciar aplicação para teste
npm run dev

# Verificar no browser se:
# - Marcadores aparecem corretamente
# - Filtros funcionam
# - Popups mostram dados completos
# - Não há erros no console
```

## 📈 Melhorias Implementadas

1. **Dados Completos**: Garante que todos os registros do CSV sejam incluídos
2. **Validação Robusta**: Múltiplas verificações de integridade
3. **Backup Automático**: Segurança na substituição
4. **Comparação**: Identifica exatamente o que mudou
5. **Flexibilidade**: Suporte a Python e Node.js
6. **Relatórios**: Feedback detalhado do processo

## 🔧 Dependências

### Python
- Módulos padrão (csv, json, os)
- Python 3.6+

### Node.js  
- Módulos padrão (fs, path)
- Node.js 12+

### Bash
- Linux/macOS/WSL
- Comandos padrão (mv, cp, mkdir)

---

**Nota**: Os scripts são seguros e sempre geram arquivos novos antes de substituir os existentes. Em caso de problemas, os backups permitem restauração rápida.
