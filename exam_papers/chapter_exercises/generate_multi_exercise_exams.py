import json
import re
from pathlib import Path
from typing import Dict, List, Any

# -----------------------------------------
# REGEX
# -----------------------------------------

EXERCISE_HEADER_RE = re.compile(
    r"^(exercise\s+[\w\.]+|miscellaneous\s+exercise|revision\s+exercise)$",
    re.IGNORECASE
)

QUESTION_RE = re.compile(
    r"^\s*(\d+[\.\)]|[\(\[]?[a-zA-Z]{1,3}[\)\].])\s+"
)


# -----------------------------------------
# Helpers
# -----------------------------------------

def flatten_strings(obj: Any) -> List[str]:
    if isinstance(obj, str):
        return [obj.strip()]

    if isinstance(obj, list):
        out = []
        for x in obj:
            out.extend(flatten_strings(x))
        return out

    if isinstance(obj, dict):
        out = []
        for v in obj.values():
            out.extend(flatten_strings(v))
        return out

    return []


def clean_question_line(line: str) -> str:
    """Remove extra numbering artifacts and normalize spaces."""
    line = re.sub(r"\s+", " ", line).strip()
    return line


def detect_difficulty(question: str) -> str:
    """Simple heuristic difficulty tagging."""
    length = len(question)

    if any(word in question.lower() for word in ["prove", "derive", "justify"]):
        return "Hard"

    if length > 180:
        return "Hard"

    if length > 100:
        return "Medium"

    return "Easy"


# -----------------------------------------
# Extract Exercises
# -----------------------------------------

def extract_exercise_blocks(chapter_data: Dict[str, Any]) -> Dict[str, List[str]]:

    lines = []

    for s in flatten_strings(chapter_data):
        for line in re.split(r"\r?\n+", s):
            line = line.strip()
            if line:
                lines.append(line)

    exercises: Dict[str, List[str]] = {}
    current_exercise = None

    for line in lines:

        if EXERCISE_HEADER_RE.match(line.lower()):
            current_exercise = line.title()
            exercises.setdefault(current_exercise, [])
            continue

        if current_exercise and (
            QUESTION_RE.match(line) or line.endswith("?")
        ):
            cleaned = clean_question_line(line)

            # Avoid duplicates
            if cleaned not in exercises[current_exercise]:
                exercises[current_exercise].append(cleaned)

    return exercises


def normalize_exercise_code(name: str) -> str:
    name = name.lower()

    if "miscellaneous" in name:
        return "misc_exercise"

    name = name.replace("exercise", "").strip()
    name = re.sub(r"[^\w\.]", "_", name)
    name = name.replace(".", "_")

    return name


# -----------------------------------------
# Main Generator
# -----------------------------------------

def generate_exams_for_chapter(
    chapter_dir: Path,
    subject="Mathematics",
    board="CBSE",
    exam_year=2026,
    duration_minutes=30,
    marks_per_question=1,
    max_questions_per_file=30
):

    chapter_file = chapter_dir / "chapter_content.json"

    if not chapter_file.exists():
        print(f"⏭ Skipping {chapter_dir.name} (no chapter_content.json)")
        return

    with open(chapter_file, "r", encoding="utf-8") as f:
        chapter_data = json.load(f)

    exercise_blocks = extract_exercise_blocks(chapter_data)

    if not exercise_blocks:
        print(f"⚠ No exercises found in {chapter_dir.name}")
        return

    output_base = chapter_dir / "exampaper"
    output_base.mkdir(exist_ok=True)

    for exercise_title, questions in exercise_blocks.items():

        if not questions:
            continue

        exercise_code = normalize_exercise_code(exercise_title)

        # 🔥 Split into chunks
        chunks = [
            questions[i:i + max_questions_per_file]
            for i in range(0, len(questions), max_questions_per_file)
        ]

        for chunk_index, chunk_questions in enumerate(chunks, start=1):

            if not chunk_questions:
                continue

            suffix = f"_part_{chunk_index}" if len(chunks) > 1 else ""
            out_file = output_base / f"{exercise_code}{suffix}.json"

            if out_file.exists():
                print(f"⏭ Skipping {out_file.name}")
                continue

            section_questions = []

            for idx, q in enumerate(chunk_questions, start=1):

                difficulty = detect_difficulty(q)

                section_questions.append({
                    "marks": marks_per_question,
                    "displayOrder": idx,
                    "mandatory": True,
                    "question": {
                        "question_text": q,
                        "question_type": "short_answer",
                        "difficulty_level": difficulty
                    },
                    "answerKey": {
                        "modelAnswer": "",
                        "keyPoints": []
                    }
                })

            total_marks = marks_per_question * len(section_questions)

            exam_json = {
                "title": f"{exercise_title}{' (Part ' + str(chunk_index) + ')' if len(chunks) > 1 else ''}",
                "subject": subject,
                "board": board,
                "examYear": exam_year,
                "examType": "CHAPTER_EXERCISE",
                "exerciseCode": exercise_code.upper(),
                "durationMinutes": duration_minutes,
                "totalMarks": total_marks,
                "instructions": "Attempt all questions.",
                "negativeMarking": False,
                "shuffleSections": False,
                "shuffleQuestions": False,
                "sections": [
                    {
                        "sectionName": "A",
                        "title": exercise_title,
                        "description": "Attempt all questions",
                        "attemptType": "ALL",
                        "compulsory": True,
                        "totalMarks": total_marks,
                        "sectionOrder": 1,
                        "questions": section_questions
                    }
                ]
            }

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(exam_json, f, indent=2, ensure_ascii=False)

            print(f"✅ Generated exam → {out_file}")
