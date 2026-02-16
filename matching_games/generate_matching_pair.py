import json
from pathlib import Path

MAX_ITEMS_PER_SET = 10


def chunk_list(data, size):
    for i in range(0, len(data), size):
        yield data[i:i + size]


def remove_duplicates(pairs):
    seen = set()
    cleaned = []
    for p in pairs:
        key = (p["left"], p["right"])
        if key not in seen:
            seen.add(key)
            cleaned.append(p)
    return cleaned


# ---------------------------------------------
# Improved Formula Concept Logic
# ---------------------------------------------
def infer_formula_concept(eq: str) -> str:
    e = eq.lower()

    if "mc" in e:
        return "Mass is converted into energy according to Einstein’s mass–energy relation."

    if "→" in eq or "->" in eq:

        if "he" in e and "4" in e:
            return "Alpha decay: mass number decreases by 4 and atomic number decreases by 2."

        if "β+" in eq or "beta+" in e or "positron" in e:
            return "Beta-plus decay: atomic number decreases by 1, mass number unchanged."

        if "β" in eq or "beta" in e:
            return "Beta-minus decay: atomic number increases by 1, mass number unchanged."

        if "γ" in eq or "gamma" in e:
            return "Gamma emission: no change in atomic number or mass number."

    if "binding energy" in e:
        return "Energy required to separate nucleons from nucleus."

    return None  # IMPORTANT: skip unclear equations


def generate_matching_pair_for_chapter(chapter_dir: Path):

    chapter_file = chapter_dir / "chapter_content_cleaned.json"

    if not chapter_file.exists():
        print(f"⏭ Skipping {chapter_dir.name} (no cleaned file)")
        return

    with open(chapter_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    output_dir = chapter_dir / "assets" / "matchingpair"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🔁 Generating Matching Pairs → {chapter_dir.name}")

    # ==========================================================
    # 1️⃣ Definition Matching
    # ==========================================================
    definitions = [
        {
            "left": d.get("term"),
            "right": d.get("definition")
        }
        for d in data.get("definitions", [])
        if d.get("term") and d.get("definition")
    ]

    definitions = remove_duplicates(definitions)

    for index, chunk in enumerate(chunk_list(definitions, MAX_ITEMS_PER_SET), start=1):

        payload = {
            "type": "matchingpair",
            "category": "definition",
            "title": f"{chapter_dir.name} - Definition Matching Set {index}",
            "difficulty": "Beginner",
            "pairs": chunk
        }

        with open(output_dir / f"mp_definition_{index:02}.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        print(f"✅ Definition Matching → Set {index}")

    # ==========================================================
    # 2️⃣ Formula Basic Matching
    # ==========================================================
    formula_basic = [
        {
            "left": f.get("equation"),
            "right": f.get("description")
        }
        for f in data.get("formulas", [])
        if f.get("equation") and f.get("description")
    ]

    formula_basic = remove_duplicates(formula_basic)

    for index, chunk in enumerate(chunk_list(formula_basic, MAX_ITEMS_PER_SET), start=1):

        payload = {
            "type": "matchingpair",
            "category": "formula_basic",
            "title": f"{chapter_dir.name} - Formula Recall Set {index}",
            "difficulty": "Beginner",
            "pairs": chunk
        }

        with open(output_dir / f"mp_formula_basic_{index:02}.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        print(f"✅ Formula Basic Matching → Set {index}")

    # ==========================================================
    # 3️⃣ Formula Conceptual Matching (FIXED)
    # ==========================================================
    formula_concept = []

    for f in data.get("formulas", []):
        eq = f.get("equation")
        if not eq:
            continue

        concept = infer_formula_concept(eq)

        if not concept:
            continue  # skip weak conceptual inference

        formula_concept.append({
            "left": eq,
            "right": concept
        })

    formula_concept = remove_duplicates(formula_concept)

    for index, chunk in enumerate(chunk_list(formula_concept, MAX_ITEMS_PER_SET), start=1):

        payload = {
            "type": "matchingpair",
            "category": "formula_conceptual",
            "title": f"{chapter_dir.name} - Formula Concept Set {index}",
            "difficulty": "Intermediate",
            "pairs": chunk
        }

        with open(output_dir / f"mp_formula_concept_{index:02}.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        print(f"✅ Formula Concept Matching → Set {index}")

    print("🚀 Matching Pair generation complete\n")
