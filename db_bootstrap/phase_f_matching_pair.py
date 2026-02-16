import json
from pathlib import Path
from .db_conn import get_connection
from .utils import load_course_config


# -------------------------------------------------
# 🔹 Matching Pair
# -------------------------------------------------

def insert_match_question(cursor, session_detail_pk, data):

    cursor.execute("""
        INSERT INTO rd_match_question
        (
            course_session_detail_id,
            instructions,
            difficulty_level,
            total_pairs,
            is_active
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (
        session_detail_pk,
        data.get("instructions"),
        data.get("difficultyLevel"),
        data.get("totalPairs"),
        1 if data.get("active", True) else 0
    ))

    return cursor.lastrowid


def insert_match_pair(cursor, pair, match_question_id):

    cursor.execute("""
        INSERT INTO rd_match_pair
        (
            match_question_id,
            left_text,
            right_text,
            display_order,
            left_type,
            right_type,
            left_image,
            right_image
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        match_question_id,
        pair.get("leftText"),
        pair.get("rightText"),
        pair.get("displayOrder"),
        pair.get("leftType", "TEXT"),
        pair.get("rightType", "TEXT"),
        pair.get("leftImage"),
        pair.get("rightImage")
    ))


def run_matchingpair_phase_for_course(course_dir: Path):

    config = load_course_config(course_dir)
    course_id = config["course_id"]

    chapters_root = course_dir / "chapters"

    print(f"\n🚀 Matching Pair Phase started for course_id={course_id}")

    conn = get_connection()
    cursor = conn.cursor()

    for session_dir in sorted(chapters_root.iterdir()):
        if not session_dir.is_dir():
            continue

        session_uuid = session_dir.name

        cursor.execute("""
            SELECT course_session_id
            FROM rd_course_sessions
            WHERE course_id = %s
              AND session_uuid = %s
            LIMIT 1
        """, (course_id, session_uuid))

        row = cursor.fetchone()
        if not row:
            continue

        session_pk = row[0]

        matching_dir = session_dir / "matchingpair"
        if not matching_dir.exists():
            continue

        print(f"\n📘 Session UUID: {session_uuid}")

        for json_file in sorted(matching_dir.glob("*.json")):

            topic = json_file.stem

            cursor.execute("""
                SELECT course_session_detail_id
                FROM rd_course_session_details
                WHERE course_session_id = %s
                  AND topic = %s
                  AND type = 'matchingpair'
                LIMIT 1
            """, (session_pk, topic))

            detail_row = cursor.fetchone()
            if not detail_row:
                print(f"⚠ No session detail for {topic}")
                continue

            session_detail_pk = detail_row[0]

            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            match_question_id = insert_match_question(
                cursor,
                session_detail_pk,
                data
            )

            for pair in data.get("pairs", []):
                insert_match_pair(
                    cursor,
                    pair,
                    match_question_id
                )

            print(
                f"  ✔ {json_file.name} → "
                f"match_question_id={match_question_id}, "
                f"pairs={len(data.get('pairs', []))}"
            )

        conn.commit()

    cursor.close()
    conn.close()

    print(
        f"\n✅ Matching Pair Phase COMPLETE for course_id={course_id}"
    )
