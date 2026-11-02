"""Transparent rule-based indicator demo. Not a predictive AI model."""
from .market import snapshot

def scan():
    results = []
    for item in snapshot():
        # Demo scores are deterministic and illustrative; no historical candles are used.
        score = round(50 + item["change_pct"] * 12, 1)
        action = "WATCH"
        if score >= 65: action = "BULLISH SETUP"
        elif score <= 35: action = "BEARISH SETUP"
        results.append({**item, "score": score, "signal": action,
                       "reason": "Demo score derived from mock daily change; not a trade instruction."})
    return sorted(results, key=lambda x: x["score"], reverse=True)
