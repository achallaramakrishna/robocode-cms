from pathlib import Path
import json
import argparse

from merge.merge_chapter_content import merge_chapter


def run_merge_from_json(json_path: Path, force: bool):

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

    print("\n🚀 STARTING MERGE PROCESS")
    print(f"📚 Course ID: {course_id}")
    print(f"🔁 Force Merge: {force}")
    print("--------------------------------------------------")

    for chapter_dir in sorted(base_dir.iterdir()):

        if not chapter_dir.is_dir():
            continue

        output_file = chapter_dir / "chapter_content.json"

        if output_file.exists() and not force:
            print(f"⏭️ Skipping {chapter_dir.name} (already merged)")
            continue

        print(f"🔄 Merging {chapter_dir.name}")
        merge_chapter(chapter_dir)

    print("\n✅ MERGE COMPLETED")
    print("--------------------------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-merge even if chapter_content.json exists"
    )

    args = parser.parse_args()

    run_merge_from_json(Path(args.json_file), force=args.force)
