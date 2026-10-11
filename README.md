# 📈 Análisis de mercado de acciones de EE.UU. (2015-2025)

Proyecto 1 del portafolio de finanzas. Análisis exploratorio y dashboard interactivo de 15 acciones de 5 sectores más el ETF `SPY` (S&P 500), con foco en **rendimiento, riesgo y diversificación** durante una década que incluyó el COVID-19 (2020) y el ciclo de alza de tasas (2022).

## 🎯 Objetivo

Responder con datos: *¿qué sectores rindieron más que el mercado, a qué costo de riesgo, y la diversificación sectorial realmente protegió en las crisis?*

| Sector | Tickers |
|---|---|
| Tecnología | AAPL, MSFT, NVDA, GOOGL, AMZN |
| Bancos | JPM, BAC, GS |
| Energía | XOM, CVX |
| Salud | JNJ, UNH, PFE |
| Consumo | KO, WMT |
| Índice | SPY |

Datos: precios diarios ajustados (Yahoo Finance vía `yfinance`), 2015-01-01 a 2025-12-31. Cada sector se modela como cartera de igual ponderación.

## 🔎 Hallazgos principales

1. **Tecnología dominó**: ~30× el capital inicial vs ~4× del SPY, con el mejor Sharpe (1,29 vs 0,80). Parte se explica por NVDA y por sesgo de supervivencia.
2. **Más retorno, más dolor**: máx. drawdown de Tecnología -42 % vs -34 % del SPY; Consumo fue el más defensivo (-22 %).
3. **Los shocks no son iguales**: la volatilidad del SPY llegó a ~93 % en abril de 2020; en 2022 Energía subió (XOM +60 %) mientras la tecnología caía (NVDA -62 %).
4. **La diversificación flaquea en crisis**: la correlación media entre acciones sube de 0,40 (2015-19) a 0,51 (2020-22).
5. **Energía y Salud quedaron rezagadas** en riesgo-retorno (Sharpe 0,40 y 0,59 vs 0,80 del mercado).

El detalle, con gráficos y narrativa, está en [`notebooks/analisis.ipynb`](notebooks/analisis.ipynb) (guardado con outputs).

## 🖥️ Dashboard (Streamlit)

`app.py` ofrece:

- **Filtros** en barra lateral: sectores, tickers, rango de fechas, tasa libre de riesgo y ventana de volatilidad.
- **KPIs**: retorno total, volatilidad anualizada, máximo drawdown y Sharpe (de la cartera de igual ponderación de la selección, o del ticker si es uno solo) + tabla por ticker.
- **Gráfico de precios normalizados** (base 100) interactivo.
- **Volatilidad móvil anualizada** configurable.
- **Heatmap de correlación** de retornos diarios.

## 🚀 Cómo ejecutar

```powershell
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

pytest                            # tests de métricas (sin red)
streamlit run app.py              # dashboard en http://localhost:8501
jupyter nbconvert --to notebook --execute --inplace notebooks/analisis.ipynb
```

La primera ejecución descarga los precios y los guarda en `data/prices.parquet`; las siguientes leen de ese cache. Para refrescar: borra el archivo o usa `load_prices(refresh=True)`.

## 🗂️ Estructura

```
01-analisis-mercado/
├── app.py                 # Dashboard Streamlit
├── src/
│   └── data.py            # Descarga + cache + métricas (reutilizable en otros proyectos)
├── notebooks/
│   └── analisis.ipynb     # Análisis narrado, con outputs
├── tests/
│   └── test_data.py       # Tests pytest con datos sintéticos
├── data/prices.parquet    # Cache de precios
└── requirements.txt
```

### Módulo `src/data.py`

Funciones puras (sin I/O) sobre `Series`/`DataFrame`: `daily_returns`, `cumulative_returns`, `rolling_volatility`, `drawdown_series`, `max_drawdown`, `annual_returns`, `annualized_return`, `annualized_volatility`, `sharpe_ratio`, `summary_table`. Más `download_prices` / `load_prices` para la obtención de datos y las constantes `SECTORS`, `TICKERS`.

## ⚠️ Limitaciones

Universo reducido y elegido con el conocimiento de hoy (sesgo de supervivencia), tasa libre de riesgo = 0 por defecto, rebalanceo diario sin costos. Es un análisis descriptivo, **no una recomendación de inversión**.

## 🛠️ Stack

Python 3.12 · pandas · numpy · yfinance · matplotlib · seaborn · plotly · Streamlit · pytest · Jupyter
