"""
Stock and crypto universe definitions.
Tech/AI/Robotics/Chips/Quantum names get a sector bonus.
"""

# Core tech focus — your edge
TECH_WATCHLIST = [
    # AI / Cloud / Software
    "NVDA", "AMD", "INTC", "AVGO", "QCOM", "AMAT", "LRCX", "KLAC", "ASML",
    "MSFT", "GOOGL", "META", "AMZN", "AAPL", "ORCL", "CRM", "SNOW", "PLTR",
    "CRWD", "NET", "ZS", "DDOG", "MDB", "AI", "PATH", "BBAI",
    # Chips / Semiconductors
    "TSM", "MU", "MRVL", "SMCI", "ARM", "MPWR", "WOLF",
    # Robotics / Automation
    "TSLA", "ABB", "ROK", "EMR", "FANUC", "IRBT", "RXRX",
    # Quantum Computing
    "IONQ", "RGTI", "QUBT", "IBM",
    # Self-Driving / EV
    "RIVN", "LCID", "NIO", "XPEV", "LI", "MBLY", "LAZR",
    # Space / Next-gen
    "RKLB", "SPCE", "LUNR",
]

# Broader S&P 500 sample
SP500_SAMPLE = [
    "JPM", "BAC", "GS", "MS", "V", "MA", "AXP", "BLK",
    "UNH", "JNJ", "PFE", "MRK", "ABBV", "TMO", "ABT", "ISRG",
    "XOM", "CVX", "COP", "SLB", "EOG",
    "WMT", "AMZN", "HD", "TGT", "COST", "LOW",
    "BRK-B", "LLY", "PG", "KO", "PEP", "MCD", "SBUX", "NKE",
    "RTX", "HON", "CAT", "DE", "BA", "LMT", "NOC",
    "NEE", "DUK", "SO", "D",
    "SPG", "AMT", "PLD", "CCI",
]

# Tickers that get +10 sector bonus in scanner scoring
TECH_BONUS_TICKERS = set(TECH_WATCHLIST)

# All stocks to scan
ALL_STOCKS = list(dict.fromkeys(TECH_WATCHLIST + SP500_SAMPLE))

# Crypto universe (Coinbase symbols)
CRYPTO_UNIVERSE = [
    "BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "LINK-USD",
    "MATIC-USD", "ARB-USD", "OP-USD", "INJ-USD", "RNDR-USD",
]
