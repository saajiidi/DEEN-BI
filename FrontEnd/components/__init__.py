"""Frontend Components Module

Reusable UI components for the Streamlit application.
"""

from .ui_components import (
    inject_base_styles,
    render_action_bar,
    render_audit_card,
    render_bi_hero,
    render_commentary_panel,
    render_footer,
    render_header,
    render_highlight_stat,
    render_kpi_note,
    render_loaded_date_context,
    render_reset_confirm,
    render_section_card,
    render_sidebar_branding,
    to_excel_bytes,
)
from .animation import render_bike_animation
from .ai_chatbot import render_floating_ai_chat

# Backward-compatible alias for older imports.
section_card = render_section_card

__all__ = [
    "inject_base_styles",
    "render_action_bar",
    "render_audit_card",
    "render_bi_hero",
    "render_commentary_panel",
    "render_reset_confirm",
    "render_footer",
    "render_header",
    "render_highlight_stat",
    "render_kpi_note",
    "render_loaded_date_context",
    "render_section_card",
    "render_sidebar_branding",
    "section_card",
    "to_excel_bytes",
    "render_bike_animation",
    "render_floating_ai_chat",
]
