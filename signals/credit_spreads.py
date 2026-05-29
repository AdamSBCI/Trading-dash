"""Credit Spreads — HYG vs TLT spread proxy, z-scored vs 1-year history."""
import yfinance as yf
import numpy as np


def score() -> dict:
    hyg = yf.Ticker("HYG")
    tlt = yf.Ticker("TLT")

    h = hyg.history(period="1y")
    t = tlt.history(period="1y")

    if h.empty or t.empty:
        return {"score": 50, "value": None, "note": "Credit spread data unavailable"}

    # Spread proxy: HYG yield approximation vs TLT (inverted — higher HYG relative = tighter spreads)
    spread = h["Close"] / t["Close"]
    current = spread.iloc[-1]
    mean = spread.mean()
    std = spread.std()
    z = (current - mean) / (std + 1e-9)

    # Tight spreads (z = -2) -> 100. Wide spreads (z = +2) -> 0.
    score_val = float(np.interp(-z, [-2, 0, 2], [0, 50, 100]))

    return {
        "score": round(score_val, 1),
        "value": round(float(z), 2),
        "note": f"Credit spread z={z:.2f} — {'tight/calm' if z < -0.5 else 'wide/stress' if z > 0.5 else 'neutral'}",
    }


if __name__ == "__main__":
    print(score())
