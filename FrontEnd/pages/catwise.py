import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime, timedelta
import plotly.graph_objects as go
from BackEnd.core.categories import get_category_for_sales, get_category_for_orders
from BackEnd.utils.data import find_columns as auto_find_columns
from BackEnd.services.hybrid_data_loader import load_hybrid_data

# --- Configuration & Mappings (Ported from Catwise-Analytics) ---

SALES_CATEGORY_MAPPING = {
    "Boxer": ["boxer"],
    "Tank Top": ["tank top", "tanktop", "tank", "top"],
    "Jeans": ["jeans"],
    "Denim Shirt": ["denim"],
    "Flannel Shirt": ["flannel"],
    "Polo Shirt": ["polo"],
    "Panjabi": ["panjabi", "punjabi"],
    "Trousers": ["trousers", "pant", "cargo", "trouser", "joggers", "track pant", "jogger"],
    "Twill Chino": ["twill chino"],
    "Mask": ["mask"],
    "Water Bottle": ["water bottle"],
    "Contrast Shirt": ["contrast"],
    "Turtleneck": ["turtleneck", "mock neck"],
    "Drop Shoulder": ["drop", "shoulder"],
    "Wallet": ["wallet"],
    "Kaftan Shirt": ["kaftan"],
    "Active Wear": ["active wear"],
    "Jersy": ["jersy"],
    "Sweatshirt": ["sweatshirt", "hoodie", "pullover"],
    "Jacket": ["jacket", "outerwear", "coat"],
    "Belt": ["belt"],
    "Sweater": ["sweater", "cardigan", "knitwear"],
    "Passport Holder": ["passport holder"],
    "Cap": ["cap"],
    "Leather Bag": ["bag", "backpack"],
}

STOCK_CATEGORY_MAPPING = {
    "Jeans Slim Fit": lambda n: "jeans" in n and "slim fit" in n,
    "Jeans Regular Fit": lambda n: "jeans" in n and "regular fit" in n,
    "Jeans Straight Fit": lambda n: "jeans" in n and "straight fit" in n,
    "Panjabi": lambda n: "panjabi" in n,
    "Active Wear": lambda n: "active wear" in n,
    "T-shirt Basic Full": lambda n: "t-shirt" in n and "full sleeve" in n,
    "T-shirt Drop-Shoulder": lambda n: "t-shirt" in n
    and ("drop-shoulder" in n or "drop shoulder" in n),
    "T-shirt Basic Half": lambda n: "t-shirt" in n
    and not ("full sleeve" in n or "drop-shoulder" in n or "drop shoulder" in n),
    "Sweatshirt": lambda n: "sweatshirt" in n,
    "Turtle-Neck": lambda n: "turtle-neck" in n or "turtleneck" in n,
    "Tank-Top": lambda n: "tank-top" in n or "tank top" in n,
    "Trousers Terry Fabric": lambda n: ("trouser" in n or "jogger" in n or "pant" in n)
    and "terry" in n,
    "Trousers Cotton Fabric": lambda n: ("trouser" in n or "jogger" in n or "pant" in n)
    and ("twill" in n or "chino" in n or "cotton" in n),
    "Polo": lambda n: "polo" in n,
    "Kaftan Shirt": lambda n: "kaftan" in n,
    "Contrast Stich": lambda n: "contrast stitch" in n or "contrast stich" in n,
    "Denim Shirt": lambda n: "denim" in n and "shirt" in n,
    "Flannel Shirt": lambda n: "flannel" in n and "shirt" in n,
    "Casual Shirt Full": lambda n: "shirt" in n
    and "full sleeve" in n
    and not any(
        k in n
        for k in ["denim", "flannel", "kaftan", "contrast", "stitch", "stich", "polo", "sweatshirt"]
    ),
    "Casual Shirt Half": lambda n: "shirt" in n
    and not any(
        k in n
        for k in [
            "full sleeve",
            "denim",
            "flannel",
            "kaftan",
            "contrast",
            "stitch",
            "stich",
            "polo",
            "t-shirt",
            "sweatshirt",
        ]
    ),
    "Belt": lambda n: "belt" in n,
    "Wallet Bifold": lambda n: "wallet" in n and "bifold" in n,
    "Wallet Trifold": lambda n: "wallet" in n and "trifold" in n,
    "Wallet Long": lambda n: "wallet" in n and "long" in n,
    "Passport Holder": lambda n: "passport holder" in n,
    "Mask": lambda n: "mask" in n,
    "Card Holder": lambda n: "card holder" in n,
    "Water Bottle": lambda n: "water bottle" in n,
    "Boxer": lambda n: "boxer" in n,
    "Bag": lambda n: "bag" in n,
}

