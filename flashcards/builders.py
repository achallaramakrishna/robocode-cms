from .utils import extract_text


def extract_term_from_definition(text: str):
    text = text.strip()

    # Remove leading articles
    for article in ["The ", "A ", "An ", "the ", "a ", "an "]:
        if text.startswith(article):
            text = text[len(article):]
            break

    # Extract term before " is "
    if " is " in text:
        return text.split(" is ")[0].strip()

    # Extract term before " are "
    if " are " in text:
        return text.split(" are ")[0].strip()

    # Extract term before colon
    if ":" in text:
        return text.split(":")[0].strip()

    # Fallback: take first 5 words max
    words = text.split()
    return " ".join(words[:5]).strip()


def build_definition_cards(data):
    cards = []

    for i, item in enumerate(data.get("definitions", []), start=1):

        text = extract_text(item)
        if not text:
            continue

        term = extract_term_from_definition(text)

        if not term or len(term) < 3:
            continue

        cards.append({
            "card_id": f"DEF_{i:03}",
            "front": {
                "type": "text",
                "content": f"What is {term}?"
            },
            "back": {
                "type": "text",
                "content": text
            },
            "tier_level": "beginner",
            "order": i
        })

    return cards



def build_formula_cards(data):
    cards = []

    for i, item in enumerate(data.get("formulas", []), start=1):

        equation = extract_text(item.get("equation"))
        description = extract_text(item.get("description"))

        if not equation:
            continue

        # Try to extract formula name from description
        title = ""
        if description:
            title = extract_term_from_definition(description)

        if title:
            question_text = f"What is the formula for {title}?"
        else:
            question_text = "State the formula."

        cards.append({
            "card_id": f"FOR_{i:03}",
            "front": {"type": "text", "content": question_text},
            "back": {"type": "text", "content": f"{equation}\n{description or ''}"},
            "tier_level": "beginner",
            "order": i
        })

    return cards


def build_concept_cards(data):
    cards = []

    for i, item in enumerate(data.get("conceptual_facts", []), start=1):

        text = extract_text(item)
        if not text:
            continue

        title = extract_term_from_definition(text)

        if title:
            question_text = f"Explain the concept of {title}."
        else:
            question_text = "Explain this concept."

        cards.append({
            "card_id": f"CON_{i:03}",
            "front": {"type": "text", "content": question_text},
            "back": {"type": "text", "content": text},
            "tier_level": "beginner",
            "order": i
        })

    return cards


def build_fact_cards(data):
    cards = []

    for i, item in enumerate(data.get("conceptual_facts", []), start=1):

        text = extract_text(item)
        if not text:
            continue

        title = extract_term_from_definition(text)

        if title:
            question_text = f"State an important fact about {title}."
        else:
            question_text = "State this fact."

        cards.append({
            "card_id": f"FAC_{i:03}",
            "front": {"type": "text", "content": question_text},
            "back": {"type": "text", "content": text},
            "tier_level": "beginner",
            "order": i
        })

    return cards


def build_assertion_cards(data):
    cards = []
    for i, item in enumerate(data.get("assertions", []), start=1):
        a = item.get("assertion")
        r = item.get("reason")
        if not a or not r:
            continue
        cards.append({
            "card_id": f"AST_{i:03}",
            "front": {"type": "text", "content": f"Assertion: {a}"},
            "back": {"type": "text", "content": f"Reason: {r}"},
            "tier_level": "beginner",
            "order": i
        })
    return cards


def build_example_cards(data):
    cards = []
    for i, item in enumerate(data.get("examples", []), start=1):
        q = extract_text(item.get("question"))
        a = extract_text(item.get("answer"))
        if not q or not a:
            continue
        cards.append({
            "card_id": f"EX_{i:03}",
            "front": {"type": "text", "content": q},
            "back": {"type": "text", "content": a},
            "tier_level": "beginner",
            "order": i
        })
    return cards


def build_comparison_cards(data):
    cards = []

    for i, item in enumerate(data.get("differences", []), start=1):

        topic = extract_text(item.get("topic"))
        points = item.get("points", [])

        for j, p in enumerate(points, start=1):

            a = extract_text(p.get("point_a"))
            b = extract_text(p.get("point_b"))

            if not a or not b:
                continue

            cards.append({
                "card_id": f"CMP_{i:03}_{j:02}",
                "front": {"type": "text", "content": f"Differentiate in {topic}:"},
                "back": {"type": "text", "content": f"A: {a}\nB: {b}"},
                "tier_level": "beginner",
                "order": j
            })

    return cards


def build_mistake_cards(data):
    cards = []
    for i, item in enumerate(data.get("mistakes", []), start=1):
        mistake = extract_text(item.get("mistake"))
        correction = extract_text(item.get("correction"))
        if not mistake or not correction:
            continue
        cards.append({
            "card_id": f"MIS_{i:03}",
            "front": {"type": "text", "content": f"Common mistake: {mistake}"},
            "back": {"type": "text", "content": f"Correct approach: {correction}"},
            "tier_level": "intermediate",
            "order": i
        })
    return cards


def build_process_cards(data):
    cards = []
    for i, item in enumerate(data.get("processes", []), start=1):
        title = extract_text(item.get("title"))
        steps = item.get("steps", [])
        if not title or not steps:
            continue
        cards.append({
            "card_id": f"PRO_{i:03}",
            "front": {"type": "text", "content": f"Explain the process: {title}"},
            "back": {"type": "text", "content": " → ".join(steps)},
            "tier_level": "beginner",
            "order": i
        })
    return cards

# ---------------------------------------------
# Dispatcher
# ---------------------------------------------

def build_flashcards_by_type(data, fc_type):

    mapping = {
        "definition": build_definition_cards,
        "formula": build_formula_cards,
        "concept": build_concept_cards,
        "fact": build_fact_cards,
        "assertion": build_assertion_cards,
        "example": build_example_cards,
        "comparison": build_comparison_cards,
        "mistake": build_mistake_cards,
        "process": build_process_cards,
        "image": build_image_cards,
    }

    builder = mapping.get(fc_type)

    if not builder:
        return []

    return builder(data)


def build_image_cards(data):
    cards = []
    for i, item in enumerate(data.get("images", []), start=1):
        img = item.get("image")
        label = extract_text(item.get("label"))
        if not img or not label:
            continue
        cards.append({
            "card_id": f"IMG_{i:03}",
            "front": {"type": "image", "content": img},
            "back": {"type": "text", "content": label},
            "tier_level": "beginner",
            "order": i
        })
    return cards
