import json
import random
from pathlib import Path

MAX_QUESTIONS_PER_SET = 12


def chunk_list(data, size):
    for i in range(0, len(data), size):
        yield data[i:i + size]


# --------------------------------------------
# Utility
# --------------------------------------------

def build_mcq(question_text, correct, distractors, difficulty):

    options = distractors + [correct]
    random.shuffle(options)

    return {
        "question_text": question_text,
        "difficulty_level": difficulty,
        "max_marks": 1,
        "options": [
            {
                "option_text": opt,
                "is_correct": opt == correct
            }
            for opt in options
        ]
    }


# --------------------------------------------
# 1️⃣ Concept Identification
# --------------------------------------------

def generate_concept_identification(data):

    questions = []
    definitions = data.get("definitions", [])

    for d in definitions:
        term = d.get("term")
        definition = d.get("definition")

        if not term or not definition:
            continue

        distractors = [
            x.get("term")
            for x in definitions
            if x.get("term") != term
        ]

        if len(distractors) < 3:
            continue

        distractors = random.sample(distractors, 3)

        questions.append(
            build_mcq(
                f"This description refers to which concept?\n\n{definition}",
                term,
                distractors,
                "medium"
            )
        )

    return questions


# --------------------------------------------
# 2️⃣ Equation Analysis (Advanced)
# --------------------------------------------

def generate_equation_analysis(data):

    questions = []

    for f in data.get("formulas", []):
        eq = f.get("equation")

        if not eq:
            continue

        eq_lower = eq.lower()

        # Alpha decay
        if "he" in eq_lower and "4" in eq_lower:
            questions.append(
                build_mcq(
                    f"In the equation below, what change occurs?\n\n{eq}",
                    "Mass number decreases by 4 and atomic number decreases by 2.",
                    [
                        "Mass number decreases by 2 only.",
                        "Atomic number decreases by 1 only.",
                        "Both mass and atomic number remain unchanged."
                    ],
                    "hard"
                )
            )

        # Beta decay
        elif "beta" in eq_lower or "β" in eq:
            questions.append(
                build_mcq(
                    f"What is the key change in beta decay?\n\n{eq}",
                    "Atomic number changes but mass number remains constant.",
                    [
                        "Mass number decreases by 1.",
                        "Both mass and atomic number decrease.",
                        "Mass number increases by 2."
                    ],
                    "hard"
                )
            )

        # Gamma emission
        elif "gamma" in eq_lower or "γ" in eq:
            questions.append(
                build_mcq(
                    f"What is the effect of gamma emission?\n\n{eq}",
                    "No change in mass number or atomic number.",
                    [
                        "Atomic number decreases by 1.",
                        "Mass number decreases by 1.",
                        "Both increase."
                    ],
                    "hard"
                )
            )

    return questions


# --------------------------------------------
# 3️⃣ Misconception Detection
# --------------------------------------------

def generate_misconception_mcqs(data):

    questions = []

    for d in data.get("definitions", []):
        term = d.get("term")
        if not term:
            continue

        questions.append(
            build_mcq(
                f"Which of the following statements about '{term}' is INCORRECT?",
                "None of the above statements are correct.",
                [
                    f"It is always a chemical reaction.",
                    f"It does not involve nuclear changes.",
                    f"It violates conservation laws."
                ],
                "advanced"
            )
        )

    return questions


# --------------------------------------------
# 4️⃣ Comparison (Higher Order)
# --------------------------------------------

def generate_comparison_analysis(data):

    questions = []

    for comp in data.get("differences", []):
        topic = comp.get("topic")
        points = comp.get("points", [])

        for p in points:
            a = p.get("point_a")
            b = p.get("point_b")

            if not a or not b:
                continue

            questions.append(
                build_mcq(
                    f"Which correctly differentiates in terms of {topic}?",
                    f"A: {a} | B: {b}",
                    [
                        f"A: {b} | B: {a}",
                        f"A: {a} | B: {a}",
                        f"A: {b} | B: {b}"
                    ],
                    "medium"
                )
            )

    return questions


# --------------------------------------------
# MASTER ENGINE
# --------------------------------------------

def generate_quizzes_for_chapter(chapter_dir: Path):

    chapter_file = chapter_dir / "chapter_content_cleaned.json"

    if not chapter_file.exists():
        print(f"⏭ Skipping {chapter_dir.name} (no cleaned file)")
        return 0

    with open(chapter_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    output_dir = chapter_dir / "assets" / "quizzes"
    output_dir.mkdir(parents=True, exist_ok=True)

    all_questions = []
    all_questions.extend(generate_concept_identification(data))
    all_questions.extend(generate_equation_analysis(data))
    all_questions.extend(generate_misconception_mcqs(data))
    all_questions.extend(generate_comparison_analysis(data))

    if not all_questions:
        print(f"⏭ No quiz content found for {chapter_dir.name}")
        return 0

    random.shuffle(all_questions)

    set_index = 1

    for chunk in chunk_list(all_questions, MAX_QUESTIONS_PER_SET):

        payload = {
            "type": "premium_mcq",
            "title": f"{chapter_dir.name} - Premium Concept Mastery Set {set_index}",
            "difficulty": "Mixed",
            "questions": chunk
        }

        with open(output_dir / f"premium_quiz_set_{set_index:02}.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        print(f"✅ Premium Quiz Set {set_index} generated")

        set_index += 1

    print("🚀 Premium Quiz generation complete\n")

    return set_index - 1
