import os
from openai import OpenAI

def get_client():
    try:
        import streamlit as st
        api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        api_key = os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=api_key)

def chat(messages: list, model: str = None) -> str:
    client = get_client()
    try:
        import streamlit as st
        model = model or st.secrets.get("MODEL_NAME", "gpt-4o")
    except Exception:
        model = model or os.getenv("MODEL_NAME", "gpt-4o")
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=16000,
    )
    return response.choices[0].message.content

def chat_simple(prompt: str) -> str:
    return chat([{"role": "user", "content": prompt}])