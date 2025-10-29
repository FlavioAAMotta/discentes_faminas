#!/usr/bin/env node
/**
 * Script para extrair dados do arquivo CSV dados_processados.csv
 * e gerar os arquivos JSON na mesma estrutura dos existentes.
 * 
 * Uso: node extract_data.js
 */

const fs = require('fs');
const path = require('path');

/**
 * Lê e processa o arquivo CSV
 */
function readCSVData(csvFilePath) {
    try {
        const fileContent = fs.readFileSync(csvFilePath, 'utf-8');
        const lines = fileContent.split('\n');
        
        if (lines.length < 2) {
            console.log('Arquivo CSV vazio ou sem dados');
            return [];
        }
        
        // Primeira linha são os headers
        const headers = lines[0].split(',').map(h => h.trim());
        console.log('Headers encontrados:', headers);
        
        const data = [];
        let processedCount = 0;
        let skippedCount = 0;
        
        for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue; // Pular linhas vazias
            
            try {
                // Dividir a linha respeitando aspas
                const values = parseCSVLine(line);
                
                if (values.length !== headers.length) {
                    console.log(`Linha ${i + 1}: Número incorreto de colunas (${values.length} vs ${headers.length})`);
                    skippedCount++;
                    continue;
                }
                
                // Criar objeto com base nos headers
                const row = {};
                headers.forEach((header, index) => {
                    row[header] = values[index] ? values[index].trim() : '';
                });
                
                // Validar campos obrigatórios
                if (!row['Local'] || !row['Local/End']) {
                    console.log(`Linha ${i + 1}: Local ou endereço vazio, pulando...`);
                    skippedCount++;
                    continue;
                }
                
                if (!row['Latitude'] || !row['Longitude']) {
                    console.log(`Linha ${i + 1}: Coordenadas vazias, pulando...`);
                    skippedCount++;
                    continue;
                }
                
                // Converter coordenadas
                const latitude = parseFloat(row['Latitude']);
                const longitude = parseFloat(row['Longitude']);
                
                if (isNaN(latitude) || isNaN(longitude)) {
                    console.log(`Linha ${i + 1}: Coordenadas inválidas, pulando...`);
                    skippedCount++;
                    continue;
                }
                
                // Converter número de estudantes
                const estudante = parseInt(row['Estudante']) || 0;
                
                // Montar registro no formato do locations.json
                const locationData = {
                    id: processedCount + 1,
                    local: row['Local'],
                    endereco: row['Local/End'],
                    disciplina: row['Disciplina'] || '',
                    preceptor: row['Preceptor'] || '',
                    estudante: estudante,
                    periodo_original: row['Período_Original'] || '',
                    turma: row['Turma'] || '',
                    categoria: row['Categoria'] || '',
                    turno: row['Turno'] || '',
                    latitude: latitude,
                    longitude: longitude
                };
                
                data.push(locationData);
                processedCount++;
                
            } catch (error) {
                console.log(`Erro na linha ${i + 1}: ${error.message}`);
                skippedCount++;
                continue;
            }
        }
        
        console.log(`\nProcessamento concluído:`);
        console.log(`  - Registros processados: ${processedCount}`);
        console.log(`  - Registros pulados: ${skippedCount}`);
        
        return data;
        
    } catch (error) {
        console.error(`Erro ao ler arquivo CSV: ${error.message}`);
        return [];
    }
}

/**
 * Parser simples para CSV que respeita aspas
 */
function parseCSVLine(line) {
    const values = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        
        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            values.push(current);
            current = '';
        } else {
            current += char;
        }
    }
    
    values.push(current); // Último valor
    return values;
}

/**
 * Extrai dados únicos para os filtros
 */
