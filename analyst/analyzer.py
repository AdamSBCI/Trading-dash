"""
Claude Analyst — scores each stock candidate on fundamental quality.
Caches results by (ticker, quarter_end) in SQLite. Same quarter = free.
"""
import json
import sqlite3
import os
from datetime import datetime, date
import yfinance as yf
import anthropic
from dotenv import load_dotenv

load_dotenv()

# Streamlit Cloud stores secrets in st.secrets; local dev uses .env
def _get_api_key(name: str) -> str:
    try:
        import streamlit as st
        return st.secrets[name]
    except Exception:
        return os.environ.get(name, "")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "cache", "analyst_cache.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=_get_api_key("ANTHROPIC_API_KEY"))
    return _client


def _init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analysis_cache (
            ticker TEXT,
            quarter_end TEXT,
            analysis TEXT,
            created_at TEXT,
            PRIMARY KEY (ticker, quarter_end)
        )
    """)
    conn.commit()
    conn.close()


def _current_quarter() -> str:
    today = date.today()
    q = (today.month - 1) // 3 + 1
    return f"{today.year}-Q{q}"


def _get_cached(ticker: str, quarter: str) -> dict | None:
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT analysis FROM analysis_cache WHERE ticker=? AND quarter_end=?",
        (ticker, quarter)
    ).fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None


def _save_cache(ticker: str, quarter: str, analysis: dict):
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO analysis_cache VALUES (?,?,?,?)",
        (ticker, quarter, json.dumps(analysis), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def _gather_financials(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    info = t.info or {}

    fins = {
        "revenue_growth_yoy": info.get("revenueGrowth"),
        "gross_margin": info.get("grossMargins"),
        "operating_margin": info.get("operatingMargins"),
        "profit_margin": info.get("profitMargins"),
        "debt_to_equity": info.get("debtToEquity"),
        "return_on_equity": info.get("returnOnEquity"),
        "free_cash_flow": info.get("freeCashflow"),
        "operating_cash_flow": info.get("operatingCashflow"),
        "forward_pe": info.get("forwardPE"),
        "peg_ratio": info.get("pegRatio"),
        "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth"),
        "revenue_quarterly_growth": info.get("revenueGrowth"),
        "short_ratio": info.get("shortRatio"),
        "analyst_target": info.get("targetMeanPrice"),
        "current_price": info.get("currentPrice"),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "company_name": info.get("longName", ticker),
    }

    # CFO/NI ratio (quality indicator)
    try:
        cfo = fins["operating_cash_flow"] or 0
        ni = info.get("netIncomeToCommon") or 1
        fins["cfo_ni_ratio"] = round(cfo / ni, 2) if ni != 0 else None
    except Exception:
        fins["cfo_ni_ratio"] = None

    # Analyst upside
    try:
        if fins["analyst_target"] and fins["current_price"]:
            fins["analyst_upside_pct"] = round(
                (fins["analyst_target"] / fins["current_price"] - 1) * 100, 1
            )
    except Exception:
        fins["analyst_upside_pct"] = None

    return {k: v for k, v in fins.items() if v is not None}


def analyze(ticker: str, use_cache: bool = True) -> dict:
    """Returns Claude's fundamental analysis. Cached per quarter."""
    quarter = _current_quarter()

    if use_cache:
        cached = _get_cached(ticker, quarter)
        if cached:
            cached["from_cache"] = True
            return cached

    fins = _gather_financials(ticker)

    prompt = f"""You are a senior equity research analyst. Analyze {ticker} ({fins.get('company_name', ticker)}) based on these financial metrics:

{json.dumps(fins, indent=2)}

Score each of the following dimensions from 1-10 and provide a brief rationale:

1. Earnings Quality: Is net income backed by real cash flow? Is CFO/NI ratio healthy (>0.8)?
2. Growth Trajectory: Are revenue and earnings accelerating? Is the forward PE justified?
3. Balance Sheet Health: Debt levels, cash position, financial flexibility.
4. Margin Trends: Are margins expanding, stable, or compressing?
5. Red Flags: Any concerns — earnings manipulation, dilution, guidance cuts, competitive threats.

Also provide:
- overall_score: weighted average (Earnings Quality 25%, Growth 30%, Balance Sheet 20%, Margins 15%, Red Flags -10% if present)
- summary: 2-3 sentence investment thesis
- key_risk: single biggest risk in one sentence
- recommendation: BUY / HOLD / AVOID with conviction level 1-3

Output ONLY valid JSON in this exact structure:
{{
  "earnings_quality": {{"score": 7, "rationale": "..."}},
  "growth_trajectory": {{"score": 8, "rationale": "..."}},
  "balance_sheet": {{"score": 6, "rationale": "..."}},
  "margin_trends": {{"score": 7, "rationale": "..."}},
  "red_flags": {{"score": 8, "rationale": "..."}},
  "overall_score": 7.2,
  "summary": "...",
  "key_risk": "...",
  "recommendation": "BUY",
  "conviction": 2
}}"""

    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="You are a senior equity research analyst. Always output valid JSON only.",
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    analysis = json.loads(text)
    analysis["ticker"] = ticker
    analysis["quarter"] = quarter
    analysis["financials"] = fins
    analysis["from_cache"] = False

    _save_cache(ticker, quarter, analysis)
    return analysis


if __name__ == "__main__":
    result = analyze("NVDA")
    print(json.dumps(result, indent=2))
