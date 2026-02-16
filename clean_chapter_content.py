import json
import re
from pathlib import Path


# -------------------------------------------------
# Utilities
# -------------------------------------------------

def is_question(text: str) -> bool:
    return text.strip().endswith("?") or text.lower().startswith(
        ("what", "define", "explain", "give", "state")
    )


def normalize_term(term: str) -> str:
    term = term.strip()
    return term[0].upper() + term[1:] if term else term


def deduplicate_objects(items, key_func):
    seen = set()
    cleaned = []
    for item in items:
        key = key_func(item)
        if key not in seen:
            seen.add(key)
            cleaned.append(item)
    return cleaned


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# -------------------------------------------------
# Cleaning Functions
# -------------------------------------------------

def clean_definitions(definitions):
    cleaned = []

    invalid_starts = (
        "if ", "when ", "while ", "in ", "this ",
        "these ", "those ", "during ", "after ",
        "before "
    )

    for d in definitions:

        term = clean_text(d.get("term", ""))
        definition = clean_text(d.get("definition", ""))

        if not term or not definition:
            continue

        if is_question(definition):
            continue

        definition_lower = definition.lower()

        # Must contain "is" or "are"
        if " is " not in definition_lower and " are " not in definition_lower:
            continue

        # Skip narrative openings
        if definition_lower.startswith(invalid_starts):
            continue

        # Term length filter
        if len(term.split()) > 5:
            continue

        # Avoid numeric-heavy term
        if any(char.isdigit() for char in term):
            continue

        # Avoid too short or too long definitions
        if len(definition) < 30 or len(definition) > 220:
            continue

        cleaned.append({
            "term": normalize_term(term),
            "definition": definition
        })

    return deduplicate_objects(
        cleaned,
        key_func=lambda x: x["term"].lower()
    )


def clean_formulas(formulas):
    cleaned = []

    for f in formulas:
        eq = clean_text(f.get("equation", ""))
        desc = clean_text(f.get("description", ""))

        if not eq:
            continue

        # Remove MCQ fragments
        if "(a)" in eq or "(b)" in eq:
            continue

        # Must contain math symbol
        if not any(sym in eq for sym in ["=", "→", "+", "-", "²", "^"]):
            continue

        cleaned.append({
            "equation": eq,
            "description": desc
        })

    return deduplicate_objects(
        cleaned,
        key_func=lambda x: x["equation"]
    )


def clean_conceptual_facts(facts):
    cleaned = []

    for fact in facts:
        fact = clean_text(fact)

        if not fact:
            continue

        if is_question(fact):
            continue

        # Must contain verb
        if not any(v in fact.lower() for v in [" is ", " are ", " has ", " have ", " occurs ", " emits ", " contains "]):
            continue

        # Avoid short fragments
        if len(fact) < 30:
            continue

        # Avoid numeric-heavy statements
        if sum(c.isdigit() for c in fact) > 6:
            continue

        cleaned.append(fact)

    return deduplicate_objects(cleaned, key_func=lambda x: x.lower())


def clean_differences(differences):
    cleaned = []

    for diff in differences:
        topic = clean_text(diff.get("topic", ""))
        points = diff.get("points", [])

        valid_points = []

        for p in points:
            a = clean_text(p.get("point_a", ""))
            b = clean_text(p.get("point_b", ""))

            if not a or not b:
                continue

            # Skip trivial comparisons
            if len(a.split()) < 2 or len(b.split()) < 2:
                continue

            if a.lower() == b.lower():
                continue

            valid_points.append({
                "point_a": a,
                "point_b": b
            })

        if topic and valid_points:
            cleaned.append({
                "topic": topic,
                "points": valid_points
            })

    return cleaned


# -------------------------------------------------
# Main Cleaner
# -------------------------------------------------

def clean_chapter(chapter_dir: Path):

    file_path = chapter_dir / "chapter_content.json"

    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} not found")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["definitions"] = clean_definitions(data.get("definitions", []))
    data["formulas"] = clean_formulas(data.get("formulas", []))
    data["conceptual_facts"] = clean_conceptual_facts(data.get("conceptual_facts", []))
    data["differences"] = clean_differences(data.get("differences", []))

    output_file = chapter_dir / "chapter_content_cleaned.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Cleaned chapter saved to: {output_file}")


# -------------------------------------------------
# CLI Runner
# -------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("chapter_path")

    args = parser.parse_args()

    clean_chapter(Path(args.chapter_path))
