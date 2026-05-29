"""Market Breadth — % of S&P 500 stocks above their 200-day SMA."""
import yfinance as yf
import numpy as np

# Representative sample of S&P 500 across sectors (100 tickers for speed)
SAMPLE_TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B","JPM","UNH",
    "XOM","JNJ","V","PG","MA","HD","CVX","MRK","ABBV","PEP",
    "KO","AVGO","COST","LLY","TMO","MCD","DHR","ABT","CSCO","ACN",
    "NEE","TXN","NKE","UPS","RTX","HON","QCOM","LOW","AMGN","IBM",
    "AMAT","SBUX","GS","CAT","BA","MMM","MDLZ","GILD","ADI","ISRG",
    "REGN","VRTX","AXP","BLK","SPGI","CB","TJX","PLD","AMT","CCI",
    "SO","DUK","D","SRE","EXC","PCG","XEL","AEP","ED","WEC",
    "CL","EL","KMB","CHD","CLX","SJM","GIS","CPB","HSY","MKC",
    "WMT","TGT","ROST","TJX","DG","DLTR","KR","SYY","YUM","CMG",
    "F","GM","STLA","TM","HMC","RACE","LYFT","UBER","ABNB","BKNG",
]


def score() -> dict:
    above = 0
    total = 0
    for ticker in SAMPLE_TICKERS:
        try:
            hist = yf.Ticker(ticker).history(period="1y")
            if len(hist) < 200:
                continue
            sma200 = hist["Close"].rolling(200).mean().iloc[-1]
            current = hist["Close"].iloc[-1]
            above += 1 if current > sma200 else 0
            total += 1
        except Exception:
            continue

    if total == 0:
        return {"score": 50, "value": None, "note": "Breadth data unavailable"}

    pct = above / total * 100
    # Map: 80% above -> 100, 30% above -> 0
    score_val = float(np.interp(pct, [30, 55, 80], [0, 50, 100]))

    return {
        "score": round(score_val, 1),
        "value": round(pct, 1),
        "note": f"{pct:.0f}% of sample above 200d SMA — {'broad rally' if pct > 65 else 'narrow/weak' if pct < 45 else 'mixed'}",
    }


if __name__ == "__main__":
    print(score())
