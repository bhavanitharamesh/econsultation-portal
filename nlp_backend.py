from transformers import pipeline
import re

positive_words = ["good", "great", "thank", "appreciate", "resolved", "helpful"]
negative_words = ["delay", "bad", "not working", "poor", "stop", "urgent"]

_sentiment = None
_summary = None

def load_models():
    global _sentiment, _summary
    try:
        _sentiment = pipeline("sentiment-analysis")
        _summary = pipeline("summarization")
    except Exception:
        _sentiment = None
        _summary = None

def predict_sentiment(text, use_model=False):
    if use_model and _sentiment:
        try:
            out = _sentiment(text[:512])[0]
            return out['label'].lower(), out['score']
        except Exception:
            pass
    t = text.lower()
    if any(w in t for w in negative_words): return "negative", 0.9
    if any(w in t for w in positive_words): return "positive", 0.9
    return "neutral", 0.6

def summarize_text(text, use_model=False):
    if use_model and _summary:
        try:
            out = _summary(text, max_length=40, min_length=5, do_sample=False)[0]
            return out['summary_text']
        except Exception:
            pass
    sentences = re.split(r'\.|\n', text)
    return sentences[0][:60]