COLUMN_ALIAS_MAPPING = {
    "name": ["item name", "product name", "product", "item", "title", "description", "name"],
    "cost": [
        "item cost",
        "price",
        "unit price",
        "cost",
        "rate",
        "mrp",
        "selling price",
        "regular price",
    ],
    "qty": [
        "quantity",
        "qty",
        "units",
        "sold",
        "count",
        "total quantity",
        "stock",
        "inventory",
        "stock quantity",
        "quantity sold",
    ],
    "date": ["date", "order date", "month", "time", "created at"],
    "order_id": [
        "order id",
        "order #",
        "invoice number",
        "invoice #",
        "order number",
        "transaction id",
        "id",
    ],
    "phone": ["phone", "contact", "mobile", "cell", "phone number", "customer phone"],
}

# --- Core Logic Functions ---


def get_product_category(name, mode="Sales Performance"):
    """Categorizes product based on central rules."""
    if mode == "Stock Count":
        # Keep specialized stock matching for now as it's more specific
        name_str = str(name).lower()
        for cat, check in STOCK_CATEGORY_MAPPING.items():
            if callable(check):
                if check(name_str): return cat
            elif any(kw.lower() in name_str for kw in check): return cat
        return "Others"
    
    return get_category_for_sales(name)


def find_columns(df):
    """Detects primary columns; using both local specific and global utility."""
    return auto_find_columns(df)


