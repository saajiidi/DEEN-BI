# Automation Pivot - Architecture & Workflow Overview

This document provides a comprehensive technical breakdown of the Automation Hub Pro (Automation Pivot) application. It is designed to assist both human developers and AI assistants in understanding the project structure, data flow, and runtime mechanics for further analysis and feature development.

## 1. System Architecture
The application is built on a modern **Streamlit** frontend with a robust, modular Python backend powered by **DuckDB** and **Pandas** for high-speed analytical data processing.

### Directory Structure
- `app.py`: The root application entrypoint. It handles basic routing across the Navigation Tabs, renders the sidebar (including Global Settings, Workspace Control, and System Logs), and initializes the custom theme.
- `FrontEnd/`: Contains all client-facing UI logic.
  - `pages/`: Individual modular tabs (e.g., `dashboard.py`, `ai_assistant.py`, `system_health.py`).
  - `components/`: Reusable UI modules (e.g., headers, footers, animations, KPI cards).
  - `utils/`: Configuration (`config.py`), state management, and error orchestration.
- `BackEnd/`: Houses the core business logic, data models, and services.
  - `services/`: High-level data retrieval scripts. `hybrid_data_loader.py` merges historical `.parquet` stores with live Google Sheet exports.
  - `core/`: Critical infrastructure files such as `gsheet_archive.py` (handles the API logic for mutating Google Sheets), and `paths.py` (dynamic directory configurations).
  - `engine/`: Processing cores like `ai_query.py` (which orchestrates the Text-to-SQL logic for Gemini).

## 2. Core Workflows & Data Loaders

### Hybrid Data Strategy
The application operates on a "Hybrid" model to maximize speed without sacrificing up-to-date information. 
The main data ingestion runs through `BackEnd.services.hybrid_data_loader.load_hybrid_data`:
1. **Historical Partition:** Attempts to pull archived data from local `data/data.parquet` files. If the file is omitted (e.g. fresh `.gitignore` clones), the app gracefully ignores the error and proceeds.
2. **Live Partition:** Fetches the active 2026 sales manifest directly from a published Google Sheet CSV link.
3. **DuckDB Union:** Joins both dataframes dynamically in an in-memory `duckdb` connection to run sub-second analytical queries. 

### Smart AI Query Integration
Integrated via `BackEnd/engine/ai_query.py` and `FrontEnd/pages/ai_assistant.py`, the AI Assistant is context-aware:
- It injects the active database schema dynamically into a generative AI prompt (Gemini-1.5-flash).
- The AI responds with a strict `SQL` query designed for `DuckDB`.
- The backend executes this query in-memory against the active `df_sales` DataFrame, then feeds the subset array back to the AI for a final, natural language answer. This securely bridges app data with Generative AI without directly streaming gigabytes of raw data.

## 3. Notable Configurations & Fixes

### Error Management and Resiliency
To prevent catastrophic Streamlit UI crashes (such as white screening on the Cloud), failures are caught and written to `System Logs` inside the UI sidebar (handled by `utils/error_handler.py` and parsed in `system_health.py`). 

### Dimension Guarantee Strategies
In the frontend views like `dashboard.py`, we construct dynamic analytic metrics. For instance, the **Peak Activity Heatmap** relies on Plotly's `px.imshow()`. To prevent `vector mismatch` or `dimension` errors caused by dataset anomalies (e.g., days/hours with 0 sales), the logic enforces `.reindex(index=range(7), columns=range(24), fill_value=0)` so UI plot geometries are always statically bound.

### Authentication & Secrets
The platform hooks directly into `.streamlit/secrets.toml`. Features relying on API connections dynamically look up variables like:
- `GEMINI_API_KEY`: Used to power your AI chatbot capabilities.
- `GOOGLE_SERVICE_ACCOUNT_JSON`: Consumed via OAuth flows to authenticate archival actions inside `gsheet_archive.py`.

## 4. Extension Guidelines
If an AI assistant or developer is modifying this application:
- **UI Tweaks:** Stick to defining logic in `FrontEnd/pages/` and keeping generic UI blocks in `FrontEnd/components/`. 
- **Dependencies:** Keep dependencies incredibly lean. Re-use existing generic parsing tools before fetching heavy packages like `langchain` if unnecessary.
- **Testing Scripts:** Always pass changes against Ruff with checking specific identifiers `ruff check . --select=E9,F63,F7,F82`.
