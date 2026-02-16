import json
from pathlib import Path


class TheoryExtractor:

    def __init__(self, page_files, output_file: Path):
        self.page_files = page_files
        self.output_file = output_file

    def extract(self):

        merged = {
            "core_definitions": [],
            "laws_or_principles": [],
            "derivations": [],
            "fundamental_equations": [],
            "conceptual_insights": [],
            "multi_concept_links": [],
            "jee_traps": [],
            "examples": []
        }

        for page_file in self.page_files:

            with open(page_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            structured = data.get("structured_content", {})

            for key in merged:
                merged[key].extend(structured.get(key, []))

        self._save(merged)
        print("✅ Theory extraction complete")

    def _save(self, data):
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
