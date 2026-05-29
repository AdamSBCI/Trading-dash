"""
Score Blender — 60% quant composite + 40% Claude fundamental score.
Flags candidates where rank changed 3+ positions (quant vs AI disagreement = alpha signal).
"""
import pandas as pd
import numpy as np
from analyst.analyzer import analyze
from concurrent.futures import ThreadPoolExecutor, as_completed


def blend(scanner_df: pd.DataFrame, max_analyze: int = 30) -> pd.DataFrame:
    """
    Takes scanner results, runs Claude analysis on top candidates,
    blends scores, re-ranks, and flags rank deltas.
    """
    if scanner_df.empty:
        return pd.DataFrame()

    # Only analyze top N to control API costs
    candidates = scanner_df.head(max_analyze).copy()

    # Run Claude analysis in parallel (with caching, most will be free)
    fundamental_scores = {}

    def fetch_analysis(ticker):
        try:
            result = analyze(ticker)
            return ticker, result
        except Exception as e:
            return ticker, {"overall_score": 5.0, "error": str(e)}

    # Only analyze stocks (not crypto — no fundamentals)
    stock_candidates = candidates[candidates.get("asset_type", "stock") != "crypto"]["ticker"].tolist()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_analysis, t): t for t in stock_candidates}
        for future in as_completed(futures):
            ticker, result = future.result()
            fundamental_scores[ticker] = result

    # Build blended dataframe
    rows = []
    for _, row in candidates.iterrows():
        ticker = row["ticker"]
        quant_score = row["composite"]
        quant_rank = row.name  # 1-based rank from scanner

        if ticker in fundamental_scores and "overall_score" in fundamental_scores[ticker]:
            fund_score = fundamental_scores[ticker]["overall_score"] * 10  # convert 1-10 to 0-100
            blended = quant_score * 0.6 + fund_score * 0.4
            analysis = fundamental_scores[ticker]
        else:
            fund_score = 50.0  # neutral if no fundamental data (crypto etc.)
            blended = quant_score * 0.8 + fund_score * 0.2
            analysis = {}

        rows.append({
            **row.to_dict(),
            "quant_score": quant_score,
            "quant_rank": quant_rank,
            "fund_score": round(fund_score, 1),
            "blended_score": round(blended, 1),
            "recommendation": analysis.get("recommendation", ""),
            "conviction": analysis.get("conviction", 0),
            "summary": analysis.get("summary", ""),
            "key_risk": analysis.get("key_risk", ""),
            "from_cache": analysis.get("from_cache", True),
            "analysis": analysis,
        })

    blended_df = pd.DataFrame(rows)
    blended_df = blended_df.sort_values("blended_score", ascending=False).reset_index(drop=True)
    blended_df.index += 1

    # Flag rank changes (quant rank vs blended rank)
    blended_df["rank_delta"] = blended_df["quant_rank"] - blended_df.index
    blended_df["rank_flag"] = blended_df["rank_delta"].apply(
        lambda d: "⬆ upgraded" if d >= 3 else ("⬇ downgraded" if d <= -3 else "")
    )

    return blended_df


if __name__ == "__main__":
    from macro_gate import run as macro_run
    from scanner.run_scanner import run as scanner_run

    gate = macro_run()
    print(f"Macro: {gate['composite']}/100 — {gate['mode']}")
    scan = scanner_run(macro_mode=gate["mode"])
    print(f"Scanner found {len(scan)} candidates")

    blended = blend(scan, max_analyze=10)
    if not blended.empty:
        print(blended[["ticker", "quant_score", "fund_score", "blended_score", "recommendation", "rank_flag"]].to_string())
