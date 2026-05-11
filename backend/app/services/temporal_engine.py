"""
Bunny - Temporal Check Engine
Proof of Process: rewards natural time-delta and gradual content evolution.
Score 0-100: higher = more natural human evolution.
"""

from datetime import datetime
from app import database as db


def calculate_temporal_score(document_id: str, current_hash: str, current_word_count: int) -> dict:
    commits = db.get_commits_by_document(document_id)
    latest = db.get_latest_commit(document_id)

    if not latest:
        return {
            "temporal_score": 50.0,
            "time_delta_hours": 0,
            "word_delta": current_word_count,
            "total_commits": 0,
            "analysis": "First commit — baseline score. Future commits reward natural evolution.",
        }

    if current_hash == latest["manuscript_hash"]:
        return {
            "temporal_score": latest["temporal_score"],
            "time_delta_hours": 0,
            "word_delta": 0,
            "total_commits": len(commits),
            "analysis": "Identical content to previous commit — no changes detected.",
        }

    time_delta_hours = (datetime.now() - datetime.fromisoformat(latest["created_at"])).total_seconds() / 3600
    word_delta = current_word_count - latest.get("word_count", 0)
    change_ratio = abs(word_delta) / max(latest.get("word_count", 1), 1)

    # Time score (0-40)
    t = (5 if time_delta_hours < 0.05 else 15 if time_delta_hours < 0.5 else
         25 if time_delta_hours < 2 else 35 if time_delta_hours < 24 else
         40 if time_delta_hours < 72 else 35 if time_delta_hours < 168 else 30)

    # Word delta score (0-30)
    w = (10 if change_ratio < 0.01 else 25 if change_ratio < 0.05 else
         30 if change_ratio < 0.15 else 20 if change_ratio < 0.3 else
         15 if change_ratio < 0.5 else 5)

    # Consistency score (0-30)
    c = 15
    if len(commits) >= 2:
        deltas = [
            (datetime.fromisoformat(commits[i]["created_at"]) -
             datetime.fromisoformat(commits[i-1]["created_at"])).total_seconds() / 3600
            for i in range(1, len(commits))
        ]
        if deltas:
            avg = sum(deltas) / len(deltas)
            if avg > 0:
                cv = (sum((d - avg)**2 for d in deltas) / len(deltas))**0.5 / avg
                c = 25 if 0.3 < cv < 2.0 else (15 if cv <= 0.3 else 20)
        c = min(30, c + min(5, len(commits)))

    score = min(100, max(0, t + w + c))
    parts = []
    if t >= 35:
        parts.append(f"Good interval ({time_delta_hours:.1f}h since last commit)")
    elif t <= 15:
        parts.append(f"Very short interval ({time_delta_hours:.1f}h)")
    if w >= 25:
        parts.append(f"Natural evolution ({word_delta:+d} words, {change_ratio*100:.1f}%)")
    elif w <= 10:
        parts.append(f"Suspicious change ({word_delta:+d} words, {change_ratio*100:.1f}%)")
    parts.append(f"Commit #{len(commits)+1} in history")

    return {
        "temporal_score": round(float(score), 2),
        "time_delta_hours": round(time_delta_hours, 2),
        "word_delta": word_delta,
        "total_commits": len(commits),
        "analysis": ". ".join(parts) + ".",
        "score_breakdown": {"time_score": t, "word_score": w, "consistency_score": c},
    }
