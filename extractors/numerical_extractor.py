import json
from pathlib import Path

class NumericalExtractor:

    def __init__(self, page_files, output_file: Path):
        self.page_files = page_files
        self.output_file = output_file

    def extract(self):

        merged = {"numerical_sections": []}

        for page_file in self.page_files:
            with open(page_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            merged["numerical_sections"].extend(
                data["structured_content"].get("numerical_sections", [])
            )

        self._save(merged)

    def _save(self, data):
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
