import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Configuração Estética (Forecast.biz Style)
st.set_page_config(page_title="Chico | Strategic Stock Analysis", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("Chico Strategic Analysis 📈")

# Sidebar - Parâmetros de Filtro (Conforme pedido)
with st.sidebar:
    st.header("Screener Filters")
    min_div = st.slider("Min Dividend Yield (%)", 0.0, 10.0, 2.0)
    max_pe = st.slider("Max P/E Ratio", 5, 100, 25)
    
    st.header("Watchlist Alerts (>20% Drop)")
    watchlist = ['NVO', 'PFE', 'XIACF', 'NEE', 'EOAN.DE', 'UNH']
    # Lógica de alerta simplificada aqui...

# Input de Stock
ticker_input = st.text_input("Enter Stock Ticker (e.g. MSFT, NVDA):", "MSFT")

if ticker_input:
    stock = yf.Ticker(ticker_input)
    hist = stock.history(period="10y")
    
    # Gráfico Estilo Forecast (Clean Line)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], fill='tozeroy', line_color='#1f77b4', name=ticker_input))
    fig.update_layout(title=f"{ticker_input} - 10 Year Performance", template="plotly_white", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # Fundamental Metrics
    col1, col2, col3, col4 = st.columns(4)
    info = stock.info
    col1.metric("Current P/E", f"{info.get('trailingPE', 'N/A')}")
    col2.metric("Div. Yield", f"{info.get('dividendYield', 0)*100:.2f}%")
    col3.metric("FCF", f"{info.get('freeCashflow', 0)/1e9:.2f}B")
    col4.metric("Market Cap", f"{info.get('marketCap', 0)/1e9:.2f}B")

    # Buffett Verdict (Placeholder Lógico)
    st.subheader("🔍 Warren Buffett Verdict")
    if info.get('trailingPE', 100) < 20 and info.get('returnOnEquity', 0) > 0.15:
        st.success("Verdict: INVEST. Strong ROE and attractive valuation.")
    else:
        st.warning("Verdict: HOLD/WAIT. Fundamentals do not meet strict value criteria.")