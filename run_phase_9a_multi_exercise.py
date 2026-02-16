from pathlib import Path
from exam_papers.chapter_exercises.generate_multi_exercise_exams import (
    generate_exams_for_chapter
)

def run_phase_9a():
    chapters_dir = Path("workspace/chapters")
    if not chapters_dir.exists():
        raise FileNotFoundError("workspace/chapters not found")

    for chapter_dir in chapters_dir.iterdir():
        if not chapter_dir.is_dir():
            continue
        try:
            print(f"📝 Processing chapter {chapter_dir.name}")
            generate_exams_for_chapter(chapter_dir)
        except Exception as e:
            print(f"❌ Failed for {chapter_dir.name}: {e}")

if __name__ == "__main__":
    run_phase_9a()
