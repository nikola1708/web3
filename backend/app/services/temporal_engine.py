"""
Bunny - Temporal Check Engine
Proof of Process: evaluates natural time-delta and word count evolution.
Score 0-100: higher = more natural human evolution.

Core Logic:
- Compare word count added against the time elapsed between commits.
- Example: 8,000 words added over 96 hours (~83 words/hr) -> Natural (High Score)
- Example: 58,000 words added in 2 hours (29,000 words/hr) -> Impossible (Low Score, Flagged)
"""

from datetime import datetime
from app import database as db

# Baseline writing speeds (words per hour)
HUMAN_MAX_WPH = 2500  # Above this is flagged as impossible for a human


def calculate_temporal_score(document_id: str, current_hash: str, current_word_count: int) -> dict:
    commits = db.get_commits_by_document(document_id)
    latest = db.get_latest_commit(document_id)

    if not latest:
        return {
            "temporal_score": 50.0,
            "time_delta_hours": 0,
            "word_delta": current_word_count,
            "total_commits": 0,
            "analysis": "First commit — baseline score. Subsequent uploads will establish your writing velocity.",
            "velocity": {
                "words_per_hour": 0,
                "pace_label": "first_commit",
                "velocity_score": 50,
                "flag": None,
            },
            "flags": [],
        }

    if current_hash == latest["manuscript_hash"]:
        return {
            "temporal_score": latest["temporal_score"],
            "time_delta_hours": 0,
            "word_delta": 0,
            "total_commits": len(commits),
            "analysis": "Identical content to previous commit — no changes detected.",
            "velocity": {
                "words_per_hour": 0,
                "pace_label": "no_change",
                "velocity_score": latest.get("temporal_score", 50),
                "flag": None,
            },
            "flags": [],
        }

    # Time delta in hours
    last_commit_time = datetime.fromisoformat(latest["created_at"])
    time_delta_hours = (datetime.now() - last_commit_time).total_seconds() / 3600
    
    # Word delta
    word_delta = current_word_count - latest.get("word_count", 0)
    
    # If words were removed, we don't penalize velocity
    if word_delta <= 0:
        return {
            "temporal_score": 90.0,
            "time_delta_hours": round(time_delta_hours, 2),
            "word_delta": word_delta,
            "total_commits": len(commits),
            "analysis": f"Content reduction ({abs(word_delta)} words removed) over {time_delta_hours:.1f} hours. Editing is a natural human process.",
            "velocity": {
                "words_per_hour": 0,
                "pace_label": "editing",
                "velocity_score": 90,
                "flag": None,
            },
            "flags": [],
        }

    # Calculate Words Per Hour (WPH)
    # Prevent division by zero if less than a minute has passed
    effective_time = max(time_delta_hours, 0.016) # min 1 minute (1/60 hr)
    wph = word_delta / effective_time

    flags = []
    
    if wph <= HUMAN_MAX_WPH:
        # Natural human speed
        score = min(100.0, max(80.0, 100.0 - (wph / HUMAN_MAX_WPH) * 20))
        label = "natural"
        flag = None
        analysis_text = f"Natural progression: {word_delta:,} words added over {time_delta_hours:.1f} hours (~{wph:.0f} words/hr)."
    else:
        # Physically impossible for a human
        score = 5.0
        label = "impossible"
        flag = f"Impossible velocity: {word_delta:,} words added in {time_delta_hours:.1f} hours ({wph:.0f} words/hr)."
        flags.append(flag)
        analysis_text = flag

    velocity_data = {
        "words_per_hour": round(wph, 1),
        "pace_label": label,
        "velocity_score": score,
        "flag": flag,
    }

    return {
        "temporal_score": round(float(score), 2),
        "time_delta_hours": round(time_delta_hours, 2),
        "word_delta": word_delta,
        "total_commits": len(commits),
        "analysis": analysis_text,
        "velocity": velocity_data,
        "flags": flags,
    }
