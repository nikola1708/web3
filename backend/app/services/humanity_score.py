"""
Bunny - Humanity Score Calculator
Combines AI detection (inverted) + temporal score into a final grade.
Score 0-100: higher = more human. Grade A+ to F.
"""


def calculate_humanity_score(ai_score: float, temporal_score: float, ai_confidence: float = 0.5) -> dict:
    human_component = 100.0 - ai_score
    ai_weight = min(0.7, 0.5 + ai_confidence * 0.2)
    temporal_weight = 1.0 - ai_weight
    humanity_score = max(0.0, min(100.0, human_component * ai_weight + temporal_score * temporal_weight))
    grade, label = _grade(humanity_score)
    return {
        "humanity_score": round(humanity_score, 2),
        "human_component": round(human_component, 2),
        "temporal_component": round(temporal_score, 2),
        "grade": grade,
        "label": label,
        "weights": {"ai_weight": round(ai_weight, 2), "temporal_weight": round(temporal_weight, 2)},
    }


def _grade(score: float):
    if score >= 90: return "A+", "Verified Human"
    if score >= 80: return "A",  "Very Likely Human"
    if score >= 70: return "B",  "Likely Human"
    if score >= 60: return "C",  "Possibly Human"
    if score >= 50: return "D",  "Uncertain"
    if score >= 35: return "E",  "Possibly AI-Assisted"
    return "F", "Likely AI-Generated"
