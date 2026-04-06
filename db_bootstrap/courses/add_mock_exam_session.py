"""
add_mock_exam_session.py
========================
Adds a "Mock Exam / Practice Test" session BEFORE the Final Model Question Paper
for all 14 Exam Prep courses.

Structure per course (2 new sessions each):
  Session N:   "Mock Exam — Full Syllabus Practice Test"   ← timed mock paper
  Session N+1: "Final Model Question Paper"                ← already exists (created earlier)

The mock session gets:
  - 1 exam_paper detail row  → mock_exam_{board}_{grade}_{course_id}.json
  - 1 quiz detail row        → mock_quiz_{board}_{grade}_{course_id}.json   (MCQ warm-up)

Note: The Final Model Question Paper session already exists at tier_order=1
      (due to tier_order defaulting to 1). This script inserts the Mock Exam
      at tier_order = final_session_tier_order - 1 (or 0 if 1 is taken, uses a gap).
      Actually we'll just use a sensible tier_order based on max existing.
"""

import mysql.connector
import uuid as uuid_mod

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Jatni@752050",
    database="robodynamics_db",
    charset="utf8mb4",
    autocommit=False
)
cur = conn.cursor()

# All 14 exam prep courses
# (course_id, board, grade, subject, marks, duration_mins)
ALL_COURSES = [
    (154, "ICSE", 10, "Mathematics",  80, 150),
    (155, "ICSE", 10, "Physics",      80, 120),
    (156, "ICSE", 10, "Chemistry",    80, 120),
    (35,  "CBSE",  6, "Mathematics",  60, 150),
    (34,  "CBSE",  5, "Mathematics",  50, 120),
    (33,  "CBSE",  4, "Mathematics",  50, 120),
    (149, "CBSE",  7, "Mathematics",  60, 150),
    (65,  "CBSE",  8, "Mathematics",  80, 180),
    (47,  "ICSE",  5, "Science",      50, 120),
    (66,  "ICSE",  5, "Mathematics",  50, 120),
    (43,  "CBSE",  6, "Mathematics",  60, 150),
    (39,  "CBSE",  6, "Mathematics",  60, 150),
    (56,  "CBSE",  4, "Hindi",        50, 120),
    (72,  "CBSE",  4, "Hindi",        50, 120),
]

results = []

for course_id, board, grade, subject, marks, duration in ALL_COURSES:
    print(f"\n{'='*65}")
    print(f"course_id={course_id}  {board} Gr{grade} {subject}")

    # Find max tier_order of existing sessions
    cur.execute(
        "SELECT MAX(tier_order) FROM rd_course_sessions WHERE course_id = %s",
        (course_id,)
    )
    max_order = cur.fetchone()[0] or 0
    mock_order  = max_order + 1   # Mock Exam goes after all content sessions

    # Check if mock session already exists
    cur.execute("""
        SELECT course_session_id, session_uuid FROM rd_course_sessions
        WHERE course_id = %s AND session_title LIKE %s
    """, (course_id, "%Mock Exam%"))
    existing = cur.fetchone()

    if existing:
        session_id, session_uuid = existing
        print(f"  Mock session already exists: id={session_id}")
    else:
        session_uuid  = str(uuid_mod.uuid4())
        session_title = f"Mock Exam — Full Syllabus Practice Test ({board} Grade {grade} {subject})"
        session_desc  = (
            f"Attempt this full-length mock exam under timed conditions to prepare for your "
            f"{board} Grade {grade} {subject} board examination. "
            f"Duration: {duration//60}h {duration%60 if duration%60 else '00'}min | "
            f"Total Marks: {marks}. "
            f"Review your answers and identify weak areas before the final exam."
        )
        cur.execute("""
            INSERT INTO rd_course_sessions
                (course_id, session_uuid, session_title, session_description,
                 tier_order, tier_level)
            VALUES (%s, %s, %s, %s, %s, 'BEGINNER')
        """, (course_id, session_uuid, session_title, session_desc, mock_order))
        session_id = cur.lastrowid
        print(f"  ✔ Mock session inserted: id={session_id}, uuid={session_uuid}, tier_order={mock_order}")

    # Add exam_paper detail (mock paper JSON)
    mock_file = f"mock_exam_{board.lower()}_grade{grade}_{subject.lower().replace(' ','_')}_{course_id}.json"

    cur.execute("""
        SELECT session_detail_id FROM rd_course_session_details
        WHERE course_session_id = %s AND type = 'exam_paper'
    """, (session_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO rd_course_session_details
                (course_session_id, course_id, topic, type, file, tier_level)
            VALUES (%s, %s, %s, 'exam_paper', %s, 'beginner')
        """, (session_id, course_id,
              f"Mock Exam Paper — {board} Grade {grade} {subject}",
              mock_file))
        print(f"  ✔ exam_paper detail inserted, file={mock_file}")
    else:
        print(f"  exam_paper detail already exists")

    # Add quiz detail (MCQ warm-up)
    quiz_file = f"mock_quiz_{board.lower()}_grade{grade}_{subject.lower().replace(' ','_')}_{course_id}.json"

    cur.execute("""
        SELECT session_detail_id FROM rd_course_session_details
        WHERE course_session_id = %s AND type = 'quiz'
    """, (session_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO rd_course_session_details
                (course_session_id, course_id, topic, type, file, tier_level)
            VALUES (%s, %s, %s, 'quiz', %s, 'beginner')
        """, (session_id, course_id,
              f"Mock Exam MCQ Warm-Up — {board} Grade {grade} {subject}",
              quiz_file))
        print(f"  ✔ quiz detail inserted, file={quiz_file}")
    else:
        print(f"  quiz detail already exists")

    results.append({
        "course_id": course_id, "board": board, "grade": grade, "subject": subject,
        "session_id": session_id, "session_uuid": session_uuid,
        "mock_file": mock_file, "quiz_file": quiz_file,
    })

conn.commit()

print(f"\n\n{'='*65}")
print("COMPLETE — Mock Exam Sessions Summary")
print(f"{'='*65}")
for r in results:
    print(f"\ncourse_id={r['course_id']:4d} | {r['board']} Gr{r['grade']} {r['subject']}")
    print(f"  mock session_id   = {r['session_id']}")
    print(f"  mock session_uuid = {r['session_uuid']}")
    print(f"  mock_exam_file    = {r['mock_file']}")
    print(f"  mock_quiz_file    = {r['quiz_file']}")

conn.close()
