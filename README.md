# SMAI — Stock Market Analysis & Insights

App de análise de ações (equity research) com interface visual inspirada no look & feel do forecast.biz.
Objetivo: reduzir o tempo entre “ideia → tese → decisão”, com módulos separados (tabs), dados de mercado/fundamentais e ferramentas de valuation (DCF).

## Principais features (v1)
- UI dark consistente, KPI cards legíveis, gráficos interativos (Plotly) com hover.
- Dados via Yahoo Finance (yfinance): preço, overview, financial statements, news.
- Fundamental Analysis: 5 áreas (2 com gráficos, 3 com análise escrita/framework).
- Sentiment: Stocktwits + Reddit search (heurístico; sujeito a rate limits).
- Buffett (DCF): cálculo de intrinsic value + sensibilidade.
- Screener: universo default + upload de CSV com coluna `Ticker`.

## Stack
- Python 3.10+ (recomendado)
- Streamlit (UI)
- yfinance (dados)
- Plotly (gráficos interativos)
- pandas/numpy (dados)
- requests (APIs externas)
- textblob (sentimento lexical básico; opcional)

## Setup rápido
### 1) Ir para a pasta do projeto
```bash
cd "C:\Users\ripth\Documents\Vibe Coding\SMAI - Stock Market Analysis & Insights"
```

### 2) Instalar dependências
```bash
python -m venv venv
.\venv\Scripts\python.exe -m pip install -U pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3) Executar a app
```bash
.\venv\Scripts\python.exe -m streamlit run SMAI/app.py
```

## Estrutura do projeto (resumo)
```
SMAI/
  app.py
  core/
  ui/
  assets/
  tests/
```
