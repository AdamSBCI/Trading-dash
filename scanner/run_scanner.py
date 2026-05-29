"""
Quantitative Scanner — scores and ranks the full universe.
Only activates when macro gate is NORMAL or better.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from scanner.universe import ALL_STOCKS, CRYPTO_UNIVERSE, TECH_BONUS_TICKERS
from scanner.factors import (
    momentum_crossover, volume_surge, relative_strength_spy,
    week52_proximity, short_interest_decline, percentile_rank_universe,
)


def _score_ticker(ticker: str, spy_20d: float) -> dict | None:
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1y")
        info = t.info or {}
        if hist.empty or len(hist) < 30:
            return None

        m = momentum_crossover(hist)
        v = volume_surge(hist)
        rs = relative_strength_spy(hist, spy_20d)
        w = week52_proximity(hist)
        si = short_interest_decline(info)

        raw = (m + v + rs + w + si) / 5

        # Tech/AI/Robotics sector bonus
        tech_bonus = 10 if ticker in TECH_BONUS_TICKERS else 0
        composite = min(100, raw + tech_bonus)

        price = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2]
        change_pct = (price / prev - 1) * 100

        return {
            "ticker": ticker,
            "price": round(price, 2),
            "change_pct": round(change_pct, 2),
            "momentum": round(m, 1),
            "volume": round(v, 1),
            "rel_strength": round(rs, 1),
            "w52_proximity": round(w, 1),
            "short_interest": round(si, 1),
            "raw_score": round(raw, 1),
            "tech_bonus": tech_bonus,
            "composite": round(composite, 1),
            "is_tech": ticker in TECH_BONUS_TICKERS,
        }
    except Exception:
        return None


def _score_crypto(ticker: str) -> dict | None:
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1y")
        if hist.empty or len(hist) < 30:
            return None

        m = momentum_crossover(hist)
        v = volume_surge(hist)
        w = week52_proximity(hist)

        # Crypto: no short interest, RS vs BTC instead of SPY
        btc = yf.Ticker("BTC-USD").history(period="1mo")
        btc_20d = (btc["Close"].iloc[-1] / btc["Close"].iloc[-21] - 1) * 100 if len(btc) > 21 else 0
        crypto_ret = (hist["Close"].iloc[-1] / hist["Close"].iloc[-21] - 1) * 100 if len(hist) > 21 else 0
        rs = float(np.interp(crypto_ret - btc_20d, [-20, 0, 20], [0, 50, 100]))

        composite = (m + v + rs + w) / 4

        price = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2]
        change_pct = (price / prev - 1) * 100

        return {
            "ticker": ticker,
            "price": round(price, 2),
            "change_pct": round(change_pct, 2),
            "momentum": round(m, 1),
            "volume": round(v, 1),
            "rel_strength": round(rs, 1),
            "w52_proximity": round(w, 1),
            "short_interest": 50.0,
            "raw_score": round(composite, 1),
            "tech_bonus": 0,
            "composite": round(composite, 1),
            "is_tech": False,
            "asset_type": "crypto",
        }
    except Exception:
        return None


def run(macro_mode: str = "NORMAL", min_score: float = 0) -> pd.DataFrame:
    """
    Returns ranked DataFrame of candidates.
    macro_mode controls filtering threshold:
      AGGRESSIVE -> show all above 50
      NORMAL     -> show all above 60
      REDUCED    -> show only above 75
      DEFENSIVE  -> return empty
    """
    if macro_mode == "DEFENSIVE":
        return pd.DataFrame()

    threshold = {"AGGRESSIVE": 50, "NORMAL": 60, "REDUCED": 75}.get(macro_mode, 60)
    threshold = max(threshold, min_score)

    # Get SPY baseline
    spy = yf.Ticker("SPY").history(period="2mo")
    spy_20d = (spy["Close"].iloc[-1] / spy["Close"].iloc[-21] - 1) * 100 if len(spy) > 21 else 0

    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        stock_futures = {executor.submit(_score_ticker, t, spy_20d): t for t in ALL_STOCKS}
        crypto_futures = {executor.submit(_score_crypto, t): t for t in CRYPTO_UNIVERSE}

        for future in as_completed({**stock_futures, **crypto_futures}):
            result = future.result()
            if result:
                result.setdefault("asset_type", "stock")
                results.append(result)

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)

    # Percentile-rank composites within universe
    df["percentile"] = percentile_rank_universe(df["composite"].tolist())

    df = df[df["composite"] >= threshold].copy()
    df = df.sort_values("composite", ascending=False).reset_index(drop=True)
    df.index += 1  # 1-based rank

    return df


if __name__ == "__main__":
    from macro_gate import run as macro_run
    gate = macro_run()
    print(f"Macro gate: {gate['composite']}/100 — {gate['mode']}")
    df = run(macro_mode=gate["mode"])
    if df.empty:
        print("Scanner disabled (DEFENSIVE mode or no qualifying stocks)")
    else:
        print(df[["ticker", "composite", "momentum", "volume", "rel_strength", "w52_proximity", "asset_type"]].head(20).to_string())
