import os
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st

from app_modules.ui_config import APP_TITLE, APP_VERSION


def inject_base_styles():
    st.markdown(
        """
        <style>
        :root {
            --primary: var(--primary-color, #1d4ed8);
            --surface: var(--background-color, #f8fafc);
            --border: var(--secondary-background-color, #dbeafe);
            --text-muted: var(--text-color, #64748b);
            --step-surface: var(--background-color, #ffffff);
            --step-text: var(--text-color, #0f172a);
            --step-active-bg: var(--secondary-background-color, #eff6ff);
            --action-surface: var(--background-color, rgba(255, 255, 255, 0.96));
            --card-shadow: rgba(0, 0, 0, 0.15);
        }
        .hub-title-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 2px solid var(--border);
            padding: 8px 0 12px 0;
            margin-bottom: 8px;
        }
        .hub-title {
            margin: 0;
            font-weight: 700;
        }
        .hub-subtitle {
            margin: 0;
            color: var(--text-muted);
            font-size: 0.95rem;
        }
        .hub-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 12px;
            box-shadow: 0 8px 24px var(--card-shadow);
        }
        .hub-step {
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 8px 10px;
            font-size: 0.9rem;
            background: var(--step-surface);
            color: var(--step-text);
        }
        .hub-step.active {
            border-color: var(--primary);
            background: var(--step-active-bg);
            font-weight: 600;
        }
        .hub-action-wrap {
            position: sticky;
            bottom: 0;
            padding: 10px;
            border: 1px solid var(--border);
            border-radius: 10px;
            background: var(--action-surface);
            backdrop-filter: blur(3px);
            z-index: 10;
        }
        @media (max-width: 900px) {
            .block-container {
                padding-left: 0.75rem !important;
                padding-right: 0.75rem !important;
            }
            .hub-title {
                font-size: 1.35rem !important;
                line-height: 1.3;
            }
            .hub-subtitle {
                font-size: 0.85rem !important;
            }
            .hub-card {
                padding: 10px 12px;
                border-radius: 10px;
            }
            .hub-step {
                font-size: 0.78rem;
                padding: 6px 8px;
                min-height: 46px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
            }
            .hub-action-wrap {
                position: static;
                margin-top: 6px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    st.markdown(
        f"""
        <div class="hub-title-row">
          <div>
            <h1 class="hub-title">{APP_TITLE} <span style="color:#1d4ed8;">{APP_VERSION}</span></h1>
            <p class="hub-subtitle">Unified logistics operations workspace</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_card(title: str, help_text: str = ""):
    st.markdown(
        f"""
        <div class="hub-card">
          <div style="font-weight:600;">{title}</div>
          <div style="color:var(--text-muted); margin-top:4px;">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_steps(steps: list[str], current_step: int):
    cols = st.columns(len(steps))
    for idx, step in enumerate(steps):
        is_active = idx == current_step
        cls = "hub-step active" if is_active else "hub-step"
        cols[idx].markdown(f'<div class="{cls}">{idx + 1}. {step}</div>', unsafe_allow_html=True)


def render_file_summary(uploaded_file, df: pd.DataFrame | None, required_columns: list[str]):
    if not uploaded_file:
        st.info("No file uploaded yet.")
        return False

    st.caption(f"File: {uploaded_file.name}")
    if df is None:
        st.warning("Could not read this file.")
        return False

    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", len(df))
    c2.metric("Columns", len(df.columns))
    c3.metric("Required", len(required_columns))

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
        return False
    st.success("Required columns check passed.")
    return True


def render_action_bar(
    primary_label: str,
    primary_key: str,
    secondary_label: str | None = None,
    secondary_key: str | None = None,
):
    st.markdown('<div class="hub-action-wrap">', unsafe_allow_html=True)
    if secondary_label and secondary_key:
        c1, c2 = st.columns([2, 1])
        primary_clicked = c1.button(primary_label, type="primary", use_container_width=True, key=primary_key)
        secondary_clicked = c2.button(secondary_label, use_container_width=True, key=secondary_key)
    else:
        primary_clicked = st.button(primary_label, type="primary", use_container_width=True, key=primary_key)
        secondary_clicked = False
    st.markdown("</div>", unsafe_allow_html=True)
    return primary_clicked, secondary_clicked


def render_reset_confirm(state_key: str, reset_fn):
    if st.button("Reset current workflow", key=f"reset_{state_key}"):
        st.session_state[f"confirm_reset_{state_key}"] = True

    if st.session_state.get(f"confirm_reset_{state_key}"):
        st.warning("Confirm reset: this clears current workflow data.")
        c1, c2 = st.columns(2)
        if c1.button("Confirm reset", key=f"confirm_yes_{state_key}", type="primary"):
            reset_fn()
            st.session_state[f"confirm_reset_{state_key}"] = False
            st.success("Workflow reset complete.")
            st.rerun()
        if c2.button("Cancel", key=f"confirm_no_{state_key}"):
            st.session_state[f"confirm_reset_{state_key}"] = False


def sample_file_download(label: str, data: list[dict], file_name: str):
    df = pd.DataFrame(data)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=label,
        data=csv_bytes,
        file_name=file_name,
        mime="text/csv",
        use_container_width=True,
    )


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    output.seek(0)
    return output.read()


def show_last_updated(path: str):
    if not os.path.exists(path):
        return
    updated = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
    st.caption(f"Last updated: {updated}")
