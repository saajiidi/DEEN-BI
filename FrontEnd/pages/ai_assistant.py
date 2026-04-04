import streamlit as st
import pandas as pd
import os
from FrontEnd.components.ui_components import render_section_card
from BackEnd.services.hybrid_data_loader import load_hybrid_data
from BackEnd.engine.ai_query import query_app_data, generic_chat


def render_ai_assistant_tab():
    """Renders the AI Assistant tab for interacting with the database."""
    render_section_card(
        "🤖 Automation Pivot AI",
        "Ask natural language questions about your database and application data",
    )

    # Ensure API Key is available
    api_key = os.environ.get("GEMINI_API_KEY", "")
    try:
        if not api_key:
            api_key = st.secrets.get("GEMINI_API_KEY", "")
    except FileNotFoundError:
        pass

    if not api_key:
        st.warning(
            "⚠️ **Gemini API Key Missing!** Please configure `GEMINI_API_KEY` in your `.streamlit/secrets.toml` file to use this feature."
        )
        with st.expander("How to configure"):
            st.code("""
# .streamlit/secrets.toml
GEMINI_API_KEY="your-api-key-here"
            """)
        return

    # Chat history state
    if "messages" not in st.session_state:
        st.session_state.messages = []

        # Initial greeting
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "👋 Hi! I'm Automation Pivot AI. How can I help you analyze your data today?",
            }
        )

    # Sidebar Data Context Control
    st.sidebar.subheader("🔌 AI Data Source")
    use_sales_data = st.sidebar.checkbox(
        "Search Sales Database", value=True, help="Allows AI to query the main sales database."
    )

    # Load dataset if needed
    df_sales = None
    if use_sales_data:
        try:
            # We don't want to load giant data for every keystroke.
            # We will use recent data or require user to specify date in the general dashboard.
            # For simplicity, we just use the default full hybrid data
            with st.spinner("Connecting AI to database..."):
                start_date = pd.Timestamp.now().replace(day=1).strftime("%Y-%m-%d")
                df_sales = load_hybrid_data(start_date=start_date)
        except Exception as e:
            st.sidebar.error(f"Could not load data context: {e}")
            df_sales = None

    # Render Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "df" in msg and msg["df"] is not None:
                st.dataframe(msg["df"], use_container_width=True)

    # Input area
    if prompt := st.chat_input("Ask a question (e.g. 'What were the total sales yesterday?'):"):

        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("AI is thinking..."):
                # Decide if we need to query data or chat normally
                if use_sales_data and df_sales is not None and not df_sales.empty:
                    # Query data
                    answer, result_df = query_app_data(prompt, df_sales, api_key)
                else:
                    # Generic chat
                    answer = generic_chat(prompt, api_key, st.session_state.messages)
                    result_df = None

                # Display output
                st.markdown(answer)
                if result_df is not None and not result_df.empty:
                    st.dataframe(result_df, use_container_width=True)

                # Save to history
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "df": result_df if result_df is not None and not result_df.empty else None,
                    }
                )
