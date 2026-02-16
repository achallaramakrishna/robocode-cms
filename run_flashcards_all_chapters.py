import json
import argparse
from pathlib import Path

from flashcards.generator import generate_flashcards_for_chapter


def run_flashcards_for_course(json_file: Path):

    if not json_file.exists():
        raise FileNotFoundError(f"Course JSON not found: {json_file}")

    with open(json_file, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    course_id = ctx.get("course_id")

    if not course_id:
        raise ValueError("course_id missing in JSON")

    base_dir = (
        Path("workspace")
        / "courses"
        / str(course_id)
        / "chapters"
    )

    if not base_dir.exists():
        raise FileNotFoundError(f"Chapters folder not found: {base_dir}")

    print("\n🚀 STARTING FLASHCARD GENERATION")
    print(f"📚 Course ID: {course_id}")
    print("--------------------------------------------------")

    chapters = sorted([
        d for d in base_dir.iterdir()
        if d.is_dir()
    ])

    if not chapters:
        print("⚠️ No chapters found.")
        return

    for chapter_dir in chapters:

        cleaned_file = chapter_dir / "chapter_content_cleaned.json"

        if not cleaned_file.exists():
            print(f"⏭️ Skipping {chapter_dir.name} (no cleaned file)")
            continue

        print(f"🧠 Generating flashcards → {chapter_dir.name}")
        generate_flashcards_for_chapter(chapter_dir)

    print("\n✅ FLASHCARD GENERATION COMPLETED")
    print("--------------------------------------------------")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate flashcards for all chapters in a course"
    )

    parser.add_argument(
        "json_file",
        type=str,
        help="Path to course JSON file"
    )

    args = parser.parse_args()

    run_flashcards_for_course(Path(args.json_file))
