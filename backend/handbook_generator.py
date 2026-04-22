import os
from backend.llm_client import chat
from backend.rag_engine import search_similar


def detect_topic_from_pdf(pdf_name: str = None) -> str:
    results = search_similar("main topic subject overview introduction", limit=8)
    context = "\n\n".join([r.get("content", "") for r in results])

    detected = chat([{"role": "user", "content": f"""Read this document content carefully and identify the main topic in 5 to 8 words.

Content:
{context[:3000]}

Reply with ONLY the topic name, nothing else.
Example replies: Machine Learning and Neural Networks
Example replies: Apartment Leasing Guidelines and Policies
Example replies: News Bias and Framing Analysis using NLP"""}])

    detected = detected.strip().strip('"').strip("'")
    print(f"Auto detected topic: {detected}")
    return detected


def generate_long_section(title: str, topic: str, context: str, style: str = "professional") -> str:

    style_instruction = {
        "professional": "Write in a formal, professional business tone suitable for corporate readers.",
        "academic": "Write in an academic tone with scholarly language, citations style, and research oriented approach.",
        "beginner": "Write in a simple, friendly, easy to understand tone suitable for complete beginners with no prior knowledge."
    }.get(style, "Write in a formal professional tone.")

    part1 = chat([{"role": "user", "content": f"""You are writing Part 1 of 3 for a handbook section.

Section: {title}
Topic: {topic}
Context: {context[:1500]}
Style instruction: {style_instruction}

Write Part 1 covering: Background, definitions, and foundational concepts.
Write at least 800 words. Be detailed and thorough. Do not summarize."""}])

    part2 = chat([{"role": "user", "content": f"""You are writing Part 2 of 3 for a handbook section.

Section: {title}
Topic: {topic}
Style instruction: {style_instruction}

Write Part 2 covering: Practical steps, processes, and implementation details.
Write at least 800 words. Be detailed and thorough. Do not summarize."""}])

    part3 = chat([{"role": "user", "content": f"""You are writing Part 3 of 3 for a handbook section.

Section: {title}
Topic: {topic}
Style instruction: {style_instruction}

Write Part 3 covering: Common challenges, best practices, tips, and real world examples.
Write at least 800 words. Be detailed and thorough. Do not summarize."""}])

    return f"{part1}\n\n{part2}\n\n{part3}"


def generate_handbook(topic: str, pdf_name: str = None, style: str = "professional", progress_callback=None) -> str:
    print("Starting handbook generation...")

    if progress_callback:
        progress_callback("Starting handbook generation. Searching knowledge base...")

    context_results = search_similar(topic, limit=10)
    context = "\n\n".join([r.get("content", "") for r in context_results])

    outline_prompt = f"""Create a detailed outline for a comprehensive handbook about: {topic}

Based on this reference content:
{context[:3000]}

The outline must have:
- Introduction
- Exactly 10 major sections with clear titles
- Each section has 4 subsections
- Conclusion

Return only the outline."""

    if progress_callback:
        progress_callback("Generating outline...")

    outline = chat([{"role": "user", "content": outline_prompt}])
    print("Outline done")

    sections = []

    if progress_callback:
        progress_callback("Generating introduction. This will take a few minutes...")

    intro_context = search_similar(f"introduction overview {topic}", limit=5)
    intro_text = "\n\n".join([r.get("content", "") for r in intro_context])

    style_instruction = {
        "professional": "Write in a formal, professional business tone.",
        "academic": "Write in an academic scholarly tone.",
        "beginner": "Write in a simple friendly tone for beginners."
    }.get(style, "Write in a formal professional tone.")

    intro_part1 = chat([{"role": "user", "content": f"""Write the first part of an introduction for a professional handbook about: {topic}

Reference content: {intro_text[:1500]}
Style: {style_instruction}

Cover: What this handbook is about, its purpose, and why this topic matters.
Write at least 800 words. Be very detailed."""}])

    intro_part2 = chat([{"role": "user", "content": f"""Write the second part of an introduction for a professional handbook about: {topic}

Style: {style_instruction}
Cover: Who should read this handbook, how to use it, and what they will learn.
Write at least 800 words. Be very detailed."""}])

    intro_part3 = chat([{"role": "user", "content": f"""Write the third part of an introduction for a professional handbook about: {topic}

Style: {style_instruction}
Cover: Historical background, context, and overview of key themes covered in this handbook.
Write at least 800 words. Be very detailed."""}])

    intro = f"{intro_part1}\n\n{intro_part2}\n\n{intro_part3}"
    sections.append(f"# Introduction\n\n{intro}")
    print("Introduction done")

    section_titles = [
        f"Fundamentals and Core Concepts of {topic}",
        f"Key Requirements and Prerequisites for {topic}",
        f"Step by Step Process Guide for {topic}",
        f"Important Deadlines and Timelines in {topic}",
        f"Documentation and Records Management in {topic}",
        f"Common Challenges and Solutions in {topic}",
        f"Best Practices and Professional Standards for {topic}",
        f"Legal Rights and Responsibilities in {topic}",
        f"Resources and Support Systems for {topic}",
        f"Future Planning and Long Term Considerations for {topic}",
    ]

    total_sections = len(section_titles)
    for i, title in enumerate(section_titles):
        if progress_callback:
            progress_callback(f"Generating section {i+1} of {total_sections}: {title}")
        print(f"Generating section {i+1}/{total_sections}")
        section_context = search_similar(f"{title} {topic}", limit=5)
        section_text = "\n\n".join([r.get("content", "") for r in section_context])
        content = generate_long_section(title, topic, section_text, style)
        sections.append(f"## Section {i+1}: {title}\n\n{content}")
        print(f"Section {i+1} done")

    if progress_callback:
        progress_callback("Generating conclusion...")

    conclusion_part1 = chat([{"role": "user", "content": f"""Write Part 1 of the conclusion for a professional handbook about: {topic}

Style: {style_instruction}
Cover: Summary of all key points and main takeaways.
Write at least 800 words. Be very detailed."""}])

    conclusion_part2 = chat([{"role": "user", "content": f"""Write Part 2 of the conclusion for a professional handbook about: {topic}

Style: {style_instruction}
Cover: Final recommendations, action steps, and advice for the reader.
Write at least 800 words. Be very detailed."""}])

    conclusion_part3 = chat([{"role": "user", "content": f"""Write Part 3 of the conclusion for a professional handbook about: {topic}

Style: {style_instruction}
Cover: Future outlook, emerging trends, and closing thoughts.
Write at least 800 words. Be very detailed."""}])

    conclusion = f"{conclusion_part1}\n\n{conclusion_part2}\n\n{conclusion_part3}"
    sections.append(f"# Conclusion\n\n{conclusion}")
    print("Conclusion done")

    full_handbook = f"# Comprehensive Handbook: {topic}\n\n"
    full_handbook += f"---\n\n## Table of Contents\n\n{outline}\n\n---\n\n"
    full_handbook += "\n\n---\n\n".join(sections)

    word_count = len(full_handbook.split())
    print(f"Handbook complete! Word count: {word_count}")

    output_path = f"outputs/handbook_{topic[:30].replace(' ', '_')}.md"
    os.makedirs("outputs", exist_ok=True)
    with open(output_path, "w") as f:
        f.write(full_handbook)
    print(f"Saved to {output_path}")

    if progress_callback:
        progress_callback(f"Handbook complete! Word count: {word_count} words. Saved to outputs folder.")

    return full_handbook