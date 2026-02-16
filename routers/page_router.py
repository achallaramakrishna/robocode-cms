import json
from pathlib import Path


class PageRouter:

    def __init__(self, classified_dir: Path):
        self.classified_dir = classified_dir

    def route(self):

        routing_map = {
            "THEORY": [],
            "DERIVATION": [],
            "TABLE": [],
            "DIAGRAM": [],
            "WORKED_EXAMPLE": [],
            "EXERCISE_SECTION": [],
            "MCQ_SECTION": [],
            "NUMERICAL_SECTION": [],
            "SHORT_ANSWER_SECTION": [],
            "LONG_ANSWER_SECTION": []
        }

        page_files = sorted(self.classified_dir.glob("page_*.json"))

        for page_file in page_files:

            with open(page_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            sections = data.get("sections_detected", [])

            for section in sections:
                routing_map[section].append(page_file)

        return routing_map
