import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from BackEnd.services.woocommerce_service import WooCommerceService

def render_woocommerce_tab():
    """Render the WooCommerce data pull tab."""
    st.header("🛍️ WooCommerce Connector")
    
    # 1. UI: Configuration Status
    if "woocommerce" not in st.secrets:
        st.warning("⚠️ WooCommerce secrets not found in `.streamlit/secrets.toml`.")
        st.info("To enable this integration, add your API keys to `.streamlit/secrets.toml`:")
        st.code("""
[woocommerce]
store_url = "https://your-store.com"
consumer_key = "ck_your_consumer_key_here"
consumer_secret = "cs_your_consumer_secret_here"
        """)
        return

    # 2. Connection Check
    wc_service = WooCommerceService()
    
    st.success("✅ WooCommerce Secrets Loaded.")

    # 3. Pull Functionality
    st.subheader("📥 Historical Data Pull")
    st.info("Fetch orders from your WooCommerce store and save them as manageable data files.")
    
    with st.expander("Configure Fetch Parameters", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now())
            
        status_filter = st.selectbox("Order Status", ["any", "completed", "processing", "on-hold", "pending"], index=0)
        
        fetch_btn = st.button("Start Historical Sync", use_container_width=True, type="primary")
        
        if fetch_btn:
            # Format dates for API (WooCommerce expects ISO8601)
            after = start_date.strftime("%Y-%m-%dT00:00:00")
            before = end_date.strftime("%Y-%m-%dT23:59:59")
            
            with st.status("Fetching orders from WooCommerce API...", expanded=True) as status:
                try:
                    # Recursive fetch
                    df = wc_service.fetch_all_historical_orders(after=after)
                    
                    if not df.empty:
                        status.update(label=f"✅ Successfully fetched {len(df)} line items!", state="complete")
                        
                        # Display preview
                        st.subheader("Data Preview")
                        st.dataframe(df.head(20), use_container_width=True)
                        
                        # Save
                        if st.button("Save to System Data Storage", use_container_width=True, type="secondary"):
                            wc_service.save_to_parquet(df)
                            st.balloons()
                            st.success("Data committed to system storage. It will now be available in the Dashboard and analytics.")
                    else:
                        status.update(label="❌ No orders found in the selected range.", state="error")
                        st.info("Check your date filters or WooCommerce store status.")
                except Exception as e:
                    status.update(label=f"⚠️ Error: {str(e)}", state="error")
                    st.error(f"Sync failed: {e}")

    # 4. Data Management Summary
    st.divider()
    st.subheader("📊 Storage Audit")
    
    from BackEnd.services.duckdb_loader import get_data_completeness
    try:
        completeness = get_data_completeness()
        if not completeness.empty:
            st.write("Current data availability by year:")
            st.dataframe(completeness, use_container_width=True)
        else:
            st.info("No data currently indexed in the system.")
    except Exception as e:
        st.caption(f"Could not load storage audit: {e}")
