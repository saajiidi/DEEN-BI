import streamlit as st
from BackEnd.commerce_ops.pathao_tab import render_pathao_tab
from BackEnd.commerce_ops.distribution_tab import render_distribution_tab
from BackEnd.commerce_ops.wp_tab import render_wp_tab
from BackEnd.commerce_ops.fuzzy_parser_tab import render_fuzzy_parser_tab
from BackEnd.commerce_ops.bike_animation import render_bike_animation

def render_operations_hub_tab():
    render_bike_animation()
    st.header("⚙️ Operations Hub")
    st.caption("Unified operational tools for logistics, messaging, and inventory distribution.")

    ops_tabs = st.tabs([
        "📦 Pathao Processor",
        "📊 Inventory Distribution",
        "💬 WhatsApp Messaging",
        "🧩 Delivery Data Parser"
    ])

    with ops_tabs[0]:
        render_pathao_tab()

    with ops_tabs[1]:
        render_distribution_tab()

    with ops_tabs[2]:
        render_wp_tab()

    with ops_tabs[3]:
        render_fuzzy_parser_tab()
