import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from BackEnd.services.strategic_intelligence import (
    detect_business_anomalies, 
    calculate_rfm_churn_risk
)

def render_war_room_page(sales_df: pd.DataFrame, returns_df: pd.DataFrame):
    """Business Intelligence War-Room for pro-active anomaly detection and strategy."""
    
    st.markdown('<div class="live-indicator"><span class="live-dot" style="background:#ef4444;"></span>Active Risk Monitoring Enabled</div>', unsafe_allow_html=True)
    
    # --- 1. PROACTIVE ANOMALIES ---
    st.subheader("🚨 Proactive Anomaly Detection")
    anomalies = detect_business_anomalies(sales_df, returns_df)
    
    if not anomalies:
        st.success("✅ No critical operational anomalies detected in the current window.")
    else:
        for anomaly in anomalies:
            color = "#ef4444" if anomaly['level'] == "CRITICAL" else "#f59e0b"
            with st.container():
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.05); border-left: 5px solid {color}; padding: 15px; border-radius: 8px; margin-bottom: 12px;">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="font-weight:800; color:{color}; text-transform:uppercase; font-size:0.75rem;">{anomaly['category']} | {anomaly['level']}</span>
                    </div>
                    <div style="font-size:1.1rem; font-weight:700; margin: 5px 0;">{anomaly['title']}</div>
                    <div style="font-size:0.85rem; opacity:0.8;">{anomaly['description']}</div>
                    <div style="margin-top:10px; font-size:0.8rem; font-weight:600; color:{color};">⚡ Suggested Action: {anomaly['action']}</div>
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    # --- 2. THE STRATEGY SIMULATOR ---
    st.subheader("🔮 Strategy 'What-If' Simulator")
    st.info("Simulate how operational improvements impact your monthly Net Sales bottom line.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🎚️ Adjusted Settings")
        rev_growth = st.slider("Monthly Revenue Growth (%)", -20, 50, 0)
        ret_reduction = st.slider("Return Rate Reduction (%)", 0, 80, 0)
        partial_conversion = st.slider("Partial -> Full Order Conversion (%)", 0, 50, 0)
        
    with col2:
        # Base metrics (Mocked or calculated from current window)
        current_rev = sales_df['item_revenue'].sum() if not sales_df.empty else 1000000
        current_ret_rate = (len(returns_df) / len(sales_df['order_id'].unique()) * 100) if not sales_df.empty and not returns_df.empty else 12.0
        
        # Simulation Logic
        sim_rev = current_rev * (1 + rev_growth/100)
        new_ret_rate = current_ret_rate * (1 - ret_reduction/100)
        savings_from_returns = current_rev * (current_ret_rate - new_ret_rate)/100
        
        sim_net_gain = (sim_rev - current_rev) + savings_from_returns
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #1e1b4b 100%); padding: 30px; border-radius: 12px; text-align: center; border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size:0.9rem; text-transform:uppercase; letter-spacing:1px; opacity:0.8;">Projected Monthly Net Gain</div>
            <div style="font-size:3rem; font-weight:800; color:#10b981; margin: 10px 0;">৳{sim_net_gain:,.0f}</div>
            <div style="font-size:0.85rem; opacity:0.7;">Based on current operational baseline of ৳{current_rev/100000:.1f}L/mo</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Micro Chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = sim_rev,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Revenue Target", 'font': {'size': 16}},
            delta = {'reference': current_rev, 'increasing': {'color': "#10b981"}},
            gauge = {
                'axis': {'range': [None, current_rev*2]},
                'bar': {'color': "#3b82f6"},
                'steps': [
                    {'range': [0, current_rev], 'color': "rgba(255,255,255,0.1)"},
                    {'range': [current_rev, current_rev*1.5], 'color': "rgba(16, 185, 129, 0.2)"}
                ],
            }
        ))
        fig.update_layout(height=180, margin=dict(l=20,r=20,t=40,b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- 3. VIP CHURN RISK ---
    st.subheader("👥 VIP Retention Engine (Churn Risk)")
    churn_df = calculate_rfm_churn_risk(sales_df)
    
    if churn_df.empty:
        st.info("No high-risk VIP churn detected. Retention is healthy.")
    else:
        st.warning(f"Detected {len(churn_df)} VIP customers at risk of churn.")
        
        # Display as a clean table with action button
        display_df = churn_df.copy()
        display_df['recency'] = display_df['recency'].astype(str) + " days ago"
        display_df.columns = ["Customer Key", "Last Purchase", "Orders", "Total Value", "Segments", "Risk Level"]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        c1, c2 = st.columns([1, 1])
        with c1:
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download VIP Re-engagement List",
                csv,
                "high_risk_vips.csv",
                "text/csv",
                use_container_width=True
            )
        with c2:
            st.button("🔔 Send Retention Notification (Mock)", use_container_width=True, disabled=True)
