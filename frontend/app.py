import gradio as gr
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from backend.pdf_processor import process_pdf
from backend.rag_engine import store_chunks, search_similar
from backend.llm_client import chat
from backend.handbook_generator import generate_handbook, detect_topic_from_pdf
from backend.exporter import export_to_word, export_to_pdf

load_dotenv()

current_pdf = {"names": [], "last_handbook": "", "last_topic": ""}

def upload_pdfs(files):
    if not files:
        return "No files uploaded. Please upload at least one PDF."

    try:
        os.makedirs("uploads", exist_ok=True)
        uploaded_names = []

        for file in files:
            pdf_path = f"uploads/{os.path.basename(file.name)}"
            with open(file.name, "rb") as f:
                content = f.read()
            with open(pdf_path, "wb") as f:
                f.write(content)

            pdf_name = os.path.basename(pdf_path)
            chunks = process_pdf(pdf_path)
            store_chunks(chunks, pdf_name)
            uploaded_names.append(pdf_name)
            current_pdf["names"].append(pdf_name)

        return f"Successfully uploaded and indexed {len(uploaded_names)} PDF(s):\n" + "\n".join(f"- {n}" for n in uploaded_names) + "\n\nYou can now ask questions or request a handbook!"

    except Exception as e:
        return f"Error processing PDF: {str(e)}"


def respond(message, history, style):
    if not message:
        return history, ""

    history = history or []

    try:
        handbook_keywords = [
            "generate handbook",
            "create handbook",
            "make handbook",
            "write handbook",
            "handbook on",
            "handbook about",
            "handbook"
        ]

        is_handbook_request = any(kw in message.lower() for kw in handbook_keywords)

        if is_handbook_request:
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": f"Starting handbook generation in {style} style. Detecting topic and searching knowledge base. Please wait..."})

            topic = message.lower()
            for kw in handbook_keywords:
                topic = topic.replace(kw, "").strip()

            vague_words = ["this", "the", "my", "document", "documents", "pdf", "file", "it", "about this", "about the", ""]
            
            if not topic or topic in vague_words or len(topic.split()) <= 2:
                history[-1] = {"role": "assistant", "content": "No specific topic found in your message. Auto detecting topic from your uploaded documents. Please wait..."}
                topic = detect_topic_from_pdf(current_pdf["names"][0] if current_pdf["names"] else None)
                history[-1] = {"role": "assistant", "content": f"Auto detected topic from your document: {topic}\n\nStarting handbook generation in {style} style. This will take 5 to 8 minutes. Please wait..."}

            progress_messages = []

            def update_progress(msg):
                progress_messages.append(msg)
                print(f"Progress: {msg}")

            handbook = generate_handbook(
                topic,
                current_pdf["names"][0] if current_pdf["names"] else None,
                style,
                update_progress
            )

            current_pdf["last_handbook"] = handbook
            current_pdf["last_topic"] = topic

            word_count = len(handbook.split())
            progress_log = "\n".join(progress_messages)
            response = f"Handbook generated successfully in {style} style.\n\nTopic: {topic}\nWord count: {word_count} words\nSaved to outputs folder\n\nProgress log:\n{progress_log}\n\n---\n\n{handbook[:3000]}\n\nFull handbook saved to outputs folder. Use the export buttons to download."

            history[-1] = {"role": "assistant", "content": response}

        else:
            if current_pdf["names"]:
                results = search_similar(message, limit=5)
                context = "\n\n".join([r.get("content", "") for r in results])

                source_names = list(set([r.get("metadata", {}).get("source", "unknown") for r in results if r.get("metadata")]))
                citation = f"\n\nSources referenced: {', '.join(source_names)}" if source_names else ""

                messages = [
                    {
                        "role": "system",
                        "content": f"""You are a helpful AI assistant. Answer questions based on the uploaded document content.

Document context:
{context[:3000]}

If the answer is in the context, use it and mention which document it came from. Otherwise use your general knowledge."""
                    },
                    {"role": "user", "content": message}
                ]
            else:
                citation = ""
                messages = [
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant. No document has been uploaded yet. Ask the user to upload a PDF first."
                    },
                    {"role": "user", "content": message}
                ]

            response = chat(messages) + citation
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": response})

    except Exception as e:
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": f"Error: {str(e)}"})

    return history, ""


def export_word():
    if not current_pdf["last_handbook"]:
        return None
    path = export_to_word(current_pdf["last_handbook"], current_pdf["last_topic"])
    return path


def export_pdf():
    if not current_pdf["last_handbook"]:
        return None
    path = export_to_pdf(current_pdf["last_handbook"], current_pdf["last_topic"])
    return path


with gr.Blocks(title="Handbook Generator") as demo:

    gr.Markdown("""
    # AI Handbook Generator
    ### Upload multiple PDFs, chat with your documents, and generate 20000 word handbooks
    """)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Step 1: Upload PDFs")
            pdf_input = gr.File(
                label="Upload PDF Documents",
                file_types=[".pdf"],
                file_count="multiple"
            )
            upload_btn = gr.Button("Process PDFs", variant="primary", size="lg")
            upload_status = gr.Markdown("No PDFs uploaded yet")

            gr.Markdown("### Step 2: Choose Style")
            style_selector = gr.Radio(
                choices=["professional", "academic", "beginner"],
                value="professional",
                label="Handbook Style"
            )

            gr.Markdown("""
            ### Example Commands
            - Summarize this document
            - What are the key concepts?
            - Generate handbook
            - Create handbook about news bias
            - What is the main topic of this document?
            """)

            gr.Markdown("### Export Last Handbook")
            export_word_btn = gr.Button("Download as Word Document", variant="secondary")
            export_pdf_btn = gr.Button("Download as PDF", variant="secondary")
            word_output = gr.File(label="Word Document", visible=True)
            pdf_output = gr.File(label="PDF Document", visible=True)

        with gr.Column(scale=2):
            gr.Markdown("### Step 3: Chat and Generate")
            chatbot = gr.Chatbot(
                label="Chat",
                height=500
            )
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="Ask a question or just type: generate handbook",
                    label="Your Message",
                    scale=4
                )
                send_btn = gr.Button("Send", variant="primary", scale=1)

            clear_btn = gr.Button("Clear Chat", variant="secondary")

    upload_btn.click(
        fn=upload_pdfs,
        inputs=[pdf_input],
        outputs=[upload_status]
    )

    send_btn.click(
        fn=respond,
        inputs=[msg_input, chatbot, style_selector],
        outputs=[chatbot, msg_input]
    )

    msg_input.submit(
        fn=respond,
        inputs=[msg_input, chatbot, style_selector],
        outputs=[chatbot, msg_input]
    )

    clear_btn.click(
        fn=lambda: ([], ""),
        outputs=[chatbot, msg_input]
    )

    export_word_btn.click(
        fn=export_word,
        outputs=[word_output]
    )

    export_pdf_btn.click(
        fn=export_pdf,
        outputs=[pdf_output]
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_error=True
    )