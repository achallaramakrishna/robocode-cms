import json
from pathlib import Path


class PageClassifier:

    def __init__(self, ocr_dir: Path, output_dir: Path):
        self.ocr_dir = ocr_dir
        self.output_dir = output_dir

    def classify(self):

        self.output_dir.mkdir(parents=True, exist_ok=True)

        page_files = sorted(self.ocr_dir.glob("page_*.json"))

        for page_file in page_files:

            with open(page_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            structured = data.get("structured_content", {})

            detected_sections = self._detect_sections(structured)

            classified_output = {
                "page_number": data["page_number"],
                "sections_detected": detected_sections,
                "structured_content": structured
            }

            output_file = self.output_dir / page_file.name

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(classified_output, f, indent=2, ensure_ascii=False)

        print("✅ Page classification complete")

    def _detect_sections(self, structured):

        sections = []

        if structured.get("core_definitions"):
            sections.append("THEORY")

        if structured.get("derivations"):
            sections.append("DERIVATION")

        if structured.get("tables"):
            sections.append("TABLE")

        if structured.get("diagrams"):
            sections.append("DIAGRAM")

        if structured.get("examples"):
            sections.append("WORKED_EXAMPLE")

        if structured.get("exercise_sections"):
            sections.append("EXERCISE_SECTION")

        if structured.get("mcq_sections"):
            sections.append("MCQ_SECTION")

        if structured.get("numerical_sections"):
            sections.append("NUMERICAL_SECTION")

        if structured.get("short_answer_sections"):
            sections.append("SHORT_ANSWER_SECTION")

        if structured.get("long_answer_sections"):
            sections.append("LONG_ANSWER_SECTION")

        return sections
