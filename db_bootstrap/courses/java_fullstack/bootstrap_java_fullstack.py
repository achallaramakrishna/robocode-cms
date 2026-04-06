"""
bootstrap_java_fullstack.py
===========================
Full bootstrap for: Java Full Stack - 120 Hours

This script runs the complete pipeline:
  Phase A  - Create course in rd_courses
  Phase B  - Create course sessions in rd_course_sessions + assign UUIDs
  Phase C  - Create workspace folder structure per session
  Phase D  - Generate all AI assets per session:
               * Flashcards       (fc_*)
               * Quizzes          (premium_quiz_set_*)
               * Matching Game    (mg_*)
               * Matching Pair    (mp_*)
               * Lab Manual       (lab_*)
               * Exam Paper       (exam_*)
  Phase E  - Register all assets as rd_course_session_details rows

Usage:
    cd db_bootstrap
    python courses/java_fullstack/bootstrap_java_fullstack.py [--phase A|B|C|D|E|ALL]
"""

import sys
import os
import json
import uuid
import argparse
from pathlib import Path

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── make sure db_bootstrap is on sys.path ──────────────────────────────────────
SCRIPT_DIR    = Path(__file__).resolve().parent          # courses/java_fullstack/
BOOTSTRAP_DIR = SCRIPT_DIR.parent.parent                 # db_bootstrap/
sys.path.insert(0, str(BOOTSTRAP_DIR))                   # adds db_bootstrap/ to path

from db_conn import get_connection

# ─────────────────────────────────────────────────────────────────────────────
COURSE_JSON = SCRIPT_DIR / "course.json"
WORKSPACE_BASE = Path(r"C:\robocode\workspace\courses")

