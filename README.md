# Automation Hub Pro v8.1

Automation Hub Pro is a Streamlit workspace for order processing, inventory distribution, and WhatsApp verification.

## Main Navigation

- Dashboard: live and manual sales dashboards
- Orders: Pathao order processor and delivery text parser
- Inventory: matrix analyzer, insights, and pick manifest
- Messaging: WhatsApp verification link generation
- More Tools: system logs and developer lab

## UX Improvements Included

- Guided workflow steps for major modules
- Upload -> validate -> preview -> export pattern
- Shared action bar and reset confirmation controls
- Unified labels and status messaging
- Optional motion effects toggle
- Sidebar sample template downloads

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project Structure

- `app.py`: application shell and navigation
- `app_modules/ui_config.py`: UI constants and labels
- `app_modules/ui_components.py`: reusable UI components
- `app_modules/pathao_tab.py`: Pathao workflow
- `app_modules/distribution_tab.py`: inventory workflow
- `app_modules/wp_tab.py`: WhatsApp workflow
- `app_modules/fuzzy_parser_tab.py`: text parser workflow
