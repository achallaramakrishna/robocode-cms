import json
import sys
from pathlib import Path


def check_json(file_path: Path):
    try:
        with file_path.open("r", encoding="utf-8") as f:
            json.load(f)
        print("✅ VALID JSON")
        print(f"   File: {file_path}")
        return True

    except json.JSONDecodeError as e:
        print("❌ INVALID JSON")
        print(f"   File: {file_path}")
        print(f"   Error: {e.msg}")
        print(f"   Line : {e.lineno}")
        print(f"   Col  : {e.colno}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage:")
        print("  python check_json_validity.py <file.json>")
        sys.exit(1)

    json_file = Path(sys.argv[1])

    if not json_file.exists():
        print(f"❌ File not found: {json_file}")
        sys.exit(1)

    check_json(json_file)
