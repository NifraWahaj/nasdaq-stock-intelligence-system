import streamlit as st
import pandas as pd
from serving.components.db import get_latest_prices, get_daily_returns
from serving.components.charts import correlation_heatmap
from serving.components.theme import NASDAQ_GREEN, NASDAQ_RED


def render():
    st.title("Market Overview")
    st.caption("Live summary of all 10 tracked NASDAQ stocks")

    prices_df = get_latest_prices()

    if prices_df.empty:
        st.info("Waiting for ingestion pipeline to populate price data...")
        _render_placeholder_ticker_grid()
        return

    _render_ticker_grid(prices_df)
    st.divider()
    _render_correlation(get_daily_returns())


def _render_ticker_grid(df: pd.DataFrame):
    cols = st.columns(5)
    for i, (idx, row) in enumerate(df.iterrows()):
        with cols[i % 5]:
            # This uses the card function from your theme.py
            with st.container(border=True): 
                st.markdown(f"**{row['symbol']}**")
                st.title(f"${row['close']:.2f}")
                vol = f"{int(row['volume']):,}"
                st.caption(f"Vol: {vol}")


def _render_placeholder_ticker_grid():
    """Shown before data is available."""
    tickers = ["AAPL","MSFT","NVDA","GOOGL","AMZN",
               "META","TSLA","INTC","AMD","NFLX"]
    cols = st.columns(5)
    for i, t in enumerate(tickers):
        with cols[i % 5]:
            st.metric(label=t, value="—", delta=None)


def _render_correlation(df: pd.DataFrame):
    st.subheader("Return Correlation Matrix")
    st.caption("Daily return correlations across all 10 tickers")
    st.plotly_chart(
        correlation_heatmap(df),
        use_container_width=True
    )