function extractFiltersData(locationsData) {
    const disciplinas = new Set();
    const periodos = new Set();
    const preceptores = new Set();
    
    locationsData.forEach(location => {
        if (location.disciplina) {
            disciplinas.add(location.disciplina);
        }
        
        if (location.periodo_original) {
            periodos.add(location.periodo_original);
        }
        
        if (location.preceptor) {
            preceptores.add(location.preceptor);
        }
    });
    
    const filtersData = {
        disciplinas: Array.from(disciplinas).sort(),
        periodos: Array.from(periodos).sort(),
        preceptores: Array.from(preceptores).sort()
    };
    
    console.log(`\nFiltros extraídos:`);
    console.log(`  - ${filtersData.disciplinas.length} disciplinas`);
    console.log(`  - ${filtersData.periodos.length} períodos`);
    console.log(`  - ${filtersData.preceptores.length} preceptores`);
    
    return filtersData;
}

/**
 * Salva dados em arquivo JSON
 */
function saveJSONFile(data, filePath) {
    try {
        fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
        console.log(`Arquivo ${filePath} salvo com sucesso!`);
        return true;
    } catch (error) {
        console.error(`Erro ao salvar ${filePath}: ${error.message}`);
        return false;
    }
}

/**
 * Compara novos dados com arquivo existente
 */
function compareWithExisting(newData, existingFile) {
    if (!fs.existsSync(existingFile)) {
        console.log(`Arquivo ${existingFile} não existe para comparação.`);
        return;
    }
    
    try {
        const existingData = JSON.parse(fs.readFileSync(existingFile, 'utf-8'));
        
        console.log(`\nComparação com ${existingFile}:`);
        console.log(`  - Registros existentes: ${existingData.length}`);
        console.log(`  - Novos registros: ${newData.length}`);
        console.log(`  - Diferença: ${newData.length - existingData.length}`);
        
        if (existingData.length > 0 && newData.length > 0) {
            console.log(`\nPrimeiro registro existente vs novo:`);
            console.log(`  Local: '${existingData[0].local}' vs '${newData[0].local}'`);
            console.log(`  Disciplina: '${existingData[0].disciplina}' vs '${newData[0].disciplina}'`);
        }
        
    } catch (error) {
        console.error(`Erro ao comparar com arquivo existente: ${error.message}`);
    }
}

/**
 * Função principal
 */
function main() {
    console.log('=== Script de Extração de Dados dos Estágios FAMINAS ===\n');
    
    // Caminhos dos arquivos
    const csvFile = 'public/dados_processados.csv';
    const locationsOutput = 'public/locations_new.json';
    const filtersOutput = 'public/filters_new.json';
    
    // Verificar se o arquivo CSV existe
    if (!fs.existsSync(csvFile)) {
        console.error(`Erro: Arquivo ${csvFile} não encontrado!`);
        return;
    }
    
    // Ler dados do CSV
    console.log('1. Lendo dados do arquivo CSV...');
    const locationsData = readCSVData(csvFile);
    
    if (locationsData.length === 0) {
        console.log('Nenhum dado válido encontrado no CSV!');
        return;
    }
    
    // Extrair dados de filtros
    console.log('\n2. Extraindo dados para filtros...');
    const filtersData = extractFiltersData(locationsData);
    
    // Salvar arquivos JSON
    console.log('\n3. Salvando arquivos JSON...');
    
    // Salvar locations
    if (saveJSONFile(locationsData, locationsOutput)) {
        compareWithExisting(locationsData, 'public/locations.json');
    }
    
    // Salvar filters
    if (saveJSONFile(filtersData, filtersOutput)) {
        compareWithExisting(filtersData, 'public/filters.json');
    }
    
    console.log(`\n=== Processamento concluído ===`);
    console.log(`Novos arquivos gerados:`);
    console.log(`  - ${locationsOutput}`);
    console.log(`  - ${filtersOutput}`);
    console.log(`\nPara substituir os arquivos atuais, execute:`);
    console.log(`  mv ${locationsOutput} public/locations.json`);
    console.log(`  mv ${filtersOutput} public/filters.json`);
}

// Executar se for chamado diretamente
if (require.main === module) {
    main();
}

module.exports = {
    readCSVData,
    extractFiltersData,
    saveJSONFile,
    compareWithExisting
};
