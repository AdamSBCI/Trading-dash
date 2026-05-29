"""
Capital Allocation Engine
Answers: how much to deploy total, how much per position, when to add/trim/exit.
"""
import numpy as np
import yfinance as yf


# Macro score -> (min_deploy_pct, max_deploy_pct)
DEPLOYMENT_BANDS = {
    "AGGRESSIVE": (0.80, 0.90),
    "NORMAL":     (0.55, 0.70),
    "REDUCED":    (0.30, 0.50),
    "DEFENSIVE":  (0.00, 0.15),
}

# Blended score thresholds for position weight tiers
SCORE_TIERS = [
    (85, 1.5),   # top conviction — 1.5x base size
    (70, 1.0),   # standard
    (55, 0.6),   # speculative / smaller
    (0,  0.0),   # below threshold — skip
]


def deployment_allocation(total_capital: float, macro_mode: str, macro_score: float) -> dict:
    """
    Returns how much capital to have deployed vs in cash, scaled within the band
    by where the macro score sits inside the mode's range.
    """
    lo, hi = DEPLOYMENT_BANDS.get(macro_mode, (0.55, 0.70))

    # Scale within band: score 0-100 mapped to lo-hi
    band_score = np.interp(macro_score, [0, 100], [lo, hi])
    deploy_pct = round(float(band_score), 4)
    cash_pct = round(1.0 - deploy_pct, 4)

    deploy_amt = total_capital * deploy_pct
    cash_amt = total_capital * cash_pct

    return {
        "total_capital": total_capital,
        "deploy_pct": deploy_pct,
        "cash_pct": cash_pct,
        "deploy_amt": round(deploy_amt, 2),
        "cash_amt": round(cash_amt, 2),
        "macro_mode": macro_mode,
        "macro_score": macro_score,
    }


def position_sizes(
    candidates: list[dict],     # [{"ticker": ..., "blended_score": ..., "price": ...}]
    deploy_amt: float,
    max_positions: int,
    risk_per_trade_pct: float,  # e.g. 2.0 = 2% of total capital per trade
    total_capital: float,
) -> list[dict]:
    """
    Allocates deploy_amt across candidates using score-weighted position sizing.
    Also calculates stop-loss levels and dollar risk per trade.
    """
    # Filter to scoreable candidates, cap at max_positions
    eligible = [c for c in candidates if c.get("blended_score", 0) >= 55][:max_positions]
    if not eligible:
        return []

    # Assign weight tier per candidate
    weighted = []
    for c in eligible:
        score = c.get("blended_score", 50)
        weight = next((w for threshold, w in SCORE_TIERS if score >= threshold), 0.0)
        if weight > 0:
            weighted.append({**c, "_weight": weight})

    if not weighted:
        return []

    total_weight = sum(c["_weight"] for c in weighted)
    max_risk_per_trade = total_capital * (risk_per_trade_pct / 100)

    results = []
    for c in weighted:
        alloc_pct = c["_weight"] / total_weight
        position_value = round(deploy_amt * alloc_pct, 2)

        price = c.get("price", 0)
        if price <= 0:
            continue

        # ATR-based stop (approximate: use 5% for now, replaced by real ATR if available)
        atr_pct = c.get("atr_pct", 5.0)
        stop_distance_pct = atr_pct * 2  # 2x ATR stop
        stop_price = round(price * (1 - stop_distance_pct / 100), 2)

        # Shares = min(position_value / price, risk-based shares)
        shares_by_value = position_value / price
        shares_by_risk = max_risk_per_trade / (price * stop_distance_pct / 100) if stop_distance_pct > 0 else shares_by_value
        shares = round(min(shares_by_value, shares_by_risk))

        actual_value = round(shares * price, 2)
        dollar_risk = round(shares * price * stop_distance_pct / 100, 2)

        results.append({
            "ticker": c["ticker"],
            "blended_score": c.get("blended_score"),
            "weight_tier": c["_weight"],
            "alloc_pct": round(alloc_pct * 100, 1),
            "position_value": actual_value,
            "shares": shares,
            "entry_price": round(price, 2),
            "stop_price": stop_price,
            "stop_pct": round(stop_distance_pct, 1),
            "dollar_risk": dollar_risk,
            "risk_pct_of_capital": round(dollar_risk / total_capital * 100, 2),
            "recommendation": c.get("recommendation", ""),
            "is_tech": c.get("is_tech", False),
        })

    return results


