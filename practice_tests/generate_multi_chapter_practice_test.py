import json
import random
from pathlib import Path


def generate_multi_chapter_practice_test(
    chapter_ids,
    output_file: Path,
    max_questions: int = 40
):
    all_questions = []

    for chapter_id in chapter_ids:
        quizzes_dir = Path("workspace/chapters") / chapter_id / "quizzes"

        if not quizzes_dir.exists():
            print(f"⚠️ Quizzes not found for chapter {chapter_id}")
            continue

        for quiz_file in quizzes_dir.glob("quiz_*.json"):
            with open(quiz_file, "r", encoding="utf-8") as f:
                quiz_data = json.load(f)
                all_questions.extend(quiz_data.get("questions", []))

    if not all_questions:
        raise RuntimeError("No questions found for multi-chapter test")

    random.shuffle(all_questions)
    selected_questions = all_questions[:max_questions]

    practice_test = {
        "test_name": "Multi-Chapter Practice Test",
        "test_type": "PRACTICE",
        "attempts_allowed": "UNLIMITED",
        "duration_minutes": 45,
        "total_marks": sum(q.get("max_marks", 1) for q in selected_questions),
        "questions": selected_questions
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(practice_test, f, indent=2, ensure_ascii=False)

    print(f"✅ Multi-chapter practice test generated → {output_file}")
