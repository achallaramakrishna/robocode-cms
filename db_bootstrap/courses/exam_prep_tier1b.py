"""
exam_prep_tier1b.py
===================
Adds Tier 1 Grade 5 & 6 additional courses (Science, alternate Math books)
to Exam Prep — rename + add Final Model Question Paper session + session detail.

Courses:
  47  - ICSE Science Grade 5        → ICSE Science Grade 5 - Exam Prep
  66  - ICSE Math Grade 5           → ICSE Mathematics Grade 5 - Exam Prep
  43  - CBSE Grade 6 RD Sharma      → CBSE Grade 6 Mathematics (RD Sharma) - Exam Prep
  39  - Grade 6 Living Maths        → CBSE Grade 6 Mathematics (Living Maths) - Exam Prep
  56  - CBSE Grade 4 Hindi          → CBSE Grade 4 Hindi - Exam Prep
  72  - Grade 4 Hindi (Devesena)    → CBSE Grade 4 Hindi Language - Exam Prep
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

# (course_id, new_name, board, grade, subject, marks, duration_mins)
TIER1B = [
    (47,  "ICSE Science Grade 5 - Exam Prep",                    "ICSE", 5,  "Science",     50,  120),
    (66,  "ICSE Mathematics Grade 5 - Exam Prep",                "ICSE", 5,  "Mathematics", 50,  120),
    (43,  "CBSE Grade 6 Mathematics (RD Sharma) - Exam Prep",    "CBSE", 6,  "Mathematics", 60,  150),
    (39,  "CBSE Grade 6 Mathematics (Living Maths) - Exam Prep", "CBSE", 6,  "Mathematics", 60,  150),
    (56,  "CBSE Grade 4 Hindi - Exam Prep",                      "CBSE", 4,  "Hindi",       50,  120),
    (72,  "CBSE Grade 4 Hindi Language - Exam Prep",             "CBSE", 4,  "Hindi",       50,  120),
]

results = []

for course_id, new_name, board, grade, subject, marks, duration in TIER1B:
    print(f"\n{'='*70}")
    print(f"course_id={course_id}  |  {new_name}")

    # 1. Get current name
    cur.execute("SELECT course_name FROM rd_courses WHERE course_id = %s", (course_id,))
    row = cur.fetchone()
    if not row:
        print(f"  ERROR: course_id={course_id} not found, skipping.")
        continue
    old_name = row[0]

    # 2. Rename
    if old_name == new_name:
        print(f"  Already renamed.")
    else:
        print(f"  Renaming: {old_name}  →  {new_name}")
        cur.execute("UPDATE rd_courses SET course_name = %s WHERE course_id = %s",
                    (new_name, course_id))
        print(f"  ✔ Renamed.")

    # 3. Check existing Final Model session
    cur.execute("""
        SELECT course_session_id, session_uuid FROM rd_course_sessions
        WHERE course_id = %s AND session_title LIKE %s
    """, (course_id, "%Final Model Question Paper%"))
    existing = cur.fetchone()

    if existing:
        session_id, session_uuid = existing
        print(f"  Session already exists: id={session_id}")
    else:
        cur.execute("SELECT MAX(tier_order) FROM rd_course_sessions WHERE course_id = %s",
                    (course_id,))
        max_order = cur.fetchone()[0] or 0
        next_order = max_order + 1

        session_uuid  = str(uuid_mod.uuid4())
        session_title = f"Final Model Question Paper – {board} Grade {grade} {subject}"
        session_desc  = (
            f"Comprehensive {board} Grade {grade} {subject} model question paper covering all chapters. "
            f"Timed practice ({duration//60}h {duration%60 if duration%60 else '00'}min) "
            f"to simulate actual board exam conditions. Total marks: {marks}."
        )
        cur.execute("""
            INSERT INTO rd_course_sessions
                (course_id, session_uuid, session_title, session_description,
                 tier_order, tier_level)
            VALUES (%s, %s, %s, %s, %s, 'BEGINNER')
        """, (course_id, session_uuid, session_title, session_desc, next_order))
        session_id = cur.lastrowid
        print(f"  ✔ Session inserted: id={session_id}, uuid={session_uuid}")

    # 4. Check existing detail
    exam_file = (f"exam_prep_final_{board.lower()}_grade{grade}"
                 f"_{subject.lower().replace(' ','_')}_{course_id}.json")

    cur.execute("""
        SELECT session_detail_id FROM rd_course_session_details
        WHERE course_session_id = %s AND type = 'exam_paper'
    """, (session_id,))
    existing_d = cur.fetchone()

    if existing_d:
        detail_id = existing_d[0]
        print(f"  Detail already exists: id={detail_id}")
    else:
        cur.execute("""
            INSERT INTO rd_course_session_details
                (course_session_id, course_id, topic, type, file, tier_level)
            VALUES (%s, %s, %s, 'exam_paper', %s, 'beginner')
        """, (session_id, course_id,
              f"Final Model Question Paper – {board} Grade {grade} {subject}",
              exam_file))
        detail_id = cur.lastrowid
        print(f"  ✔ Detail inserted: id={detail_id}, file={exam_file}")

    results.append({
        "course_id": course_id, "new_name": new_name,
        "board": board, "grade": grade, "subject": subject,
        "marks": marks, "duration": duration,
        "session_id": session_id, "session_uuid": session_uuid,
        "detail_id": detail_id, "exam_file": exam_file,
    })

conn.commit()
print(f"\n\n{'='*70}")
print("COMPLETE — Tier 1B Summary")
print(f"{'='*70}")
for r in results:
    print(f"\ncourse_id={r['course_id']:4d} | {r['board']} Gr{r['grade']} {r['subject']} | {r['new_name']}")
    print(f"  session_id   = {r['session_id']}")
    print(f"  session_uuid = {r['session_uuid']}")
    print(f"  detail_id    = {r['detail_id']}")
    print(f"  exam_file    = {r['exam_file']}")

conn.close()
