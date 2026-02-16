import json
from pathlib import Path


class ChapterMerger:

    def __init__(self, chapter_dir: Path):
        self.chapter_dir = chapter_dir

    def merge(self):

        final_data = {}

        for subfolder in ["theory", "exercises", "mcq", "numericals"]:
            folder = self.chapter_dir / subfolder

            if folder.exists():
                for file in folder.glob("*.json"):
                    with open(file, "r", encoding="utf-8") as f:
                        final_data[subfolder] = json.load(f)

        output_file = self.chapter_dir / "final_chapter_content.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)

        print("✅ Chapter merged successfully")
