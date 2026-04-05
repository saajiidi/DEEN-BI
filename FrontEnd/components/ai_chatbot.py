import streamlit as st
import pandas as pd
import os
from BackEnd.services.hybrid_data_loader import load_hybrid_data
from BackEnd.engine.ai_query import query_app_data, generic_chat

def render_floating_ai_chat():
    """Renders a floating-style AI chat box at the bottom of the page."""
    
    # 1. CSS for the floating button and chat container
    st.markdown("""
        <style>
        .floating-chat-toggle {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 9999;
            background: linear-gradient(135deg, #1d4ed8, #3b82f6);
            color: white;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            cursor: pointer;
            border: none;
            transition: transform 0.3s ease;
        }
        .floating-chat-toggle:hover {
            transform: scale(1.1);
        }
        </style>
    """, unsafe_allow_html=True)

    # State for visibility
    if "show_ai_chat" not in st.session_state:
        st.session_state.show_ai_chat = False
    
    # Render Chat as a Popover in Sidebar or Bottom-Right via Popover (Streamlit native)
    # The native popover doesn't stay fixed in the corner easily in standard layout.
    # We'll use a sidebar popover as a "docked" chat system, or a bottom popover.
    
    # Let's use a sidebar docked popover as it's more stable in Streamlit
    with st.sidebar:
        st.divider()
        with st.popover("🤖 Ask AI Assistant", use_container_width=True):
            st.subheader("Automation Pivot AI")
            st.caption("Ask questions about your sales, inventory, or customers.")
            
            # Chat history state
            if "ai_messages" not in st.session_state:
                st.session_state.ai_messages = [
                    {"role": "assistant", "content": "👋 Hi! I'm here to help. What's on your mind?"}
                ]

            # Render history
            for msg in st.session_state.ai_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    if "df" in msg and msg["df"] is not None:
                        st.dataframe(msg["df"], use_container_width=True)

            # Input
            if prompt := st.chat_input("Type your question...", key="ai_chat_input"):
                st.session_state.ai_messages.append({"role": "user", "content": prompt})
                
                # Fetch API Key
                api_key = os.environ.get("GEMINI_API_KEY", st.secrets.get("GEMINI_API_KEY", ""))
                
                if not api_key:
                    with st.chat_message("assistant"):
                        st.error("Gemini API Key is missing in secrets!")
                else:
                    with st.chat_message("assistant"):
                        with st.spinner("AI is thinking..."):
                            # For the floating chat, we won't auto-load giant DFs unless asked
                            # But we can load recent hybrid data quickly
                            try:
                                df_sales = load_hybrid_data(start_date=(pd.Timestamp.now() - pd.Timedelta(days=30)).strftime("%Y-%m-%d"))
                                answer, result_df = query_app_data(prompt, df_sales, api_key)
                            except:
                                answer = generic_chat(prompt, api_key, st.session_state.ai_messages)
                                result_df = None
                            
                            st.markdown(answer)
                            if result_df is not None and not result_df.empty:
                                st.dataframe(result_df, use_container_width=True)
                            
                            st.session_state.ai_messages.append({
                                "role": "assistant", 
                                "content": answer,
                                "df": result_df if result_df is not None and not result_df.empty else None
                            })
                st.rerun()
