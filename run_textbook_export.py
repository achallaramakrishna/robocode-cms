import json
import argparse
from pathlib import Path


def generate_textbook_practice(chapter_dir: Path):

    chapter_file = chapter_dir / "chapter_content.json"

    if not chapter_file.exists():
        print(f"⏭ Skipping {chapter_dir.name} (no chapter_content.json)")
        return

    with open(chapter_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    output_dir = chapter_dir / "assets" / "textbook_practice"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "textbook_questions.json"

    payload = {
        "type": "textbook_practice",
        "chapter_id": data.get("chapter_id"),
        "exercise_sections": data.get("exercise_sections", []),
        "mcq_sections": data.get("mcq_sections", []),
        "examples": data.get("examples", [])
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"✅ Exported → {output_file}")


def run_from_json(json_file: Path):

    if not json_file.exists():
        raise FileNotFoundError("Course JSON not found")

    with open(json_file, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    course_id = ctx.get("course_id")
    if not course_id:
        raise ValueError("course_id missing in JSON")

    base_dir = Path("workspace") / "courses" / str(course_id) / "chapters"

    if not base_dir.exists():
        raise FileNotFoundError("Chapters folder not found")

    print("🚀 EXPORTING TEXTBOOK QUESTIONS")
    print(f"📚 Course ID: {course_id}")
    print("--------------------------------------------------")

    for chapter in base_dir.iterdir():
        if chapter.is_dir():
            print(f"📘 Processing {chapter.name}")
            generate_textbook_practice(chapter)

    print("--------------------------------------------------")
    print("✅ EXPORT COMPLETED")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file")
    args = parser.parse_args()

    run_from_json(Path(args.json_file))
