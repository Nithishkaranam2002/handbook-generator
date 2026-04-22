import streamlit as st
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from backend.pdf_processor import process_pdf
from backend.rag_engine import store_chunks, search_similar
from backend.llm_client import chat
from backend.handbook_generator import generate_handbook, detect_topic_from_pdf
from backend.exporter import export_to_word, export_to_pdf

load_dotenv()

st.set_page_config(
    page_title="AI Handbook Generator",
    page_icon="📖",
    layout="wide"
)

st.title("AI Handbook Generator")
st.markdown("Upload PDFs, chat with your documents, and generate 20000 word handbooks")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_names" not in st.session_state:
    st.session_state.pdf_names = []
if "last_handbook" not in st.session_state:
    st.session_state.last_handbook = ""
if "last_topic" not in st.session_state:
    st.session_state.last_topic = ""

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### Step 1: Upload PDFs")
    uploaded_files = st.file_uploader(
        "Upload PDF Documents",
        type=["pdf"],
        accept_multiple_files=True
    )

    if st.button("Process PDFs", type="primary"):
        if uploaded_files:
            os.makedirs("uploads", exist_ok=True)
            for uploaded_file in uploaded_files:
                pdf_path = f"uploads/{uploaded_file.name}"
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    chunks = process_pdf(pdf_path)
                    store_chunks(chunks, uploaded_file.name)
                    st.session_state.pdf_names.append(uploaded_file.name)
            st.success(f"Successfully uploaded and indexed {len(uploaded_files)} PDF(s)")
        else:
            st.error("Please upload at least one PDF")

    if st.session_state.pdf_names:
        st.markdown("**Uploaded documents:**")
        for name in st.session_state.pdf_names:
            st.markdown(f"- {name}")

    st.markdown("### Step 2: Choose Style")
    style = st.radio(
        "Handbook Style",
        ["professional", "academic", "beginner"],
        index=0
    )

    st.markdown("""
    ### Example Commands
    - Summarize this document
    - What are the key concepts?
    - generate handbook
    - create handbook about machine learning
    """)

    if st.session_state.last_handbook:
        st.markdown("### Export Last Handbook")

        if st.button("Download as Word Document"):
            path = export_to_word(
                st.session_state.last_handbook,
                st.session_state.last_topic
            )
            with open(path, "rb") as f:
                st.download_button(
                    label="Click to Download Word",
                    data=f,
                    file_name=f"handbook_{st.session_state.last_topic[:20]}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

        if st.button("Download as PDF"):
            path = export_to_pdf(
                st.session_state.last_handbook,
                st.session_state.last_topic
            )
            with open(path, "rb") as f:
                st.download_button(
                    label="Click to Download PDF",
                    data=f,
                    file_name=f"handbook_{st.session_state.last_topic[:20]}.pdf",
                    mime="application/pdf"
                )

with col2:
    st.markdown("### Step 3: Chat and Generate")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question or type: generate handbook"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            handbook_keywords = [
                "generate handbook",
                "create handbook",
                "make handbook",
                "write handbook",
                "handbook on",
                "handbook about",
                "handbook"
            ]

            is_handbook_request = any(
                kw in prompt.lower() for kw in handbook_keywords
            )

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

                def update_progress(msg):
                    status_text.text(msg)

                with st.spinner(f"Generating handbook about {topic}. This takes 5 to 8 minutes..."):
                    handbook = generate_handbook(
                        topic,
                        st.session_state.pdf_names[0]
                        if st.session_state.pdf_names else None,
                        style,
                        update_progress
                    )

                progress_bar.progress(100)
                st.session_state.last_handbook = handbook
                st.session_state.last_topic = topic

                word_count = len(handbook.split())
                response = f"Handbook generated successfully in {style} style.\n\nTopic: {topic}\n\nWord count: {word_count} words\n\nFull handbook saved to outputs folder."
                st.markdown(response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )

            else:
                if st.session_state.pdf_names:
                    results = search_similar(prompt, limit=5)
                    context = "\n\n".join(
                        [r.get("content", "") for r in results]
                    )
                    source_names = list(set([
                        r.get("metadata", {}).get("source", "unknown")
                        for r in results if r.get("metadata")
                    ]))
                    citation = f"\n\nSources: {', '.join(source_names)}" if source_names else ""

                    messages = [
                        {
                            "role": "system",
                            "content": f"""You are a helpful AI assistant. Answer based on the uploaded document content.

Document context:
{context[:3000]}

If the answer is in the context, use it and mention which document it came from."""
                        },
                        {"role": "user", "content": prompt}
                    ]
                else:
                    citation = ""
                    messages = [
                        {
                            "role": "system",
                            "content": "You are a helpful AI assistant. Ask the user to upload a PDF first."
                        },
                        {"role": "user", "content": prompt}
                    ]

                with st.spinner("Thinking..."):
                    response = chat(messages) + citation

                st.markdown(response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )