import json
from pathlib import Path


def load_course_config(course_dir: Path) -> dict:
    config_path = course_dir / "course.json"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Missing course.json at {config_path}"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
