import pandas as pd
import streamlit as st
from .data_display import _safe_datetime_series


def skeleton_metric(icon: str = "📊"):
    """Skeleton loading state for metric cards - renders instantly while data loads."""
    st.markdown(
        f"""
        <div class="hub-card metric-icon-card" style="opacity: 0.7;">
          <div class="metric-icon-wrap" style="animation: pulse 1.5s infinite;">{icon}</div>
          <div class="metric-content">
            <div class="metric-highlight-label" style="background: linear-gradient(90deg, #e2e8f0 25%, #cbd5e1 50%, #e2e8f0 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; height: 14px; width: 80px; border-radius: 4px; margin-bottom: 8px;"></div>
            <div class="metric-highlight-value" style="background: linear-gradient(90deg, #e2e8f0 25%, #cbd5e1 50%, #e2e8f0 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; height: 28px; width: 100px; border-radius: 4px;"></div>
          </div>
        </div>
        <style>
          @keyframes shimmer {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
          }}
          @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def skeleton_row(count: int = 6):
    """Render multiple skeleton metric cards in a row."""
    cols = st.columns(count)
    icons = ["📦", "💰", "🛒", "📅", "👥", "💎"]
    for i, col in enumerate(cols):
        with col:
            skeleton_metric(icon=icons[i % len(icons)])















def badge(note: str):
    if not note:
        return
    st.markdown(f'<div class="bi-kpi-note">{note}</div>', unsafe_allow_html=True)




def icon_metric(label: str, value: str, icon: str = "📊", delta: str = "", delta_val: float = 0, loading: bool = False):
    """Render metric card with optional loading skeleton state."""
    if loading:
        skeleton_metric(icon=icon)
        return

    delta_class = "delta-up" if delta_val >= 0 else "delta-down"
    delta_icon = "↑" if delta_val >= 0 else "↓"
    delta_html = f'<div class="metric-delta {delta_class}">{delta_icon} {delta}</div>' if delta else ""

    st.markdown(
        f"""
        <div class="hub-card metric-icon-card">
          <div class="metric-icon-wrap">{icon}</div>
          <div class="metric-content">
            <div class="metric-highlight-label">{label}</div>
            <div class="metric-highlight-value" style="font-size: 1.8rem;">{value}</div>
            {delta_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_highlight(label: str, value: str, delta: str = "", delta_type: str = "up", help_text: str = "", icon: str = None):
    """Premium Enterprise KPI card with glassmorphism, motion transitions, and optional icon."""
    delta_icon = "↑" if delta_type == "up" else "↓"
    delta_color = "#10b981" if delta_type == "up" else "#ef4444"
    
    delta_html = f'<div style="display: flex; align-items: center; gap: 4px; color: {delta_color}; font-size: 0.85rem; font-weight: 700; margin-top: 4px;"><span>{delta_icon} {delta}</span></div>' if delta else ""
    help_block = f'<div style="color: #64748b; font-size: 0.75rem; margin-top: 8px; font-weight: 500;">{help_text}</div>' if help_text else ""
    icon_html = f'<div style="font-size: 1.2rem; opacity: 0.8;">{icon}</div>' if icon else ""
    
    html_content = f"""
    <div class="hub-card metric-highlight">
        <div style="display: flex; justify-content: space-between; align-items: start; width: 100%;">
            <div class="metric-highlight-label">{label}</div>
            {icon_html}
        </div>
        <div class="metric-highlight-value" style="margin-top: 5px;">{value}</div>
        {delta_html}
        {help_block}
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)












def date_context(
    requested_start=None,
    requested_end=None,
    loaded_start=None,
    loaded_end=None,
    label: str = "Loaded data",
):
    requested_parts = []
    if requested_start is not None:
        requested_parts.append(f"from {pd.to_datetime(requested_start).strftime('%Y-%m-%d')}")
    if requested_end is not None:
        requested_parts.append(f"to {pd.to_datetime(requested_end).strftime('%Y-%m-%d')}")
    requested_text = " ".join(requested_parts).strip()
    prefix = f"Requested range: {requested_text}" if requested_text else "Requested range: not specified"

    loaded_start_series = _safe_datetime_series(loaded_start)
    loaded_end_series = _safe_datetime_series(loaded_end)
    loaded_start_ts = loaded_start_series.min() if not loaded_start_series.empty and loaded_start_series.notna().any() else pd.NaT
    loaded_end_ts = loaded_end_series.max() if not loaded_end_series.empty and loaded_end_series.notna().any() else pd.NaT
    if pd.notna(loaded_start_ts) and pd.notna(loaded_end_ts):
        st.caption(
            f"{prefix} | {label}: {loaded_start_ts.strftime('%Y-%m-%d %H:%M')} to {loaded_end_ts.strftime('%Y-%m-%d %H:%M')}"
        )
    else:
        st.caption(f"{prefix} | {label}: dates are not available in the current result.")











def operational_card(title: str, order_count: int, item_count: int, revenue: float, icon: str = "📦", delta_text: str = "", delta_val: int = 0, item_label: str = "Items", is_alert: bool = False):
    """Premium multi-line operational metric card with optional alert pulse."""
    delta_class = "delta-up" if delta_val >= 0 else "delta-down"
    delta_icon = "↑" if delta_val >= 0 else "↓"
    delta_html = f'<div class="{delta_class}" style="margin-top:8px; font-size:0.85rem; font-weight:700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{delta_icon} {delta_text}</div>' if delta_text else ""

    pulse_css = "animation: pulse-amber 2s infinite;" if is_alert else ""
    border_style = "2px solid #F59E0B" if is_alert else "1px solid var(--outline)"

    st.markdown(
        f"""
        <style>
        @keyframes pulse-amber {{
            0% {{ box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.4); }}
            70% {{ box-shadow: 0 0 0 10px rgba(245, 158, 11, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }}
        }}
        .op-card {{
            padding: 1.25rem;
            height: 140px;
            min-height: 140px;
            max-height: 140px;
            background: var(--surface);
            border-radius: 16px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            overflow: hidden;
            box-sizing: border-box;
        }}
        .op-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 20px -5px rgba(0,0,0,0.1);
            border-color: var(--primary);
        }}
        </style>
        <div class="op-card" style="{pulse_css} border: {border_style};">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="font-size: 0.95rem; font-weight: 700; color: var(--on-surface); line-height: 1.2; letter-spacing: -0.01em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{title}</div>
                <div style="font-size: 1.5rem; opacity: 0.9; flex-shrink: 0;">{icon}</div>
            </div>
            <div style="margin-top: 8px;">
                <div style="display: flex; gap: 12px; margin-bottom: 4px;">
                    <div style="font-size: 0.8rem; color: var(--on-surface-variant); font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Orders: <span style="color: var(--on-surface);">{order_count:,}</span></div>
                    <div style="font-size: 0.8rem; color: var(--on-surface-variant); font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{item_label}: <span style="color: var(--on-surface);">{item_count:,}</span></div>
                </div>
                <div style="font-size: 1.5rem; font-weight: 800; color: var(--primary); letter-spacing: -0.03em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">TK {revenue:,.0f}</div>
                {delta_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
