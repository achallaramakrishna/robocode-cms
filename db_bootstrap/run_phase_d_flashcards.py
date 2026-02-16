import json
import argparse

from pathlib import Path
from .db_conn import get_connection
from .utils import load_course_config



def get_session_detail_pk(cursor, session_pk, topic):
    cursor.execute("""
        SELECT course_session_detail_id
        FROM rd_course_session_details
        WHERE course_session_id = %s
          AND topic = %s
          AND type = 'flashcard'
        LIMIT 1
    """, (session_pk, topic))

    row = cursor.fetchone()

    if not row:
        raise RuntimeError(
            f"No flashcard session detail for topic={topic}"
        )

    return row[0]


def insert_flashcard_set(cursor, set_name, set_description, session_detail_pk):
    cursor.execute("""
        INSERT INTO rd_flashcard_sets
        (
            set_name,
            set_description,
            course_session_detail_id
        )
        VALUES (%s, %s, %s)
    """, (
        set_name,
        set_description,
        session_detail_pk
    ))

    return cursor.lastrowid

def delete_existing_flashcard_set(cursor, session_detail_pk):
    # Delete cards first (FK constraint safe)
    cursor.execute("""
        DELETE f
        FROM rd_flashcards f
        JOIN rd_flashcard_sets s
          ON f.flashcard_set_id = s.flashcard_set_id
        WHERE s.course_session_detail_id = %s
    """, (session_detail_pk,))

    # Delete sets
    cursor.execute("""
        DELETE FROM rd_flashcard_sets
        WHERE course_session_detail_id = %s
    """, (session_detail_pk,))

def insert_flashcard(cursor, card, flashcard_set_id):
    question = card.get("front", {}).get("content", "")
    answer = card.get("back", {}).get("content", "")

    tier_level = card.get("tier_level", "beginner").lower()
    tier_order = card.get("order", 1)

    cursor.execute("""
        INSERT INTO rd_flashcards
        (
            question,
            answer,
            flashcard_set_id,
            tier_level,
            tier_order
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (
        question,
        answer,
        flashcard_set_id,
        tier_level,
        tier_order
    ))



def run_flashcard_phase_for_course(course_id: int, workspace_root: Path):

    course_dir = workspace_root / str(course_id)
    chapters_root = course_dir / "chapters"

    print(f"\n🚀 Flashcard Phase started for course_id={course_id}")

    if not chapters_root.exists():
        print("⚠️ No chapters folder found.")
        return

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
            print(f"⚠️ Session not found in DB: {session_uuid}")
            continue

        session_pk = row[0]

        print(f"\n📘 Session UUID: {session_uuid}")

        flashcard_dir = session_dir / "assets" / "flashcards"

        if not flashcard_dir.exists():
            continue

        for json_file in sorted(flashcard_dir.glob("*.json")):

            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                print(f"⚠️ Invalid JSON format: {json_file}")
                continue

            meta = data.get("meta", {})
            cards = data.get("cards", [])

            if not isinstance(cards, list):
                print(f"⚠️ 'cards' must be list in {json_file}")
                continue

            topic = json_file.stem

            session_detail_pk = get_session_detail_pk(
                cursor,
                session_pk,
                topic
            )

            set_name = meta.get("set_name", topic)
            set_description = meta.get(
                "set_type",
                f"Flashcards for {topic}"
            )

            
            delete_existing_flashcard_set(cursor, session_detail_pk)

            flashcard_set_id = insert_flashcard_set(
                cursor,
                set_name,
                set_description,
                session_detail_pk
            )

            inserted_cards = 0

            for card in cards:
                insert_flashcard(
                    cursor,
                    card,
                    flashcard_set_id
                )
                inserted_cards += 1

            print(
                f"  ✔ {json_file.name} → "
                f"set_id={flashcard_set_id}, "
                f"cards_inserted={inserted_cards}"
            )

        conn.commit()

    cursor.close()
    conn.close()

    print(
        f"\n✅ Flashcard Phase COMPLETE for course_id={course_id}"
    )


if __name__ == "__main__":

    import argparse

    print("🚀 Flashcard Phase Script Started")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "json_path",
        help="Course JSON config path"
    )

    args = parser.parse_args()

    workspace_root = Path(r"C:\robocode\workspace\courses")

    json_path = Path(args.json_path)

    if not json_path.exists():
        raise FileNotFoundError(
            f"JSON file not found: {json_path}"
        )

    with open(json_path, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    if "course_id" not in ctx:
        raise ValueError("course_id missing in JSON.")

    course_id = ctx["course_id"]

    print(f"\n🎯 Running Flashcard Phase ONLY for course_id={course_id}")

    run_flashcard_phase_for_course(course_id, workspace_root)
