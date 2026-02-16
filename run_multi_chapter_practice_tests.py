from pathlib import Path
from practice_tests.generate_multi_chapter_practice_test import (
    generate_multi_chapter_practice_test
)

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

WORKSPACE_BASE = Path("workspace/courses")
OUTPUT_BASE = Path("practice_tests/multi_chapter")

MAX_QUESTIONS = 40
VERSIONS_PER_GROUP = 1   # increase if you want multiple sets


# --------------------------------------------------
# Utility: Collect All Chapter UUIDs Across Courses
# --------------------------------------------------

def collect_all_chapter_ids():
    chapter_ids = []

    if not WORKSPACE_BASE.exists():
        raise FileNotFoundError("workspace/courses not found")

    for course_dir in WORKSPACE_BASE.iterdir():
        if not course_dir.is_dir():
            continue

        chapters_dir = course_dir / "chapters"
        if not chapters_dir.exists():
            continue

        for chapter_dir in chapters_dir.iterdir():
            if chapter_dir.is_dir():
                chapter_ids.append(chapter_dir.name)

    return chapter_ids


# --------------------------------------------------
# DEFINE PRACTICE GROUPS
# --------------------------------------------------

PRACTICE_GROUPS = {
    "geometry": [
        "036af6d6-2fb1-4a8b-ac6c-cff16325eef6",
        "0a76dc9b-cca0-401d-92b3-98b2f5643997"
    ],
    "algebra": [
        "6e76b7be-086d-47fd-a1c7-aa2d14468225",
        "37088fd9-0ac3-4b81-88cc-53a6b4b11489"
    ],
    "full_syllabus": collect_all_chapter_ids()
}


# --------------------------------------------------
# Main Runner
# --------------------------------------------------

def run_multi_chapter_practice_tests():

    print("🚀 Starting Multi-Chapter Practice Test Generation")

    for group_name, chapter_ids in PRACTICE_GROUPS.items():

        if not chapter_ids:
            print(f"⏭ Skipping {group_name} (no chapters found)")
            continue

        group_output_dir = OUTPUT_BASE / group_name
        group_output_dir.mkdir(parents=True, exist_ok=True)

        for version in range(1, VERSIONS_PER_GROUP + 1):

            output_file = group_output_dir / f"practice_test_{version}.json"

            # Resume-safe
            if output_file.exists():
                print(f"⏭ Skipping {group_name} v{version} (already exists)")
                continue

            try:
                print(f"🧠 Building test → {group_name} (Version {version})")

                generate_multi_chapter_practice_test(
                    chapter_ids=chapter_ids,
                    output_file=output_file,
                    max_questions=MAX_QUESTIONS
                )

                print(f"✅ Created → {output_file}")

            except Exception as e:
                print(f"❌ Failed for {group_name} v{version}: {e}")

    print("\n🎯 Multi-Chapter Practice Test Generation Complete")


# --------------------------------------------------

if __name__ == "__main__":
    run_multi_chapter_practice_tests()
