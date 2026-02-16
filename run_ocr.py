import os
import json
import argparse
from pathlib import Path

from ocr.ocr_runner import run_ocr_for_chapter


def run_ocr_from_json(json_path: Path, prompt_file: Path, force: bool):

    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    if "course_id" not in ctx:
        raise ValueError("❌ 'course_id' missing in JSON file.")

    course_id = ctx["course_id"]

    BASE_DIR = Path(__file__).resolve().parent

    chapters_dir = (
        BASE_DIR
        / "workspace"
        / "courses"
        / str(course_id)
        / "chapters"
    )

    if not chapters_dir.exists():
        raise FileNotFoundError(
            f"❌ Chapters folder not found: {chapters_dir}"
        )

    if not prompt_file.exists():
        raise FileNotFoundError(
            f"❌ Prompt file not found: {prompt_file}"
        )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("❌ OPENAI_API_KEY environment variable not set.")

    chapter_dirs = sorted([
        d for d in chapters_dir.iterdir()
        if d.is_dir()
    ])

    if not chapter_dirs:
        raise RuntimeError("❌ No chapters found to OCR.")

    print("\n🚀 STARTING OCR PROCESS")
    print(f"📚 Course ID: {course_id}")
    print(f"📂 Chapters Folder: {chapters_dir}")
    print(f"📝 Prompt File: {prompt_file}")
    print(f"🔁 Force Reprocess: {force}")
    print("--------------------------------------------------")

    for chapter_dir in chapter_dirs:

        print(f"\n📘 Processing Chapter: {chapter_dir.name}")

        run_ocr_for_chapter(
            chapter_dir=chapter_dir,
            api_key=api_key,
            prompt_file=prompt_file,
            force_reprocess=force
        )

    print("\n✅ OCR COMPLETED SUCCESSFULLY")
    print("--------------------------------------------------")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Robo Dynamics Phase D - OCR Runner"
    )

    parser.add_argument(
        "json_file",
        type=str,
        help="Path to course JSON file"
    )

    parser.add_argument(
        "prompt_file",
        type=str,
        help="Path to OCR prompt file"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocess all pages even if OCR JSON exists"
    )

    args = parser.parse_args()

    run_ocr_from_json(
        Path(args.json_file),
        Path(args.prompt_file),
        force=args.force
    )
