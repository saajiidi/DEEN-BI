import streamlit as st
import pandas as pd
import plotly.express as px
from .orders_analytics_lib.woo_api import WooCommerceClient
from .orders_analytics_lib.filters import apply_filters
from .orders_analytics_lib.utils import classify_trend, format_currency, get_date_range
from datetime import datetime

def render_orders_analytics_tab():
    st.header("📊 Orders Analytics Dashboard")
    st.caption("Deep-dive sales analytics with 7-cluster filtering and trend insights.")

    # Initialize API Client
    # Note: WooCommerceClient uses st.secrets["woocommerce"] which is already configured
    client = WooCommerceClient()

    # --- TOP LEVEL FILTERS (Optional: could stay in sidebar or top) ---
    # To fit into the main app's structure, we might want some filters in the sidebar 
    # and some in the main area. For now, let's keep the UI consistent with the request.

    with st.expander("🔍 Filter Controls", expanded=True):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            time_option = st.selectbox(
                "Time Frame",
                ["Last 7 Days", "Last 15 Days", "Last 30 Days", "Last 3 Months", "Last 6 Months", "Last 1 Year", "Custom Frame"],
                key="oa_time_frame"
            )
            custom_start, custom_end = None, None
            if time_option == "Custom Frame":
                custom_start = st.date_input("Start Date", key="oa_start")
                custom_end = st.date_input("End Date", key="oa_end")

        after, before = get_date_range(time_option, custom_start, custom_end)

        # Fetch Data (with caching via st.cache_data inside the client)
        with st.spinner("Fetching data from WooCommerce..."):
            raw_orders = client.fetch_orders(after=after, before=before)
            products = client.fetch_products()
            categories_raw = client.fetch_categories()
            categories = [c['name'] for c in categories_raw]

        if not raw_orders:
            st.warning("No orders found for the selected time frame.")
            return

        with c2:
            all_skus = sorted(list(set([item['sku'] for order in raw_orders for item in order.get('line_items', []) if item.get('sku')])))
            selected_cats = st.multiselect("Categories", categories, key="oa_cats")
            selected_skus = st.multiselect("SKUs", all_skus, key="oa_skus")

        with c3:
            platforms = st.multiselect("Platform/Location", ["E-commerce", "Outlets", "WhatsApp", "Facebook"], default=["E-commerce", "Outlets"], key="oa_plats")
            bundle_only = st.checkbox("Bundled Orders Only", value=False, key="oa_bundle")

    # Variant & Price filters in another section or sidebar
    with st.expander("🎨 Variant & Price Filters", expanded=False):
        v1, v2, v3, v4 = st.columns(4)
        
        colors = sorted(list(set([m['value'] for o in raw_orders for i in o.get('line_items', []) for m in i.get('meta_data', []) if m['key'] in ['pa_color', 'Color']])))
        sizes = sorted(list(set([m['value'] for o in raw_orders for i in o.get('line_items', []) for m in i.get('meta_data', []) if m['key'] in ['pa_size', 'Size']])))
        fits = sorted(list(set([m['value'] for o in raw_orders for i in o.get('line_items', []) for m in i.get('meta_data', []) if m['key'] in ['pa_fit', 'Fit']])))
        
        with v1: selected_colors = st.multiselect("Colors", colors, key="oa_colors")
        with v2: selected_sizes = st.multiselect("Sizes", sizes, key="oa_sizes")
        with v3: selected_fits = st.multiselect("Fits", fits, key="oa_fits")
        with v4: price_range = st.slider("Price Range (BDT)", 0, 20000, (0, 20000), key="oa_price")

    # Campaign Filters
    all_coupons = sorted(list(set([c.get('code') for o in raw_orders for c in o.get('coupon_lines', [])])))
    selected_coupons = st.multiselect("Filter by Coupons", all_coupons, key="oa_coupons")

    # Collect all filters
    filters_dict = {
        "categories": selected_cats,
        "skus": selected_skus,
        "colors": selected_colors,
        "sizes": selected_sizes,
        "fits": selected_fits,
        "price_range": price_range,
        "platforms": platforms,
        "coupons": selected_coupons,
        "is_bundle": True if bundle_only else None
    }

    # Apply Filtering
    df = apply_filters(raw_orders, products, filters_dict)

    if df.empty:
        st.error("No data matches the selected filters.")
        return

    # Trend Type Filter Logic
    trend_data = df.groupby("sku")["quantity"].sum().reset_index()
    trend_data["trend"] = trend_data["quantity"].apply(classify_trend)
    
    selected_trends = st.multiselect("Filter by Trend Type", ["Fast Moving", "Slow Moving", "Non-Moving"], default=["Fast Moving", "Slow Moving", "Non-Moving"], key="oa_trends")
    
    # Map trend back to main DF
    df = df.merge(trend_data[["sku", "trend"]], on="sku", how="left")
    df = df[df["trend"].isin(selected_trends)]

    if df.empty:
        st.warning("No data matches the selected Trend filters.")
        return

    # 3. View Selection Tabs
    view1, view2 = st.tabs(["📈 Performance Analytics", "🛒 WooCommerce Style Order List"])

    with view1:
        # 1. Key Metrics
        m1, m2, m3, m4 = st.columns(4)
        total_sales = df["item_total"].sum()
        total_orders = df["order_id"].nunique()
        total_units = df["quantity"].sum()
        avg_order_val = total_sales / total_orders if total_orders > 0 else 0

        m1.metric("Total Sales", format_currency(total_sales))
        m2.metric("Orders", f"{total_orders:,}")
        m3.metric("Units Sold", f"{total_units:,}")
        m4.metric("Avg Order Value", format_currency(avg_order_val))

        st.divider()

        # 2. Charts
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Sales by Trend Type")
            trend_sales = df.groupby("trend")["item_total"].sum().reset_index()
            fig_trend = px.pie(trend_sales, values="item_total", names="trend", hole=0.4, 
                               color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_trend.update_layout(showlegend=True, margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig_trend, use_container_width=True)

        with c2:
            st.subheader("Platform Distribution")
            plat_sales = df.groupby("platform")["item_total"].sum().reset_index()
            fig_plat = px.bar(plat_sales, x="platform", y="item_total", 
                              color="platform", color_discrete_sequence=px.colors.qualitative.Bold)
            st.plotly_chart(fig_plat, use_container_width=True)

        # 3. Tables
        with st.expander("📋 Top Products & Order Details", expanded=True):
            t1, t2 = st.tabs(["Top Products", "Raw Order Items"])
            with t1:
                top_prods = df.groupby(["sku", "product_name", "trend"])["quantity"].sum().reset_index().sort_values("quantity", ascending=False).head(15)
                st.dataframe(top_prods, use_container_width=True)
            with t2:
                st.dataframe(df[["date", "order_id", "sku", "product_name", "quantity", "price", "item_total", "trend", "platform"]], use_container_width=True)

    with view2:
        render_woo_mimic_list(raw_orders)

def render_woo_mimic_list(orders):
    """
    Renders a table mimicking the WordPress WooCommerce order list.
    """
    st.subheader("Order Processing Terminal")
    st.markdown("""
        <style>
        .woo-table { width: 100%; border-collapse: collapse; font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen-Sans,Ubuntu,Cantarell,"Helvetica Neue",sans-serif; }
        .woo-table th { background: #fdfdfd; text-align: left; padding: 10px; border-bottom: 2px solid #e5e5e5; color: #32373c; font-size: 14px; }
        .woo-table td { padding: 12px 10px; border-bottom: 1px solid #e5e5e5; vertical-align: middle; color: #32373c; font-size: 13px; }
        .status-processing { background: #c6e1c6; color: #1e4620; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; text-transform: uppercase; }
        .status-pending { background: #f8dda7; color: #94660c; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; text-transform: uppercase; }
        .order-link { color: #0073aa; font-weight: 600; text-decoration: none; }
        .order-link:hover { color: #00a0d2; }
        </style>
    """, unsafe_allow_html=True)

    # Filter for Processing orders primarily
    status_filter = st.multiselect("Filter by Status", ["processing", "pending", "on-hold", "completed", "cancelled"], default=["processing"], key="woo_mimic_status")
    
    filtered_orders = [o for o in orders if o.get("status") in status_filter]

    if not filtered_orders:
        st.info("No orders found matching the selected status.")
        return

    # Build the HTML Table
    html = '<table class="woo-table"><thead><tr>'
    html += '<th>Order</th><th>Date</th><th>Status</th><th>Total</th><th>Payment</th>'
    html += '</tr></thead><tbody>'

    for order in filtered_orders:
        oid = order.get("id")
        date_obj = datetime.fromisoformat(order.get("date_created").replace("Z", "+00:00"))
        date_str = date_obj.strftime("%b %d, %Y")
        status = order.get("status")
        total = order.get("total")
        currency = order.get("currency_symbol", "৳")
        customer = f"{order.get('billing', {}).get('first_name', '')} {order.get('billing', {}).get('last_name', '')}"
        payment = order.get("payment_method_title", "N/A")

        status_class = f"status-{status}" if status in ["processing", "pending"] else ""
        
        html += f"""
            <tr>
                <td><a class="order-link" href="#">#{oid} {customer}</a></td>
                <td>{date_str}</td>
                <td><span class="{status_class}">{status}</span></td>
                <td>{currency}{total}</td>
                <td>{payment}</td>
            </tr>
        """
    
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)
