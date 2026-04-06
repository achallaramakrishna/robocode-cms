"""
upload_day01_splits.py
=======================
Uploads per-sub-topic split assets for Day 1 to prod and registers them in DB.

Also generates HTML note files (one per topic section) by running
generate_session_html.py on prod.

What this does:
  1. Upload 6 lab manual JSONs   → assets/lab_manuals/
  2. Upload 6 flashcard set JSONs → assets/flashcards/
  3. Upload generate_session_html.py to /tmp/ and run it
     → creates 6 HTML files in /opt/robodynamics/session_materials/162/
  4. Add DB rows (rd_course_session_details) for all 12 new JSON files

Run from: C:\\...\\db_bootstrap\\courses\\java_fullstack\\
    python upload_day01_splits.py
"""

import subprocess
import sys
from pathlib import Path
from datetime import date

# ─── Config ───────────────────────────────────────────────────────────────────

PLINK    = r"C:\Program Files\PuTTY\plink.exe"
PSCP     = r"C:\Program Files\PuTTY\pscp.exe"
SSH_HOST = "root@168.231.123.108"
SSH_PASS = "Jatni@752050"

COURSE_ID        = 162
COURSE_SESSION_ID = 2669
SESSION_UUID     = "be0aaa5c-9ba5-41d7-a524-9d3f71b97ca7"
ENROLLMENT_ID    = 203

PROD_WORKSPACE   = "/opt/robodynamics/cms-engine/workspace/courses"
PROD_SM          = "/opt/robodynamics/session_materials"
VENV_PYTHON      = "/opt/robodynamics/venv/bin/python3"

SESSION_ASSET_BASE = f"{PROD_WORKSPACE}/{COURSE_ID}/chapters/{SESSION_UUID}/assets"
NOTES_JSON_PROD    = f"{SESSION_ASSET_BASE}/notes/notes_day_01.json"

LOCAL_SPLITS  = Path(__file__).parent / "generated_content" / "day_01" / "splits"
LOCAL_HTML_GEN = Path(__file__).parent / "generate_session_html.py"


# ─── SSH/SCP helpers ─────────────────────────────────────────────────────────

def run_remote(cmd: str) -> str:
    result = subprocess.run(
        [PLINK, "-ssh", SSH_HOST, "-pw", SSH_PASS, "-batch", cmd],
        capture_output=True, text=True
    )
    out = result.stdout.strip()
    err = result.stderr.strip()
    if err:
        print(f"    [stderr] {err[:200]}")
    return out


