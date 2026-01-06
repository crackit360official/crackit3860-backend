# services/common.py
def normalize_difficulty(value: str) -> str:
    mapping = {
        "easy": "Easy",
        "medium": "Medium",
        "intermediate": "Medium",
        "hard": "Hard"
    }
    return mapping.get(value.strip().lower(), "Medium")