def process_analytics(df, mapping, mode="Sales Performance"):
    """Core data processing and exhaustive metric calculation."""
    df = df.copy()

    df["Clean_Name"] = df[mapping["name"]].fillna("Unknown").astype(str)
    df = df[~df["Clean_Name"].str.contains("Choose Any", case=False, na=False)]

    cost_col = mapping.get("cost")
    qty_col = mapping.get("qty")
    date_col = mapping.get("date")

    df["Clean_Cost"] = pd.to_numeric(df[cost_col], errors="coerce").fillna(0) if cost_col else 0
    df["Clean_Qty"] = pd.to_numeric(df[qty_col], errors="coerce").fillna(0) if qty_col else 0
    df.loc[df["Clean_Qty"] < 0, "Clean_Qty"] = 0

    df["Total Amount"] = df["Clean_Cost"] * df["Clean_Qty"]
    df["Category"] = df["Clean_Name"].apply(lambda n: get_product_category(n, mode=mode))

    # Time-based analytics
    timeframe = "Full Report"
    trend_df = pd.DataFrame()
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df_timed = df.dropna(subset=[date_col])
        if not df_timed.empty:
            df_timed = df_timed.sort_values(date_col)
            timeframe = f"{df_timed[date_col].min().strftime('%d %b %y')} - {df_timed[date_col].max().strftime('%d %b %y')}"
            
            # Resample for trends
            resample_rule = "W" if (df_timed[date_col].max() - df_timed[date_col].min()).days > 60 else "D"
            trend_df = df_timed.set_index(date_col).resample(resample_rule).agg({
                "Total Amount": "sum",
                "Clean_Qty": "sum"
            }).reset_index()

    # Summary
    summary = df.groupby("Category").agg({"Clean_Qty": "sum", "Total Amount": "sum", "Clean_Name": "nunique"}).reset_index()
    summary.columns = ["Category", "Total Qty", "Total Amount", "SKU Count"]

    t_rev = summary["Total Amount"].sum()
    t_qty = summary["Total Qty"].sum()
    if t_rev > 0: summary["Revenue Share (%)"] = (summary["Total Amount"] / t_rev * 100).round(2)
    if t_qty > 0: summary["Quantity Share (%)"] = (summary["Total Qty"] / t_qty * 100).round(2)

    # Top items by category
    top_items = df.groupby("Clean_Name").agg({
        "Clean_Qty": "sum", 
        "Total Amount": "sum", 
        "Category": "first"
    }).reset_index()
    top_items.columns = ["Product Name", "Total Qty", "Total Amount", "Category"]
    top_items = top_items.sort_values("Total Amount", ascending=False)

    # Basket Analysis
    group_cols = [c for c in [mapping.get("order_id"), mapping.get("phone")] if c and c in df.columns]
    basket_stats = {"avg_value": 0, "total_orders": 0, "bundles": []}
    
    if group_cols:
        order_groups = df.groupby(group_cols).agg({
            "Total Amount": "sum",
            "Category": lambda x: list(set(x))
        })
        basket_stats["avg_value"] = order_groups["Total Amount"].mean()
        basket_stats["total_orders"] = len(order_groups)
        
        # Simple association (category pairs)
        multi_cat_orders = order_groups[order_groups["Category"].map(len) > 1]
        if not multi_cat_orders.empty:
            pairs = []
            for cats in multi_cat_orders["Category"]:
                cats.sort()
                for i in range(len(cats)):
                    for j in range(i + 1, len(cats)):
                        pairs.append(f"{cats[i]} + {cats[j]}")
            basket_stats["bundles"] = pd.Series(pairs).value_counts().head(10).to_dict()

    # Price Drilldown
    drilldown = (
        df.groupby(["Category", "Clean_Cost"])
        .agg({"Clean_Qty": "sum", "Total Amount": "sum"})
        .reset_index()
    )
    drilldown.columns = ["Category", "Price (TK)", "Total Qty", "Total Amount"]

    return {
        "summary": summary,
        "top_items": top_items,
        "drilldown": drilldown,
        "timeframe": timeframe,
        "trend_df": trend_df,
        "basket": basket_stats,
        "total_qty": t_qty,
        "total_rev": t_rev,
        "raw_df": df
    }


# --- UI Tab Functions ---


