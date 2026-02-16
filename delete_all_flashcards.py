from pathlib import Path

def delete_all_flashcards():
    base_dir = Path("workspace/courses")

    deleted = 0

    for course_dir in base_dir.iterdir():
        chapters_dir = course_dir / "chapters"

        if not chapters_dir.exists():
            continue

        for chapter_dir in chapters_dir.iterdir():
            flash_dir = chapter_dir / "flashcards"
            if not flash_dir.exists():
                continue

            for file in flash_dir.glob("*.json"):
                file.unlink()
                deleted += 1

    print(f"🗑 Deleted {deleted} flashcard JSON files")

if __name__ == "__main__":
    delete_all_flashcards()
