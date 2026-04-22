import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_client():
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
    )

def chat(messages: list, model: str = None) -> str:
    client = get_client()
    model = model or os.getenv("MODEL_NAME", "gpt-4o")
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=16000,
    )
    return response.choices[0].message.content

def chat_simple(prompt: str) -> str:
    return chat([{"role": "user", "content": prompt}])