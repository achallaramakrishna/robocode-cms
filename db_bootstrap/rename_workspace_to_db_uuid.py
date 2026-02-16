from pathlib import Path
from db_bootstrap.db_conn import get_connection

COURSE_ID = 54
CHAPTERS_DIR = Path(r"C:\robocode\workspace\courses\54\chapters")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT session_uuid
    FROM rd_course_sessions
    WHERE course_id = %s
      AND session_type = 'session'
    ORDER BY course_session_id
""", (COURSE_ID,))

db_uuids = [row[0] for row in cursor.fetchall()]

workspace_dirs = sorted([d for d in CHAPTERS_DIR.iterdir() if d.is_dir()])

if len(db_uuids) != len(workspace_dirs):
    raise RuntimeError(
        f"Mismatch: DB sessions={len(db_uuids)} "
        f"Workspace folders={len(workspace_dirs)}"
    )

print("🔄 Renaming workspace folders to match DB UUIDs")

for folder, new_uuid in zip(workspace_dirs, db_uuids):
    new_path = CHAPTERS_DIR / new_uuid

    if folder.name == new_uuid:
        print(f"✔ Already correct: {folder.name}")
        continue

    folder.rename(new_path)
    print(f"🔁 {folder.name} → {new_uuid}")

print("✅ Workspace rename complete")
