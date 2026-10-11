"""Dashboard Streamlit: análisis de mercado de acciones de EE.UU."""
import pandas as pd
import plotly.express as px
import streamlit as st

from src import data as d

st.set_page_config(page_title="Análisis de mercado EE.UU.", page_icon="📈", layout="wide")


@st.cache_data(show_spinner="Cargando precios...")
def get_prices() -> pd.DataFrame:
    return d.load_prices()


prices = get_prices()

# ---------------- Barra lateral ----------------
st.sidebar.header("Filtros")
sectors = st.sidebar.multiselect("Sectores", list(d.SECTORS), default=["Tecnología", "Índice"])
available = [t for s in sectors for t in d.SECTORS[s]]
tickers = st.sidebar.multiselect("Tickers", available, default=available)
min_d, max_d = prices.index.min().date(), prices.index.max().date()
date_range = st.sidebar.date_input("Rango de fechas", (min_d, max_d), min_value=min_d, max_value=max_d)
rf = st.sidebar.number_input("Tasa libre de riesgo anual (%)", 0.0, 10.0, 0.0, 0.25) / 100
window = st.sidebar.slider("Ventana de volatilidad (días)", 10, 126, 21)

st.title("📈 Análisis de mercado: acciones de EE.UU.")

if len(date_range) != 2:
    st.info("Selecciona fecha de inicio y de fin.")
    st.stop()
if not tickers:
    st.warning("Selecciona al menos un ticker.")
    st.stop()

sub = prices.loc[str(date_range[0]):str(date_range[1]), tickers].dropna(how="all")
if len(sub) < 3:
    st.warning("El rango de fechas elegido tiene muy pocos datos.")
    st.stop()
rets = d.daily_returns(sub)

# ---------------- KPIs ----------------
table = d.summary_table(sub, rf)
st.subheader("Indicadores clave")
if len(tickers) == 1:
    t = tickers[0]
    row = table.loc[t]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Retorno total", f"{row['Retorno total']:.1%}")
    c2.metric("Volatilidad anual", f"{row['Volatilidad']:.1%}")
    c3.metric("Max drawdown", f"{row['Max drawdown']:.1%}")
    c4.metric("Sharpe", f"{row['Sharpe']:.2f}")
else:
    # Cartera de igual ponderación de la selección
    port = (1 + rets.mean(axis=1)).cumprod()
    port_r = port.pct_change().fillna(0)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Retorno total (cartera igual pond.)", f"{port.iloc[-1] - 1:.1%}")
    c2.metric("Volatilidad anual", f"{d.annualized_volatility(port_r):.1%}")
    c3.metric("Max drawdown", f"{d.max_drawdown(port):.1%}")
    c4.metric("Sharpe", f"{d.sharpe_ratio(port_r, rf):.2f}")
    st.caption("KPIs de la cartera de igual ponderación con los tickers seleccionados. Detalle por ticker abajo.")

st.dataframe(
    table.style.format(
        {"Retorno total": "{:.1%}", "Retorno anualizado": "{:.1%}", "Volatilidad": "{:.1%}",
         "Max drawdown": "{:.1%}", "Sharpe": "{:.2f}"}
    ),
    width="stretch",
)

# ---------------- Gráficos ----------------
st.subheader("Precios normalizados (base 100)")
norm = (sub / sub.bfill().iloc[0] * 100)
st.plotly_chart(px.line(norm, labels={"value": "Base 100", "Date": "", "variable": "Ticker"}), width="stretch")

st.subheader(f"Volatilidad móvil anualizada ({window} días)")
vol = d.rolling_volatility(rets, window).dropna(how="all")
if vol.empty:
    st.info("El rango es más corto que la ventana de volatilidad.")
else:
    st.plotly_chart(px.line(vol, labels={"value": "Volatilidad", "Date": "", "variable": "Ticker"}), width="stretch")

st.subheader("Correlación de retornos diarios")
if len(tickers) < 2:
    st.info("Selecciona al menos 2 tickers para ver correlaciones.")
else:
    st.plotly_chart(
        px.imshow(rets.corr(), text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="auto"),
        width="stretch",
    )

st.caption("Fuente: Yahoo Finance (precios ajustados). Análisis descriptivo, no es una recomendación de inversión.")

