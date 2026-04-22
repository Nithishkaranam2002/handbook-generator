AI Handbook Generator
A web application that transforms PDF documents into comprehensive 20,000+ word professional handbooks through a conversational chat interface.
Live Demo: https://nithishkaranam2002-handbook-genera-frontendstreamlit-app-czvowl.streamlit.app/

What This Project Does
Most people struggle to extract deep knowledge from documents. Reading a 50-page research paper takes hours. This application solves that by:

Accepting any PDF document as input
Building a searchable knowledge base from the content
Allowing natural conversation about the document
Generating a fully structured 20,000+ word handbook on demand

The entire interaction happens through a simple chat interface. Upload, ask, generate.

Features

Upload multiple PDF documents simultaneously
Chat with document content using semantic search and RAG
Auto detect topic from uploaded documents
Generate 20,000 to 35,000 word structured handbooks
Three writing styles: professional, academic, beginner friendly
Real time progress tracking during handbook generation
Source citations showing which document each answer came from
Export handbook as Word document
Export handbook as Markdown file
Auto clear database when uploading new documents


How It Works
RAG (Retrieval Augmented Generation)
Instead of asking GPT-4o to answer from memory, the system:

Breaks the PDF into 1000 character chunks with 200 character overlap
Converts each chunk into a 1536 dimensional embedding vector using OpenAI text-embedding-3-small
Stores these vectors in Supabase with pgvector extension
When a question comes in, converts it to an embedding and finds the most similar chunks using cosine similarity
Sends those relevant chunks as context to GPT-4o
GPT-4o answers based on your actual document content

This means the AI always answers from your documents, not from hallucination.
LongWriter Technique for 20,000+ Words
Standard LLMs have an output limit of around 4,000 tokens per response. To generate 20,000+ words, the system:

First generates a detailed outline from document context
Generates the introduction in 3 separate API calls, each targeting 800 words
Generates 10 major sections, each in 3 separate API calls targeting 800 words
Generates the conclusion in 3 separate API calls
Combines all parts into one structured document

This results in 33 total API calls per handbook, producing 25,000 to 35,000 words of structured content.
Auto Topic Detection
When a user types just "generate handbook" without specifying a topic, the system automatically:

Retrieves the top 8 most representative chunks from the database
Sends them to GPT-4o asking for the main topic
Uses the detected topic for all generation
Informs the user what topic was detected


Tech Stack
ComponentTechnologyFrontendStreamlitLLMGPT-4o via OpenAI APIEmbeddingstext-embedding-3-smallVector DatabaseSupabase with pgvectorPDF ProcessingpdfplumberWord Exportpython-docxMarkdown ExportBuilt-in Python


Project Structure
handbook-generator/
│
├── backend/
│   ├── __init__.py
│   ├── pdf_processor.py        # PDF text extraction and chunking
│   ├── rag_engine.py           # Embeddings and vector search
│   ├── llm_client.py           # OpenAI API client
│   ├── handbook_generator.py   # LongWriter implementation
│   ├── supabase_client.py      # Database connection
│   └── exporter.py             # Word and Markdown export
│
├── frontend/
│   ├── __init__.py
│   └── streamlit_app.py        # Streamlit chat interface
│
├── .streamlit/
│   └── config.toml             # Streamlit configuration
│
├── uploads/                    # Temporary PDF storage
├── outputs/                    # Generated handbooks
├── .env                        # API keys (not committed)
├── .gitignore
├── requirements.txt
└── README.md

Setup Instructions
Prerequisites

Python 3.12 or higher
uv package manager
OpenAI API key with credits
Supabase account (free tier works)

Step 1: Clone the Repository
git clone https://github.com/Nithishkaranam2002/handbook-generator.git
cd handbook-generator
Step 2: Create Virtual Environment
uv venv --python 3.12
source .venv/bin/activate
Step 3: Install Dependencies
uv add streamlit pdfplumber supabase python-dotenv openai python-docx
Step 4: Configure Environment Variables
Create a .env file in the root directory:
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_secret_key_here
MODEL_NAME=gpt-4o
Step 5: Set Up Supabase Database
Go to your Supabase project, open SQL Editor, and run:
create extension if not exists vector;

create table documents (
  id bigserial primary key,
  content text,
  metadata jsonb,
  embedding vector(1536)
);

create or replace function match_documents (
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
returns table (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
language sql stable
as $$
  select
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) as similarity
  from documents
  where 1 - (documents.embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
$$;
Step 6: Run the Application
python -m streamlit run frontend/streamlit_app.py
Open your browser at http://localhost:8501

How to Use

Open the app at the live link or locally
Upload one or more PDF files using the file uploader
Click Process PDFs and wait for the success message
Choose your preferred writing style
Type any question in the chat box or just type: generate handbook
Wait 5 to 8 minutes for handbook generation
Download as Word or Markdown using the buttons


Example Test

Upload any research paper or technical document
Ask: what are the main contributions of this paper?
Ask: summarize the methodology
Type: generate handbook
Wait 5 to 8 minutes
Receive a 25,000+ word structured handbook
Download as Word document


Challenges and Solutions
Challenge 1: LLM Output Limits
GPT-4o has a maximum output of around 4,000 tokens per response which is far less than 20,000 words. Solution: implement LongWriter technique by splitting generation into 33 focused API calls and combining results.
Challenge 2: PDF Knowledge Retrieval
Simply asking GPT-4o about a PDF without context leads to hallucination. Solution: implement RAG with vector embeddings so every response is grounded in actual document content.
Challenge 3: Topic Detection
Users should not need to manually specify topics. Solution: auto topic detection by analyzing the most representative document chunks and asking GPT-4o to identify the main subject.
Challenge 4: Multiple PDF Support
Supporting multiple PDFs requires careful knowledge management. Solution: store source metadata with each chunk so the system can cite which document each piece of information came from.

Submission
Built for the LunarTech AI Engineering Apprenticeship Assignment.
GitHub Repository: https://github.com/Nithishkaranam2002/handbook-generator
Live Application: https://nithishkaranam2002-handbook-genera-frontendstreamlit-app-czvowl.streamlit.app/
