import json
import argparse
from pathlib import Path

from db_conn import get_connection


ASSET_TYPE_MAP = {
    "flashcards": "flashcard",
    "flashcard": "flashcard",
    "quiz": "quiz",
    "quizzes": "quiz",
    "matchingpair": "matchingpair",
    "matchingpairs": "matchingpair",
    "matchinggame": "matchinggame",
    "exampaper": "exampaper",
    "practice_tests": "exampaper",
    "textbook_practice": "exampaper",
    "mcq": "mcq"
}


# -------------------------------------------------
# DB Helpers
# -------------------------------------------------

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
        raise RuntimeError(
            f"No rd_course_sessions row for session_uuid={session_uuid}"
        )

    return row[0]


def get_next_session_detail_id(cursor, session_pk):
    cursor.execute("""
        SELECT COALESCE(MAX(session_detail_id), 0)
        FROM rd_course_session_details
        WHERE course_session_id = %s
    """, (session_pk,))

    max_id = cursor.fetchone()[0]
    return max_id + 1


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


# -------------------------------------------------
# Phase-C Core
# -------------------------------------------------

def run_phase_c_for_course(course_id: int, workspace_root: Path):

    course_dir = workspace_root / str(course_id)
    chapters_root = course_dir / "chapters"

    if not chapters_root.exists():
        print(f"⚠️ No chapters folder for course {course_id}")
        return

    print(f"\n🚀 Phase-C started for course_id={course_id}")
    print(f"📂 Chapters root: {chapters_root}")

    conn = get_connection()
    cursor = conn.cursor()

    total_inserted = 0
    total_skipped = 0

    for session_dir in sorted(chapters_root.iterdir()):

        if not session_dir.is_dir():
            continue

        session_uuid = session_dir.name

        try:
            session_pk = get_session_pk_from_uuid(
                cursor,
                course_id,
                session_uuid
            )
        except Exception:
            print(f"⚠️ Session not found in DB, skipping: {session_uuid}")
            continue

        print(f"\n📘 Session UUID: {session_uuid} → DB ID: {session_pk}")

        assets_root = session_dir / "assets"

        if not assets_root.exists():
            print("⚠️ No assets folder, skipping")
            continue

        for asset_type_folder in assets_root.iterdir():

            if not asset_type_folder.is_dir():
                continue

            asset_type = ASSET_TYPE_MAP.get(
                asset_type_folder.name.lower()
            )

            if not asset_type:
                print(f"⚠️ Unknown asset type: {asset_type_folder.name}")
                continue

            inserted = 0
            skipped = 0

            for json_file in sorted(asset_type_folder.glob("*.json")):

                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                topic = data.get("topic", json_file.stem)
                file_path = str(json_file)

                if detail_exists(cursor, session_pk, asset_type, topic):
                    skipped += 1
                    continue

                session_detail_id = get_next_session_detail_id(
                    cursor,
                    session_pk
                )

                cursor.execute("""
                    INSERT INTO rd_course_session_details
                    (
                        course_id,
                        course_session_id,
                        session_detail_id,
                        topic,
                        type,
                        file,
                        version,
                        tier_level
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, 1, 'BEGINNER')
                """, (
                    course_id,
                    session_pk,
                    session_detail_id,
                    topic,
                    asset_type,
                    file_path
                ))

                inserted += 1

            conn.commit()

            total_inserted += inserted
            total_skipped += skipped

            print(f"  ✔ {asset_type}: inserted={inserted}, skipped={skipped}")

    cursor.close()
    conn.close()

    print(
        f"\n✅ Phase-C COMPLETE for course_id={course_id} → "
        f"inserted={total_inserted}, skipped={total_skipped}"
    )


# -------------------------------------------------
# Entry Point
# -------------------------------------------------

if __name__ == "__main__":

    print("🚀 Phase-C Script Started")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "json_path",
        nargs="?",
        help="Course JSON config path"
    )

    args = parser.parse_args()

    workspace_root = Path(r"C:\robocode\workspace\courses")

    # ---------------------------------------------
    # Run Specific Course
    # ---------------------------------------------
    if args.json_path:

        json_path = Path(args.json_path)

        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            ctx = json.load(f)

        if "course_id" not in ctx:
            raise ValueError("course_id missing in JSON.")

        course_id = ctx["course_id"]

        print(f"\n🎯 Running Phase-C ONLY for course_id={course_id}")

        run_phase_c_for_course(course_id, workspace_root)

    # ---------------------------------------------
    # Run ALL Courses
    # ---------------------------------------------
    else:

        print("\n🚀 Running Phase-C for ALL courses")

        for course_folder in workspace_root.iterdir():

            if not course_folder.is_dir():
                continue

            try:
                run_phase_c_for_course(
                    int(course_folder.name),
                    workspace_root
                )
            except Exception as e:
                print(f"❌ Error processing {course_folder.name}: {e}")
