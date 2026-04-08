import pandas as pd
import streamlit as st
import plotly.express as px
from FrontEnd.components import ui
from BackEnd.core.categories import parse_sku_variants

def render_deep_dive_tab(df_sales: pd.DataFrame, stock_df: pd.DataFrame):
    """Exhaustive Advanced Filtering for Deep-Dive Clusters."""
    if df_sales.empty:
        st.info("No data available for deep-dive analysis. Finalized orders (Completed/Shipped) are required.")
        return

    # PRE-PROCESSING: Parsing Product Variants & Local Trends
    if "item_revenue" not in df_sales.columns:
        df_sales["item_revenue"] = pd.to_numeric(df_sales.get("line_total", df_sales.get("order_total", 0)), errors="coerce").fillna(0)
        
    if "price" not in df_sales.columns:
        df_sales["price"] = pd.to_numeric(df_sales["item_revenue"], errors="coerce") / pd.to_numeric(df_sales["qty"], errors="coerce").clip(lower=1)
        df_sales["price"] = df_sales["price"].fillna(0)
        
    if "_variant_parsed" not in df_sales.columns:
        df_sales[["_color", "_size"]] = df_sales["item_name"].apply(lambda x: pd.Series(parse_sku_variants(x)))
        df_sales["_variant_parsed"] = True

    # --- Trend Type Logic ---
    # Calculate velocity based on current window length
    days_active = (df_sales["order_date"].max() - df_sales["order_date"].min()).days or 1
    v_agg = df_sales.groupby("item_name")["qty"].sum().reset_index()
    v_agg["v_rate"] = v_agg["qty"] / days_active
    
    def classify_trend(rate):
        if rate > 3.0: return "🔥 Fast Moving"
        if rate > 0.8: return "⚖️ Regular"
        if rate > 0: return "🐌 Slow Moving"
        return "❄️ Non-Moving"

    v_agg["Trend"] = v_agg["v_rate"].apply(classify_trend)
    if "Trend" not in df_sales.columns:
        df_sales = df_sales.merge(v_agg[["item_name", "Trend"]], on="item_name", how="left")

    # --- Campaign / Coupon logic ---
    if "Coupons" not in df_sales.columns:
        df_sales["Coupons"] = "None"

    # MAIN UI LAYOUT
    st.markdown("### 🔍 Advanced Market Deep-Dive")
    
    # FILTER CONTROL CENTER
    with st.expander("🛠️ Advanced Cluster Filters", expanded=True):
        f_c1, f_c2, f_c3, f_c4 = st.columns(4)
        
        with f_c1:
            st.markdown("**📦 Product & Variants**")
            # 1. Category
            cat_list = sorted([str(c) for c in df_sales["Category"].dropna().unique() if str(c).strip()])
            sel_cats = st.multiselect("Categories", ["All"] + cat_list, default=["All"])
            active_cats = [] if "All" in sel_cats or not sel_cats else sel_cats
            
            # Cascade for SKUs
            sku_options = df_sales[df_sales["Category"].isin(active_cats)] if active_cats else df_sales
            avail_skus = sorted([str(s) for s in sku_options["sku"].unique() if str(s).strip() and s != "Unknown"])
            sel_skus = st.multiselect("SKUs", ["All"] + avail_skus, default=["All"])
            active_skus = [] if "All" in sel_skus or not sel_skus else sel_skus
            
            # Cascade for Colors
            color_options = sku_options[sku_options["sku"].astype(str).isin(active_skus)] if active_skus else sku_options
            avail_colors = sorted([str(c) for c in color_options["_color"].unique() if str(c).strip() and c != "Unknown"])
            sel_colors = st.multiselect("Colors", ["All"] + avail_colors, default=["All"])
            active_colors = [] if "All" in sel_colors or not sel_colors else sel_colors
            
            # Cascade for Sizes
            size_options = color_options[color_options["_color"].isin(active_colors)] if active_colors else color_options
            avail_sizes = sorted([str(s) for s in size_options["_size"].unique() if str(s).strip() and s != "Unknown"])
            sel_sizes = st.multiselect("Sizes", ["All"] + avail_sizes, default=["All"])
            active_sizes = [] if "All" in sel_sizes or not sel_sizes else sel_sizes

        with f_c2:
            st.markdown("**💰 Financials**")
            min_p = float(df_sales["price"].min())
            max_p = float(df_sales["price"].max())
            price_range = st.slider("Price Range (TK)", min_p, max_p, (min_p, max_p))
            
            st.markdown("**📉 Moving Trends**")
            sel_trends = st.multiselect("Velocity Type", ["🔥 Fast Moving", "⚖️ Regular", "🐌 Slow Moving"])

        with f_c3:
            st.markdown("**📍 Platform & Geo**")
            sel_sources = st.multiselect("Platform/Source", sorted(df_sales["source"].unique()))
            sel_cities = st.multiselect("Market Regions", sorted(df_sales["city"].unique()))
            
            # Sub-window Filtering (Zoom within range)
            st.markdown("**⏱️ Local Time Frame**")
            start_f, end_f = st.date_input("Zoom Frame", 
                                           [df_sales["order_date"].min().date(), df_sales["order_date"].max().date()],
                                           min_value=df_sales["order_date"].min().date(),
                                           max_value=df_sales["order_date"].max().date())

        with f_c4:
            st.markdown("**🎫 Marketing & Campaigns**")
            coupons = [c for c in df_sales["Coupons"].unique() if c != "None"]
            sel_coupons = st.multiselect("Active Coupons", sorted(coupons))
            
            is_disc = st.checkbox("Show Only Non-Full-Price Orders")
            
            # Logic: Bundle detection (Order has multiple items or specific bundle keywords)
            # Simplification: Multiple qty in one line or specific SKUs
            sel_bundle = st.checkbox("Bundle/Multipack Only")

    # APPLY COMPREHENSIVE FILTERING
    w_df = df_sales.copy()
    
    # Time Zoom
    w_df = w_df[(w_df["order_date"].dt.date >= start_f) & (w_df["order_date"].dt.date <= end_f)]
    
    # Logic Filters
    if active_cats: w_df = w_df[w_df["Category"].isin(active_cats)]
    if active_colors: w_df = w_df[w_df["_color"].isin(active_colors)]
    if active_sizes: w_df = w_df[w_df["_size"].isin(active_sizes)]
    if active_skus: w_df = w_df[w_df["sku"].astype(str).isin(active_skus)]
    
    w_df = w_df[(w_df["price"] >= price_range[0]) & (w_df["price"] <= price_range[1])]
    if sel_trends: w_df = w_df[w_df["Trend"].isin(sel_trends)]
    if sel_sources: w_df = w_df[w_df["source"].isin(sel_sources)]
    if sel_cities: w_df = w_df[w_df["city"].isin(sel_cities)]
    if sel_coupons: w_df = w_df[w_df["Coupons"].isin(sel_coupons)]
    if is_disc: 
        # Check if item_revenue per unit is less than price (price is usually regular_price in WC)
        w_df = w_df[w_df["item_revenue"] < (w_df["price"] * w_df["qty"])]
    if sel_bundle:
        w_df = w_df[w_df["qty"] > 1] # Simple bundle proxy

    # VISUALIZATION SUITE
    st.markdown(f"**Found {len(w_df)} records matching these constraints**")
    
    cluster_t1, cluster_t2, cluster_t3, cluster_t4 = st.tabs(["📊 Performance Mix", "🔍 Variant Analysis", "🛒 Basket Context", "📋 Cluster Data Ledger"])
    
    with cluster_t1:
        c1, c2 = st.columns(2)
        with c1:
            # Trend Revenue Pie
            t_rev = w_df.groupby("Trend")["item_revenue"].sum().reset_index()
            fig = px.pie(t_rev, values="item_revenue", names="Trend", title="Revenue Contribution by Moving Type",
                         hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            # Source/Platform Bar
            s_rev = w_df.groupby("source")["item_revenue"].sum().reset_index()
            fig = px.bar(s_rev, x="source", y="item_revenue", title="revenue by platform source",
                         color="item_revenue", color_continuous_scale="Tealgrn")
            st.plotly_chart(fig, use_container_width=True)

    with cluster_t2:
        v_c1, v_c2 = st.columns(2)
        with v_c1:
            # Size Distribution
            sz_df = w_df.groupby("_size")["qty"].sum().reset_index()
            fig = px.bar(sz_df, x="_size", y="qty", title="Unit Volume by Size Cluster", 
                         color="qty", color_continuous_scale="Portland")
            st.plotly_chart(fig, use_container_width=True)
        with v_c2:
            # Color Distribution
            clr_df = w_df.groupby("_color")["item_revenue"].sum().reset_index()
            fig = px.pie(clr_df, values="item_revenue", names="_color", title="Revenue by Color Palette",
                         color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig, use_container_width=True)

    with cluster_t3:
        b_c1, b_c2 = st.columns(2)
        with b_c1:
            # Quantity Distribution (Basket logic)
            q_dist = w_df.groupby("qty")["order_id"].nunique().reset_index()
            q_dist.columns = ["Items in Line", "Orders"]
            fig = px.bar(q_dist, x="Items in Line", y="Orders", title="Bulk Purchase Propensity",
                         text_auto=True, color_discrete_sequence=["#F59E0B"])
            st.plotly_chart(fig, use_container_width=True)
        with b_c2:
            # City Mix within this cluster
            city_mix = w_df.groupby("city")["item_revenue"].sum().reset_index().sort_values("item_revenue", ascending=False).head(8)
            fig = px.bar(city_mix, x="item_revenue", y="city", title="Market Hotspots", 
                         orientation='h', color="item_revenue", color_continuous_scale="Agsunset")
            st.plotly_chart(fig, use_container_width=True)

    with cluster_t4:
        st.dataframe(
            w_df[["order_id", "order_date", "item_name", "sku", "qty", "item_revenue", "Trend", "Coupons", "source", "city"]],
            use_container_width=True, hide_index=True
        )
