import json
import sys
from pathlib import Path
from phase_a_courses import ensure_course


def run(json_path: str):
    course_file = Path(json_path)

    if not course_file.exists():
        raise FileNotFoundError(f"{course_file} not found")

    # Load course metadata
    with open(course_file, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    # Ensure course exists in DB
    course_id = ensure_course(ctx)

    # Persist course_id back into JSON
    ctx["course_id"] = course_id
    with open(course_file, "w", encoding="utf-8") as f:
        json.dump(ctx, f, indent=2)

    print(f"📌 Phase A complete. Using course_id={course_id}")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage:")
        print("python phase_a_runner.py <path_to_json>")
        sys.exit(1)

    run(sys.argv[1])
