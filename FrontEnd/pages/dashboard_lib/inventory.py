import pandas as pd
import streamlit as st
import plotly.express as px
from FrontEnd.components import ui

def render_inventory_health(stock_df: pd.DataFrame, forecast_df: pd.DataFrame):
    st.subheader("Inventory Health")
    if stock_df is None or stock_df.empty:
        st.info("No live stock snapshot is available yet.")
        return
    inventory = stock_df.copy()
    inventory["Stock Quantity"] = pd.to_numeric(inventory.get("Stock Quantity", 0), errors="coerce").fillna(0)
    inventory["Price"] = pd.to_numeric(inventory.get("Price", 0), errors="coerce").fillna(0)
    inventory["Value"] = inventory["Stock Quantity"] * inventory["Price"]
    low_stock = inventory[inventory["Stock Quantity"] <= 5]
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Products", f"{len(inventory):,}")
    with m2: st.metric("Low Stock", f"{len(low_stock):,}")
    with m3: st.metric("Inventory Value", f"TK {inventory['Value'].sum():,.0f}")
    st.markdown("#### Low Stock Watchlist")
    st.dataframe(inventory.sort_values("Stock Quantity").head(20)[["Name", "SKU", "Stock Quantity", "Price", "Value"]], use_container_width=True, hide_index=True)
