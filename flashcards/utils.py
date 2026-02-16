def extract_text(value):
    if isinstance(value, str):
        return value.strip()

    if isinstance(value, dict):
        for k in ("definition", "text", "content"):
            if k in value and isinstance(value[k], str):
                return value[k].strip()
        return " ".join(str(v) for v in value.values())

    return ""
