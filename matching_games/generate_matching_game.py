import json
import re
from pathlib import Path


MAX_ITEMS_PER_GAME = 12


def chunk_list(data, size):
    for i in range(0, len(data), size):
        yield data[i:i + size]


def clean_equation(eq: str) -> str:
    eq = re.sub(r"\s+", " ", eq)
    return eq.strip()


def infer_formula_concept(eq: str) -> str:

    eq = clean_equation(eq)
    e = eq.lower()

    # -----------------------------
    # Mass–Energy Equivalence
    # -----------------------------
    if "e" in e and ("Δm" in eq or "dm" in e) and "c" in e and "=" in eq:
        return "Mass–energy equivalence: energy is released when mass is converted during nuclear reactions (E = Δmc²)."

    # -----------------------------
    # Alpha Decay
    # -----------------------------
    if "→" in eq or "->" in eq:
        if "4he" in e or ("he" in e and "4" in e):
            return "Alpha decay: mass number decreases by 4 and atomic number decreases by 2."

        # -------------------------
        # Beta Minus
        # -------------------------
        if "β-" in eq or "beta-" in e:
            return "Beta-minus decay: atomic number increases by 1 while mass number remains unchanged."

        # -------------------------
        # Beta Plus
        # -------------------------
        if "β+" in eq or "beta+" in e or "positron" in e:
            return "Beta-plus decay: atomic number decreases by 1 while mass number remains unchanged."

        # -------------------------
        # Generic Beta (if unclear sign)
        # -------------------------
        if "β" in eq or "beta" in e:
            return "Beta decay: atomic number changes by 1 while mass number remains unchanged."

        # -------------------------
        # Gamma Emission
        # -------------------------
        if "γ" in eq or "gamma" in e:
            return "Gamma emission: no change in atomic number or mass number; nucleus loses excess energy."

    # -----------------------------
    # Fallback
    # -----------------------------
    return "Conceptual understanding required: determine what changes in atomic number, mass number, or energy."


def generate_matching_game_for_chapter(chapter_dir: Path):

    chapter_file = chapter_dir / "chapter_content_cleaned.json"

    if not chapter_file.exists():
        print(f"⏭ Skipping {chapter_dir.name} (no cleaned file)")
        return

    with open(chapter_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    output_dir = chapter_dir / "assets" / "matchinggame"
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------
    # DEFINITIONS
    # ------------------------------------------------
    def_index = 1

    definition_items = [
        {
            "itemName": d["term"],
            "matchingText": d["definition"]
        }
        for d in data.get("definitions", [])
    ]

    for chunk in chunk_list(definition_items, MAX_ITEMS_PER_GAME):

        payload = {
            "type": "matchinggame",
            "category": "definition",
            "title": f"{chapter_dir.name} - Definitions Set {def_index}",
            "difficulty": "Medium",
            "items": chunk
        }

        with open(output_dir / f"mg_definition_{def_index:02}.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        print(f"✅ Matching Game (Definitions) → Set {def_index}")
        def_index += 1

    # ------------------------------------------------
    # FORMULAS (BASIC)
    # ------------------------------------------------
    basic_index = 1

    basic_items = [
        {
            "itemName": clean_equation(f.get("equation", "")),
            "matchingText": f.get("description", "")
        }
        for f in data.get("formulas", [])
        if f.get("equation")
    ]

    for chunk in chunk_list(basic_items, MAX_ITEMS_PER_GAME):

        payload = {
            "type": "matchinggame",
            "category": "formula_basic",
            "title": f"{chapter_dir.name} - Formulas (Basic) Set {basic_index}",
            "difficulty": "Medium",
            "items": chunk
        }

        with open(output_dir / f"mg_formula_basic_{basic_index:02}.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        print(f"✅ Matching Game (Formulas Basic) → Set {basic_index}")
        basic_index += 1

    # ------------------------------------------------
    # FORMULAS (CONCEPTUAL)
    # ------------------------------------------------
    concept_index = 1

    concept_items = []

    for fobj in data.get("formulas", []):
        eq = fobj.get("equation")
        if not eq:
            continue

        eq = clean_equation(eq)

        concept_items.append({
            "itemName": eq,
            "matchingText": infer_formula_concept(eq)
        })

    for chunk in chunk_list(concept_items, MAX_ITEMS_PER_GAME):

        payload = {
            "type": "matchinggame",
            "category": "formula_conceptual",
            "title": f"{chapter_dir.name} - Formulas (Conceptual) Set {concept_index}",
            "difficulty": "Hard",
            "items": chunk
        }

        with open(output_dir / f"mg_formula_concept_{concept_index:02}.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        print(f"✅ Matching Game (Formulas Conceptual) → Set {concept_index}")
        concept_index += 1
