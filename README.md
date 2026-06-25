# Observatório da Violência Contra a Mulher no Amazonas

Projeto de análise de dados e visualização em Power BI que mapeia a violência contra a mulher no Amazonas e a rede pública de serviços de enfrentamento. O objetivo é reunir dados públicos dispersos em um painel interativo e acessível, que evidencie a dimensão do problema e ajude a localizar onde buscar ajuda.

Desenvolvido como projeto de extensão universitária (Estácio, 2026) por João Guilherme Barbosa da Silva — Manaus/AM.

## Sobre o projeto

A violência contra a mulher no Amazonas é agravada pela dimensão territorial do estado e pela dispersão geográfica dos serviços de atendimento. Os dados existem, mas estão espalhados em várias fontes e em grande volume, o que dificulta enxergar o quadro completo. Este projeto integra três fontes oficiais em um único dashboard.

Números consolidados:

- **134.970 denúncias** de violência contra a mulher no AM (ONDH / Disque 100 e Ligue 180), de 2023 ao 1º semestre de 2026
- **6.758 notificações** de violência feminina (SINAN / DATASUS), referentes a 2025
- **260 unidades** da rede de atendimento georreferenciadas em **74 municípios** (100% localizadas no mapa)
- Crescimento de aproximadamente **36%** nas denúncias de 2024 para 2025

## O dashboard

O painel em Power BI está organizado em sete páginas que respondem a perguntas concretas sobre o fenômeno:

- **Painel Geral** — indicadores-chave (total de denúncias, tipos predominantes, variação anual, cobertura)
- **Evolução Temporal** — tendência das denúncias de 2023 a 2026
- **Perfil da Vítima** — faixa etária, raça/cor e relação com o suspeito
- **Canal de Atendimento** — por onde as denúncias chegam
- **Tipo de Violência** — hierarquia das violações (física, psíquica, negligência, sexual, patrimonial)
- **Capital x Interior** — análise da concentração das denúncias e discussão sobre subnotificação
- **Mapa da Rede** — localização das 260 unidades, com filtro por tipo de serviço e município

O arquivo está em [`powerbi/dashboard_violencia_contra_mulher_no_amazonas.pbix`](powerbi/dashboard_violencia_contra_mulher_no_amazonas.pbix) e pode ser aberto no Power BI Desktop (gratuito).

## Fontes de dados

| Fonte | Órgão | Uso no projeto |
|---|---|---|
| ONDH / Disque 100 e Ligue 180 | Ouvidoria Nacional de Direitos Humanos | Base principal de denúncias |
| SINAN | DATASUS / Ministério da Saúde | Notificações de violência feminina |
| CADSUAS | Ministério do Desenvolvimento e Assistência Social | Rede SUAS (CRAS e CREAS) |
| Malha municipal | IBGE | Padronização de nomes e georreferenciamento |
| Portal de agendamento de CRAS | Público | Complemento da rede de CRAS |

Todas as fontes são públicas e abertas.

## Estrutura do repositório

```
observatorio-violencia-mulher/
├── dados/
│   ├── brutos/          # Fontes originais (arquivos grandes do Disque 100 não versionados)
│   ├── tratados/        # Bases tratadas e prontas para o Power BI
│   ├── tratar_dados.py          # Tratamento de SINAN e rede SUAS
│   ├── tratar_ondh.py           # Tratamento da base ONDH / Disque 100
│   ├── gerar_centroides.py      # Geocodificação dos municípios (OpenStreetMap)
│   ├── gerar_cras_web.py        # Coleta dos CRAS do portal público
│   ├── integrar_unidades_xlsx.py# Integração da rede de enfrentamento
│   └── mapear_fonte.py          # Perfilamento de novas fontes de dados
├── powerbi/             # Dashboard (.pbix)
└── README.md
```

### Bases tratadas (`dados/tratados/`)

- `ondh_violencia_mulher_am.csv` — 134.970 denúncias (ONDH / Disque 100)
- `sinan_violencia_feminina_am.csv` — notificações por município (SINAN)
- `rede_atendimento_am_completa.csv` — 260 unidades da rede georreferenciadas
- `municipios_centroides.csv` — coordenadas dos 62 municípios do AM

## Pipeline de dados

O tratamento foi feito em Python e cobre as seguintes etapas:

1. **Coleta** das fontes públicas (denúncias, notificações e rede de serviços)
2. **Correção de codificação** e limpeza dos arquivos brutos
3. **Padronização de nomes de municípios** usando o IBGE como referência canônica
4. **Filtragem** dos registros do Amazonas referentes a violência contra a mulher (de mais de 12 milhões de registros nacionais para 134.970 do recorte de interesse)
5. **Georreferenciamento** das unidades por GPS exato ou geocodificação (OpenStreetMap)
6. **Consolidação** das bases para importação no Power BI

Os arquivos brutos do Disque 100 (centenas de MB cada) não são versionados e podem ser baixados novamente no Portal de Dados Abertos do Governo Federal.

## Tecnologias

- **Power BI** — modelagem, medidas DAX e visualização
- **Python** — coleta, tratamento e georreferenciamento dos dados
- **Git / GitHub** — versionamento e registro do histórico do projeto

## Autor

João Guilherme Barbosa da Silva — Manaus/AM
Projeto de extensão universitária (Estácio, 2026)
