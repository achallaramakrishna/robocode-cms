import json
import argparse
from pathlib import Path

# Import generator
from practice_tests.generate_textbook_practice_test import (
    generate_practice_test_for_chapter
)


def run_for_course(json_file: Path):

    if not json_file.exists():
        raise FileNotFoundError(f"JSON not found: {json_file}")

    with open(json_file, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    course_id = ctx.get("course_id")

    if not course_id:
        raise ValueError("❌ course_id missing in JSON")

    base_dir = Path("workspace") / "courses" / str(course_id) / "chapters"

    if not base_dir.exists():
        raise FileNotFoundError(f"Course folder not found: {base_dir}")

    print("🚀 GENERATING TEXTBOOK PRACTICE TESTS (12A & 12B)")
    print(f"📚 Course ID: {course_id}")

    for chapter in sorted(base_dir.iterdir()):

        if not chapter.is_dir():
            continue

        print(f"\n📘 {chapter.name}")

        generate_practice_test_for_chapter(chapter)

    print("\n✅ Textbook Practice JSON Generation Complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", help="Course JSON file path")
    args = parser.parse_args()

    run_for_course(Path(args.json_file))
