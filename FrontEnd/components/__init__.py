"""Frontend Components Module

Reusable UI components for the Streamlit application.
"""

from .ui_components import (
    inject_base_styles,
    action_bar,
    audit_card,
    bi_hero,
    commentary_panel,
    footer,
    header,
    highlight_stat,
    kpi_note,
    loaded_date_context,
    reset_confirm,
    section_card,
    sidebar_branding,
    to_excel_bytes,
)
from .animation import bike_animation
from .ai_chatbot import floating_ai_chat

# Backward-compatible alias for older imports.
section_card = section_card

__all__ = [
    "inject_base_styles",
    "action_bar",
    "audit_card",
    "bi_hero",
    "commentary_panel",
    "reset_confirm",
    "footer",
    "header",
    "highlight_stat",
    "kpi_note",
    "loaded_date_context",
    "section_card",
    "sidebar_branding",
    "section_card",
    "to_excel_bytes",
    "bike_animation",
    "floating_ai_chat",
]
