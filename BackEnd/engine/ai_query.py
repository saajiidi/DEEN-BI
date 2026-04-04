import re
import pandas as pd
import duckdb
import google.generativeai as genai
import streamlit as st
from typing import Tuple, Optional


def query_app_data(
    prompt: str, df: pd.DataFrame, api_key: str
) -> Tuple[str, Optional[pd.DataFrame]]:
    """
    Transforms natural language into SQL, runs it against the user's data,
    and returns an AI-generated natural language answer alongside the resulting dataframe.
    """
    if df is None or df.empty:
        return "The dataset is empty. I cannot search an empty database.", None

    if not api_key:
        return "⚠️ Please provide a Gemini API Key to use the smart search.", None

    try:
        genai.configure(api_key=api_key)
        # Using a reliable model for SQL and text generation
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Limit schema size to avoid token overflow
        schema_summary = df.dtypes.to_string()

        # 1. Prompt AI to generate SQL
        sql_sys_prompt = f"""
        You are an elite data engineering AI.
        You have a table named 'my_data' containing real e-commerce data.
        Schema:
        {schema_summary}
        
        User question: "{prompt}"
        
        Write a valid DuckDB SQL query to get the answer. 
        - Return ONLY the SQL query wrapped in ```sql and ```.
        - Handle strings with ILIKE for case-insensitive matching.
        - NEVER drop or create tables. Only SELECT.
        - Return 0 or NULL instead of breaking if math is impossible.
        """

        resp1 = model.generate_content(sql_sys_prompt)
        text1 = resp1.text

        # Extract SQL
        match = re.search(r"```[sS]ql\n(.*?)```", text1, re.DOTALL)
        if match:
            sql = match.group(1).strip()
        else:
            sql = text1.replace("```", "").strip()

        # Sanitize basic safety
        if "DROP" in sql.upper() or "ALTER" in sql.upper() or "DELETE" in sql.upper():
            return "❌ AI generated an unsafe query. Operation aborted.", None

        # Execute DuckDB query
        con = duckdb.connect(database=":memory:")
        con.register("my_data", df)
        result_df = con.execute(sql).fetchdf()
        con.close()

        # 2. Prompt AI to formulate the final answer based on the result
        result_preview = result_df.head(20).to_string()
        answer_prompt = f"""
        User asked: "{prompt}"
        I ran this SQL against their database: {sql}
        And got this result:
        {result_preview}
        
        Please provide a concise, helpful, and friendly English answer based on these results. 
        If it's an aggregation, state the numbers clearly. If it's a search, summarize it.
        """

        resp2 = model.generate_content(answer_prompt)
        return resp2.text, result_df

    except Exception as e:
        return f"I encountered an error while searching the data: {str(e)}", None


def generic_chat(prompt: str, api_key: str, history: list) -> str:
    """General conversational chatbot when not specifically searching data."""
    if not api_key:
        return "⚠️ Please provide a Gemini API Key to chat."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Format history for Gemini
        formatted_history = []
        for msg in history:
            role = "minion" if msg["role"] == "assistant" else "user"
            formatted_history.append(
                {"role": role if role == "user" else "model", "parts": [msg["content"]]}
            )

        chat = model.start_chat(history=formatted_history)
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        return f"Chat error: {str(e)}"
