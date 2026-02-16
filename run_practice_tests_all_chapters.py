import json
import argparse
from pathlib import Path

from practice_tests.generate_chapter_practice_test import generate_practice_test_for_chapter


VERSIONS_PER_CHAPTER = 3


def run_for_course(json_file: Path):

    if not json_file.exists():
        raise FileNotFoundError("Course JSON not found")

    with open(json_file, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    course_id = ctx.get("course_id")
    if not course_id:
        raise ValueError("course_id missing")

    base_dir = Path("workspace") / "courses" / str(course_id) / "chapters"
    if not base_dir.exists():
        raise FileNotFoundError(f"Chapters folder not found: {base_dir}")

    print("🚀 STARTING HYBRID PRACTICE TEST GENERATION")
    print(f"📚 Course ID: {course_id}")
    print("--------------------------------------------------")

    chapters = sorted([d for d in base_dir.iterdir() if d.is_dir()])

    for chapter in chapters:
        cleaned_file = chapter / "chapter_content_cleaned.json"
        if not cleaned_file.exists():
            print(f"⏭ Skipping {chapter.name} (no cleaned file)")
            continue

        print(f"\n🧠 Chapter → {chapter.name}")
        for v in range(1, VERSIONS_PER_CHAPTER + 1):
            generate_practice_test_for_chapter(chapter, version=v)

    print("\n--------------------------------------------------")
    print("✅ HYBRID PRACTICE TEST GENERATION COMPLETED")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file")
    args = parser.parse_args()
    run_for_course(Path(args.json_file))
