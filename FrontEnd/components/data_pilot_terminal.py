import streamlit as st
import pandas as pd
import sqlite3
from BackEnd.commerce_ops.persistence import KeyManager
from BackEnd.services.nlp_engine import LLMAgent

def render_advanced_sql_terminal(sales_df: pd.DataFrame = None, returns_df: pd.DataFrame = None, stock_df: pd.DataFrame = None):
    st.markdown("### 🚀 Advanced SQL Data Pilot")
    
    # Initialize in-memory database
    conn = sqlite3.connect(':memory:')
    schema_info = []
    
    if sales_df is not None and not sales_df.empty:
        sales_df.to_sql('sales', conn, index=False)
        schema_info.append(f"Table 'sales' columns: {', '.join(sales_df.columns)}")
        
    if returns_df is not None and not returns_df.empty:
        returns_df.to_sql('returns', conn, index=False)
        schema_info.append(f"Table 'returns' columns: {', '.join(returns_df.columns)}")
        
    if stock_df is not None and not stock_df.empty:
        stock_df.to_sql('stock', conn, index=False)
        schema_info.append(f"Table 'stock' columns: {', '.join(stock_df.columns)}")

    # --- Terminal UI ---
    st.markdown("""
    <style>
    .terminal-box {
        background-color: #0c0c0c;
        color: #00ff00;
        font-family: 'Courier New', Courier, monospace;
        padding: 15px;
        border-radius: 8px;
        height: 200px;
        overflow-y: auto;
        border: 1px solid #333;
        margin-bottom: 20px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.8);
    }
    .term-prefix { color: #ff00ff; font-weight: bold; }
    .term-msg { color: #00ff00; }
    .term-error { color: #ff3333; }
    </style>
    """, unsafe_allow_html=True)
    
    if "pilot_term_logs" not in st.session_state:
        st.session_state.pilot_term_logs = [
            "DEEN-OPS Data Pilot Terminal initialized.",
            "Connecting to SQLite In-Memory Database...",
            "Available Tables loaded: sales, returns, stock.",
            "Ready for queries."
        ]
        
    def log_to_term(msg, is_error=False):
        css_class = "term-error" if is_error else "term-msg"
        st.session_state.pilot_term_logs.append(f"<span class='{css_class}'>{msg}</span>")
        
    terminal_html = "<div class='terminal-box'>"
    for log in st.session_state.pilot_term_logs[-15:]:
        terminal_html += f"<div><span class='term-prefix'>root@data-pilot:~$</span> {log}</div>"
    terminal_html += "</div>"
    st.markdown(terminal_html, unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.markdown("#### 💻 Custom SQL Engine")
        st.caption("Write advanced SQL queries (JOINs, VIEWs, Aggregations) directly against your loaded data.")
        
        query = st.text_area("SQL Query", value="SELECT * FROM sales LIMIT 5", height=150, key=KeyManager.get_key("pilot", "sql_input"))
        
        if st.button("▶ Execute SQL", type="primary", use_container_width=True):
            try:
                log_to_term(f"Executing: {query}")
                result_df = pd.read_sql_query(query, conn)
                log_to_term(f"Success: {len(result_df)} rows returned.")
                st.success(f"Query executed successfully! ({len(result_df)} rows)")
                st.dataframe(result_df, use_container_width=True)
            except Exception as e:
                log_to_term(f"ERROR: {str(e)}", is_error=True)
                st.error(f"SQL Error: {str(e)}")
                
    with c2:
        st.markdown("#### 🤖 ML / NLP Assistant")
        st.caption("Ask in plain English. Our NLP model will generate the SQL.")
        
        nl_query = st.text_area("Natural Language Request", placeholder="e.g., Show me the top 5 product categories by revenue from the sales table", height=100)
        
        if st.button("✨ Suggest SQL", use_container_width=True):
            with st.spinner("AI is thinking..."):
                try:
                    schema_context = "\n".join(schema_info)
                    prompt = f"Given the following SQLite schemas:\n{schema_context}\n\nWrite a valid SQLite query for: '{nl_query}'. Return ONLY the SQL code, no markdown ticks, no explanation."
                    
                    agent = LLMAgent()
                    sql_suggestion = agent.query(prompt, pd.DataFrame()) 
                    sql_suggestion = sql_suggestion.replace('```sql', '').replace('```', '').strip()
                    
                    log_to_term(f"AI Suggested SQL for: '{nl_query}'")
                    st.session_state[KeyManager.get_key("pilot", "sql_input")] = sql_suggestion
                    st.info("SQL Generated & Copied to editor!")
                    st.rerun()
                except Exception as e:
                    log_to_term(f"AI Error: {str(e)}", is_error=True)
                    st.error(f"Failed to generate SQL: {e}")

    # --- Draggable Floating Chatbot UI ---
    st.markdown("""
    <div id="drag-chatbot" style="position:fixed; bottom:30px; right:30px; width:340px; height:450px; background-color:#1e1e1e; border-radius:12px; border:1px solid #3b82f6; box-shadow: 0 15px 35px rgba(0,0,0,0.6); display:flex; flex-direction:column; z-index:99999; font-family: 'Inter', sans-serif;">
        <div id="drag-chatbot-header" style="background:linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding:12px 15px; border-radius:11px 11px 0 0; color:white; font-weight:600; display:flex; justify-content:space-between; align-items:center; cursor:move;">
            <div style="display:flex; align-items:center; gap:8px;">
                <span>🤖</span>
                <span>Data Pilot AI</span>
            </div>
            <span style="cursor:pointer; font-size:1.2rem; line-height:1;" onclick="document.getElementById('drag-chatbot').style.display='none'">&times;</span>
        </div>
        
        <div style="flex:1; padding:15px; overflow-y:auto; display:flex; flex-direction:column; gap:12px; background-color:#121212;">
            <div style="background-color:#2d3748; color:#e2e8f0; padding:10px 14px; border-radius:12px 12px 12px 2px; max-width:85%; align-self:flex-start; font-size:0.9rem; line-height:1.4;">
                Hello Commander. I am your Data Pilot assistant. You can use the Terminal above to run advanced operations. 
            </div>
            <div style="background-color:#2d3748; color:#e2e8f0; padding:10px 14px; border-radius:12px 12px 12px 2px; max-width:85%; align-self:flex-start; font-size:0.9rem; line-height:1.4;">
                Need a complex JOIN or VIEW? Type your request in the NLP Assistant panel and I'll write the SQL for you.
            </div>
        </div>
        
        <div style="padding:12px; background-color:#1e1e1e; border-top:1px solid #333; border-radius:0 0 11px 11px;">
            <div style="display:flex; background-color:#2d3748; border-radius:20px; overflow:hidden; padding:4px;">
                <input type="text" placeholder="Interaction via NLP panel above..." disabled style="flex:1; background:transparent; border:none; color:white; padding:8px 12px; outline:none; font-size:0.9rem;">
            </div>
        </div>
    </div>
    
    <script>
        const chatbot = document.getElementById("drag-chatbot");
        const chatbotHeader = document.getElementById("drag-chatbot-header");
        let isDragging = false, currentX = 0, currentY = 0, initialX, initialY, xOffset = 0, yOffset = 0;

        chatbotHeader.addEventListener("mousedown", e => {
            if (e.target === chatbotHeader || e.target.parentNode === chatbotHeader) {
                initialX = e.clientX - xOffset; initialY = e.clientY - yOffset; isDragging = true;
            }
        });
        document.addEventListener("mouseup", () => { initialX = currentX; initialY = currentY; isDragging = false; });
        document.addEventListener("mousemove", e => {
            if (!isDragging) return; e.preventDefault();
            currentX = e.clientX - initialX; currentY = e.clientY - initialY;
            xOffset = currentX; yOffset = currentY;
            chatbot.style.transform = `translate3d(${currentX}px, ${currentY}px, 0)`;
        });
    </script>
    """, unsafe_allow_html=True)