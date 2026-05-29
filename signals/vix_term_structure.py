"""VIX Term Structure — front-month VIX / VIX3M. Contango = calm. Backwardation = stress."""
import yfinance as yf
import numpy as np


def score() -> dict:
    vix = yf.Ticker("^VIX")
    vix3m = yf.Ticker("^VIX3M")

    v1 = vix.history(period="5d")
    v3 = vix3m.history(period="5d")

    if v1.empty or v3.empty:
        return {"score": 50, "value": None, "note": "Term structure data unavailable"}

    front = v1["Close"].iloc[-1]
    three_month = v3["Close"].iloc[-1]
    ratio = front / three_month

    # Map: 0.85 -> 100 (deep contango=calm), 1.15 -> 0 (backwardation=stress)
    score_val = float(np.interp(ratio, [0.85, 1.0, 1.15], [100, 60, 0]))

    condition = "contango (calm)" if ratio < 1.0 else "backwardation (stress)"
    return {
        "score": round(score_val, 1),
        "value": round(ratio, 3),
        "note": f"VIX/VIX3M {ratio:.3f} — {condition}",
    }


if __name__ == "__main__":
    print(score())
