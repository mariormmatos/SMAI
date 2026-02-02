# Contexto do projeto — SMAI (Stock Market Analysis & Insights)

## Objetivo
Criar uma app (SMAI) para avaliar ações de forma rápida, estruturada e visualmente apelativa.
A app deve suportar:
- Análise fundamental com framework (tese + riscos + catalisadores)
- Métricas e gráficos ao longo do tempo
- Sentiment de comunidades (Reddit/Stocktwits)
- Valuation “Buffett” via DCF
- Screener para gerar ideias (universe + filtros)
- Watchlist/alerts e report (export)

A UI deve ser inspirada no look & feel do forecast.biz:
- Dark, moderna, com bom contraste e gráficos “filled area”
- Interação fluída, com hover e tooltips

---

## Módulos (cada módulo = uma tab/ecrã)
### 1) Fundamental Analysis
Deve conter 5 áreas internas:
1. Financial Statements Analysis (gráficos)
2. Valuation Metrics (gráficos)
3. Growth Potential & Competitive Positioning (texto/framework)
4. Risk Analysis (texto/framework)
5. Recent News & Catalysts (texto + links)

Requisitos dos gráficos:
- Timeframe selecionável (1D, 1M, 6M, 1Y, 5Y, 10Y)
- Filled area style e markers
- Hover por data/ano com valores
- Eixos formatados (~s), evitando “muitos zeros”

### 2) Stock News & Summaries
- Notícias do ticker (via yfinance quando possível)
- Fallback: headlines de mercado (RSS)
- Sumário curto (no futuro: LLM opcional, mas nesta fase focar em heurísticas)

### 3) Stock Screener
- Universo default + upload CSV (coluna `Ticker`)
- Filtros base (Market Cap, P/E, ROE, Growth)
- Output: tabela ordenável + score

### 4) Technical Analysis
- Price candles + volume, MAs, RSI (v1)
- Tudo em Plotly com hover

### 5) Sentiment
- Stocktwits stream + Reddit search
- Score simples (média/positivos/negativos)
- Mostrar posts recentes e tendência

### 6) Buffett (DCF)
- Inputs editáveis: FCF0, growth, discount, terminal growth, years
- Output: intrinsic value + tabela PV + sensibilidade

### 7) Watchlist & Alerts
- Lista local (persistência simples: JSON)
- Alertas: preço abaixo/acima, P/E threshold, etc. (v2)

### 8) Report
- Resumo executivo: tese, valuation, riscos, catalisadores
- Export HTML/PDF (v2)

---

## Fontes de dados
- Yahoo Finance via yfinance (principal)
- Stocktwits API (sem auth; pode rate-limit)
- Reddit search endpoint (sem auth; pode rate-limit)
- Nota: estes serviços podem falhar — a app deve degradar com warnings e continuar.

---

## Princípios de qualidade (não negociáveis)
- Legibilidade: dark theme sem “cards” brancos; alto contraste.
- Interatividade: tooltips/hover em gráficos.
- Robustez: lidar com missing fields e timeouts.
- Transparência: distinguir dados (factos) de interpretações (texto/framework).
- Escalabilidade: preparar refactor para estrutura modular.

---

## Roadmap curto (prioridades)
1) Refactor: separar `core/` e `ui/` (ver `SMAI/`)
2) Cache com TTL + retries/backoff para APIs
3) Technical indicators (RSI/MAs) em Plotly
4) Watchlist persistente e alerts
5) Export report (HTML/PDF)
