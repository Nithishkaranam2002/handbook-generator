import os
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


def export_to_word(handbook_text: str, topic: str) -> str:
    doc = Document()

    title = doc.add_heading(f"Comprehensive Handbook: {topic}", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    lines = handbook_text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("# "):
            doc.add_heading(line[2:], level=1)
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=2)
        elif line.startswith("### "):
            doc.add_heading(line[4:], level=3)
        elif line.startswith("---"):
            doc.add_paragraph("─" * 50)
        else:
            para = doc.add_paragraph(line)
            para.style.font.size = Pt(11)

    output_path = f"outputs/handbook_{topic[:30].replace(' ', '_')}.docx"
    os.makedirs("outputs", exist_ok=True)
    doc.save(output_path)
    print(f"Word document saved to {output_path}")
    return output_path


def export_to_markdown(handbook_text: str, topic: str) -> str:
    output_path = f"outputs/handbook_{topic[:30].replace(' ', '_')}.md"
    os.makedirs("outputs", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(handbook_text)
    print(f"Markdown saved to {output_path}")
    return output_path


def export_to_pdf(handbook_text: str, topic: str) -> str:
    return export_to_markdown(handbook_text, topic)