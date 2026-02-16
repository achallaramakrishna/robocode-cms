from pathlib import Path
from .db_conn import get_connection


def detail_exists(cursor, session_pk, asset_type, topic):
    cursor.execute("""
        SELECT course_session_detail_id
        FROM rd_course_session_details
        WHERE course_session_id = %s
          AND type = %s
          AND topic = %s
        LIMIT 1
    """, (session_pk, asset_type, topic))
    return cursor.fetchone()


def insert_detail(cursor, course_id, session_pk, topic, asset_type, file_path):
    cursor.execute("""
        INSERT INTO rd_course_session_details
        (
            course_id,
            course_session_id,
            topic,
            type,
            file,
            version,
            tier_level
        )
        VALUES (%s, %s, %s, %s, %s, 1, 'BEGINNER')
    """, (course_id, session_pk, topic, asset_type, file_path))

    return cursor.lastrowid
