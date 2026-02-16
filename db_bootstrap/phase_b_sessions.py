import uuid
from pathlib import Path
from db_conn import get_connection


def create_sessions_from_pdfs(course_id: int, input_pdf_path: str):
    """
    Phase-B:
    - Create course sessions from PDFs if missing
    - Reuses existing workspace UUIDs if present
    """

    conn = get_connection()
    cursor = conn.cursor()

    pdf_files = sorted(Path(input_pdf_path).rglob("*.pdf"))

    print(f"🔍 Scanning PDFs in: {input_pdf_path}")
    print(f"📄 PDFs found: {len(pdf_files)}")

    # Workspace location
    workspace_dir = Path(
        rf"C:\robocode\workspace\courses\{course_id}\chapters"
    )

    existing_workspace_uuids = []

    if workspace_dir.exists():
        existing_workspace_uuids = sorted(
            [d.name for d in workspace_dir.iterdir() if d.is_dir()]
        )

        print(
            f"📂 Found existing workspace folders: "
            f"{len(existing_workspace_uuids)}"
        )

    for index, pdf_file in enumerate(pdf_files):

        session_title = pdf_file.stem

        cursor.execute("""
            SELECT course_session_id
            FROM rd_course_sessions
            WHERE course_id = %s
              AND session_title = %s
            LIMIT 1
        """, (course_id, session_title))

        row = cursor.fetchone()

        if row:
            continue

        # 🔥 Reuse UUID if workspace exists
        if index < len(existing_workspace_uuids):
            session_uuid = existing_workspace_uuids[index]
            print(
                f"♻ Reusing workspace UUID for "
                f"'{session_title}' → {session_uuid}"
            )
        else:
            session_uuid = str(uuid.uuid4())
            print(
                f"➕ Generating new UUID for "
                f"'{session_title}' → {session_uuid}"
            )

        cursor.execute("""
            INSERT INTO rd_course_sessions
            (
                course_id,
                session_title,
                session_uuid,
                session_type,
                tier_level,
                tier_order,
                version
            )
            VALUES (%s, %s, %s, 'session', 'BEGINNER',1,1)
        """, (course_id, session_title, session_uuid))

        print(f"➕ Inserted session '{session_title}'")

    conn.commit()
    cursor.close()
    conn.close()


def sync_session_uuids(course_id: int):
    """
    Ensure every rd_course_sessions row has a session_uuid.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT course_session_id, session_uuid
        FROM rd_course_sessions
        WHERE course_id = %s
    """, (course_id,))

    rows = cursor.fetchall()
    updated = 0

    for course_session_id, session_uuid in rows:
        if session_uuid:
            continue

        new_uuid = str(uuid.uuid4())

        cursor.execute("""
            UPDATE rd_course_sessions
            SET session_uuid = %s
            WHERE course_session_id = %s
        """, (new_uuid, course_session_id))

        updated += 1
        print(f"🔁 Assigned UUID to session_id={course_session_id}")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"✅ Session UUID sync complete (updated={updated})")
