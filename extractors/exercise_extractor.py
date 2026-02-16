import re


EXERCISE_PATTERN = re.compile(r"(EXERCISE[-\s]*\d+\(?[A-Z]?\)?|Exercise Questions)", re.IGNORECASE)
QUESTION_PATTERN = re.compile(r"^\s*(\d+\.?)\s+(.*)")
HINT_PATTERN = re.compile(r"\[Hint.*?\]", re.IGNORECASE)


def extract_exercises_from_pages(pages_json):

    exercise_sections = []
    current_section = None
    current_question = None

    for page in pages_json:

        page_number = page.get("page_number")
        text_lines = page.get("text", "").split("\n")

        for line in text_lines:

            line = line.strip()
            if not line:
                continue

            # ---------------------------------------
            # 1️⃣ Detect Exercise Heading
            # ---------------------------------------
            if EXERCISE_PATTERN.search(line):

                if current_section:
                    exercise_sections.append(current_section)

                current_section = {
                    "section_title": line.strip(),
                    "page_start": page_number,
                    "questions": []
                }

                current_question = None
                continue

            # ---------------------------------------
            # 2️⃣ Detect New Question
            # ---------------------------------------
            q_match = QUESTION_PATTERN.match(line)

            if q_match and current_section:

                number = q_match.group(1)
                question_text = q_match.group(2)

                current_question = {
                    "number": number.strip(),
                    "question_text": question_text.strip(),
                    "sub_parts": [],
                    "hints": [],
                    "page_number": page_number
                }

                current_section["questions"].append(current_question)
                continue

            # ---------------------------------------
            # 3️⃣ Detect Hint
            # ---------------------------------------
            if HINT_PATTERN.search(line) and current_question:
                current_question["hints"].append(line.strip())
                continue

            # ---------------------------------------
            # 4️⃣ Continuation Line
            # ---------------------------------------
            if current_question:
                current_question["question_text"] += " " + line.strip()

    if current_section:
        exercise_sections.append(current_section)

    return exercise_sections
