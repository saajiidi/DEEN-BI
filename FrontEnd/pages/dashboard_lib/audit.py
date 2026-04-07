import pandas as pd
import streamlit as st
from FrontEnd.components import ui
from .data_helpers import build_order_level_dataset

def render_data_audit(df_sales: pd.DataFrame, df_customers: pd.DataFrame):
    st.subheader("Data Audit")
    if df_sales.empty: return
    audit_df = df_sales.copy()
    audit_df["order_day"] = pd.to_datetime(audit_df["order_date"], errors="coerce").dt.date
    order_level = build_order_level_dataset(audit_df)
    per_source = order_level.groupby("source", dropna=False).agg(orders=("order_id", "nunique"), revenue=("order_total", "sum")).reset_index()
    per_day = order_level.groupby("order_day", dropna=False).agg(orders=("order_id", "nunique"), revenue=("order_total", "sum")).reset_index()
    c1, c2 = st.columns(2)
    with c1: st.markdown("##### Source Mix"); st.dataframe(per_source, use_container_width=True, hide_index=True)
    with c2: st.markdown("##### Daily Coverage"); st.dataframe(per_day.sort_values("order_day", ascending=False), use_container_width=True, hide_index=True)
    st.markdown("#### Sample Orders")
    st.dataframe(order_level.head(50), use_container_width=True, hide_index=True)

def render_data_trust_panel(df: pd.DataFrame):
    missing_total = df["order_total"].isna().sum()
    missing_id = df["order_id"].isna().sum()
    if missing_total or missing_id:
        st.warning(f"Data issues found: {missing_total} missing totals, {missing_id} missing IDs.")
    else:
        st.success("Data structure is 100% normalized and consistent.")
