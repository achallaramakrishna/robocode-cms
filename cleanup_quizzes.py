import argparse
import json
from pathlib import Path


def delete_quizzes_for_course(json_path: Path):

    with open(json_path, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    course_id = ctx["course_id"]

    chapters_dir = Path("workspace/courses") / str(course_id) / "chapters"

    if not chapters_dir.exists():
        raise FileNotFoundError(f"{chapters_dir} not found")

    deleted = 0

    for chapter_dir in chapters_dir.iterdir():

        quizzes_dir = chapter_dir / "quizzes"

        if not quizzes_dir.exists():
            continue

        for quiz_file in quizzes_dir.glob("quiz_*.json"):
            quiz_file.unlink()
            deleted += 1
            print(f"🗑 Deleted {quiz_file}")

    print(f"\n✅ Deleted {deleted} quiz files.")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("json_path", type=str)

    args = parser.parse_args()

    delete_quizzes_for_course(Path(args.json_path))
