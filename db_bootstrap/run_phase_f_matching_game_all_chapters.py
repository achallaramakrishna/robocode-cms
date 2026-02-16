import json
import argparse
from pathlib import Path
from .db_conn import get_connection


# -------------------------------------------------
# DELETE EXISTING MATCH QUESTION (IDEMPOTENT)
# -------------------------------------------------

def delete_existing_match_question(cursor, session_detail_pk):

    cursor.execute("""
        SELECT match_question_id
        FROM rd_match_question
        WHERE course_session_detail_id = %s
    """, (session_detail_pk,))

    row = cursor.fetchone()
    if not row:
        return

    match_question_id = row[0]

    cursor.execute("""
        DELETE FROM rd_match_pair
        WHERE match_question_id = %s
    """, (match_question_id,))

    cursor.execute("""
        DELETE FROM rd_match_question
        WHERE match_question_id = %s
    """, (match_question_id,))


# -------------------------------------------------
# INSERT HELPERS
# -------------------------------------------------

def insert_match_question(cursor, session_detail_pk, data):

    instructions = data.get("title") or "Match the following"
    difficulty = data.get("difficulty") or "Beginner"
    total_pairs = len(data.get("pairs", []))

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
        instructions,
        difficulty,
        total_pairs,
        1
    ))

    return cursor.lastrowid


def insert_match_pair(cursor, match_question_id, pair, order):

    left_text = pair.get("left")
    right_text = pair.get("right")

    if not left_text or not right_text:
        print(f"⚠ Skipping invalid pair → {pair}")
        return

    cursor.execute("""
        INSERT INTO rd_match_pair
        (
            match_question_id,
            left_text,
            right_text,
            display_order,
            left_type,
            right_type
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        match_question_id,
        left_text,
        right_text,
        order,
        "TEXT",
        "TEXT"
    ))


# -------------------------------------------------
# MAIN RUNNER (JSON DRIVEN)
# -------------------------------------------------

def run_phase_f_matching_pair_for_course(course_id: int, workspace_root: Path):

    print(f"\n🚀 Matching Pair Phase started for course_id={course_id}")

    conn = get_connection()
    cursor = conn.cursor()

    chapters_dir = workspace_root / str(course_id) / "chapters"

    if not chapters_dir.exists():
        raise FileNotFoundError(f"Chapters folder not found: {chapters_dir}")

    for chapter_dir in sorted(chapters_dir.iterdir()):

        if not chapter_dir.is_dir():
            continue

        session_uuid = chapter_dir.name

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

        matching_dir = chapter_dir / "assets" / "matchingpair"

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

            detail = cursor.fetchone()
            if not detail:
                print(f"⚠ No session detail for {topic}")
                continue

            session_detail_pk = detail[0]

            # 🔥 Delete previous before insert
            delete_existing_match_question(cursor, session_detail_pk)

            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            match_question_id = insert_match_question(
                cursor,
                session_detail_pk,
                data
            )

            for index, pair in enumerate(data.get("pairs", []), start=1):
                insert_match_pair(
                    cursor,
                    match_question_id,
                    pair,
                    index
                )

            print(
                f"  ✔ {json_file.name} → "
                f"pairs_inserted={len(data.get('pairs', []))}"
            )

        conn.commit()

    cursor.close()
    conn.close()

    print("\n✅ Matching Pair Phase COMPLETE")


# -------------------------------------------------
# ENTRY POINT
# -------------------------------------------------

if __name__ == "__main__":

    print("🚀 Matching Pair Phase Script Started")

    parser = argparse.ArgumentParser()
    parser.add_argument("json_path", help="Course JSON path")

    args = parser.parse_args()

    json_path = Path(args.json_path)

    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    if "course_id" not in ctx:
        raise ValueError("course_id missing in JSON")

    course_id = ctx["course_id"]

    workspace_root = Path(r"C:\robocode\workspace\courses")

    print(f"\n🎯 Running Matching Pair ONLY for course_id={course_id}")

    run_phase_f_matching_pair_for_course(course_id, workspace_root)
