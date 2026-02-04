# services/common.py
def normalize_difficulty(diff: str | None) -> str | None:
    if not diff:
        return None
    mapping = {
        "easy": "easy",
        "medium": "medium",
        "hard": "hard",
        "intermediate": "intermediate"
    }
    return mapping.get(diff.lower())
