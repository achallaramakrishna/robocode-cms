import json
import argparse
from pathlib import Path
from db_bootstrap.db_conn import get_connection


# ----------------------------------------------------
# Insert Quiz Question (Required for FK)
# ----------------------------------------------------
def insert_quiz_question(cursor, session_id, question_text):

    cursor.execute("""
        INSERT INTO rd_quiz_questions
        (
            course_session_id,
            question_text,
            question_type,
            difficulty_level,
            is_active
        )
        VALUES (%s,%s,'DESCRIPTIVE','MEDIUM',1)
    """, (session_id, question_text))

    return cursor.lastrowid


# ----------------------------------------------------
# Insert Exam Section Question
# ----------------------------------------------------
def insert_section_question(cursor, section_id, question_id, order):

    cursor.execute("""
        INSERT INTO rd_exam_section_questions
        (
            section_id,
            question_id,
            marks,
            display_order,
            mandatory
        )
        VALUES (%s,%s,1,%s,1)
    """, (section_id, question_id, order))


# ----------------------------------------------------
# Generate Practice From JSON
# ----------------------------------------------------
def generate_practice_from_files(chapter_dir, session_id,
                                 session_detail_id, session_uuid):

    assets_dir = chapter_dir / "assets" / "practice_tests"

    if not assets_dir.exists():
        print(f"⏭ No practice_tests folder for {session_uuid}")
        return

    practice_files = list(assets_dir.glob("practice_*.json"))

    if not practice_files:
        print(f"⏭ No practice JSON files found for {session_uuid}")
        return

    conn = get_connection()
    cursor = conn.cursor()

    for asset_file in practice_files:

        with open(asset_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        section_title = data.get("section", "Practice")
        questions = data.get("questions", [])

        if not questions:
            continue

        print(f"\n📘 Generating Practice Test → {asset_file.name}")

        # Insert Exam Paper
        cursor.execute("""
            INSERT INTO rd_exam_papers
            (
                course_session_detail_id,
                title,
                subject,
                board,
                exam_year,
                duration_minutes,
                total_marks,
                exam_type,
                version,
                shuffle_sections,
                shuffle_questions,
                status
            )
            VALUES (%s,%s,'Physics','CBSE',2026,30,%s,
                    'PRACTICE_TEST',1,0,0,'PUBLISHED')
        """, (
            session_detail_id,
            f"Practice Test - {section_title}",
            len(questions)
        ))

        exam_paper_id = cursor.lastrowid

        # Insert Section
        cursor.execute("""
            INSERT INTO rd_exam_sections
            (
                exam_paper_id,
                section_name,
                title,
                total_marks,
                attempt_type,
                compulsory,
                section_order
            )
            VALUES (%s,'A',%s,%s,'ALL',1,1)
        """, (
            exam_paper_id,
            section_title,
            len(questions)
        ))

        section_id = cursor.lastrowid

        # Insert Questions
        for i, q in enumerate(questions, start=1):

            question_text = q.get("question_text", "").strip()

            if not question_text:
                continue

            # Step 1: Insert into rd_quiz_questions
            question_id = insert_quiz_question(
                cursor,
                session_id,
                question_text
            )

            # Step 2: Link to exam section
            insert_section_question(
                cursor,
                section_id,
                question_id,
                i
            )

        print(f"   ✔ Inserted Practice Test → {section_title}")

    conn.commit()
    cursor.close()
    conn.close()


# ----------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------
def run_from_json(json_path: Path):

    with open(json_path, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    course_id = ctx["course_id"]

    root = Path("workspace/courses") / str(course_id)
    chapters_root = root / "chapters"

    conn = get_connection()
    cursor = conn.cursor()

    print("🚀 Phase G – Textbook Practice Tests Started")
    print(f"📚 Course ID: {course_id}")

    for chapter_dir in sorted(chapters_root.iterdir()):

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

        session_id = row[0]

        # IMPORTANT: type = 'exampaper'
        cursor.execute("""
            SELECT course_session_detail_id
            FROM rd_course_session_details
            WHERE course_session_id = %s
              AND type = 'exampaper'
            LIMIT 1
        """, (session_id,))

        detail_row = cursor.fetchone()
        if not detail_row:
            print(f"⏭ No session_detail (exampaper) for {session_uuid}")
            continue

        session_detail_id = detail_row[0]

        generate_practice_from_files(
            chapter_dir,
            session_id,
            session_detail_id,
            session_uuid
        )

    cursor.close()
    conn.close()

    print("\n✅ Phase G Completed Successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", help="Course JSON file path")
    args = parser.parse_args()

    run_from_json(Path(args.json_file))
