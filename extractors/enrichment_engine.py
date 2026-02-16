import json
import re
from pathlib import Path


def classify_question(text):
    text_lower = text.lower()

    if "calculate" in text_lower or "find" in text_lower:
        return "numerical"

    if "explain" in text_lower or "describe" in text_lower:
        return "long"

    if "state" in text_lower or "define" in text_lower:
        return "short"

    if "assertion" in text_lower and "reason" in text_lower:
        return "assertion"

    return "short"


def enrich_chapter(chapter_dir: Path):

    cleaned_file = chapter_dir / "chapter_content_cleaned.json"

    if not cleaned_file.exists():
        print(f"⏭ No cleaned file in {chapter_dir.name}")
        return

    with open(cleaned_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    enriched = data.copy()

    enriched.setdefault("short_questions", [])
    enriched.setdefault("long_questions", [])
    enriched.setdefault("numericals", [])
    enriched.setdefault("assertions", [])

    exercises = data.get("exercises", [])

    for item in exercises:
        q_text = item.get("question", "")
        page = item.get("page")

        q_type = classify_question(q_text)

        entry = {
            "question": q_text,
            "page": page
        }

        if q_type == "numerical":
            enriched["numericals"].append(entry)

        elif q_type == "long":
            enriched["long_questions"].append(entry)

        elif q_type == "assertion":
            enriched["assertions"].append(entry)

        else:
            enriched["short_questions"].append(entry)

    output_file = chapter_dir / "chapter_content_enriched.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"✅ Enriched content saved → {output_file}")
