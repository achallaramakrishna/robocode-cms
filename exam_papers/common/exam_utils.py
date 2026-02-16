import re

EXERCISE_HEADER_RE = re.compile(
    r"(exercise\s+[0-9a-zA-Z\.]+|miscellaneous\s+exercise|revision\s+exercise)",
    re.IGNORECASE
)

QUESTION_RE = re.compile(r"^\s*(\d+[\.\)]|[a-zA-Z][\)\.])\s+")


def normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def is_question(line: str) -> bool:
    if QUESTION_RE.match(line):
        return True
    if line.endswith("?"):
        return True
    keywords = (
        "find", "solve", "prove", "show", "state",
        "write", "evaluate", "calculate", "explain"
    )
    return any(line.lower().startswith(k) for k in keywords)
