# Reactor DataViz Folium - Visualização de Dados de Segurança Pública

## 📖 Sobre o Projeto

Este projeto utiliza a biblioteca **Folium** para criar visualizações interativas de dados geográficos, focando especificamente em dados de **segurança pública do estado de São Paulo**. O objetivo é demonstrar como transformar dados tabulares de ocorrências criminais em mapas informativos e interativos.

## 🎯 Objetivos

- **Aprender Folium**: Explorar as funcionalidades da biblioteca Folium para visualização de dados em mapas
- **Análise Geoespacial**: Aplicar técnicas de análise geoespacial em dados reais de segurança pública
- **Visualização de Dados**: Criar mapas interativos que facilitem a compreensão de padrões criminais
- **Processamento de Dados**: Implementar pipeline completo de ETL para dados públicos

## 📊 Fonte dos Dados

Os dados utilizados são **Dados Públicos de Segurança da SSP-SP** (Secretaria da Segurança Pública de São Paulo), especificamente:

- **Ocorrências de Veículos Subtraídos** (2025 - 1º semestre)
- **Dados Populacionais** para normalização estatística
- **Shapefiles dos Municípios de SP** para mapeamento geográfico

### Características dos Dados:
- **Sistemas de origem**: R.D.O. (Registro Digital de Ocorrências) e S.P.J. (Sistema de Polícia Judiciária)
- **Granularidade**: Cada linha representa um veículo subtraido
- **Privacidade**: Seguem a Lei de Acesso à Informação (art. 31) para proteger identidade das pessoas
- **Localização**: Endereços sensíveis são omitidos por questões de privacidade

## 🏗️ Estrutura do Projeto

```
├── data/
│   ├── external/          # Dados brutos externos
│   ├── processed/         # Dados processados e limpos
│   └── raw/              # Dados originais sem processamento
├── utils/
│   ├── constants.py      # Constantes e configurações
│   └── __init__.py
├── data_etl.py           # Script de ETL e processamento de dados
├── dataviz_folium_ssp.ipynb  # Notebook principal com análises e visualizações
└── README.md
```

## 🔧 Tecnologias Utilizadas

- **Python 3.x**
- **Folium** - Visualização de mapas interativos
- **Pandas** - Manipulação e análise de dados
- **GeoPandas** - Análise de dados geoespaciais  
- **Jupyter Notebook** - Ambiente de desenvolvimento e apresentação
- **GeoPy** - Geocodificação de endereços
- **NumPy** - Computação numérica

## 🚀 Funcionalidades

1. **ETL de Dados**: Carregamento, limpeza e processamento de dados de múltiplas fontes
2. **Geocodificação**: Conversão de endereços em coordenadas geográficas
3. **Mapas Coropléticos**: Visualização de densidade de ocorrências por município
4. **Mapas de Pontos**: Localização específica de ocorrências
5. **Análise Temporal**: Visualização de padrões ao longo do tempo
6. **Normalização Populacional**: Cálculo de taxas por habitantes

## 📈 Principais Análises

- Distribuição geográfica de veículos subtraídos no estado de SP
- Identificação de hotspots criminais
- Análise de padrões temporais
- Comparação entre municípios com normalização populacional
- Visualização de tendências regionais

## 🎨 Visualizações Geradas

- **Mapas Coropléticos**: Densidade de ocorrências por região com escala de cores
- **Mapas de Calor**: Identificação visual de áreas de maior concentração
- **Mapas Interativos**: Com tooltips, popups e controles de camadas
- **Dashboards Geográficos**: Combinação de múltiplas visualizações

---

*Este projeto faz parte dos estudos de visualização de dados geoespaciais e serve como exemplo prático de aplicação das técnicas de análise de dados de segurança pública.*
