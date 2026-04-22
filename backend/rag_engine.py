import os
from openai import OpenAI
from dotenv import load_dotenv
from backend.supabase_client import get_supabase_client

load_dotenv()

def get_embedding(text: str) -> list:
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000]
    )
    return response.data[0].embedding

def store_chunks(chunks: list, pdf_name: str):
    supabase = get_supabase_client()
    print(f"Storing {len(chunks)} chunks in database...")
    
    for i, chunk in enumerate(chunks):
        try:
            embedding = get_embedding(chunk)
            supabase.table("documents").insert({
                "content": chunk,
                "metadata": {"source": pdf_name, "chunk_index": i},
                "embedding": embedding
            }).execute()
            print(f"Stored chunk {i+1}/{len(chunks)}")
        except Exception as e:
            print(f"Error storing chunk {i}: {e}")
    
    print("All chunks stored successfully!")

def search_similar(query: str, limit: int = 5) -> list:
    supabase = get_supabase_client()
    query_embedding = get_embedding(query)
    
    try:
        result = supabase.rpc("match_documents", {
            "query_embedding": query_embedding,
            "match_threshold": 0.0,
            "match_count": limit
        }).execute()
        
        if result.data:
            return result.data
        
        result = supabase.table("documents").select("content, metadata").limit(limit).execute()
        return result.data
        
    except Exception as e:
        print(f"Search error: {e}")
        result = supabase.table("documents").select("content, metadata").limit(limit).execute()
        return result.data