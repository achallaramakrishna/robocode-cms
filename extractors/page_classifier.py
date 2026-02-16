import json
from pathlib import Path


class PageClassifier:

    def __init__(self, page_files):
        self.page_files = page_files

    def classify(self):

        classified_pages = {}

        for page_file in self.page_files:

            with open(page_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            sc = data.get("structured_content", {})
            sections = []

            # THEORY
            if (
                sc.get("core_definitions")
                or sc.get("laws_or_principles")
                or sc.get("fundamental_equations")
                or sc.get("conceptual_insights")
                or sc.get("multi_concept_links")
                or sc.get("jee_traps")
                or sc.get("examples")
            ):
                sections.append("THEORY")

            # DERIVATION
            if sc.get("derivations"):
                sections.append("DERIVATION")

            # EXERCISE
            if sc.get("exercise_sections"):
                sections.append("EXERCISE_SECTION")

            # MCQ
            if sc.get("mcq_sections"):
                sections.append("MCQ_SECTION")

            # NUMERICAL
            if sc.get("numerical_sections"):
                sections.append("NUMERICAL_SECTION")

            # SHORT / LONG ANSWER
            if sc.get("short_long_sections"):
                sections.append("SHORT_LONG_SECTION")

            # DIAGRAM
            if sc.get("diagrams"):
                sections.append("DIAGRAM")

            classified_pages[page_file] = sections

        return classified_pages
