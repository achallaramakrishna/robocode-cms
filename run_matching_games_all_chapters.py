from pathlib import Path
from matching_games.generate_matching_pair import generate_matching_pair_for_chapter
from matching_games.generate_matching_game import generate_matching_game_for_chapter


def run_all_matching_assets():

    base_dir = Path("workspace/courses")

    if not base_dir.exists():
        raise FileNotFoundError("❌ workspace/courses not found")

    print("🚀 Starting Matching Assets Generation")

    for course_dir in base_dir.iterdir():

        if not course_dir.is_dir():
            continue

        chapters_dir = course_dir / "chapters"

        if not chapters_dir.exists():
            continue

        print(f"\n📚 Processing Course: {course_dir.name}")

        for chapter_dir in chapters_dir.iterdir():

            if not chapter_dir.is_dir():
                continue

            print(f"🔁 Processing Chapter: {chapter_dir.name}")

            try:
                generate_matching_pair_for_chapter(chapter_dir)
                generate_matching_game_for_chapter(chapter_dir)

            except Exception as e:
                print(f"❌ Failed for chapter {chapter_dir.name}: {e}")

    print("\n✅ Matching Assets Generation Complete")


if __name__ == "__main__":
    run_all_matching_assets()
