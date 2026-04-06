"""
upload_to_prod.py
==================
Uploads generated content to prod VPS and registers assets in DB.

For Session 1:
  - Set 1: OVERWRITES placeholder files with real AI content
  - Set 2: Creates NEW files + NEW DB rows (with set_number=2 in filename)

Usage:
    python upload_to_prod.py --session 1
    python upload_to_prod.py --session 1 --set 1    # only upload set 1
    python upload_to_prod.py --session 1 --set 2    # only upload set 2 + register DB

Requires:
    - PuTTY tools: plink.exe + pscp.exe at C:\\Program Files\\PuTTY\\
    - Generated files from generate_session_content.py in ./generated_content/
"""

import sys
import os
import json
import subprocess
import argparse
from pathlib import Path
from datetime import date

# ─── Config ───────────────────────────────────────────────────────────────────

PLINK  = r"C:\Program Files\PuTTY\plink.exe"
PSCP   = r"C:\Program Files\PuTTY\pscp.exe"
SSH_HOST = "root@168.231.123.108"
SSH_PASS = "Jatni@752050"

PROD_WORKSPACE = "/opt/robodynamics/cms-engine/workspace/courses"
PROD_DB_BOOTSTRAP = "/opt/robodynamics/cms-engine/db_bootstrap"
VENV_PYTHON = "/opt/robodynamics/venv/bin/python3"

GENERATED_DIR = Path(__file__).parent / "generated_content"

# State file with session UUIDs
STATE_FILE = Path(__file__).parent / "prod_state.json"

# ─── Mapping: asset_type -> folder on prod, DB type, filename prefix ──────────

ASSET_CONFIG = {
    "notes":         {"folder": "notes",        "db_type": "notes",        "prefix": "notes_"},
    "flashcards":    {"folder": "flashcards",    "db_type": "flashcard",    "prefix": "fc_"},
    "quiz":          {"folder": "quizzes",       "db_type": "quiz",         "prefix": "quiz_"},
    "matching_game": {"folder": "matchinggame",  "db_type": "matchinggame", "prefix": "mg_"},
    "matching_pair": {"folder": "matchingpair",  "db_type": "matchingpair", "prefix": "mp_"},
    "lab_manual":    {"folder": "lab_manuals",   "db_type": "lab_manual",   "prefix": "lab_"},
    "exam_paper":    {"folder": "exam_papers",   "db_type": "exam_paper",   "prefix": "exam_"},
}

# Mapping: local set_N filename -> asset type
FILENAME_TO_TYPE = {
    "notes_":  "notes",
    "fc_":     "flashcards",
    "quiz_":   "quiz",
    "mg_":     "matching_game",
    "mp_":     "matching_pair",
    "lab_":    "lab_manual",
    "exam_":   "exam_paper",
}


def get_asset_type_from_filename(filename: str) -> str:
    for prefix, atype in FILENAME_TO_TYPE.items():
        if filename.startswith(prefix):
            return atype
    return None


# ─── SSH/SCP helpers ─────────────────────────────────────────────────────────

def run_remote(cmd: str, capture=True) -> str:
    """Run a command on the remote server via plink."""
    result = subprocess.run(
        [PLINK, "-ssh", SSH_HOST, "-pw", SSH_PASS, "-batch", cmd],
        capture_output=capture,
        text=True
    )
    if result.returncode != 0 and result.stderr:
        stderr = result.stderr.strip()
        if stderr:
            print(f"  [stderr] {stderr}")
    return result.stdout.strip() if capture else ""