def add_trim_signals(
    positions: list[dict],     # your current open positions
    scanner_df,                # latest scanner results DataFrame
    macro_score: float,
    macro_mode: str,
) -> list[dict]:
    """
    For each open position, recommend ADD / HOLD / TRIM / EXIT based on:
    - Current macro mode vs when you entered
    - Current scanner score vs entry score
    - Distance from stop
    """
    import pandas as pd
    signals = []

    score_lookup = {}
    if scanner_df is not None and not scanner_df.empty and "ticker" in scanner_df.columns:
        score_lookup = dict(zip(scanner_df["ticker"], scanner_df.get("composite", scanner_df.get("blended_score", []))))

    for pos in positions:
        ticker = pos.get("ticker", "")
        entry_price = pos.get("entry_price", 0)
        current_price = pos.get("current_price", entry_price)
        stop_price = pos.get("stop_price", entry_price * 0.95)
        shares = pos.get("shares", 0)
        entry_score = pos.get("entry_score", 60)
        current_score = score_lookup.get(ticker, entry_score)

        pnl_pct = (current_price / entry_price - 1) * 100 if entry_price > 0 else 0
        distance_to_stop_pct = (current_price / stop_price - 1) * 100 if stop_price > 0 else 999

        # Decision logic
        if macro_mode == "DEFENSIVE":
            action = "EXIT"
            reason = "Macro turned DEFENSIVE — exit all positions"
        elif current_price <= stop_price:
            action = "EXIT"
            reason = f"Price hit stop loss (${stop_price:.2f})"
        elif macro_mode == "REDUCED" and pnl_pct > 15:
            action = "TRIM 50%"
            reason = "REDUCED macro mode + position up 15%+ — lock in gains"
        elif current_score >= entry_score + 10 and macro_mode in ("AGGRESSIVE", "NORMAL"):
            action = "ADD"
            reason = f"Score improved {entry_score:.0f}→{current_score:.0f}, macro supports"
        elif current_score < entry_score - 15:
            action = "TRIM 50%"
            reason = f"Score deteriorated {entry_score:.0f}→{current_score:.0f}"
        elif pnl_pct > 30 and macro_mode == "NORMAL":
            action = "TRIM 25%"
            reason = "Up 30%+ in NORMAL mode — reduce to protect profits"
        elif distance_to_stop_pct < 3:
            action = "WATCH"
            reason = f"Within 3% of stop (${stop_price:.2f}) — be ready to exit"
        else:
            action = "HOLD"
            reason = "No action needed — thesis intact"

        action_color = {
            "ADD": "#00ff88",
            "HOLD": "#88ccff",
            "WATCH": "#ffaa00",
            "TRIM 25%": "#ffaa00",
            "TRIM 50%": "#ff8844",
            "EXIT": "#ff4444",
        }.get(action, "#888888")

        signals.append({
            **pos,
            "current_score": current_score,
            "pnl_pct": round(pnl_pct, 2),
            "pnl_dollars": round((current_price - entry_price) * shares, 2),
            "distance_to_stop_pct": round(distance_to_stop_pct, 1),
            "action": action,
            "reason": reason,
            "action_color": action_color,
        })

    return signals


def get_atr_pct(ticker: str) -> float:
    """14-day ATR as % of price."""
    try:
        hist = yf.Ticker(ticker).history(period="1mo")
        if len(hist) < 15:
            return 5.0
        high = hist["High"]
        low = hist["Low"]
        close = hist["Close"]
        tr = np.maximum(high - low, np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1))))
        atr = tr.rolling(14).mean().iloc[-1]
        return round(float(atr / close.iloc[-1] * 100), 2)
    except Exception:
        return 5.0
