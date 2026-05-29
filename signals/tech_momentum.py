"""Tech Sector Momentum — QQQ vs SPY relative strength. Your edge: know when tech is leading."""
import yfinance as yf
import numpy as np


def score() -> dict:
    qqq = yf.Ticker("QQQ")
    spy = yf.Ticker("SPY")

    q = qqq.history(period="3mo")
    s = spy.history(period="3mo")

    if q.empty or s.empty:
        return {"score": 50, "value": None, "note": "Tech momentum data unavailable"}

    # 20-day relative return
    q20 = (q["Close"].iloc[-1] / q["Close"].iloc[-21] - 1) * 100
    s20 = (s["Close"].iloc[-1] / s["Close"].iloc[-21] - 1) * 100
    spread = q20 - s20

    # Also check 60-day trend
    q60 = (q["Close"].iloc[-1] / q["Close"].iloc[-61] - 1) * 100 if len(q) > 61 else 0
    s60 = (s["Close"].iloc[-1] / s["Close"].iloc[-61] - 1) * 100 if len(s) > 61 else 0
    spread60 = q60 - s60

    combined = spread * 0.6 + spread60 * 0.4
    # Map: +5% outperformance -> 100, -5% underperformance -> 0
    score_val = float(np.interp(combined, [-5, 0, 5], [0, 50, 100]))

    return {
        "score": round(score_val, 1),
        "value": round(spread, 2),
        "note": f"QQQ vs SPY 20d: {spread:+.1f}% — {'tech leading' if spread > 1 else 'tech lagging' if spread < -1 else 'in line'}",
    }


if __name__ == "__main__":
    print(score())
