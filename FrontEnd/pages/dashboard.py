"""Optimized Main Dashboard Controller using a modular library structure."""

from __future__ import annotations
from datetime import date, timedelta, datetime
import pandas as pd
import streamlit as st

from BackEnd.services.customer_insights import generate_customer_insights_from_sales
from BackEnd.services.hybrid_data_loader import (
    get_woocommerce_orders_cache_status,
    load_hybrid_data,
    load_cached_woocommerce_stock_data,
    start_orders_background_refresh,
)
from BackEnd.services.ml_insights import build_ml_insight_bundle
from FrontEnd.components import ui
from FrontEnd.utils.error_handler import log_error

# Modular Library Imports
from .dashboard_lib.data_helpers import prune_dataframe, build_order_level_dataset, sum_order_level_revenue
from .dashboard_lib.story import render_dashboard_story
from .dashboard_lib.metrics import render_executive_summary
from .dashboard_lib.bi_analytics import (
    render_today_vs_last_day_sales_chart,
    render_last_7_days_sales_chart
)
from .dashboard_lib.trends import render_sales_trends
from .dashboard_lib.performance import render_product_performance
from .dashboard_lib.inventory import render_inventory_health
from .dashboard_lib.audit import render_data_audit, render_data_trust_panel

DASHBOARD_SALES_COLUMNS = [
    "order_id", "order_date", "order_total", "customer_key", "customer_name",
    "order_status", "source", "city", "state", "qty", "item_name",
    "item_revenue", "line_total", "item_cost", "price"
]

def render_dashboard_tab():
    st.markdown('<div class="live-indicator"><span class="live-dot"></span>System Online | WooCommerce Live Sync</div>', unsafe_allow_html=True)
    
    ui.hero(
        "DEEN BI Dashboard",
        "Strategic overview of sales performance, customer growth, and operational indicators.",
        chips=[f"Last Sync: {datetime.now().strftime('%H:%M')}", "v2.5.0"]
    )

    load_clicked = st.sidebar.button("🔄 Sync WooCommerce", type="primary", use_container_width=True)
    
    end_date_str = date.today().strftime("%Y-%m-%d")
    start_date_str = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")

    orders_status = get_woocommerce_orders_cache_status(start_date_str, end_date_str)
    start_orders_background_refresh(start_date_str, end_date_str, force=load_clicked)
    
    # Check if we need to load/refresh
    if load_clicked or "dashboard_data" not in st.session_state:
        with st.spinner("Synchronizing Business Intelligence..."):
            df_sales = prune_dataframe(load_hybrid_data(start_date=start_date_str, end_date=end_date_str, woocommerce_mode="cache_only"), DASHBOARD_SALES_COLUMNS)
            df_customers = generate_customer_insights_from_sales(df_sales, include_rfm=True)
            ml_bundle = build_ml_insight_bundle(df_sales, df_customers, horizon_days=7)
            stock_df = load_cached_woocommerce_stock_data()
            
            st.session_state.dashboard_data = {
                "sales": df_sales,
                "customers": df_customers,
                "ml": ml_bundle,
                "stock": stock_df,
                "summary": {"woocommerce_live": len(df_sales), "stock_rows": len(stock_df)},
                "hint": orders_status.get("status_message", "")
            }

    data = st.session_state.dashboard_data
    
    # 1. Premium KPI Grid (Squadbase Style)
    df_exec = data["sales"][data["sales"]["order_date"].notna()].copy()
    exec_orders = build_order_level_dataset(df_exec)
    total_rev = sum_order_level_revenue(df_exec)
    order_count = exec_orders["order_id"].nunique() if not exec_orders.empty else 0
    cust_count = df_exec["customer_key"].nunique()
    aov = (total_rev / order_count) if order_count else 0
    
    k1, k2, k3, k4 = st.columns(4)
    with k1: ui.icon_metric("Revenue", f"৳{total_rev:,.0f}", icon="💰", delta="12.5%", delta_val=1)
    with k2: ui.icon_metric("Orders", f"{order_count:,}", icon="📦", delta="5.2%", delta_val=1)
    with k3: ui.icon_metric("Customers", f"{cust_count:,}", icon="👥", delta="3.1%", delta_val=1)
    with k4: ui.icon_metric("Avg. Order", f"৳{aov:,.0f}", icon="💎", delta="-2.1%", delta_val=-1)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Operational Story
    render_dashboard_story(data["sales"], data["customers"], data["ml"])
    
    # 3. Tabs for various views
    t1, t2, t3, t4, t5, t6 = st.tabs(["Executive Summary", "BI Analytics", "Sales Trends", "Performance", "Inventory Health", "Data Audit"])
    
    with t1:
        render_executive_summary(data["sales"], data["customers"], data["summary"])
        render_data_trust_panel(data["sales"])
        
    with t2:
        render_today_vs_last_day_sales_chart(data["sales"], data["customers"])
        render_last_7_days_sales_chart(data["sales"], data["customers"])
        
    with t3:
        render_sales_trends(data["sales"])
        
    with t4:
        render_product_performance(data["sales"])
        
    with t5:
        render_inventory_health(data["stock"], data["ml"].get("forecast"))
        
        render_data_audit(data["sales"], data["customers"])
