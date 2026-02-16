import json
from pathlib import Path
from flashcards.builders import build_flashcards_by_type

# ---------------------------------------------
# CONFIGURATION
# ---------------------------------------------

MAX_CARDS_PER_SET = 15
DEFAULT_TIER = "beginner"

FLASHCARD_TYPES = [
    "definition",
    "formula",
    "concept",
    "fact",
    "assertion",
    "example",
    "comparison",
    "mistake",
    "process",
    "image"
]

# ---------------------------------------------
# CORE GENERATOR
# ---------------------------------------------

def generate_flashcards_for_chapter(chapter_dir: Path):

    content_file = chapter_dir / "chapter_content_cleaned.json"

    if not content_file.exists():
        print(f"⏭️ Skipping {chapter_dir.name} (no cleaned file)")
        return

    with open(content_file, "r", encoding="utf-8") as f:
        chapter_data = json.load(f)

    chapter_title = chapter_data.get("chapter_title", chapter_dir.name)

    out_dir = chapter_dir / "assets" / "flashcards"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📘 Generating flashcards for {chapter_title}")

    for fc_type in FLASHCARD_TYPES:

        cards = build_flashcards_by_type(chapter_data, fc_type)

        if not cards:
            continue

        # Split into chunks
        card_chunks = [
            cards[i:i + MAX_CARDS_PER_SET]
            for i in range(0, len(cards), MAX_CARDS_PER_SET)
        ]

        for index, chunk in enumerate(card_chunks, start=1):

            payload = {
                "meta": {
                    "asset_type": "flashcard",
                    "category": fc_type,
                    "tier": DEFAULT_TIER,
                    "set_number": index,
                    "max_cards": MAX_CARDS_PER_SET,
                    "chapter_id": chapter_dir.name,
                    "chapter_title": chapter_title,
                    "version": 2
                },
                "cards": chunk
            }

            output_file = out_dir / f"fc_{fc_type}_{DEFAULT_TIER}_{index:02}.json"

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)

            print(f"✅ {output_file.name}")

    print("🚀 Flashcard generation complete")
