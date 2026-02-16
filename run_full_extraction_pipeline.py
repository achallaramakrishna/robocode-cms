import json
import argparse
from pathlib import Path

from run_extraction_pipeline import run_extraction_for_chapter


def run_for_course(json_file: Path):

    if not json_file.exists():
        raise FileNotFoundError("Course JSON not found")

    with open(json_file, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    course_id = ctx.get("course_id")

    if not course_id:
        raise ValueError("course_id missing")

    base_dir = (
        Path("workspace")
        / "courses"
        / str(course_id)
        / "chapters"
    )

    if not base_dir.exists():
        raise FileNotFoundError("Chapters folder not found")

    chapters = [d for d in base_dir.iterdir() if d.is_dir()]

    for chapter in chapters:
        run_extraction_for_chapter(chapter)

    print("\n🚀 FULL EXTRACTION COMPLETED")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("json_file")

    args = parser.parse_args()

    run_for_course(Path(args.json_file))
