import json
from pathlib import Path
import argparse

from clean_chapter_content import clean_chapter


def run_clean_for_course(json_path: Path):

    if not json_path.exists():
        raise FileNotFoundError(f"JSON not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    if "course_id" not in ctx:
        raise ValueError("course_id missing in JSON")

    course_id = ctx["course_id"]

    base_dir = (
        Path("workspace")
        / "courses"
        / str(course_id)
        / "chapters"
    )

    if not base_dir.exists():
        raise FileNotFoundError(f"Chapters directory not found: {base_dir}")

    print("\n🚀 STARTING CLEANING PROCESS")
    print(f"📚 Course ID: {course_id}")
    print("--------------------------------------------------")

    for chapter_dir in sorted(base_dir.iterdir()):

        if not chapter_dir.is_dir():
            continue

        chapter_file = chapter_dir / "chapter_content.json"

        if not chapter_file.exists():
            print(f"⏭️ Skipping {chapter_dir.name} (no chapter_content.json)")
            continue

        print(f"🧹 Cleaning {chapter_dir.name}")
        clean_chapter(chapter_dir)

    print("\n✅ CLEANING COMPLETED FOR ALL CHAPTERS")
    print("--------------------------------------------------")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("json_file")

    args = parser.parse_args()

    run_clean_for_course(Path(args.json_file))
