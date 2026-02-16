from pathlib import Path
from extractors.smart_router import process_chapter  # adjust if needed

def test_one_chapter():
    chapter_dir = Path(
        r"workspace/courses/55/chapters/0dec357d-d0b5-4f3b-b8bc-860161152e48"
    )

    if not chapter_dir.exists():
        raise FileNotFoundError(f"{chapter_dir} not found")

    print(f"🚀 Running extraction for {chapter_dir.name}")

    process_chapter(chapter_dir)

    print("✅ Extraction completed")


if __name__ == "__main__":
    test_one_chapter()
