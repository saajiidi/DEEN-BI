import re

import pandas as pd


# --- File Upload Logic ---
def read_uploaded_file(uploaded_file) -> pd.DataFrame | None:
    """Read an uploaded CSV or Excel file into a DataFrame.

    Args:
        uploaded_file: Streamlit UploadedFile object

    Returns:
        DataFrame or None if no file provided
    """
    if not uploaded_file:
        return None
    uploaded_file.seek(0)
    if uploaded_file.name.lower().endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)


# --- Category Logic ---
def get_category_from_name(name):
    """
    Determines the category/sub-category for commerce operations using centralized logic.
    For daily reports, returns the SHORT sub-category name as requested.
    """
    try:
        from BackEnd.core.categories import get_category_for_sales, get_subcategory_name
        full_cat = get_category_for_sales(name)
        return get_subcategory_name(full_cat)
    except:
        return "Items"


# --- Address Logic ---
def normalize_city_name(city_name):
    """
    Standardizes city/district names to match Pathao specific formats or correct spelling.
    """
    if not city_name:
        return ""

    c = city_name.strip()
    c_lower = c.lower()

    # User requested mappings
    if "brahmanbaria" in c_lower:
        return "B. Baria"
    if "narsingdi" in c_lower or "narsinghdi" in c_lower:
        return "Narshingdi"
    if "bagura" in c_lower or "bogura" in c_lower:
        return "Bogra"

    # Other common corrections
    if "chattogram" in c_lower:
        return "Chittagong"
    if "cox" in c_lower and "bazar" in c_lower:
        return "Cox's Bazar"
    if "chapainawabganj" in c_lower:
        return "Chapainawabganj"

    # Default: Title Case
    return c.title()