def upload_file(local_path: Path, remote_path: str) -> bool:
    """Upload a local file to prod via pscp."""
    result = subprocess.run(
        [PSCP, "-pw", SSH_PASS, str(local_path), f"{SSH_HOST}:{remote_path}"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def load_prod_state() -> dict:
    """Load state file with course_id and session UUIDs."""
    if not STATE_FILE.exists():
        print(f"Error: State file not found: {STATE_FILE}")
        print("Run bootstrap_prod.py first to create the state file.")
        sys.exit(1)
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def get_session_info(state: dict, day: int) -> dict:
    """Get session UUID and course_session_id for a given day."""
    sessions = state.get("sessions", [])
    for s in sessions:
        if s["day"] == day:
            return s
    return None


def get_next_session_detail_id(course_id: int, course_session_id: int) -> int:
    """Get the next available session_detail_id for the given session."""
    # Run a Python snippet remotely to query DB
    script = f"""
import sys
sys.path.insert(0, '{PROD_DB_BOOTSTRAP}')
from db_conn import get_connection
conn = get_connection()
c = conn.cursor()
c.execute("SELECT MAX(session_detail_id) FROM rd_course_session_details WHERE course_id = {course_id}")
row = c.fetchone()
max_id = row[0] if row[0] else 0
print(max_id)
conn.close()
"""
    # Write script to temp file and run it
    tmp_script = Path(__file__).parent / "_tmp_query.py"
    tmp_script.write_text(script, encoding="utf-8")

    # Upload and run
    upload_file(tmp_script, "/tmp/_tmp_query.py")
    result = run_remote(f"source /opt/robodynamics/venv/bin/activate && python3 /tmp/_tmp_query.py")
    tmp_script.unlink(missing_ok=True)

    try:
        return int(result.strip()) + 1
    except:
        return 100  # fallback


def register_asset_in_db(course_id: int, course_session_id: int, session_detail_id: int,
                          asset_type: str, file_path: str, topic: str) -> bool:
    """Register an asset in rd_course_session_details."""
    script = f"""
import sys
sys.path.insert(0, '{PROD_DB_BOOTSTRAP}')
from db_conn import get_connection
from datetime import date

conn = get_connection()
c = conn.cursor()

# Check if already exists
c.execute(
    "SELECT course_session_detail_id FROM rd_course_session_details WHERE course_session_id = %s AND file = %s",
    ({course_session_id}, '{file_path}')
)
if c.fetchone():
    print("EXISTS")
    conn.close()
    sys.exit(0)

c.execute(
    \"\"\"INSERT INTO rd_course_session_details
    (topic, creation_date, version, course_id, course_session_id, type, file, session_detail_id, tier_level, tier_order)
    VALUES (%s, %s, 1, %s, %s, %s, %s, %s, 'BEGINNER', 1)\"\"\",
    ('{topic}', date.today().isoformat(), {course_id}, {course_session_id}, '{asset_type}', '{file_path}', {session_detail_id})
)
conn.commit()
print(f"INSERTED id={{c.lastrowid}}")
conn.close()
"""
    tmp_script = Path(__file__).parent / "_tmp_insert.py"
    tmp_script.write_text(script, encoding="utf-8")
    upload_file(tmp_script, "/tmp/_tmp_insert.py")
    result = run_remote(f"source /opt/robodynamics/venv/bin/activate && python3 /tmp/_tmp_insert.py")
    tmp_script.unlink(missing_ok=True)
    return result.strip()


# ─── Main upload logic ────────────────────────────────────────────────────────

def upload_session(day: int, sets_to_upload: list):
    """Upload generated content for a session to prod."""
    state = load_prod_state()
    course_id = state["course_id"]
    session_info = get_session_info(state, day)

    if not session_info:
        print(f"Error: No session found for day {day} in prod_state.json")
        sys.exit(1)

    session_uuid = session_info["session_uuid"]
    course_session_id = session_info["course_session_id"]
    session_title = session_info["session_title"]

    print(f"\n{'='*60}")
    print(f"Uploading content for Day {day}: {session_title}")
    print(f"  course_id: {course_id}")
    print(f"  course_session_id: {course_session_id}")
    print(f"  session_uuid: {session_uuid}")
    print(f"{'='*60}")

    # Remote asset base path
    remote_base = f"{PROD_WORKSPACE}/{course_id}/chapters/{session_uuid}/assets"

    for set_num in sets_to_upload:
        local_set_dir = GENERATED_DIR / f"day_{day:02d}" / f"set_{set_num}"

        if not local_set_dir.exists():
            print(f"\n⚠️  No generated content found for Set {set_num} at: {local_set_dir}")
            print(f"    Run generate_session_content.py --session {day} --set {set_num} first")
            continue

        print(f"\n--- Uploading Set {set_num} ---")

        json_files = list(local_set_dir.glob("*.json"))
        if not json_files:
            print(f"  No JSON files found in {local_set_dir}")
            continue

        # For Set 2, get next available session_detail_id
        if set_num == 2:
            next_detail_id = get_next_session_detail_id(course_id, course_session_id)
            print(f"  Next session_detail_id: {next_detail_id}")
        else:
            next_detail_id = None

        for local_file in sorted(json_files):
            if local_file.name.startswith("_raw_"):
                continue  # Skip raw debug files

            # Determine asset type
            asset_type = get_asset_type_from_filename(local_file.name)
            if not asset_type:
                print(f"  ⚠️  Cannot determine asset type for: {local_file.name}")
                continue

            config = ASSET_CONFIG[asset_type]
            folder = config["folder"]
            db_type = config["db_type"]

            # Remote file path
            # Set 1: overwrite existing files (use set1 naming that matches existing DB rows)
            # Set 2: use set2 naming for new files
            if set_num == 1:
                # Map to existing filenames
                existing_map = {
                    "notes":         f"notes_day_{day:02d}.json",
                    "flashcards":    f"fc_concept_beginner_01.json",
                    "quiz":          f"premium_quiz_set_01.json",
                    "matching_game": f"mg_definition_01.json",
                    "matching_pair": f"mp_definition_01.json",
                    "lab_manual":    f"lab_day_{day:02d}.json",
                    "exam_paper":    f"exam_paper_day_{day:02d}.json",
                }
                remote_filename = existing_map.get(asset_type, local_file.name)
            else:
                # Set 2: use descriptive name
                remote_filename = local_file.name

            remote_path = f"{remote_base}/{folder}/{remote_filename}"

            # Upload
            print(f"  ⬆  {asset_type}: {local_file.name} → {folder}/{remote_filename}", end="", flush=True)
            success = upload_file(local_file, remote_path)

            if success:
                print(f" ✅")
            else:
                print(f" ❌")
                continue

            # Register in DB (only for Set 2 - new rows)
            if set_num == 2:
                topic = f"{session_title} - {asset_type.replace('_', ' ').title()} (Banking/Finance)"
                result = register_asset_in_db(
                    course_id, course_session_id, next_detail_id,
                    db_type, remote_path, topic
                )
                print(f"     DB: {result}")
                next_detail_id += 1
            else:
                print(f"     (Set 1: overwriting existing file - no new DB row needed)")

    print(f"\n✅ Upload complete for Day {day}!")
    print(f"\nVerify on: https://robodynamics.in/course/monitor/v2?courseId={course_id}&enrollmentId=203")


def main():
    parser = argparse.ArgumentParser(description="Upload generated content to prod and register in DB")
    parser.add_argument("--session", type=int, required=True, help="Session day number (e.g., 1)")
    parser.add_argument("--set", type=int, choices=[1, 2], default=None, help="Upload only set 1 or set 2")
    args = parser.parse_args()

    sets = [args.set] if args.set else [1, 2]
    upload_session(args.session, sets)


if __name__ == "__main__":
    main()
