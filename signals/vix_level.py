"""VIX Level Signal — percentile rank vs trailing 1 year. Low VIX = high score."""
import yfinance as yf
import numpy as np


def score() -> dict:
    vix = yf.Ticker("^VIX")
    hist = vix.history(period="1y")
    if hist.empty:
        return {"score": 50, "value": None, "note": "VIX data unavailable"}

    current = hist["Close"].iloc[-1]
    percentile = float(np.percentile(hist["Close"], 100) - current) / (
        hist["Close"].max() - hist["Close"].min() + 1e-9
    ) * 100

    # Invert: low VIX = high score
    rank = float(100 - np.searchsorted(np.sort(hist["Close"]), current) / len(hist["Close"]) * 100)

    # Bonuses and penalties
    if current < 15:
        rank = min(100, rank + 5)
    elif current > 30:
        rank = max(0, rank - 10)

    return {
        "score": round(rank, 1),
        "value": round(float(current), 2),
        "note": f"VIX {current:.1f} — {'very calm' if current < 15 else 'elevated' if current > 25 else 'normal'}",
    }


if __name__ == "__main__":
    print(score())
