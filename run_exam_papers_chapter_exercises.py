from pathlib import Path
from exam_papers.chapter_exercises.generate_chapter_exams import (
    generate_chapter_exams
)

def run_chapter_exam_generation():
    chapters = Path("workspace/chapters")

    for chapter_dir in chapters.iterdir():
        if not chapter_dir.is_dir():
            continue
        try:
            print(f"📝 Generating exams for {chapter_dir.name}")
            generate_chapter_exams(chapter_dir)
        except Exception as e:
            print(f"❌ Failed for {chapter_dir.name}: {e}")

if __name__ == "__main__":
    run_chapter_exam_generation()
