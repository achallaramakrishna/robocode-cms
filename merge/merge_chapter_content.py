import json
from pathlib import Path


def merge_chapter(chapter_dir: Path):

    ocr_dir = chapter_dir / "ocr_openai"

    if not ocr_dir.exists():
        print(f"⏭ Skipping {chapter_dir.name} (no OCR folder)")
        return

    page_files = sorted(ocr_dir.glob("page_*.json"))

    if not page_files:
        print(f"⏭ No OCR pages found for {chapter_dir.name}")
        return

    print(f"📄 Found {len(page_files)} OCR pages")

    # --------------------------------------------------
    # Initialize clean chapter structure
    # --------------------------------------------------

    chapter_data = {
        "chapter_id": chapter_dir.name,
        "metadata": {
            "source": "ocr_openai_structured",
            "page_count": len(page_files),
            "version": "4.0_structured_merge"
        },
        "definitions": [],
        "formulas": [],
        "differences": [],
        "unit_mappings": [],
        "conceptual_facts": [],
        "examples": [],
        "exercise_sections": [],
        "mcq_sections": [],
        "numerical_sections": [],
        "short_long_sections": [],
        "diagrams": [],
        "tables": []
    }

    # --------------------------------------------------
    # Merge structured_content from each page
    # --------------------------------------------------

    total_exercises = 0

    for page_file in page_files:

        with open(page_file, "r", encoding="utf-8") as f:
            page_data = json.load(f)

        structured = page_data.get("structured_content", {})

        chapter_data["definitions"].extend(structured.get("definitions", []))
        chapter_data["formulas"].extend(structured.get("formulas", []))
        chapter_data["differences"].extend(structured.get("differences", []))
        chapter_data["unit_mappings"].extend(structured.get("unit_mappings", []))
        chapter_data["conceptual_facts"].extend(structured.get("conceptual_facts", []))
        chapter_data["examples"].extend(structured.get("examples", []))

        # --------------------------------------------------
        # Robust Exercise Extraction
        # --------------------------------------------------

        page_exercises = structured.get("exercise_sections", [])

        for section in page_exercises:

            title = section.get("section_title", "").strip()

            # Normalize title
            normalized_title = title.upper().replace("–", "-").replace(" ", "")

            # Try to find existing section with same title
            existing_section = None
            for sec in chapter_data["exercise_sections"]:
                sec_title = sec.get("section_title", "").upper().replace("–", "-").replace(" ", "")
                if sec_title == normalized_title:
                    existing_section = sec
                    break

            if existing_section:
                existing_section["questions"].extend(section.get("questions", []))
            else:
                chapter_data["exercise_sections"].append(section)

            total_exercises += 1


        chapter_data["mcq_sections"].extend(structured.get("mcq_sections", []))
        chapter_data["numerical_sections"].extend(structured.get("numerical_sections", []))
        chapter_data["short_long_sections"].extend(structured.get("short_long_sections", []))
        chapter_data["diagrams"].extend(structured.get("diagrams", []))
        chapter_data["tables"].extend(structured.get("tables", []))

    # --------------------------------------------------
    # Save merged chapter
    # --------------------------------------------------

    output_file = chapter_dir / "chapter_content.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chapter_data, f, indent=2, ensure_ascii=False)

    print(f"📘 Total exercise sections merged: {total_exercises}")
    print(f"✅ Chapter merged successfully → {output_file}")
