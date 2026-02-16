from extractors.theory_extractor import TheoryExtractor
from extractors.exercise_extractor import ExerciseExtractor
from extractors.mcq_extractor import MCQExtractor
from extractors.numerical_extractor import NumericalExtractor
from extractors.short_long_extractor import ShortLongExtractor


class SmartRouter:

    def __init__(self, classified_pages, assets_dir):
        self.classified_pages = classified_pages
        self.assets_dir = assets_dir

    def route(self):

        theory_pages = []
        exercise_pages = []
        mcq_pages = []
        numerical_pages = []
        short_long_pages = []
        diagram_pages = []

        for page_file, sections in self.classified_pages.items():

            if "THEORY" in sections:
                theory_pages.append(page_file)

            if "EXERCISE_SECTION" in sections:
                exercise_pages.append(page_file)

            if "MCQ_SECTION" in sections:
                mcq_pages.append(page_file)

            if "NUMERICAL_SECTION" in sections:
                numerical_pages.append(page_file)

            if "SHORT_LONG_SECTION" in sections:
                short_long_pages.append(page_file)

            if "DIAGRAM" in sections:
                diagram_pages.append(page_file)

        # Now call extractors only for relevant pages

        if theory_pages:
            TheoryExtractor(
                theory_pages,
                self.assets_dir / "theory.json"
            ).extract()

        if exercise_pages:
            ExerciseExtractor(
                exercise_pages,
                self.assets_dir / "exercise.json"
            ).extract()

        if mcq_pages:
            MCQExtractor(
                mcq_pages,
                self.assets_dir / "mcq.json"
            ).extract()

        if numerical_pages:
            NumericalExtractor(
                numerical_pages,
                self.assets_dir / "numerical.json"
            ).extract()

        if short_long_pages:
            ShortLongExtractor(
                short_long_pages,
                self.assets_dir / "short_long.json"
            ).extract()

        
