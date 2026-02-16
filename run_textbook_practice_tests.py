import json
import argparse
from pathlib import Path

from practice_tests.generate_textbook_practice_test import (
    generate_practice_test_for_chapter
)


def run_for_course(json_file: Path):

    with open(json_file, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    course_id = ctx.get("course_id")

    base_dir = Path("workspace") / "courses" / str(course_id) / "chapters"

    print("🚀 GENERATING TEXTBOOK PRACTICE TESTS (12A & 12B)")

    for chapter in sorted(base_dir.iterdir()):

        if not chapter.is_dir():
            continue

        print(f"\n📘 {chapter.name}")

        generate_practice_test_for_chapter(chapter)

    print("\n✅ DONE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file")
    args = parser.parse_args()
    run_for_course(Path(args.json_file))
