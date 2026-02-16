import json
import argparse
from pathlib import Path

from flashcards.generator import generate_flashcards_for_chapter


def run_flashcards_from_json(json_path: Path):

    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    if "course_id" not in ctx:
        raise ValueError("course_id missing in JSON. Run ingest first.")

    course_id = ctx["course_id"]

    chapters_dir = Path("workspace") / "courses" / str(course_id) / "chapters"

    if not chapters_dir.exists():
        raise FileNotFoundError(f"Chapters folder not found: {chapters_dir}")

    print(f"\n📚 Generating flashcards for Course → {course_id}")

    chapter_dirs = sorted([
        d for d in chapters_dir.iterdir()
        if d.is_dir()
    ])

    if not chapter_dirs:
        print("⚠️ No chapters found.")
        return

    for chapter_dir in chapter_dirs:

        cleaned_file = chapter_dir / "chapter_content_cleaned.json"

        if not cleaned_file.exists():
            print(f"⏭️ Skipping {chapter_dir.name} (no cleaned file)")
            continue

        print(f"🧠 Generating flashcards for {chapter_dir.name}")
        generate_flashcards_for_chapter(chapter_dir)

    print("\n✅ Flashcard generation completed for course.")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate flashcards for a specific course"
    )
    parser.add_argument(
        "json_path",
        type=str,
        help="Path to course JSON file"
    )

    args = parser.parse_args()

    run_flashcards_from_json(Path(args.json_path))
