import streamlit as st
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from backend.pdf_processor import process_pdf
from backend.rag_engine import store_chunks, search_similar
from backend.llm_client import chat
from backend.handbook_generator import generate_handbook, detect_topic_from_pdf
from backend.exporter import export_to_word, export_to_markdown
from backend.supabase_client import get_supabase_client

load_dotenv()

st.set_page_config(
    page_title="AI Handbook Generator",
    page_icon="📖",
    layout="wide"
)

st.markdown("""
<style>
    .main-title { font-size: 2.5rem; font-weight: bold; }
    .sub-title { color: gray; margin-bottom: 1rem; }
    .stDownloadButton button { width: 100%; }
    .stButton button { width: 100%; }
    [data-testid="stChatMessage"] p {
        font-size: 0.9rem !important;
        font-weight: normal !important;
        line-height: 1.6;
    }
    [data-testid="stChatMessage"] h1 { font-size: 1.1rem !important; }
    [data-testid="stChatMessage"] h2 { font-size: 1rem !important; }
    [data-testid="stChatMessage"] h3 { font-size: 0.95rem !important; }
    [data-testid="stChatMessage"] strong {
        font-size: 0.9rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stChatMessage"] li {
        font-size: 0.9rem !important;
        font-weight: normal !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">AI Handbook Generator</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Upload PDFs, chat with your documents, and generate 20000+ word handbooks using GPT-4o and RAG</p>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_names" not in st.session_state:
    st.session_state.pdf_names = []
if "last_handbook" not in st.session_state:
    st.session_state.last_handbook = ""
if "last_topic" not in st.session_state:
    st.session_state.last_topic = ""
if "word_data" not in st.session_state:
    st.session_state.word_data = None
if "md_data" not in st.session_state:
    st.session_state.md_data = None

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### Step 1: Upload PDFs")
    uploaded_files = st.file_uploader(
        "Upload one or more PDF documents",
        type=["pdf"],
        accept_multiple_files=True,
        help="You can upload multiple PDFs at once"
    )

    if st.button("Process PDFs", type="primary", use_container_width=True):
        if uploaded_files:
            os.makedirs("uploads", exist_ok=True)

            try:
                supabase = get_supabase_client()
                supabase.table("documents").delete().neq("id", 0).execute()
                st.session_state.pdf_names = []
                st.session_state.messages = []
                st.session_state.last_handbook = ""
                st.session_state.last_topic = ""
                st.session_state.word_data = None
                st.session_state.md_data = None
            except Exception as e:
                st.warning(f"Could not clear old data: {str(e)}")

            progress = st.progress(0)
            total = len(uploaded_files)
            new_uploads = []

            for i, uploaded_file in enumerate(uploaded_files):
                pdf_path = f"uploads/{uploaded_file.name}"
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                with st.spinner(f"Processing {uploaded_file.name}..."):
                    chunks = process_pdf(pdf_path)
                    store_chunks(chunks, uploaded_file.name)

                if uploaded_file.name not in st.session_state.pdf_names:
                    st.session_state.pdf_names.append(uploaded_file.name)
                    new_uploads.append(uploaded_file.name)

                progress.progress((i + 1) / total)

            st.success(f"Successfully uploaded and indexed {len(new_uploads)} PDF(s)")
        else:
            st.error("Please upload at least one PDF first")

    if st.session_state.pdf_names:
        st.markdown("**Indexed documents:**")
        for name in st.session_state.pdf_names:
            st.markdown(f"- {name}")

        if st.button("Clear All Documents", use_container_width=True):
            try:
                supabase = get_supabase_client()
                supabase.table("documents").delete().neq("id", 0).execute()
                st.session_state.pdf_names = []
                st.session_state.messages = []
                st.session_state.last_handbook = ""
                st.session_state.last_topic = ""
                st.session_state.word_data = None
                st.session_state.md_data = None
                st.success("All documents cleared!")
                st.rerun()
            except Exception as e:
                st.error(f"Error clearing: {str(e)}")

    st.markdown("---")
    st.markdown("### Step 2: Choose Style")
    style = st.radio(
        "Handbook Writing Style",
        ["professional", "academic", "beginner"],
        index=0
    )

    st.markdown("---")
    st.markdown("""
    ### Example Commands
    - Summarize this document
    - What are the key concepts?
    - What is the main methodology?
    - generate handbook
    - create handbook about RAG
    """)

    st.markdown("---")

    if st.session_state.last_handbook:
        st.markdown("### Download Last Handbook")
        st.markdown(f"**Topic:** {st.session_state.last_topic}")
        st.markdown(f"**Words:** {len(st.session_state.last_handbook.split())}")

        if st.session_state.word_data:
            st.download_button(
                label="Download as Word Document",
                data=st.session_state.word_data,
                file_name=f"handbook_{st.session_state.last_topic[:20].replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                key="sidebar_word_btn"
            )

        if st.session_state.md_data:
            st.download_button(
                label="Download as Markdown",
                data=st.session_state.md_data,
                file_name=f"handbook_{st.session_state.last_topic[:20].replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True,
                key="sidebar_md_btn"
            )

with col2:
    st.markdown("### Step 3: Chat and Generate")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("word_data"):
                col_w, col_m = st.columns(2)
                with col_w:
                    st.download_button(
                        label="Download Word",
                        data=message["word_data"],
                        file_name=message.get("word_filename", "handbook.docx"),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key=f"word_{message.get('key', 'default')}"
                    )
                with col_m:
                    st.download_button(
                        label="Download Markdown",
                        data=message["md_data"],
                        file_name=message.get("md_filename", "handbook.md"),
                        mime="text/markdown",
                        use_container_width=True,
                        key=f"md_{message.get('key', 'default')}"
                    )

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if prompt := st.chat_input("Ask a question or type: generate handbook"):
        with st.chat_message("user"):
            st.markdown(prompt)

        handbook_keywords = [
            "generate handbook",
            "create handbook",
            "make handbook",
            "write handbook",
            "handbook on",
            "handbook about",
            "handbook"
        ]

        is_handbook_request = any(kw in prompt.lower() for kw in handbook_keywords)

        if is_handbook_request:
            topic = prompt.lower()
            for kw in handbook_keywords:
                topic = topic.replace(kw, "").strip()

            vague_words = [
                "this", "the", "my", "document", "documents",
                "pdf", "file", "it", "about this", "about the", ""
            ]

            if not topic or topic in vague_words or len(topic.split()) <= 2:
                with st.spinner("Auto detecting topic from your documents..."):
                    topic = detect_topic_from_pdf(
                        st.session_state.pdf_names[0]
                        if st.session_state.pdf_names else None
                    )
                st.info(f"Auto detected topic: {topic}")

            progress_bar = st.progress(0)
            status_text = st.empty()
            progress_steps = [0]

            def update_progress(msg):
                progress_steps[0] += 1
                progress = min(progress_steps[0] / 13, 0.99)
                progress_bar.progress(progress)
                status_text.text(msg)

            with st.spinner(f"Generating handbook about {topic} in {style} style. This takes 5 to 8 minutes..."):
                handbook = generate_handbook(
                    topic,
                    st.session_state.pdf_names[0]
                    if st.session_state.pdf_names else None,
                    style,
                    update_progress
                )

            progress_bar.progress(100)
            status_text.empty()

            st.session_state.last_handbook = handbook
            st.session_state.last_topic = topic

            os.makedirs("outputs", exist_ok=True)

            word_path = export_to_word(handbook, topic)
            md_path = export_to_markdown(handbook, topic)

            with open(word_path, "rb") as f:
                word_data = f.read()
            with open(md_path, "r", encoding="utf-8") as f:
                md_data = f.read()

            st.session_state.word_data = word_data
            st.session_state.md_data = md_data

            word_count = len(handbook.split())
            msg_key = str(int(time.time()))

            word_filename = f"handbook_{topic[:20].replace(' ', '_')}.docx"
            md_filename = f"handbook_{topic[:20].replace(' ', '_')}.md"

            preview = ' '.join(handbook.split()[:300])

            response_text = f"""Handbook generated successfully in **{style}** style.

**Topic:** {topic}

**Word count:** {word_count} words

**Preview of first 300 words:**

{preview}...

Download the full handbook using the buttons below or from the left sidebar."""

            with st.chat_message("assistant"):
                st.markdown(response_text)
                col_w, col_m = st.columns(2)
                with col_w:
                    st.download_button(
                        label="Download Word Document",
                        data=word_data,
                        file_name=word_filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key=f"word_chat_{msg_key}"
                    )
                with col_m:
                    st.download_button(
                        label="Download Markdown",
                        data=md_data,
                        file_name=md_filename,
                        mime="text/markdown",
                        use_container_width=True,
                        key=f"md_chat_{msg_key}"
                    )

            st.session_state.messages.append({
                "role": "user",
                "content": prompt
            })
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "word_data": word_data,
                "md_data": md_data,
                "word_filename": word_filename,
                "md_filename": md_filename,
                "key": msg_key
            })

        else:
            if st.session_state.pdf_names:
                with st.spinner("Searching documents..."):
                    results = search_similar(prompt, limit=5)
                    context = "\n\n".join([r.get("content", "") for r in results])
                    source_names = list(set([
                        r.get("metadata", {}).get("source", "unknown")
                        for r in results if r.get("metadata")
                    ]))
                    citation = f"\n\n**Sources referenced:** {', '.join(source_names)}" if source_names else ""

                    messages = [
                        {
                            "role": "system",
                            "content": f"""You are a helpful AI assistant. Answer questions based on uploaded document content.

Document context:
{context[:3000]}

If the answer is in the context use it and mention which document it came from. Otherwise use your general knowledge."""
                        },
                        {"role": "user", "content": prompt}
                    ]
            else:
                citation = ""
                messages = [
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant. No document uploaded yet. Ask the user to upload a PDF first."
                    },
                    {"role": "user", "content": prompt}
                ]

            with st.spinner("Thinking..."):
                response = chat(messages) + citation

            with st.chat_message("assistant"):
                st.markdown(response)

            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": response})