def render_catwise_analytics_tab():
    """Renders the Catwise Analytics feature in the main dashboard."""
    st.header("📦 Catwise Smart Analytics")
    st.info("Upload sales or stock data to see automated categorical performance insights.")

    mode = st.radio("Select Analysis Mode", ["Sales Performance", "Stock Count"], horizontal=True)
    data_source = st.radio("Select Data Source", ["Upload File", "Use System Hybrid Data"], horizontal=True)
    
    df = None
    if data_source == "Upload File":
        uploaded_file = st.file_uploader(
            f"Upload {mode} Data (Excel or CSV)", type=["xlsx", "csv"], key="catwise_uploader"
        )
        if uploaded_file:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                st.success(f"Attached: {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error reading file: {e}")
    else:
        with st.spinner("Loading System Hybrid Data..."):
            df = load_hybrid_data()
            if not df.empty:
                st.success(f"System Data Loaded ({len(df):,} rows)")
            else:
                st.warning("No system data found. Please ensure data exists in 'data/' or Google Sheet is connected.")

    if df is not None and not df.empty:
        try:
            if mode == "Stock Count" and "Type" in df.columns:
                df = df[df["Type"].str.lower().isin(["variation", "simple"])]

            auto_cols = find_columns(df)
            all_cols = list(df.columns)

            with st.expander("🛠️ Column Mapping & Preview", expanded=False):
                mc1, mc2, mc3 = st.columns(3)
                mc4, mc5, mc6 = st.columns(3)

                def get_idx(key):
                    return all_cols.index(auto_cols[key]) if key in auto_cols else 0

                m_name = mc1.selectbox(
                    "Product Name", all_cols, index=get_idx("name"), key="mw_name"
                )
                m_cost = mc2.selectbox("Price/Cost", all_cols, index=get_idx("cost"), key="mw_cost")
                m_qty = mc3.selectbox(
                    "Quantity/Stock", all_cols, index=get_idx("qty"), key="mw_qty"
                )
                m_date = mc4.selectbox(
                    "Date (Opt)",
                    ["None"] + all_cols,
                    index=get_idx("date") + 1 if "date" in auto_cols else 0,
                    key="mw_date",
                )
                m_order = mc5.selectbox(
                    "Order ID (Opt)",
                    ["None"] + all_cols,
                    index=get_idx("order_id") + 1 if "order_id" in auto_cols else 0,
                    key="mw_order",
                )
                m_phone = mc6.selectbox(
                    "Phone (Opt)",
                    ["None"] + all_cols,
                    index=get_idx("phone") + 1 if "phone" in auto_cols else 0,
                    key="mw_phone",
                )

                mapping = {
                    "name": m_name,
                    "cost": m_cost,
                    "qty": m_qty,
                    "date": m_date if m_date != "None" else None,
                    "order_id": m_order if m_order != "None" else None,
                    "phone": m_phone if m_phone != "None" else None,
                }

                st.dataframe(df.head(5), use_container_width=True)

            if st.button("🔥 Generate Engine Insights", use_container_width=True):
                results = process_analytics(df, mapping, mode=mode)
                
                # --- Metrics Row ---
                st.subheader(f"📊 {mode} Summary: {results['timeframe']}")
                m1, m2, m3, m4 = st.columns(4)
                
                if mode == "Sales Performance":
                    b = results["basket"]
                    m1.metric("Orders", f"{b['total_orders']:,}" if b["total_orders"] > 0 else "N/A")
                    m2.metric("Units Sold", f"{results['total_qty']:,.0f}")
                    m3.metric("Total Revenue", f"TK {results['total_rev']:,.0f}")
                    m4.metric("Avg Basket", f"TK {b['avg_value']:,.0f}" if b["avg_value"] > 0 else "N/A")
                else:
                    m1.metric("SKU Count", f"{len(df):,}")
                    m2.metric("Stock Qty", f"{results['total_qty']:,.0f}")
                    m3.metric("Stock Value", f"TK {results['total_rev']:,.0f}")
                    m4.metric("Avg/SKU", f"{results['total_qty']/len(df):,.1f}" if len(df) > 0 else "N/A")

                st.divider()

                # --- Tabbed Deep Dive ---
                t_overview, t_trends, t_basket, t_rankings, t_data = st.tabs([
                    "📌 Overview", 
                    "📈 Trends", 
                    "🧺 Basket Insights", 
                    "🏆 Product Rankings", 
                    "📑 Full Data"
                ])

                with t_overview:
                    v1, v2 = st.columns(2)
                    summ_sorted = results["summary"].sort_values("Total Amount", ascending=False)
                    label_prefix = "Revenue" if mode == "Sales Performance" else "Value"
                    
                    # Enhanced Donut Chart
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=summ_sorted["Category"],
                        values=summ_sorted["Total Amount"],
                        hole=.5,
                        textinfo='percent+label',
                        marker=dict(colors=px.colors.qualitative.Pastel)
                    )])
                    fig_pie.update_layout(title=f"{label_prefix} Distribution", margin=dict(t=40, b=10, l=10, r=10))
                    v1.plotly_chart(fig_pie, use_container_width=True)

                    # Category Qty Bar
                    fig_bar = px.bar(
                        results["summary"].sort_values("Total Qty", ascending=False),
                        x="Category", y="Total Qty",
                        color="Category",
                        title="Volume by Category",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    v2.plotly_chart(fig_bar, use_container_width=True)

                with t_trends:
                    if not results["trend_df"].empty:
                        df_trend = results["trend_df"]
                        fig_trend = go.Figure()
                        fig_trend.add_trace(go.Scatter(
                            x=df_trend[mapping["date"]], y=df_trend["Total Amount"],
                            mode='lines+markers', name='Revenue',
                            line=dict(color='#1d4ed8', width=3)
                        ))
                        fig_trend.update_layout(
                            title="Performance Trend",
                            xaxis_title="Timeline",
                            yaxis_title="Amount (TK)",
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_trend, use_container_width=True)
                        
                        # Qty Trend
                        fig_qty = px.area(
                            df_trend, x=mapping["date"], y="Clean_Qty",
                            title="Volume Trend",
                            color_discrete_sequence=['#10b981']
                        )
                        st.plotly_chart(fig_qty, use_container_width=True)
                    else:
                        st.info("No valid date column provided for trend analysis.")

                with t_basket:
                    if mode == "Sales Performance" and results["basket"]["total_orders"] > 0:
                        b = results["basket"]
                        c1, c2 = st.columns([2, 3])
                        with c1:
                            st.write("### 🧺 Basket Composition")
                            st.metric("Avg Basket Value", f"TK {b['avg_value']:,.2f}")
                            st.metric("Total Order Sample", f"{b['total_orders']:,}")
                            
                        with c2:
                            if b["bundles"]:
                                st.write("### 🤝 Top Category Bundles")
                                bundles_df = pd.DataFrame(list(b["bundles"].items()), columns=["Bundle", "Occurrences"])
                                fig_bundles = px.bar(
                                    bundles_df, x="Occurrences", y="Bundle",
                                    orientation='h', title="Common Cross-Purchases",
                                    color_discrete_sequence=['#8b5cf6']
                                )
                                st.plotly_chart(fig_bundles, use_container_width=True)
                            else:
                                st.info("Not enough multi-item orders for bundle analysis.")
                    else:
                        st.info("Basket analysis requires Order ID or Phone number for grouping products into orders.")

                with t_rankings:
                    st.write("### 🏆 Top 25 Products")
                    st.dataframe(results["top_items"].head(25), use_container_width=True)
                    
                    # Treemap of categories vs products
                    fig_tree = px.treemap(
                        results["top_items"].head(100),
                        path=["Category", "Product Name"],
                        values="Total Amount",
                        title="Category & Product Hierarchy (Top 100)",
                        color="Total Amount",
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig_tree, use_container_width=True)

                with t_data:
                    st.write("### 📑 Categorized Data")
                    st.dataframe(results["summary"].sort_values("Total Amount", ascending=False), use_container_width=True)
                    st.write("### 🔍 Price Point Breakdown")
                    st.dataframe(results["drilldown"], use_container_width=True)

                # --- Export Actions ---
                st.divider()
                buf = BytesIO()
                with pd.ExcelWriter(buf, engine="xlsxwriter") as wr:
                    results["summary"].to_excel(wr, sheet_name="Category Summary", index=False)
                    results["top_items"].to_excel(wr, sheet_name="Product Rankings", index=False)
                    results["drilldown"].to_excel(wr, sheet_name="Price Points", index=False)
                    if not results["trend_df"].empty:
                        results["trend_df"].to_excel(wr, sheet_name="Trends", index=False)

                fname = f"CatwiseReport_{results['timeframe'].replace(' ', '_')}.xlsx"
                st.download_button(
                    "📥 Export Comprehensive Analysis",
                    data=buf.getvalue(),
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        except Exception as e:
            st.exception(e)
