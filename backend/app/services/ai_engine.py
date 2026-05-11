"""
Bunny - AI Detection Engine
Linguistic heuristics + optional DeBERTa model for AI pattern detection.
Score 0-100: higher = more likely AI-generated.
"""

import re
import math
import random
from app.config import settings

_model = None
_tokenizer = None


def _load_model():
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch
        print(f"Loading model: {settings.MODEL_NAME}...")
        _tokenizer = AutoTokenizer.from_pretrained(settings.MODEL_NAME)
        _model = AutoModelForSequenceClassification.from_pretrained(settings.MODEL_NAME, num_labels=2)
        _model.eval()
        return _model, _tokenizer
    except Exception as e:
        print(f"Model load failed ({e}), using heuristics only.")
        return None, None


def _analyze_linguistic_features(text: str) -> dict:
    if not text.strip():
        return {"error": "empty text"}

    words = text.split()
    word_count = len(words)
    sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]

    unique_words = set(w.lower().strip(".,!?;:'\"()[]{}") for w in words)
    vocabulary_richness = len(unique_words) / max(word_count, 1)

    sent_lengths = [len(s.split()) for s in sentences]
    avg_sent = sum(sent_lengths) / max(len(sent_lengths), 1)
    variance = sum((l - avg_sent) ** 2 for l in sent_lengths) / max(len(sent_lengths), 1)
    burstiness = math.sqrt(variance) / max(avg_sent, 1)

    word_freq: dict = {}
    for w in words:
        k = w.lower().strip(".,!?;:'\"()[]{}") 
        if k:
            word_freq[k] = word_freq.get(k, 0) + 1
    hapax_ratio = sum(1 for c in word_freq.values() if c == 1) / max(len(word_freq), 1)

    punct = sum(1 for c in text if c in ".,!?;:'-\"()[]{}—–…")
    punctuation_density = punct / max(word_count, 1)

    contractions = re.findall(r"\b\w+'\w+\b", text)
    contraction_rate = len(contractions) / max(word_count, 1) * 100

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    para_lengths = [len(p.split()) for p in paragraphs]
    para_var = 0.0
    if len(para_lengths) > 1:
        avg_p = sum(para_lengths) / len(para_lengths)
        para_var = sum((l - avg_p) ** 2 for l in para_lengths) / len(para_lengths)

    first_person = sum(1 for w in words if w.lower() in {"i", "me", "my", "mine", "myself", "we", "us", "our"})

    return {
        "vocabulary_richness": round(vocabulary_richness, 4),
        "sentence_length_variance": round(variance, 2),
        "burstiness": round(burstiness, 4),
        "hapax_ratio": round(hapax_ratio, 4),
        "punctuation_density": round(punctuation_density, 4),
        "contraction_rate": round(contraction_rate, 4),
        "paragraph_length_variance": round(para_var, 2),
        "first_person_rate": round(first_person / max(word_count, 1) * 100, 4),
        "avg_sentence_length": round(avg_sent, 2),
        "word_count": word_count,
        "unique_word_count": len(unique_words),
    }


def _heuristic_ai_score(features: dict) -> float:
    score = 50.0
    vr = features.get("vocabulary_richness", 0.5)
    score += 10 if vr < 0.4 else (-10 if vr > 0.65 else 0)
    b = features.get("burstiness", 0.5)
    score += 12 if b < 0.3 else (-12 if b > 0.6 else 0)
    h = features.get("hapax_ratio", 0.4)
    score += 8 if h < 0.3 else (-8 if h > 0.5 else 0)
    sv = features.get("sentence_length_variance", 50)
    score += 8 if sv < 20 else (-8 if sv > 80 else 0)
    cr = features.get("contraction_rate", 1)
    score += 5 if cr < 0.5 else (-5 if cr > 2.0 else 0)
    pv = features.get("paragraph_length_variance", 200)
    score += 5 if pv < 50 else (-5 if pv > 500 else 0)
    return max(0.0, min(100.0, score))


def analyze_text(text: str) -> dict:
    features = _analyze_linguistic_features(text)
    heuristic = _heuristic_ai_score(features)

    if settings.USE_MOCK_MODEL:
        ai_score = max(0, min(100, heuristic + random.gauss(0, 5)))
        model_used = "mock_heuristic"
        confidence = 0.6
    else:
        model, tokenizer = _load_model()
        if model is not None:
            try:
                import torch
                inputs = tokenizer(
                    text, return_tensors="pt", truncation=True, max_length=512, padding=True
                )
                with torch.no_grad():
                    probs = torch.softmax(model(**inputs).logits, dim=-1)
                model_score = probs[0][1].item() * 100
                ai_score = model_score * 0.7 + heuristic * 0.3
                model_used = settings.MODEL_NAME
                confidence = 0.85
            except Exception:
                ai_score = heuristic
                model_used = "heuristic_fallback"
                confidence = 0.5
        else:
            ai_score = heuristic
            model_used = "heuristic_fallback"
            confidence = 0.5

    return {
        "ai_score": round(ai_score, 2),
        "linguistic_features": features,
        "model_used": model_used,
        "confidence": round(confidence, 2),
    }
