import json
import argparse
from pathlib import Path
from normalizer.normalizer import normalize_chapter


def run_normalizer_from_json(json_path: Path):

    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    if "course_id" not in ctx:
        raise ValueError("course_id missing in JSON.")

    course_id = ctx["course_id"]

    chapters_dir = Path("workspace/courses") / str(course_id) / "chapters"

    if not chapters_dir.exists():
        raise FileNotFoundError(f"Chapters folder not found: {chapters_dir}")

    print(f"\n📚 Normalizing Course → {course_id}")

    for chapter_dir in chapters_dir.iterdir():

        if not chapter_dir.is_dir():
            continue

        ocr_dir = chapter_dir / "ocr_openai"

        if not ocr_dir.exists():
            print(f"⏭️ Skipping {chapter_dir.name} (no OCR folder)")
            continue

        print(f"🔄 Normalizing {chapter_dir.name}")

        normalize_chapter(chapter_dir)

    print("\n✅ Normalization completed.")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Normalize OCR to LMS schema")
    parser.add_argument("json_path", type=str)

    args = parser.parse_args()

    run_normalizer_from_json(Path(args.json_path))
