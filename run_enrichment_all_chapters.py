import json
import argparse
from pathlib import Path
from extractors.enrichment_engine import enrich_chapter


def run_for_course(json_file: Path):

    with open(json_file, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    course_id = ctx.get("course_id")

    base_dir = Path("workspace") / "courses" / str(course_id) / "chapters"

    for chapter in base_dir.iterdir():
        if chapter.is_dir():
            enrich_chapter(chapter)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file")
    args = parser.parse_args()

    run_for_course(Path(args.json_file))
