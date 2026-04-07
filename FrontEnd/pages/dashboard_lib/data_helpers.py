import pandas as pd
import streamlit as st
from BackEnd.utils.sales_schema import ensure_sales_schema

def prune_dataframe(df: pd.DataFrame, preferred_columns: list[str]) -> pd.DataFrame:
    sales = ensure_sales_schema(df)
    if sales.empty:
        return sales
    available = [col for col in preferred_columns if col in sales.columns]
    if not available:
        return sales
    return sales.loc[:, available].copy()

def build_order_level_dataset(df: pd.DataFrame) -> pd.DataFrame:
    sales = ensure_sales_schema(df)
    if sales.empty:
        return pd.DataFrame()

    optional_columns = [col for col in ["order_day", "day_name", "day_num", "hour", "region", "_import_time"] if col in sales.columns]
    order_rows = sales[sales["order_id"].replace("", pd.NA).notna()].copy()
    no_order_id_rows = sales[sales["order_id"].replace("", pd.NA).isna()].copy()

    grouped_orders = pd.DataFrame()
    if not order_rows.empty:
        aggregations = {
            "order_date": ("order_date", "min"),
            "order_total": ("order_total", "max"),
            "customer_key": ("customer_key", lambda s: next((v for v in s if str(v).strip()), "")),
            "customer_name": ("customer_name", lambda s: next((v for v in s if str(v).strip()), "")),
            "order_status": ("order_status", lambda s: next((v for v in s if str(v).strip()), "")),
            "source": ("source", lambda s: ", ".join(sorted({str(v) for v in s if str(v).strip()}))),
            "city": ("city", lambda s: next((v for v in s if str(v).strip()), "")),
            "state": ("state", lambda s: next((v for v in s if str(v).strip()), "")),
            "qty": ("qty", "sum"),
        }
        for col in optional_columns:
            aggregations[col] = (col, "first")
        grouped_orders = order_rows.sort_values("order_date").groupby("order_id", as_index=False).agg(**aggregations)

    passthrough_rows = pd.DataFrame()
    if not no_order_id_rows.empty:
        passthrough_rows = no_order_id_rows[
            ["order_id", "order_date", "order_total", "customer_key", "customer_name", "order_status", "source", "city", "state", "qty"] + optional_columns
        ].copy()

    frames = [frame for frame in [grouped_orders, passthrough_rows] if not frame.empty]
    if not frames:
        return pd.DataFrame(columns=["order_id", "order_date", "order_total", "customer_key", "customer_name", "order_status", "source", "city", "state", "qty"] + optional_columns)
    return pd.concat(frames, ignore_index=True, sort=False)

def sum_order_level_revenue(df: pd.DataFrame) -> float:
    orders = build_order_level_dataset(df)
    if orders.empty:
        return 0.0
    return float(pd.to_numeric(orders["order_total"], errors="coerce").fillna(0).sum())

def estimate_line_revenue(df: pd.DataFrame) -> pd.Series:
    sales = ensure_sales_schema(df)
    if sales.empty:
        return pd.Series(dtype="float64")
    qty = pd.to_numeric(sales.get("qty", 0), errors="coerce").fillna(0)
    direct_candidates = []
    for col in ["item_revenue", "Item Revenue", "line_total", "Line Total"]:
        if col in sales.columns:
            direct_candidates.append(pd.to_numeric(sales[col], errors="coerce"))
    if direct_candidates:
        return direct_candidates[0].fillna(0)
    for col in ["item_cost", "Item Cost", "price", "Price"]:
        if col in sales.columns:
            unit_price = pd.to_numeric(sales[col], errors="coerce").fillna(0)
            if unit_price.gt(0).any():
                return unit_price * qty
    line_counts = sales.groupby("order_id")["order_id"].transform("size").replace(0, pd.NA)
    qty_totals = sales.groupby("order_id")["qty"].transform("sum").replace(0, pd.NA)
    order_total = pd.to_numeric(sales.get("order_total", 0), errors="coerce").fillna(0)
    return (order_total * (qty / qty_totals)).fillna(order_total / line_counts).fillna(order_total)
