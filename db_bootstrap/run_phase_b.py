import json
import sys
from pathlib import Path
from phase_b_sessions import (
    create_sessions_from_pdfs,
    sync_session_uuids
)


def run(json_path: str):

    course_file = Path(json_path)

    if not course_file.exists():
        raise FileNotFoundError(f"{course_file} not found")

    with open(course_file, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    if "course_id" not in ctx:
        raise ValueError("course_id missing. Run Phase A first.")

    if "input_pdf_path" not in ctx:
        raise ValueError("input_pdf_path missing in JSON.")

    course_id = ctx["course_id"]
    input_pdf_path = ctx["input_pdf_path"]

    create_sessions_from_pdfs(course_id, input_pdf_path)
    sync_session_uuids(course_id)

    print("📌 Phase B complete: sessions + UUIDs are in sync")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage:")
        print("python run_phase_b.py <path_to_json>")
        sys.exit(1)

    run(sys.argv[1])
