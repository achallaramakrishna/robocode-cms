"""
exam_prep_setup.py
==================
Step 1: Rename 8 Tier 1 courses with '- Exam Prep' suffix
Step 2: Add a new session "Final Model Question Paper" at end of each course
Step 3: Add rd_course_session_details row (exam_paper type) for the new session
Step 4: Print UUIDs and session IDs so we can upload the exam paper JSONs

Run on prod: /opt/robodynamics/venv/bin/python3 exam_prep_setup.py

NOTE: course 154 was already renamed in a previous run (partial failure).
      The script skips rename if name already ends with '- Exam Prep'.
      It also skips adding a new session if one already exists with title
      containing 'Final Model Question Paper'.
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

# ── Check actual columns of rd_course_sessions ────────────────────────────
cur.execute("DESCRIBE rd_course_sessions")
session_cols = [r[0] for r in cur.fetchall()]
print("rd_course_sessions columns:", session_cols)

cur.execute("DESCRIBE rd_course_session_details")
detail_cols = [r[0] for r in cur.fetchall()]
print("rd_course_session_details columns:", detail_cols)
print()

# ── Tier 1 courses ─────────────────────────────────────────────────────────
TIER1 = [
    # (course_id, new_course_name,                                board,  grade, marks, duration_mins)
    (154, "Concise Math Grade 10 - Exam Prep (ICSE)",           "ICSE",  10,    80,    180),
    (155, "Concise Physics Grade 10 - Exam Prep (ICSE)",        "ICSE",  10,    80,    180),
    (156, "Concise Chemistry Grade 10 - Exam Prep (ICSE)",      "ICSE",  10,    80,    180),
    (35,  "CBSE Grade 6 Mathematics - Exam Prep",               "CBSE",   6,    60,    150),
    (34,  "CBSE Grade 5 Mathematics - Exam Prep",               "CBSE",   5,    50,    120),
    (33,  "CBSE Grade 4 Mathematics - Exam Prep",               "CBSE",   4,    50,    120),
    (149, "CBSE Grade 7 Mathematics - Exam Prep",               "CBSE",   7,    60,    150),
    (65,  "CBSE Grade 8 Mathematics - Exam Prep",               "CBSE",   8,    80,    180),
]

results = []

for course_id, new_name, board, grade, marks, duration in TIER1:
    print(f"\n{'='*70}")
    print(f"course_id={course_id}  |  {new_name}")
    print(f"{'='*70}")

    # ── 1. Get current course info ─────────────────────────────────────
    cur.execute("SELECT course_name FROM rd_courses WHERE course_id = %s", (course_id,))
    row = cur.fetchone()
    if not row:
        print(f"  ERROR: course_id={course_id} not found, skipping.")
        continue
    old_name = row[0]

    # ── 2. Rename (skip if already renamed) ────────────────────────────
    if old_name == new_name:
        print(f"  Already renamed: {old_name}")
    else:
        print(f"  Renaming: {old_name}  →  {new_name}")
        cur.execute(
            "UPDATE rd_courses SET course_name = %s WHERE course_id = %s",
            (new_name, course_id)
        )
        print(f"  ✔ Renamed.")

    # ── 3. Check if Final Model Question Paper session already exists ──
    cur.execute("""
        SELECT course_session_id, session_title, session_uuid
        FROM rd_course_sessions
        WHERE course_id = %s AND session_title LIKE %s
    """, (course_id, "%Final Model Question Paper%"))
    existing_session = cur.fetchone()

    if existing_session:
        existing_sid, existing_title, existing_uuid = existing_session
        print(f"  Session already exists: id={existing_sid}, uuid={existing_uuid}")
        session_id   = existing_sid
        session_uuid = existing_uuid
    else:
        # ── 4. Find max tier_order ────────────────────────────────────
        cur.execute(
            "SELECT MAX(tier_order) FROM rd_course_sessions WHERE course_id = %s",
            (course_id,)
        )
        max_order = cur.fetchone()[0] or 0
        next_order = max_order + 1
        print(f"  Existing max tier_order={max_order}, inserting at {next_order}")

        # ── 5. Insert new session ─────────────────────────────────────
        session_uuid  = str(uuid_mod.uuid4())
        session_title = f"Final Model Question Paper – {board} Grade {grade}"
        session_desc  = (
            f"Comprehensive {board} Grade {grade} model question paper covering all chapters. "
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

    # ── 6. Check if session detail already exists ─────────────────────
    cur.execute("""
        SELECT session_detail_id FROM rd_course_session_details
        WHERE course_session_id = %s AND type = 'exam_paper'
    """, (session_id,))
    existing_detail = cur.fetchone()

    exam_file = f"exam_prep_final_{board.lower()}_grade{grade}_{course_id}.json"

    if existing_detail:
        print(f"  Session detail already exists: id={existing_detail[0]}")
        detail_id = existing_detail[0]
    else:
        cur.execute("""
            INSERT INTO rd_course_session_details
                (course_session_id, course_id, topic, type, file, tier_level)
            VALUES (%s, %s, %s, 'exam_paper', %s, 'beginner')
        """, (
            session_id,
            course_id,
            f"Final Model Question Paper – {board} Grade {grade}",
            exam_file,
        ))
        detail_id = cur.lastrowid
        print(f"  ✔ Session detail inserted: id={detail_id}, file={exam_file}")

    results.append({
        "course_id":    course_id,
        "new_name":     new_name,
        "board":        board,
        "grade":        grade,
        "marks":        marks,
        "duration":     duration,
        "session_id":   session_id,
        "session_uuid": session_uuid,
        "detail_id":    detail_id,
        "exam_file":    exam_file,
    })

conn.commit()
print(f"\n\n{'='*70}")
print("COMPLETE — Final Summary")
print(f"{'='*70}")
for r in results:
    print(f"\ncourse_id={r['course_id']:4d} | {r['board']} Gr{r['grade']} | {r['new_name']}")
    print(f"  session_id   = {r['session_id']}")
    print(f"  session_uuid = {r['session_uuid']}")
    print(f"  detail_id    = {r['detail_id']}")
    print(f"  exam_file    = {r['exam_file']}")

conn.close()
