import json
from pathlib import Path
from .db_conn import get_connection
from .utils import load_course_config


CREATED_BY_USER_ID = 67  # change to admin user id


def get_session_pk_from_uuid(cursor, course_id, session_uuid):
    cursor.execute("""
        SELECT course_session_id
        FROM rd_course_sessions
        WHERE course_id = %s
          AND session_uuid = %s
        LIMIT 1
    """, (course_id, session_uuid))
    row = cursor.fetchone()
    if not row:
        raise RuntimeError(f"No session found for UUID {session_uuid}")
    return row[0]


def get_session_detail_id(cursor, session_pk, topic):
    cursor.execute("""
        SELECT course_session_detail_id
        FROM rd_course_session_details
        WHERE course_session_id = %s
          AND topic = %s
          AND type = 'quiz'
        LIMIT 1
    """, (session_pk, topic))
    row = cursor.fetchone()
    if not row:
        raise RuntimeError(f"No session detail found for topic {topic}")
    return row[0]

def delete_existing_quiz(cursor, session_detail_id):

    # Get existing quiz id
    cursor.execute("""
        SELECT quiz_id
        FROM rd_quizzes
        WHERE course_session_detail_id = %s
    """, (session_detail_id,))

    row = cursor.fetchone()

    if not row:
        return

    quiz_id = row[0]

    # Delete mappings
    cursor.execute("""
        DELETE FROM rd_quiz_question_map
        WHERE quiz_id = %s
    """, (quiz_id,))

    # Get question ids
    cursor.execute("""
        SELECT question_id
        FROM rd_quiz_questions
        WHERE course_session_detail_id = %s
    """, (session_detail_id,))

    question_ids = [r[0] for r in cursor.fetchall()]

    if question_ids:

        # Delete options
        cursor.execute("""
            DELETE FROM rd_quiz_options
            WHERE question_id IN ({})
        """.format(",".join(["%s"] * len(question_ids))),
        question_ids)

        # Delete questions
        cursor.execute("""
            DELETE FROM rd_quiz_questions
            WHERE question_id IN ({})
        """.format(",".join(["%s"] * len(question_ids))),
        question_ids)

    # Delete quiz
    cursor.execute("""
        DELETE FROM rd_quizzes
        WHERE quiz_id = %s
    """, (quiz_id,))

def run_phase_e_for_course(course_id: int, workspace_root: Path):

    course_dir = workspace_root / str(course_id)
    chapters_root = course_dir / "chapters"

    if not chapters_root.exists():
        raise FileNotFoundError(f"No chapters folder for {course_id}")

    print(f"\n🚀 Quiz Phase started for course_id={course_id}")

    if not chapters_root.exists():
        return

    print(f"\n🚀 Quiz Phase started for course_id={course_id}")

    conn = get_connection()
    cursor = conn.cursor()

    for session_dir in chapters_root.iterdir():
        if not session_dir.is_dir():
            continue

        session_uuid = session_dir.name
        session_pk = get_session_pk_from_uuid(
            cursor, course_id, session_uuid
        )

        quiz_dir = session_dir / "quizzes"
        if not quiz_dir.exists():
            continue

        print(f"\n📘 Session UUID: {session_uuid}")

        for quiz_file in sorted(quiz_dir.glob("*.json")):

            data = json.load(open(quiz_file, encoding="utf-8"))

            quiz_name = data.get("title", quiz_file.stem)
            difficulty = data.get("difficulty_level", "Medium")
            duration = data.get("duration_minutes", 10)
            questions = data.get("questions", [])

            topic = quiz_file.stem
            session_detail_id = get_session_detail_id(
                cursor, session_pk, topic
            )

            # 🔥 Delete old quiz if exists
            delete_existing_quiz(cursor, session_detail_id)
            # Insert Quiz
            cursor.execute("""
                INSERT INTO rd_quizzes (
                    quiz_name,
                    difficulty_level,
                    quiz_type,
                    status,
                    course_id,
                    course_session_id,
                    total_questions,
                    duration_minutes,
                    created_by_user_id,
                    course_session_detail_id
                )
                VALUES (%s,%s,'multiple_choice','ACTIVE',
                        %s,%s,%s,%s,%s,%s)
            """, (
                quiz_name,
                difficulty,
                course_id,
                session_pk,
                len(questions),
                duration,
                CREATED_BY_USER_ID,
                session_detail_id
            ))

            quiz_id = cursor.lastrowid

            inserted_q = 0

            for q in questions:

                cursor.execute("""
                    INSERT INTO rd_quiz_questions (
                        question_text,
                        question_type,
                        difficulty_level,
                        correct_answer,
                        max_marks,
                        tier_level,
                        course_session_detail_id,
                        course_session_id
                    )
                    VALUES (%s,%s,%s,%s,1,'BEGINNER',%s,%s)
                """, (
                    q["question_text"],
                    "multiple_choice",
                    q.get("difficulty_level", "Medium"),
                    q.get("correct_answer"),
                    session_detail_id,
                    session_pk
                ))

                question_id = cursor.lastrowid

                # Insert options
                for opt in q.get("options", []):
                    cursor.execute("""
                        INSERT INTO rd_quiz_options (
                            question_id,
                            option_text,
                            is_correct
                        )
                        VALUES (%s,%s,%s)
                    """, (
                        question_id,
                        opt["option_text"],
                        1 if opt["is_correct"] else 0
                    ))

                # Map question to quiz
                cursor.execute("""
                    INSERT INTO rd_quiz_question_map (
                        quiz_id, question_id
                    )
                    VALUES (%s,%s)
                """, (quiz_id, question_id))

                inserted_q += 1

            # Update session detail
            cursor.execute("""
                UPDATE rd_course_session_details
                SET quiz_id = %s
                WHERE course_session_detail_id = %s
            """, (quiz_id, session_detail_id))

            conn.commit()

            print(f"  ✔ {quiz_file.name} → quiz_id={quiz_id}, questions={inserted_q}")

    cursor.close()
    conn.close()

    print(f"\n✅ Quiz Phase COMPLETE for course_id={course_id}")


import argparse


if __name__ == "__main__":

    print("🚀 Quiz Phase Script Started")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "json_path",
        help="Course JSON config path (REQUIRED)"
    )

    args = parser.parse_args()

    json_path = Path(args.json_path)

    if not json_path.exists():
        raise FileNotFoundError(
            f"JSON file not found: {json_path}"
        )

    with open(json_path, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    if "course_id" not in ctx:
        raise ValueError("course_id missing in JSON")

    course_id = ctx["course_id"]

    workspace_root = Path(r"C:\robocode\workspace\courses")

    print(f"\n🎯 Running Quiz Phase ONLY for course_id={course_id}")

    run_phase_e_for_course(course_id, workspace_root)
