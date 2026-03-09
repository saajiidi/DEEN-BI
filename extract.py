import os

with open("app.py", "r", encoding="utf-8") as f:
    lines = f.read().split("\n")

out = [
    "import io",
    "import pandas as pd",
    "import streamlit as st",
    "from app_modules.wp_processor import WhatsAppOrderProcessor",
    "from app_modules.error_handler import log_error",
    "",
    "def render_wp_tab():"
]

for l in lines[454:492]:
    out.append("    " + l if l else "")

with open("app_modules/wp_tab.py", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("Extracted wp_tab.py!")
