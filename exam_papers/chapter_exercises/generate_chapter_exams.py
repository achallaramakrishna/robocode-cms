import random


def generate_chapter_exams(chapter_dir: Path):

    chapter_file = chapter_dir / "chapter_content.json"

    if not chapter_file.exists():
        print(f"⏭ Skipping {chapter_dir.name} (no chapter_content.json)")
        return

    with open(chapter_file, "r", encoding="utf-8") as f:
        chapter_data = json.load(f)

    exercises = extract_exercises(chapter_data)

    if not exercises:
        print(f"⚠ No exercises detected in {chapter_dir.name}")
        return

    out_base = chapter_dir / "exampaper"
    out_base.mkdir(exist_ok=True)

    for title, questions in exercises.items():

        if not questions:
            continue

        safe_name = (
            title.lower()
            .replace(" ", "_")
            .replace(".", "_")
            .replace(":", "")
        )

        # -----------------------------
        # 1️⃣ Randomized Practice Sets
        # -----------------------------

        for set_no in range(1, 4):   # 3 randomized sets

            shuffled_questions = questions.copy()
            random.shuffle(shuffled_questions)

            out_file = out_base / f"{safe_name}_practice_{set_no}.json"

            if out_file.exists():
                print(f"⏭ Skipping {out_file.name}")
                continue

            exam_json = generate_exam_json(
                exercise_title=f"{title} - Practice Set {set_no}",
                questions=shuffled_questions,
                subject="Mathematics",
                board="CBSE",
                exam_year=2026,
                max_questions=30
            )

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(exam_json, f, indent=2, ensure_ascii=False)

            print(f"✅ Generated → {out_file}")

        # -----------------------------
        # 2️⃣ Difficulty-Based Sets
        # -----------------------------

        easy_q = questions[:10]
        medium_q = questions[10:20]
        hard_q = questions[20:30]

        difficulty_map = {
            "easy": easy_q,
            "medium": medium_q,
            "hard": hard_q
        }

        for level, qset in difficulty_map.items():

            if not qset:
                continue

            out_file = out_base / f"{safe_name}_{level}.json"

            if out_file.exists():
                print(f"⏭ Skipping {out_file.name}")
                continue

            exam_json = generate_exam_json(
                exercise_title=f"{title} - {level.capitalize()} Level",
                questions=qset,
                subject="Mathematics",
                board="CBSE",
                exam_year=2026,
                max_questions=30
            )

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(exam_json, f, indent=2, ensure_ascii=False)

            print(f"✅ Generated → {out_file}")
