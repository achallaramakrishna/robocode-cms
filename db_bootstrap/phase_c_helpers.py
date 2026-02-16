def resolve_session_pk(cursor, session_uuid: str) -> int:
    cursor.execute("""
        SELECT course_session_id
        FROM rd_course_sessions
        WHERE session_uuid = %s
        LIMIT 1
    """, (session_uuid,))

    row = cursor.fetchone()
    if not row:
        raise ValueError(
            f"No rd_course_sessions row for session_uuid={session_uuid}"
        )

    return row[0]
