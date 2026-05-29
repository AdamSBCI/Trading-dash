"""
5 quantitative scoring factors. Each scored 0-100 via percentile rank across universe.
"""
import numpy as np
import pandas as pd


def momentum_crossover(hist: pd.DataFrame) -> float:
    """10-day EMA crossed above 50-day EMA in last 5 days + 3-month return magnitude."""
    if len(hist) < 55:
        return 50.0
    close = hist["Close"]
    ema10 = close.ewm(span=10).mean()
    ema50 = close.ewm(span=50).mean()

    # Did crossover happen in last 5 days?
    crossed = any(
        ema10.iloc[-(i+1)] > ema50.iloc[-(i+1)] and ema10.iloc[-(i+2)] <= ema50.iloc[-(i+2)]
        for i in range(min(5, len(ema10)-1))
    )

    # Gap size between EMAs (%)
    gap = (ema10.iloc[-1] - ema50.iloc[-1]) / ema50.iloc[-1] * 100

    # 3-month return
    ret3m = (close.iloc[-1] / close.iloc[-63] - 1) * 100 if len(close) > 63 else 0

    raw = (10 if crossed else 0) + max(0, gap) * 2 + max(0, ret3m) * 0.5
    return float(np.clip(raw, 0, 100))


def volume_surge(hist: pd.DataFrame) -> float:
    """5-day avg volume / 20-day avg volume. Expanding = institutions accumulating."""
    if len(hist) < 21:
        return 50.0
    vol = hist["Volume"]
    ratio = vol.iloc[-5:].mean() / (vol.iloc[-20:].mean() + 1)
    # Map: 0.7 -> 0, 1.0 -> 50, 2.0 -> 100
    return float(np.interp(ratio, [0.7, 1.0, 2.0], [0, 50, 100]))


def relative_strength_spy(hist: pd.DataFrame, spy_20d_return: float) -> float:
    """20-day return vs SPY 20-day return. Outperformance = higher score."""
    if len(hist) < 21:
        return 50.0
    ret = (hist["Close"].iloc[-1] / hist["Close"].iloc[-21] - 1) * 100
    spread = ret - spy_20d_return
    return float(np.interp(spread, [-10, 0, 10], [0, 50, 100]))


def week52_proximity(hist: pd.DataFrame) -> float:
    """Current price / 52-week high. Above 0.95 scores highest."""
    if len(hist) < 5:
        return 50.0
    high52 = hist["Close"].rolling(min(252, len(hist))).max().iloc[-1]
    ratio = hist["Close"].iloc[-1] / high52
    return float(np.interp(ratio, [0.7, 0.85, 0.95, 1.0], [0, 40, 90, 100]))


def short_interest_decline(ticker_info: dict) -> float:
    """Declining short interest = shorts covering = bullish."""
    try:
        short_pct = ticker_info.get("shortPercentOfFloat", 0) or 0
        # Lower short % = better. Map 0% -> 80, 30%+ -> 20
        base = float(np.interp(short_pct * 100, [0, 10, 20, 30], [80, 60, 40, 20]))
        return base
    except Exception:
        return 50.0


def percentile_rank_universe(scores: list[float]) -> list[float]:
    """Convert raw scores to percentile ranks within the universe."""
    arr = np.array(scores)
    ranks = []
    for s in arr:
        rank = float(np.searchsorted(np.sort(arr), s)) / len(arr) * 100
        ranks.append(round(rank, 1))
    return ranks
