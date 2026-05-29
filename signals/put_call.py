"""Put/Call Sentiment — VIX 20-day rate of change as proxy. Rapidly rising VIX = fear = low score."""
import yfinance as yf
import numpy as np


def score() -> dict:
    vix = yf.Ticker("^VIX")
    hist = vix.history(period="3mo")

    if len(hist) < 25:
        return {"score": 50, "value": None, "note": "Put/call data unavailable"}

    current = hist["Close"].iloc[-1]
    prior_20 = hist["Close"].iloc[-21]
    roc = (current - prior_20) / prior_20 * 100

    # ROC -30% -> 100 (fear receding), ROC +50% -> 0 (fear spiking)
    score_val = float(np.interp(roc, [-30, 0, 50], [100, 60, 0]))

    return {
        "score": round(score_val, 1),
        "value": round(roc, 1),
        "note": f"VIX 20d ROC {roc:+.1f}% — {'fear receding' if roc < -10 else 'fear rising' if roc > 15 else 'neutral'}",
    }


if __name__ == "__main__":
    print(score())
