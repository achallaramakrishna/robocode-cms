from pathlib import Path
from db_bootstrap.db_conn import get_connection


def sync_session_uuids_from_workspace(course_id: int, course_dir: Path):
    chapters_root = course_dir / "chapters"

    if not chapters_root.exists():
        raise RuntimeError(f"No chapters folder at {chapters_root}")

    conn = get_connection()
    cursor = conn.cursor()

    print(f"🔄 Syncing session_uuid from workspace for course_id={course_id}")
    print(f"📂 Chapters root: {chapters_root}")

    # Get DB sessions ordered by ID
    cursor.execute("""
        SELECT course_session_id, session_title
        FROM rd_course_sessions
        WHERE course_id = %s
        ORDER BY course_session_id
    """, (course_id,))

    db_sessions = cursor.fetchall()

    # Get workspace UUID folders
    workspace_folders = sorted(
        [d.name for d in chapters_root.iterdir() if d.is_dir()]
    )

    if len(db_sessions) != len(workspace_folders):
        raise RuntimeError(
            f"Mismatch: DB sessions={len(db_sessions)} "
            f"Workspace folders={len(workspace_folders)}"
        )

    updated = 0

    for (session_id, session_title), folder_uuid in zip(db_sessions, workspace_folders):
        cursor.execute("""
            UPDATE rd_course_sessions
            SET session_uuid = %s
            WHERE course_session_id = %s
        """, (folder_uuid, session_id))

        updated += 1
        print(
            f"🔁 DB_ID={session_id} ({session_title}) "
            f"→ UUID={folder_uuid}"
        )

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n✅ UUID sync complete → updated={updated}")


if __name__ == "__main__":
    COURSE_ID = 54
    COURSE_DIR = Path(r"C:\robocode\workspace\courses\54")

    sync_session_uuids_from_workspace(COURSE_ID, COURSE_DIR)
