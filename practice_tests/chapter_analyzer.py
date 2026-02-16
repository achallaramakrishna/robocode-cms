import json
from pathlib import Path
from typing import Dict, Any


WEIGHTS = {
    "definitions": 1,
    "facts": 1,
    "concepts": 2,
    "processes": 2,
    "assertions": 2,
    "mistakes": 2,
    "differences": 2,
    "images": 2,
    "formulas": 3,
    "examples": 3,
    "numericals": 3,
}


def safe_len(v) -> int:
    return len(v) if isinstance(v, list) else 0


def analyze_chapter(cleaned_file: Path) -> Dict[str, Any]:
    if not cleaned_file.exists():
        raise FileNotFoundError(f"Cleaned chapter file not found: {cleaned_file}")

    with open(cleaned_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    counts = {
        "definitions": safe_len(data.get("definitions", [])),
        "facts": safe_len(data.get("facts", [])),
        "concepts": safe_len(data.get("concepts", [])),
        "processes": safe_len(data.get("processes", [])),
        "assertions": safe_len(data.get("assertions", [])),
        "mistakes": safe_len(data.get("mistakes", [])),
        "differences": safe_len(data.get("differences", [])),
        "images": safe_len(data.get("images", [])),
        "formulas": safe_len(data.get("formulas", [])),
        "examples": safe_len(data.get("examples", [])),
        "numericals": safe_len(data.get("numericals", [])),
        "mcqs": safe_len(data.get("mcqs", [])),
        "true_false": safe_len(data.get("true_false", [])),
        "short_questions": safe_len(data.get("short_questions", [])),
        "long_questions": safe_len(data.get("long_questions", [])),
    }

    formula_score = counts["formulas"] * 3 + counts["examples"] * 3 + counts["numericals"] * 3
    theory_score = counts["concepts"] * 2 + counts["processes"] * 2 + counts["long_questions"] * 2
    objective_score = counts["definitions"] * 1 + counts["facts"] * 1 + counts["mcqs"] * 2 + counts["true_false"] * 2 + counts["assertions"] * 2

    if formula_score > theory_score + 4:
        chapter_type = "formula_heavy"
    elif theory_score > formula_score + 4:
        chapter_type = "theory_heavy"
    else:
        chapter_type = "balanced"

    weighted_total = 0
    for k, w in WEIGHTS.items():
        weighted_total += counts.get(k, 0) * w

    return {
        "chapter_type": chapter_type,
        "counts": counts,
        "scores": {
            "formula_score": formula_score,
            "theory_score": theory_score,
            "objective_score": objective_score,
            "weighted_total": weighted_total,
        }
    }


def allocate_section_marks(chapter_type: str, total_marks: int = 40) -> Dict[str, int]:
    """
    Controlled Dynamic (Hybrid):
    - Keep total marks fixed.
    - Adapt section marks within bounded ranges.
    """
    if chapter_type == "formula_heavy":
        A, B, C, D = 8, 10, 14, 8  # objective, short, numerical, long
    elif chapter_type == "theory_heavy":
        A, B, C, D = 6, 12, 8, 14
    else:
        A, B, C, D = 10, 10, 10, 10

    # safety: ensure sum == total_marks (adjust D)
    diff = total_marks - (A + B + C + D)
    D += diff

    return {"A": A, "B": B, "C": C, "D": D}
