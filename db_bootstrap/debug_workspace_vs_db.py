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

db_uuids = sorted([row[0] for row in cursor.fetchall()])
workspace_dirs = sorted([d.name for d in CHAPTERS_DIR.iterdir() if d.is_dir()])

print("\nDB UUIDs:")
for u in db_uuids:
    print("  ", u)

print("\nWorkspace Folders:")
for w in workspace_dirs:
    print("  ", w)

print("\nExtra in Workspace:")
for w in workspace_dirs:
    if w not in db_uuids:
        print("  ", w)

print("\nMissing in Workspace:")
for u in db_uuids:
    if u not in workspace_dirs:
        print("  ", u)