def upload_file(local_path: Path, remote_path: str) -> bool:
    result = subprocess.run(
        [PSCP, "-pw", SSH_PASS, str(local_path), f"{SSH_HOST}:{remote_path}"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"    PSCP error: {result.stderr.strip()[:200]}")
    return result.returncode == 0


# ─── Step 1 & 2: Upload split JSON files ─────────────────────────────────────

def upload_split_files():
    print("\n" + "=" * 62)
    print("STEP 1/2: Upload split lab manuals and flashcard sets")
    print("=" * 62)

    files = [
        # (local_filename, remote_subfolder, db_type, topic_label)
        ("lab_d01_01_jvm_platform.json",   "lab_manuals", "lab_manual",
         "Day 1 — Lab: JVM, JDK & JRE — Java Platform Architecture"),
        ("lab_d01_02_primitives.json",      "lab_manuals", "lab_manual",
         "Day 1 — Lab: Primitive Data Types & Ranges"),
        ("lab_d01_03_operators.json",       "lab_manuals", "lab_manual",
         "Day 1 — Lab: Operators & EMI Calculator"),
        ("lab_d01_04_flow_control.json",    "lab_manuals", "lab_manual",
         "Day 1 — Lab: Flow Control — ATM Simulator"),
        ("lab_d01_05_arrays.json",          "lab_manuals", "lab_manual",
         "Day 1 — Lab: Arrays & Arrays Utility Class"),
        ("lab_d01_06_capstone.json",        "lab_manuals", "lab_manual",
         "Day 1 — Lab: Capstone — Mini Bank Statement Generator"),
        ("fc_d01_01_jvm_platform.json",    "flashcards",  "flashcard",
         "Day 1 — Flashcards: JVM, JDK & JRE Platform Architecture"),
        ("fc_d01_02_primitives.json",       "flashcards",  "flashcard",
         "Day 1 — Flashcards: Primitive Data Types & Type Conversion"),
        ("fc_d01_03_operators.json",        "flashcards",  "flashcard",
         "Day 1 — Flashcards: Operators, Short-Circuit & Precision"),
        ("fc_d01_04_flow_control.json",     "flashcards",  "flashcard",
         "Day 1 — Flashcards: Flow Control — Loops, Switch & Break/Continue"),
        ("fc_d01_05_arrays.json",           "flashcards",  "flashcard",
         "Day 1 — Flashcards: Arrays, Varargs & java.util.Arrays"),
        ("fc_d01_06_best_practices.json",   "flashcards",  "flashcard",
         "Day 1 — Flashcards: Best Practices, Naming & NullPointerException"),
    ]

    uploaded = []
    for filename, subfolder, db_type, topic in files:
        local = LOCAL_SPLITS / filename
        if not local.exists():
            print(f"  MISSING local file: {filename}")
            continue
        remote_dir  = f"{SESSION_ASSET_BASE}/{subfolder}"
        remote_path = f"{remote_dir}/{filename}"

        # Ensure remote dir exists
        run_remote(f"mkdir -p {remote_dir}")

        # Upload
        print(f"  Uploading {filename} ...", end=" ", flush=True)
        ok = upload_file(local, remote_path)
        print("OK" if ok else "FAILED")

        if ok:
            uploaded.append((filename, remote_path, db_type, topic))

    return uploaded


# ─── Step 3: Generate HTML notes ─────────────────────────────────────────────

def generate_html_notes():
    print("\n" + "=" * 62)
    print("STEP 3: Generate per-topic HTML notes on prod")
    print("=" * 62)

    # Upload generate_session_html.py
    remote_gen = "/tmp/generate_session_html.py"
    print(f"  Uploading generate_session_html.py ...", end=" ", flush=True)
    ok = upload_file(LOCAL_HTML_GEN, remote_gen)
    print("OK" if ok else "FAILED")
    if not ok:
        print("  Cannot generate HTML notes — skipping.")
        return []

    # Ensure output dir exists
    sm_dir = f"{PROD_SM}/{COURSE_ID}"
    run_remote(f"mkdir -p {sm_dir}")

    # Run the generator
    cmd = (f"source /opt/robodynamics/venv/bin/activate && "
           f"{VENV_PYTHON} {remote_gen} "
           f"--notes {NOTES_JSON_PROD} "
           f"--course-id {COURSE_ID} "
           f"--session-day 1")

    print(f"  Running HTML generator ...", flush=True)
    output = run_remote(cmd)
    if output:
        for line in output.splitlines():
            print(f"    {line}")

    # List generated files
    ls_out = run_remote(f"ls {sm_dir}/session1_*.html 2>/dev/null")
    html_files = [f.strip() for f in ls_out.splitlines() if f.strip()]
    print(f"  HTML files generated: {len(html_files)}")
    for hf in html_files:
        print(f"    {hf}")

    return html_files


# ─── Step 4: Register in DB ──────────────────────────────────────────────────

def register_in_db(uploaded_files):
    print("\n" + "=" * 62)
    print("STEP 4: Register new files in rd_course_session_details")
    print("=" * 62)

    today = date.today().isoformat()

    # Build Python script to run on prod
    inserts = []
    for filename, remote_path, db_type, topic in uploaded_files:
        safe_topic = topic.replace("'", "\\'")
        safe_path  = remote_path.replace("'", "\\'")
        inserts.append(
            f"    insert_if_new(cur, {COURSE_SESSION_ID}, {COURSE_ID}, "
            f"'{db_type}', '{safe_path}', '{safe_topic}', '{today}')"
        )

    insert_block = "\n".join(inserts)

    script = f"""import mysql.connector
conn = mysql.connector.connect(
    host='localhost', user='root', password='Jatni@752050',
    database='robodynamics_db', charset='utf8mb4', autocommit=False
)
cur = conn.cursor()

def insert_if_new(cur, session_id, course_id, db_type, file_path, topic, today):
    cur.execute(
        "SELECT course_session_detail_id FROM rd_course_session_details "
        "WHERE course_session_id = %s AND file = %s",
        (session_id, file_path)
    )
    if cur.fetchone():
        print(f"  EXISTS  {{file_path.split('/')[-1]}}")
        return
    cur.execute(
        \"\"\"INSERT INTO rd_course_session_details
            (topic, creation_date, version, course_id, course_session_id,
             type, file, session_detail_id, tier_level, tier_order)
           VALUES (%s, %s, 1, %s, %s, %s, %s, 0, 'BEGINNER', 1)\"\"\",
        (topic, today, course_id, session_id, db_type, file_path)
    )
    print(f"  INSERTED id={{cur.lastrowid}}  {{file_path.split('/')[-1]}}")

{insert_block}

conn.commit()
conn.close()
print("DB registration complete.")
"""

    tmp = Path(__file__).parent / "_tmp_register.py"
    tmp.write_text(script, encoding="utf-8")

    remote_tmp = "/tmp/_tmp_register_splits.py"
    upload_file(tmp, remote_tmp)
    tmp.unlink(missing_ok=True)

    output = run_remote(
        f"source /opt/robodynamics/venv/bin/activate && "
        f"{VENV_PYTHON} {remote_tmp}"
    )
    for line in output.splitlines():
        print(f"  {line}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Course {COURSE_ID} — Day 1 Split Assets Upload")
    print(f"Session UUID: {SESSION_UUID}")

    uploaded = upload_split_files()
    html_files = generate_html_notes()
    register_in_db(uploaded)

    print(f"\n{'='*62}")
    print("COMPLETE")
    print(f"  Uploaded   : {len(uploaded)} split JSON files")
    print(f"  HTML notes : {len(html_files)} files generated")
    print(f"  DB rows    : registered above")
    print(f"\nVerify: https://robodynamics.in/course/monitor/v2"
          f"?courseId={COURSE_ID}&enrollmentId={ENROLLMENT_ID}")


if __name__ == "__main__":
    main()