# ─────────────────────────────────────────────────────────────────────────────
def load_course_json():
    with open(COURSE_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def save_course_json(ctx):
    with open(COURSE_JSON, "w", encoding="utf-8") as f:
        json.dump(ctx, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────────────────────
# PHASE A – Ensure course exists
# ─────────────────────────────────────────────────────────────────────────────
def phase_a(ctx):
    print("\n" + "="*60)
    print("PHASE A — Creating course in rd_courses")
    print("="*60)

    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT course_id FROM rd_courses
        WHERE course_name = %s AND course_category_id = %s LIMIT 1
    """, (ctx["course_name"], ctx["course_category_id"]))
    row = cursor.fetchone()

    if row:
        course_id = row[0]
        print(f"⏭  Course already exists → course_id={course_id}")
    else:
        cursor.execute("""
            INSERT INTO rd_courses
            (course_name, course_category_id, category, course_level, tier_level, is_active)
            VALUES (%s, %s, %s, %s, %s, 1)
        """, (
            ctx["course_name"],
            ctx["course_category_id"],
            ctx.get("subject"),
            ctx.get("board"),
            ctx.get("tier_level", "beginner").lower()
        ))
        conn.commit()
        course_id = cursor.lastrowid
        print(f"✅  Course inserted → course_id={course_id}")

    cursor.close()
    conn.close()

    ctx["course_id"] = course_id
    save_course_json(ctx)
    print(f"📌  Phase A complete — course_id={course_id}")
    return course_id


# ─────────────────────────────────────────────────────────────────────────────
# PHASE B – Ensure sessions exist
# ─────────────────────────────────────────────────────────────────────────────
def phase_b(ctx):
    print("\n" + "="*60)
    print("PHASE B — Creating course sessions in rd_course_sessions")
    print("="*60)

    course_id = ctx["course_id"]
    conn      = get_connection()
    cursor    = conn.cursor()

    sessions_with_ids = []

    for idx, sess in enumerate(ctx["sessions"], start=1):
        title = sess["session_title"]

        cursor.execute("""
            SELECT course_session_id, session_uuid
            FROM rd_course_sessions
            WHERE course_id = %s AND session_title = %s LIMIT 1
        """, (course_id, title))
        row = cursor.fetchone()

        if row:
            session_id, session_uuid = row
            print(f"⏭  Session exists [{idx:02d}]: '{title}' → id={session_id}")
        else:
            session_uuid = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO rd_course_sessions
                (course_id, session_title, session_uuid, session_type, tier_level, tier_order, version)
                VALUES (%s, %s, %s, 'session', 'BEGINNER', %s, 1)
            """, (course_id, title, session_uuid, idx))
            conn.commit()
            session_id = cursor.lastrowid
            print(f"✅  Session inserted [{idx:02d}]: '{title}' → id={session_id}, uuid={session_uuid}")

        sessions_with_ids.append({
            **sess,
            "course_session_id": session_id,
            "session_uuid":      session_uuid
        })

    cursor.close()
    conn.close()

    # Persist session IDs back into JSON
    ctx["sessions"] = sessions_with_ids
    save_course_json(ctx)
    print(f"📌  Phase B complete — {len(sessions_with_ids)} sessions ready")
    return sessions_with_ids


# ─────────────────────────────────────────────────────────────────────────────
# PHASE C – Create workspace folder structure
# ─────────────────────────────────────────────────────────────────────────────
def phase_c(ctx):
    print("\n" + "="*60)
    print("PHASE C — Creating workspace folder structure")
    print("="*60)

    course_id = ctx["course_id"]
    base      = WORKSPACE_BASE / str(course_id) / "chapters"

    asset_dirs = [
        "assets/flashcards",
        "assets/quizzes",
        "assets/matchinggame",
        "assets/matchingpair",
        "assets/lab_manuals",
        "assets/exam_papers",
        "assets/notes",
    ]

    for sess in ctx["sessions"]:
        session_uuid = sess["session_uuid"]
        chapter_dir  = base / session_uuid

        for d in asset_dirs:
            full_path = chapter_dir / d
            full_path.mkdir(parents=True, exist_ok=True)

        print(f"📁  [{sess['day']:02d}] Workspace ready: {chapter_dir.name}")

    print(f"📌  Phase C complete — workspace at: {base}")


# ─────────────────────────────────────────────────────────────────────────────
# PHASE D – Generate AI content assets per session
# ─────────────────────────────────────────────────────────────────────────────

def _topics_text(topics):
    return "\n".join(f"  - {t}" for t in topics)


def generate_flashcards(sess, out_dir: Path):
    """Generate flashcard JSON for a session."""
    title  = sess["session_title"]
    topics = sess["topics"]
    uuid_  = sess["session_uuid"]

    cards = []
    card_id = 1

    # Concept cards
    for topic in topics[:8]:
        cards.append({
            "card_id": f"CON_{card_id:03d}",
            "front": {"type": "text", "content": f"What is {topic}?"},
            "back":  {"type": "text", "content": f"[AI-generated explanation for: {topic}. This will be populated by the enrichment engine.]"},
            "tier_level": "beginner",
            "order": card_id
        })
        card_id += 1

    # Definition cards
    for topic in topics[:5]:
        cards.append({
            "card_id": f"DEF_{card_id:03d}",
            "front": {"type": "text", "content": f"Define: {topic}"},
            "back":  {"type": "text", "content": f"[AI-generated definition for: {topic}.]"},
            "tier_level": "beginner",
            "order": card_id
        })
        card_id += 1

    # Best practice cards
    for topic in topics[:3]:
        cards.append({
            "card_id": f"BP_{card_id:03d}",
            "front": {"type": "text", "content": f"What are the best practices for {topic}?"},
            "back":  {"type": "text", "content": f"[AI-generated best practices for: {topic}.]"},
            "tier_level": "beginner",
            "order": card_id
        })
        card_id += 1

    # Code-example cards
    for topic in topics[:4]:
        cards.append({
            "card_id": f"CODE_{card_id:03d}",
            "front": {"type": "text", "content": f"Write a code example for: {topic}"},
            "back":  {"type": "code", "language": "java", "content": f"// Code example for {topic}\n// [To be generated by enrichment engine]"},
            "tier_level": "beginner",
            "order": card_id
        })
        card_id += 1

    data = {
        "meta": {
            "asset_type":    "flashcard",
            "category":      "concept",
            "tier":          "beginner",
            "set_number":    1,
            "chapter_id":    uuid_,
            "chapter_title": title,
            "version":       1
        },
        "cards": cards
    }

    out_file = out_dir / "fc_concept_beginner_01.json"
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      💡 Flashcards → {out_file.name} ({len(cards)} cards)")
    return out_file


def generate_quiz(sess, out_dir: Path):
    """Generate MCQ quiz JSON for a session."""
    title  = sess["session_title"]
    topics = sess["topics"]
    uuid_  = sess["session_uuid"]

    questions = []
    for i, topic in enumerate(topics, start=1):
        questions.append({
            "question_text":   f"Which of the following BEST describes '{topic}'?",
            "difficulty_level": "medium",
            "max_marks":        1,
            "options": [
                {"option_text": f"Correct answer about {topic}",        "is_correct": True},
                {"option_text": f"Incorrect distractor 1 for {topic}",  "is_correct": False},
                {"option_text": f"Incorrect distractor 2 for {topic}",  "is_correct": False},
                {"option_text": f"Incorrect distractor 3 for {topic}",  "is_correct": False}
            ]
        })
        questions.append({
            "question_text":   f"What is the primary purpose of {topic} in Java Full Stack development?",
            "difficulty_level": "easy",
            "max_marks":        1,
            "options": [
                {"option_text": f"Primary purpose of {topic} [correct]", "is_correct": True},
                {"option_text": f"Wrong purpose 1",                       "is_correct": False},
                {"option_text": f"Wrong purpose 2",                       "is_correct": False},
                {"option_text": f"Wrong purpose 3",                       "is_correct": False}
            ]
        })

    data = {
        "type":       "premium_mcq",
        "title":      f"{title} - Premium Concept Mastery Set 1",
        "difficulty": "Mixed",
        "chapter_id": uuid_,
        "questions":  questions[:20]   # cap at 20
    }

    out_file = out_dir / "premium_quiz_set_01.json"
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      📝 Quiz → {out_file.name} ({len(data['questions'])} questions)")
    return out_file


def generate_matching_game(sess, out_dir: Path):
    """Generate matching game JSON."""
    title  = sess["session_title"]
    topics = sess["topics"]
    uuid_  = sess["session_uuid"]

    items = []
    for topic in topics[:8]:
        items.append({
            "itemName":    topic,
            "matchingText": f"[AI-generated description/definition for: {topic}]"
        })

    data = {
        "type":       "matchinggame",
        "category":   "definition",
        "title":      f"{title} - Definitions Set 1",
        "difficulty": "Medium",
        "chapter_id": uuid_,
        "items":      items
    }

    out_file = out_dir / "mg_definition_01.json"
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      🎮 Matching Game → {out_file.name} ({len(items)} items)")
    return out_file


def generate_matching_pair(sess, out_dir: Path):
    """Generate matching pair JSON."""
    title  = sess["session_title"]
    topics = sess["topics"]
    uuid_  = sess["session_uuid"]

    pairs = []
    for topic in topics[:8]:
        pairs.append({
            "left":  topic,
            "right": f"[AI-generated match/description for: {topic}]"
        })

    data = {
        "type":       "matchingpair",
        "category":   "definition",
        "title":      f"{title} - Matching Set 1",
        "difficulty": "Beginner",
        "chapter_id": uuid_,
        "pairs":      pairs
    }

    out_file = out_dir / "mp_definition_01.json"
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      🔗 Matching Pair → {out_file.name} ({len(pairs)} pairs)")
    return out_file


def generate_lab_manual(sess, out_dir: Path):
    """Generate lab manual JSON."""
    title  = sess["session_title"]
    topics = sess["topics"]
    uuid_  = sess["session_uuid"]
    day    = sess["day"]

    exercises = []
    for i, topic in enumerate(topics[:6], start=1):
        exercises.append({
            "exercise_number": i,
            "title":           f"Lab {i}: Hands-on with {topic}",
            "objective":       f"Students will understand and implement {topic}.",
            "prerequisites":   topics[:max(0, i-1)],
            "estimated_time":  "20-30 minutes",
            "difficulty":      "beginner",
            "steps": [
                f"Step 1: Set up the environment for {topic}",
                f"Step 2: Write code implementing {topic}",
                f"Step 3: Test your implementation",
                f"Step 4: Discuss the output with the trainer"
            ],
            "expected_output": f"[Expected output description for {topic}]",
            "challenge":       f"Extension: Modify your {topic} implementation to handle edge cases."
        })

    data = {
        "type":        "lab_manual",
        "title":       f"Day {day} Lab Manual - {title}",
        "session":     f"Day {day}",
        "chapter_id":  uuid_,
        "duration":    "4 hours",
        "tools_required": [
            "JDK 21", "Eclipse IDE", "MySQL Workbench",
            "VS Code", "Node.js", "Git", "Maven"
        ],
        "exercises": exercises
    }

    out_file = out_dir / f"lab_day_{day:02d}.json"
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      🧪 Lab Manual → {out_file.name} ({len(exercises)} exercises)")
    return out_file


def generate_exam_paper(sess, out_dir: Path):
    """Generate exam paper JSON."""
    title  = sess["session_title"]
    topics = sess["topics"]
    uuid_  = sess["session_uuid"]
    day    = sess["day"]

    sections = []

    # Section A: MCQ
    mcq_qs = []
    for i, topic in enumerate(topics[:5], start=1):
        mcq_qs.append({
            "question_number": i,
            "question_text":   f"Which of the following CORRECTLY describes {topic}?",
            "marks":           1,
            "options": [
                f"Correct answer about {topic}",
                f"Wrong answer 1",
                f"Wrong answer 2",
                f"Wrong answer 3"
            ],
            "correct_option": 1
        })
    sections.append({
        "section_name":  "Section A - Multiple Choice Questions",
        "section_type":  "mcq",
        "total_marks":   5,
        "instructions":  "Choose the correct answer. Each question carries 1 mark.",
        "questions":     mcq_qs
    })

    # Section B: Short Answer
    short_qs = []
    for i, topic in enumerate(topics[:4], start=1):
        short_qs.append({
            "question_number": i,
            "question_text":   f"Explain {topic} with a suitable example.",
            "marks":           3,
            "expected_length": "3-5 lines"
        })
    sections.append({
        "section_name":  "Section B - Short Answer Questions",
        "section_type":  "short_answer",
        "total_marks":   12,
        "instructions":  "Answer any 4 questions. Each question carries 3 marks.",
        "questions":     short_qs
    })

    # Section C: Long Answer / Coding
    long_qs = []
    for i, topic in enumerate(topics[:3], start=1):
        long_qs.append({
            "question_number": i,
            "question_text":   f"Write a complete Java program demonstrating {topic}. Explain the code with comments.",
            "marks":           8,
            "expected_length": "20-30 lines of code + explanation"
        })
    sections.append({
        "section_name":  "Section C - Long Answer / Coding Questions",
        "section_type":  "coding",
        "total_marks":   16,
        "instructions":  "Answer any 2 questions. Each question carries 8 marks.",
        "questions":     long_qs
    })

    data = {
        "type":               "exam_paper",
        "title":              f"Day {day} Assessment - {title}",
        "session":            f"Day {day}",
        "chapter_id":         uuid_,
        "duration_minutes":   60,
        "total_marks":        33,
        "exam_type":          "Session Assessment",
        "instructions":       [
            "Read all questions carefully before answering.",
            "Attempt all sections.",
            "Show your working/code clearly.",
            "Mobile phones are not allowed."
        ],
        "sections": sections
    }

    out_file = out_dir / f"exam_day_{day:02d}.json"
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      📋 Exam Paper → {out_file.name} ({sum(len(s['questions']) for s in sections)} questions)")
    return out_file


def generate_notes(sess, out_dir: Path):
    """Generate structured session notes JSON."""
    title       = sess["session_title"]
    topics      = sess["topics"]
    uuid_       = sess["session_uuid"]
    day         = sess["day"]
    description = sess.get("session_description", "")

    topic_notes = []
    for topic in topics:
        topic_notes.append({
            "topic":       topic,
            "summary":     f"[AI-generated summary for {topic}]",
            "key_points": [
                f"Key point 1 about {topic}",
                f"Key point 2 about {topic}",
                f"Key point 3 about {topic}"
            ],
            "code_example": {
                "language":    "java",
                "description": f"Example demonstrating {topic}",
                "code":        f"// {topic} example\n// [To be enriched by AI pipeline]"
            },
            "common_mistakes": [
                f"Common mistake 1 when using {topic}",
                f"Common mistake 2 when using {topic}"
            ]
        })

    data = {
        "type":         "session_notes",
        "title":        f"Day {day} Notes - {title}",
        "session":      f"Day {day}",
        "chapter_id":   uuid_,
        "description":  description,
        "learning_objectives": [
            f"Understand and explain {topics[0]}" if topics else "Complete the session",
            f"Implement {topics[1]} in code" if len(topics) > 1 else "",
            f"Apply best practices for {topics[2]}" if len(topics) > 2 else ""
        ],
        "topics": topic_notes,
        "home_assignment": {
            "title":       f"Day {day} Home Assignment",
            "description": f"Practice the concepts covered today: {', '.join(topics[:3])}",
            "tasks": [
                f"Task 1: Implement a program demonstrating {topics[0]}" if topics else "",
                f"Task 2: Write unit tests for {topics[1]}" if len(topics) > 1 else "",
                f"Task 3: Document your learnings for {topics[2]}" if len(topics) > 2 else ""
            ]
        },
        "references": [
            "https://docs.oracle.com/en/java/",
            "https://spring.io/docs",
            "https://react.dev/docs",
            "https://www.youtube.com/playlist?list=PLWKjhJtqVAbk2qRZtWSzCIN38JC_NdhW5"
        ]
    }

    out_file = out_dir / f"notes_day_{day:02d}.json"
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      📖 Notes → {out_file.name} ({len(topics)} topics)")
    return out_file


def phase_d(ctx):
    print("\n" + "="*60)
    print("PHASE D — Generating AI content assets per session")
    print("="*60)

    course_id = ctx["course_id"]
    base      = WORKSPACE_BASE / str(course_id) / "chapters"

    generated = []  # [(session_id, asset_type, topic, file_path)]

    for sess in ctx["sessions"]:
        session_uuid = sess["session_uuid"]
        session_id   = sess["course_session_id"]
        day          = sess["day"]
        chapter_dir  = base / session_uuid

        print(f"\n  📅 Day {day:02d}: {sess['session_title']}")

        fc_file   = generate_flashcards(  sess, chapter_dir / "assets/flashcards")
        quiz_file = generate_quiz(        sess, chapter_dir / "assets/quizzes")
        mg_file   = generate_matching_game(sess, chapter_dir / "assets/matchinggame")
        mp_file   = generate_matching_pair(sess, chapter_dir / "assets/matchingpair")
        lab_file  = generate_lab_manual(  sess, chapter_dir / "assets/lab_manuals")
        exam_file = generate_exam_paper(  sess, chapter_dir / "assets/exam_papers")
        notes_file = generate_notes(      sess, chapter_dir / "assets/notes")

        generated.append((session_id, "flashcard",    "fc_concept_beginner_01",        str(fc_file)))
        generated.append((session_id, "quiz",         "premium_quiz_set_01",            str(quiz_file)))
        generated.append((session_id, "matchinggame", "mg_definition_01",              str(mg_file)))
        generated.append((session_id, "matchingpair", "mp_definition_01",              str(mp_file)))
        generated.append((session_id, "lab_manual",   f"lab_day_{day:02d}",            str(lab_file)))
        generated.append((session_id, "exam_paper",   f"exam_day_{day:02d}",           str(exam_file)))
        generated.append((session_id, "notes",        f"notes_day_{day:02d}",          str(notes_file)))

    print(f"\n📌  Phase D complete — {len(generated)} assets generated")
    return generated


# ─────────────────────────────────────────────────────────────────────────────
# PHASE E – Register assets as rd_course_session_details
# ─────────────────────────────────────────────────────────────────────────────
def phase_e(ctx):
    print("\n" + "="*60)
    print("PHASE E — Registering assets in rd_course_session_details")
    print("="*60)

    course_id = ctx["course_id"]
    base      = WORKSPACE_BASE / str(course_id) / "chapters"
    conn      = get_connection()
    cursor    = conn.cursor()

    inserted = 0
    skipped  = 0

    asset_map = {
        "flashcard":    ("assets/flashcards",  "fc_concept_beginner_01.json"),
        "quiz":         ("assets/quizzes",     "premium_quiz_set_01.json"),
        "matchinggame": ("assets/matchinggame","mg_definition_01.json"),
        "matchingpair": ("assets/matchingpair","mp_definition_01.json"),
        "lab_manual":   (None, None),   # dynamic per session
        "exam_paper":   (None, None),   # dynamic per session
        "notes":        (None, None),   # dynamic per session
    }

    for sess in ctx["sessions"]:
        session_uuid = sess["session_uuid"]
        session_id   = sess["course_session_id"]
        day          = sess["day"]
        chapter_dir  = base / session_uuid

        assets = [
            ("flashcard",    "fc_concept_beginner_01",     chapter_dir / "assets/flashcards/fc_concept_beginner_01.json"),
            ("quiz",         "premium_quiz_set_01",         chapter_dir / "assets/quizzes/premium_quiz_set_01.json"),
            ("matchinggame", "mg_definition_01",            chapter_dir / "assets/matchinggame/mg_definition_01.json"),
            ("matchingpair", "mp_definition_01",            chapter_dir / "assets/matchingpair/mp_definition_01.json"),
            ("lab_manual",   f"lab_day_{day:02d}",         chapter_dir / f"assets/lab_manuals/lab_day_{day:02d}.json"),
            ("exam_paper",   f"exam_day_{day:02d}",        chapter_dir / f"assets/exam_papers/exam_day_{day:02d}.json"),
            ("notes",        f"notes_day_{day:02d}",       chapter_dir / f"assets/notes/notes_day_{day:02d}.json"),
        ]

        for asset_type, topic, file_path in assets:
            cursor.execute("""
                SELECT course_session_detail_id
                FROM rd_course_session_details
                WHERE course_session_id = %s AND type = %s AND topic = %s
                LIMIT 1
            """, (session_id, asset_type, topic))

            if cursor.fetchone():
                skipped += 1
                continue

            cursor.execute("""
                INSERT INTO rd_course_session_details
                (course_id, course_session_id, topic, type, file, version, tier_level)
                VALUES (%s, %s, %s, %s, %s, 1, 'BEGINNER')
            """, (course_id, session_id, topic, asset_type, str(file_path)))

            inserted += 1

        conn.commit()
        print(f"  ✅ Day {day:02d}: {len(assets)} asset rows registered (session_id={session_id})")

    cursor.close()
    conn.close()

    print(f"\n📌  Phase E complete — inserted={inserted}, skipped={skipped}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Bootstrap Java Full Stack course")
    parser.add_argument("--phase", default="ALL",
                        choices=["A","B","C","D","E","ALL"],
                        help="Which phase to run (default: ALL)")
    args = parser.parse_args()

    ctx   = load_course_json()
    phase = args.phase.upper()

    print(f"\n🚀  Java Full Stack Course Bootstrap")
    print(f"    Course  : {ctx['course_name']}")
    print(f"    Phase   : {phase}")
    print(f"    Sessions: {len(ctx['sessions'])}")

    if phase in ("A", "ALL"):
        phase_a(ctx)
        ctx = load_course_json()

    if phase in ("B", "ALL"):
        if "course_id" not in ctx:
            print("❌  Run Phase A first (course_id missing)"); sys.exit(1)
        phase_b(ctx)
        ctx = load_course_json()

    if phase in ("C", "ALL"):
        if "course_id" not in ctx:
            print("❌  Run Phase A first (course_id missing)"); sys.exit(1)
        phase_c(ctx)

    if phase in ("D", "ALL"):
        if not ctx["sessions"] or "course_session_id" not in ctx["sessions"][0]:
            print("❌  Run Phase B first (course_session_id missing)"); sys.exit(1)
        phase_d(ctx)

    if phase in ("E", "ALL"):
        if not ctx["sessions"] or "course_session_id" not in ctx["sessions"][0]:
            print("❌  Run Phase B first (course_session_id missing)"); sys.exit(1)
        phase_e(ctx)

    print("\n\n🎉  Bootstrap complete!")
    print(f"    Course ID : {ctx.get('course_id', 'N/A')}")
    print(f"    Sessions  : {len(ctx['sessions'])}")
    print(f"    Website   : https://robodynamics.in")


if __name__ == "__main__":
    main()
