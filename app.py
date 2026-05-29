"""
Trading Dashboard — 5-page Streamlit app
Page 0: Market Overview (TradingView)
Page 1: Macro Deployment Gate
Page 2: Quant Scanner
Page 3: Claude Analyst
Page 4: Watchlist
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar nav ──────────────────────────────────────────────────────────────
st.sidebar.title("Trading System")
page = st.sidebar.radio(
    "Navigate",
    ["Market Overview", "Macro Gate", "Quant Scanner", "Claude Analyst", "Positions", "Watchlist"],
    index=0,
)
st.sidebar.markdown("---")

# ── Capital Allocation (persists across all pages) ────────────────────────
st.sidebar.subheader("Capital Settings")
total_capital = st.sidebar.number_input(
    "Total deployable capital ($)",
    min_value=1000,
    max_value=10_000_000,
    value=st.session_state.get("total_capital", 50000),
    step=1000,
    format="%d",
)
st.session_state["total_capital"] = total_capital

max_positions = st.sidebar.slider(
    "Max simultaneous positions",
    min_value=3, max_value=20,
    value=st.session_state.get("max_positions", 8),
)
st.session_state["max_positions"] = max_positions

risk_per_trade = st.sidebar.slider(
    "Max risk per trade (% of capital)",
    min_value=0.5, max_value=5.0,
    value=st.session_state.get("risk_per_trade", 2.0),
    step=0.5,
)
st.session_state["risk_per_trade"] = risk_per_trade

st.sidebar.markdown("---")
st.sidebar.caption("Data: yfinance + TradingView · AI: Claude Sonnet")


# ── TradingView widget helpers ────────────────────────────────────────────────
def tv_widget(html: str, height: int = 400):
    components.html(html, height=height, scrolling=False)


# Sector symbol lists for TradingView widgets
TV_SECTORS = {
    "AI & Cloud": [
        "NASDAQ:NVDA", "NASDAQ:AMD", "NASDAQ:MSFT", "NASDAQ:GOOGL",
        "NASDAQ:META", "NASDAQ:AMZN", "NASDAQ:PLTR", "NASDAQ:AI",
        "NASDAQ:CRWD", "NASDAQ:NET", "NASDAQ:DDOG", "NASDAQ:SNOW",
    ],
    "Chips & Semiconductors": [
        "NYSE:TSM", "NASDAQ:AVGO", "NASDAQ:QCOM", "NASDAQ:AMAT",
        "NASDAQ:LRCX", "NASDAQ:KLAC", "NASDAQ:MU", "NASDAQ:MRVL",
        "NASDAQ:ARM", "NASDAQ:ASML", "NASDAQ:MPWR", "NASDAQ:SMCI",
    ],
    "Robotics & Automation": [
        "NASDAQ:TSLA", "NYSE:ROK", "NYSE:EMR", "NASDAQ:IRBT",
        "NYSE:ABB", "NASDAQ:PATH", "NASDAQ:RXRX", "NYSE:ISRG",
    ],
    "Quantum Computing": [
        "NYSE:IONQ", "NASDAQ:RGTI", "NASDAQ:QUBT", "NYSE:IBM",
        "NASDAQ:MSFT", "NASDAQ:GOOGL",
    ],
    "Self-Driving & EV": [
        "NASDAQ:TSLA", "NASDAQ:RIVN", "NASDAQ:LCID", "NYSE:NIO",
        "NASDAQ:XPEV", "NASDAQ:LI", "NASDAQ:MBLY", "NASDAQ:LAZR",
    ],
    "Space & Next-Gen": [
        "NASDAQ:RKLB", "NYSE:SPCE", "NASDAQ:LUNR", "NASDAQ:ASTS",
    ],
    "Crypto": [
        "BINANCE:BTCUSDT", "BINANCE:ETHUSDT", "BINANCE:SOLUSDT",
        "BINANCE:AVAXUSDT", "BINANCE:LINKUSDT", "COINBASE:SOLUSD",
    ],
}

# ── Helpers ──────────────────────────────────────────────────────────────────
def score_color(score: float) -> str:
    if score >= 65:
        return "#00ff88"
    elif score >= 45:
        return "#88ccff"
    elif score >= 30:
        return "#ffaa00"
    return "#ff4444"


def signal_bar(score: float, label: str, note: str):
    color = score_color(score)
    st.markdown(
        f"""
        <div style='margin-bottom:8px;'>
            <div style='display:flex;justify-content:space-between;margin-bottom:2px;'>
                <span style='font-size:13px;font-weight:600;'>{label}</span>
                <span style='font-size:13px;color:{color};font-weight:700;'>{score:.0f}/100</span>
            </div>
            <div style='background:#1e2130;border-radius:4px;height:8px;'>
                <div style='background:{color};width:{score}%;height:8px;border-radius:4px;'></div>
            </div>
            <div style='font-size:11px;color:#888;margin-top:2px;'>{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def recommendation_badge(rec: str, conviction: int) -> str:
    colors = {"BUY": "#00ff88", "HOLD": "#ffaa00", "AVOID": "#ff4444"}
    color = colors.get(rec, "#888888")
    stars = "●" * conviction + "○" * (3 - conviction)
    return f"<span style='background:{color};color:#000;padding:2px 8px;border-radius:4px;font-weight:700;font-size:12px;'>{rec}</span> <span style='color:{color};font-size:11px;'>{stars}</span>"


# ════════════════════════════════════════════════════════════════════════════
# PAGE 0 — MARKET OVERVIEW (TradingView)
# ════════════════════════════════════════════════════════════════════════════
if page == "Market Overview":
    st.title("Market Overview")
    st.caption("Live market data · TradingView widgets · your tech/AI/robotics sectors")

    # ── Ticker Tape ────────────────────────────────────────────────────────
    tv_widget("""
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
      {
        "symbols": [
          {"proName":"FOREXCOM:SPXUSD","title":"S&P 500"},
          {"proName":"FOREXCOM:NSXUSD","title":"Nasdaq 100"},
          {"description":"VIX","proName":"CBOE:VIX"},
          {"description":"NVDA","proName":"NASDAQ:NVDA"},
          {"description":"AMD","proName":"NASDAQ:AMD"},
          {"description":"MSFT","proName":"NASDAQ:MSFT"},
          {"description":"GOOGL","proName":"NASDAQ:GOOGL"},
          {"description":"META","proName":"NASDAQ:META"},
          {"description":"TSLA","proName":"NASDAQ:TSLA"},
          {"description":"PLTR","proName":"NASDAQ:PLTR"},
          {"description":"IONQ","proName":"NYSE:IONQ"},
          {"description":"TSM","proName":"NYSE:TSM"},
          {"description":"AVGO","proName":"NASDAQ:AVGO"},
          {"description":"RKLB","proName":"NASDAQ:RKLB"},
          {"description":"BTC","proName":"BINANCE:BTCUSDT"},
          {"description":"ETH","proName":"BINANCE:ETHUSDT"},
          {"description":"SOL","proName":"BINANCE:SOLUSDT"}
        ],
        "showSymbolLogo": true,
        "isTransparent": true,
        "displayMode": "adaptive",
        "colorTheme": "dark",
        "locale": "en"
      }
      </script>
    </div>
    """, height=80)

    st.markdown("---")

    # ── Row 1: Market Overview + Macro quick status ─────────────────────────
    col_main, col_macro = st.columns([2, 1])

    with col_main:
        st.subheader("Major Indices & Key Tech")
        tv_widget("""
        <div class="tradingview-widget-container">
          <div class="tradingview-widget-container__widget"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js" async>
          {
            "colorTheme": "dark",
            "dateRange": "1D",
            "showChart": true,
            "locale": "en",
            "largeChartUrl": "",
            "isTransparent": true,
            "showSymbolLogo": true,
            "showFloatingTooltip": true,
            "width": "100%",
            "height": "400",
            "plotLineColorGrowing": "rgba(41, 98, 255, 1)",
            "plotLineColorFalling": "rgba(41, 98, 255, 1)",
            "gridLineColor": "rgba(42, 46, 57, 0)",
            "scaleFontColor": "rgba(134, 137, 147, 1)",
            "belowLineFillColorGrowing": "rgba(41, 98, 255, 0.12)",
            "belowLineFillColorFalling": "rgba(41, 98, 255, 0.12)",
            "belowLineFillColorGrowingBottom": "rgba(41, 98, 255, 0)",
            "belowLineFillColorFallingBottom": "rgba(41, 98, 255, 0)",
            "symbolActiveColor": "rgba(41, 98, 255, 0.12)",
            "tabs": [
              {
                "title": "Indices",
                "symbols": [
                  {"s":"FOREXCOM:SPXUSD","d":"S&P 500"},
                  {"s":"FOREXCOM:NSXUSD","d":"Nasdaq 100"},
                  {"s":"FOREXCOM:DJI","d":"Dow Jones"},
                  {"s":"NASDAQ:QQQ","d":"QQQ ETF"},
                  {"s":"AMEX:SMH","d":"Semiconductors"},
                  {"s":"AMEX:ARKK","d":"ARK Innovation"}
                ],
                "originalTitle": "Indices"
              },
              {
                "title": "AI & Cloud",
                "symbols": [
                  {"s":"NASDAQ:NVDA","d":"NVIDIA"},
                  {"s":"NASDAQ:AMD","d":"AMD"},
                  {"s":"NASDAQ:MSFT","d":"Microsoft"},
                  {"s":"NASDAQ:GOOGL","d":"Alphabet"},
                  {"s":"NASDAQ:META","d":"Meta"},
                  {"s":"NASDAQ:PLTR","d":"Palantir"},
                  {"s":"NASDAQ:CRWD","d":"CrowdStrike"},
                  {"s":"NASDAQ:NET","d":"Cloudflare"}
                ],
                "originalTitle": "AI & Cloud"
              },
              {
                "title": "Chips",
                "symbols": [
                  {"s":"NYSE:TSM","d":"TSMC"},
                  {"s":"NASDAQ:AVGO","d":"Broadcom"},
                  {"s":"NASDAQ:AMAT","d":"Applied Materials"},
                  {"s":"NASDAQ:QCOM","d":"Qualcomm"},
                  {"s":"NASDAQ:ARM","d":"ARM Holdings"},
                  {"s":"NASDAQ:MU","d":"Micron"},
                  {"s":"NASDAQ:SMCI","d":"Super Micro"},
                  {"s":"NASDAQ:MRVL","d":"Marvell"}
                ],
                "originalTitle": "Chips"
              },
              {
                "title": "Robotics & EV",
                "symbols": [
                  {"s":"NASDAQ:TSLA","d":"Tesla"},
                  {"s":"NASDAQ:RIVN","d":"Rivian"},
                  {"s":"NYSE:NIO","d":"NIO"},
                  {"s":"NASDAQ:MBLY","d":"Mobileye"},
                  {"s":"NYSE:ROK","d":"Rockwell"},
                  {"s":"NYSE:ISRG","d":"Intuitive Surgical"},
                  {"s":"NASDAQ:PATH","d":"UiPath"},
                  {"s":"NASDAQ:RKLB","d":"Rocket Lab"}
                ],
                "originalTitle": "Robotics & EV"
              },
              {
                "title": "Quantum",
                "symbols": [
                  {"s":"NYSE:IONQ","d":"IonQ"},
                  {"s":"NASDAQ:RGTI","d":"Rigetti"},
                  {"s":"NASDAQ:QUBT","d":"Quantum Computing"},
                  {"s":"NYSE:IBM","d":"IBM"}
                ],
                "originalTitle": "Quantum"
              },
              {
                "title": "Crypto",
                "symbols": [
                  {"s":"BINANCE:BTCUSDT","d":"Bitcoin"},
                  {"s":"BINANCE:ETHUSDT","d":"Ethereum"},
                  {"s":"BINANCE:SOLUSDT","d":"Solana"},
                  {"s":"BINANCE:AVAXUSDT","d":"Avalanche"},
                  {"s":"BINANCE:LINKUSDT","d":"Chainlink"},
                  {"s":"COINBASE:MATICUSD","d":"Polygon"}
                ],
                "originalTitle": "Crypto"
              }
            ]
          }
          </script>
        </div>
        """, height=420)

    with col_macro:
        st.subheader("Macro Status")
        if "macro_data" in st.session_state:
            d = st.session_state["macro_data"]
            color = d["color"]
            st.markdown(
                f"""<div style='background:#1e2130;border-radius:12px;padding:20px;text-align:center;margin-bottom:12px;'>
                    <div style='font-size:11px;color:#aaa;'>MACRO SCORE</div>
                    <div style='font-size:52px;font-weight:900;color:{color};line-height:1;'>{d['composite']:.0f}</div>
                    <div style='font-size:18px;font-weight:700;color:{color};margin-top:4px;'>{d['mode']}</div>
                </div>""",
                unsafe_allow_html=True,
            )
            for key, label in [("vix_level","VIX"),("tech_momentum","Tech Mom."),("breadth","Breadth"),("credit_spreads","Credit")]:
                sig = d["signals"].get(key, {})
                s = sig.get("score", 50)
                c = score_color(s)
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;margin-bottom:6px;font-size:12px;'>"
                    f"<span style='color:#aaa;'>{label}</span>"
                    f"<span style='color:{c};font-weight:700;'>{s:.0f}</span></div>"
                    f"<div style='background:#1e2130;border-radius:3px;height:5px;margin-bottom:8px;'>"
                    f"<div style='background:{c};width:{s}%;height:5px;border-radius:3px;'></div></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("Go to Macro Gate page and click Refresh to load macro signals.")

        st.markdown("---")
        st.subheader("Fear & Greed")
        tv_widget("""
        <div class="tradingview-widget-container">
          <div class="tradingview-widget-container__widget"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-single-quote.js" async>
          {
            "symbol": "CBOE:VIX",
            "width": "100%",
            "colorTheme": "dark",
            "isTransparent": true,
            "locale": "en"
          }
          </script>
        </div>
        """, height=100)

        tv_widget("""
        <div class="tradingview-widget-container">
          <div class="tradingview-widget-container__widget"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-single-quote.js" async>
          {
            "symbol": "NASDAQ:QQQ",
            "width": "100%",
            "colorTheme": "dark",
            "isTransparent": true,
            "locale": "en"
          }
          </script>
        </div>
        """, height=100)

    st.markdown("---")

    # ── Row 2: Heatmap ──────────────────────────────────────────────────────
    st.subheader("S&P 500 Sector Heatmap")
    tv_widget("""
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-stock-heatmap.js" async>
      {
        "exchanges": [],
        "dataSource": "SPX500",
        "grouping": "sector",
        "blockSize": "market_cap_basic",
        "blockColor": "change",
        "locale": "en",
        "symbolUrl": "",
        "colorTheme": "dark",
        "hasTopBar": true,
        "isDataSetEnabled": false,
        "isZoomEnabled": true,
        "hasSymbolTooltip": true,
        "isMonoSize": false,
        "width": "100%",
        "height": "450"
      }
      </script>
    </div>
    """, height=470)

    st.markdown("---")

    # ── Row 3: Your sector charts ───────────────────────────────────────────
    st.subheader("Your Sectors — Live Charts")

    # symbol-overview requires ["Display Name", "EXCHANGE:TICKER|1D"] format
    SECTOR_CHART_SYMBOLS = {
        "AI & Cloud": [
            ["NVIDIA", "NASDAQ:NVDA|1D"],
            ["AMD", "NASDAQ:AMD|1D"],
            ["Microsoft", "NASDAQ:MSFT|1D"],
            ["Alphabet", "NASDAQ:GOOGL|1D"],
            ["Meta", "NASDAQ:META|1D"],
            ["Palantir", "NASDAQ:PLTR|1D"],
            ["Amazon", "NASDAQ:AMZN|1D"],
            ["CrowdStrike", "NASDAQ:CRWD|1D"],
            ["Cloudflare", "NASDAQ:NET|1D"],
            ["Snowflake", "NASDAQ:SNOW|1D"],
        ],
        "Chips & Semiconductors": [
            ["TSMC", "NYSE:TSM|1D"],
            ["Broadcom", "NASDAQ:AVGO|1D"],
            ["Applied Materials", "NASDAQ:AMAT|1D"],
            ["Qualcomm", "NASDAQ:QCOM|1D"],
            ["ARM Holdings", "NASDAQ:ARM|1D"],
            ["Micron", "NASDAQ:MU|1D"],
            ["Marvell", "NASDAQ:MRVL|1D"],
            ["Super Micro", "NASDAQ:SMCI|1D"],
            ["Lam Research", "NASDAQ:LRCX|1D"],
            ["KLA Corp", "NASDAQ:KLAC|1D"],
        ],
        "Robotics & Automation": [
            ["Tesla", "NASDAQ:TSLA|1D"],
            ["Rockwell", "NYSE:ROK|1D"],
            ["Emerson", "NYSE:EMR|1D"],
            ["UiPath", "NASDAQ:PATH|1D"],
            ["Intuitive Surgical", "NASDAQ:ISRG|1D"],
            ["ABB", "NYSE:ABB|1D"],
            ["Recursion Pharma", "NASDAQ:RXRX|1D"],
        ],
        "Quantum Computing": [
            ["IonQ", "NYSE:IONQ|1D"],
            ["Rigetti", "NASDAQ:RGTI|1D"],
            ["Quantum Computing", "NASDAQ:QUBT|1D"],
            ["IBM", "NYSE:IBM|1D"],
            ["Microsoft", "NASDAQ:MSFT|1D"],
            ["Alphabet", "NASDAQ:GOOGL|1D"],
        ],
        "Self-Driving & EV": [
            ["Tesla", "NASDAQ:TSLA|1D"],
            ["Rivian", "NASDAQ:RIVN|1D"],
            ["Lucid", "NASDAQ:LCID|1D"],
            ["NIO", "NYSE:NIO|1D"],
            ["XPeng", "NASDAQ:XPEV|1D"],
            ["Li Auto", "NASDAQ:LI|1D"],
            ["Mobileye", "NASDAQ:MBLY|1D"],
            ["Luminar", "NASDAQ:LAZR|1D"],
        ],
        "Space & Next-Gen": [
            ["Rocket Lab", "NASDAQ:RKLB|1D"],
            ["Virgin Galactic", "NYSE:SPCE|1D"],
            ["Intuitive Machines", "NASDAQ:LUNR|1D"],
            ["AST SpaceMobile", "NASDAQ:ASTS|1D"],
        ],
        "Crypto": [
            ["Bitcoin", "BINANCE:BTCUSDT|1D"],
            ["Ethereum", "BINANCE:ETHUSDT|1D"],
            ["Solana", "BINANCE:SOLUSDT|1D"],
            ["Avalanche", "BINANCE:AVAXUSDT|1D"],
            ["Chainlink", "BINANCE:LINKUSDT|1D"],
            ["Render", "BINANCE:RNDRUSDT|1D"],
        ],
    }

    import json as _json

    sector_tab_names = list(SECTOR_CHART_SYMBOLS.keys())
    tabs = st.tabs(sector_tab_names)

    for tab, (sector_name, sym_pairs) in zip(tabs, SECTOR_CHART_SYMBOLS.items()):
        with tab:
            symbols_json = _json.dumps(sym_pairs)
            tv_widget(f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js" async>
              {{
                "symbols": {symbols_json},
                "chartOnly": false,
                "width": "100%",
                "height": 350,
                "locale": "en",
                "colorTheme": "dark",
                "autosize": false,
                "showVolume": false,
                "showMA": true,
                "hideDateRanges": false,
                "hideMarketStatus": false,
                "hideSymbolLogo": true,
                "scalePosition": "right",
                "scaleMode": "Normal",
                "fontFamily": "-apple-system, BlinkMacSystemFont, Trebuchet MS, Roboto, Ubuntu, sans-serif",
                "fontSize": "10",
                "noTimeScale": false,
                "valuesTracking": "1",
                "changeMode": "price-and-percent",
                "chartType": "area",
                "maLineColor": "#2962FF",
                "maLineWidth": 1,
                "maLength": 9,
                "lineWidth": 2,
                "lineType": 0,
                "dateRanges": ["1d|1","1m|30","3m|60","12m|1D","60m|1W","all|1M"]
              }}
              </script>
            </div>
            """, height=370)

            # Single-quote tiles for every stock in the sector
            tv_syms = TV_SECTORS.get(sector_name, [])
            if tv_syms:
                cols = st.columns(min(4, len(tv_syms)))
                for i, sym in enumerate(tv_syms):
                    with cols[i % len(cols)]:
                        tv_widget(f"""
                        <div class="tradingview-widget-container">
                          <div class="tradingview-widget-container__widget"></div>
                          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-single-quote.js" async>
                          {{
                            "symbol": "{sym}",
                            "width": "100%",
                            "colorTheme": "dark",
                            "isTransparent": true,
                            "locale": "en"
                          }}
                          </script>
                        </div>
                        """, height=80)

    st.markdown("---")

    # ── Row 4: Crypto overview + Economic calendar ──────────────────────────
    col_crypto, col_cal = st.columns([1, 1])

    with col_crypto:
        st.subheader("Crypto Market")
        tv_widget("""
        <div class="tradingview-widget-container">
          <div class="tradingview-widget-container__widget"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-screener.js" async>
          {
            "width": "100%",
            "height": 450,
            "defaultColumn": "overview",
            "screener_type": "crypto_mkt",
            "displayCurrency": "USD",
            "colorTheme": "dark",
            "locale": "en",
            "isTransparent": true
          }
          </script>
        </div>
        """, height=470)

    with col_cal:
        st.subheader("Economic Calendar")
        tv_widget("""
        <div class="tradingview-widget-container">
          <div class="tradingview-widget-container__widget"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
          {
            "colorTheme": "dark",
            "isTransparent": true,
            "width": "100%",
            "height": 450,
            "locale": "en",
            "importanceFilter": "0,1",
            "countryFilter": "us"
          }
          </script>
        </div>
        """, height=470)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 1 — MACRO GATE
# ════════════════════════════════════════════════════════════════════════════
elif page == "Macro Gate":
    st.title("L1 — Macro Deployment Gate")
    st.caption("6 signals · composite score 0-100 · deployment zone gating")

    refresh = st.button("Refresh Signals", type="primary")

    if refresh or "macro_data" not in st.session_state:
        with st.spinner("Fetching macro signals..."):
            from macro_gate import run as macro_run
            st.session_state["macro_data"] = macro_run()

    data = st.session_state.get("macro_data")
    if not data:
        st.info("Click 'Refresh Signals' to load macro data.")
        st.stop()

    composite = data["composite"]
    mode = data["mode"]
    color = data["color"]

    # Main composite display
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown(
            f"""
            <div style='background:#1e2130;border-radius:12px;padding:24px;text-align:center;'>
                <div style='font-size:14px;color:#aaa;margin-bottom:4px;'>COMPOSITE SCORE</div>
                <div style='font-size:64px;font-weight:900;color:{color};line-height:1;'>{composite:.0f}</div>
                <div style='font-size:12px;color:#aaa;margin-top:4px;'>out of 100</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        deploy_desc = {
            "AGGRESSIVE": "Deploy full position sizing. Tech leaders and high-conviction setups.",
            "NORMAL": "Standard position sizing. Follow scanner signals.",
            "REDUCED": "Half position sizing. Only highest-conviction setups (score 75+).",
            "DEFENSIVE": "No new positions. Protect capital. Consider hedges.",
        }
        st.markdown(
            f"""
            <div style='background:#1e2130;border-radius:12px;padding:24px;text-align:center;'>
                <div style='font-size:14px;color:#aaa;margin-bottom:4px;'>DEPLOYMENT MODE</div>
                <div style='font-size:36px;font-weight:900;color:{color};line-height:1.2;'>{mode}</div>
                <div style='font-size:12px;color:#aaa;margin-top:8px;'>{deploy_desc.get(mode, "")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        # Gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=composite,
            domain={"x": [0, 1], "y": [0, 1]},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#555"},
                "bar": {"color": color},
                "bgcolor": "#1e2130",
                "steps": [
                    {"range": [0, 30], "color": "#2a1a1a"},
                    {"range": [30, 45], "color": "#2a2010"},
                    {"range": [45, 65], "color": "#1a2030"},
                    {"range": [65, 100], "color": "#1a2a1a"},
                ],
                "threshold": {"line": {"color": color, "width": 3}, "thickness": 0.75, "value": composite},
            },
            number={"font": {"color": color}},
        ))
        fig.update_layout(
            height=200,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#ccc",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Signal Breakdown")

    signal_labels = {
        "vix_level": "VIX Level",
        "vix_term_structure": "VIX Term Structure",
        "breadth": "Market Breadth",
        "credit_spreads": "Credit Spreads",
        "put_call": "Put/Call Sentiment",
        "tech_momentum": "Tech Sector Momentum",
    }

    signals = data.get("signals", {})
    col_a, col_b = st.columns(2)
    items = list(signal_labels.items())
    for i, (key, label) in enumerate(items):
        sig = signals.get(key, {})
        with (col_a if i < 3 else col_b):
            signal_bar(sig.get("score", 50), label, sig.get("note", ""))

    # Historical VIX chart
    st.markdown("---")
    st.subheader("VIX — 1 Year")
    vix_hist = yf.Ticker("^VIX").history(period="1y")
    if not vix_hist.empty:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=vix_hist.index, y=vix_hist["Close"],
            fill="tozeroy", fillcolor="rgba(255,68,68,0.1)",
            line=dict(color="#ff4444", width=1.5),
            name="VIX",
        ))
        fig2.add_hline(y=15, line_dash="dot", line_color="#00ff88", annotation_text="Low (15)")
        fig2.add_hline(y=30, line_dash="dot", line_color="#ff4444", annotation_text="High (30)")
        fig2.update_layout(
            height=250, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#ccc", xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Capital Deployment Panel ───────────────────────────────────────────
    if data:
        st.markdown("---")
        st.subheader("Capital Deployment Plan")

        from allocation import deployment_allocation
        alloc = deployment_allocation(
            total_capital=st.session_state.get("total_capital", 50000),
            macro_mode=data["mode"],
            macro_score=data["composite"],
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Capital", f"${alloc['total_capital']:,.0f}")
        c2.metric(
            "Deploy Now",
            f"${alloc['deploy_amt']:,.0f}",
            f"{alloc['deploy_pct']*100:.0f}% of capital",
        )
        c3.metric(
            "Keep as Cash",
            f"${alloc['cash_amt']:,.0f}",
            f"{alloc['cash_pct']*100:.0f}% reserve",
        )
        c4.metric(
            "Max Risk / Trade",
            f"${alloc['total_capital'] * st.session_state.get('risk_per_trade', 2.0) / 100:,.0f}",
            f"{st.session_state.get('risk_per_trade', 2.0):.1f}% of capital",
        )

        # Visual allocation bar
        deploy_pct = alloc["deploy_pct"] * 100
        cash_pct = alloc["cash_pct"] * 100
        st.markdown(
            f"""
            <div style='margin-top:16px;'>
                <div style='display:flex;justify-content:space-between;font-size:12px;color:#aaa;margin-bottom:4px;'>
                    <span>Deployed ({deploy_pct:.0f}%)</span>
                    <span>Cash Reserve ({cash_pct:.0f}%)</span>
                </div>
                <div style='background:#2a2a2a;border-radius:8px;height:24px;display:flex;overflow:hidden;'>
                    <div style='background:{data["color"]};width:{deploy_pct}%;height:24px;
                                display:flex;align-items:center;justify-content:center;
                                font-size:12px;font-weight:700;color:#000;'>
                        ${alloc['deploy_amt']:,.0f}
                    </div>
                    <div style='background:#1e2130;width:{cash_pct}%;height:24px;
                                display:flex;align-items:center;justify-content:center;
                                font-size:12px;color:#888;'>
                        ${alloc['cash_amt']:,.0f}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Per-position size table
        max_pos = st.session_state.get("max_positions", 8)
        base_size = alloc["deploy_amt"] / max_pos
        st.markdown(f"""
        <div style='margin-top:16px;background:#1e2130;border-radius:8px;padding:16px;font-size:13px;'>
            <div style='color:#aaa;margin-bottom:10px;font-weight:600;'>
                Position Size Guide — {max_pos} max positions, ${base_size:,.0f} base size
            </div>
            <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;'>
                <div style='background:#0d2a1a;border-radius:6px;padding:10px;text-align:center;'>
                    <div style='color:#00ff88;font-size:18px;font-weight:700;'>${base_size*1.5:,.0f}</div>
                    <div style='color:#aaa;font-size:11px;margin-top:2px;'>HIGH CONVICTION</div>
                    <div style='color:#555;font-size:10px;'>Score 85+ · 1.5x base</div>
                </div>
                <div style='background:#0d1a2a;border-radius:6px;padding:10px;text-align:center;'>
                    <div style='color:#88ccff;font-size:18px;font-weight:700;'>${base_size:,.0f}</div>
                    <div style='color:#aaa;font-size:11px;margin-top:2px;'>STANDARD</div>
                    <div style='color:#555;font-size:10px;'>Score 70–84 · 1x base</div>
                </div>
                <div style='background:#1a1a2a;border-radius:6px;padding:10px;text-align:center;'>
                    <div style='color:#888;font-size:18px;font-weight:700;'>${base_size*0.6:,.0f}</div>
                    <div style='color:#aaa;font-size:11px;margin-top:2px;'>SPECULATIVE</div>
                    <div style='color:#555;font-size:10px;'>Score 55–69 · 0.6x base</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 2 — QUANT SCANNER
# ════════════════════════════════════════════════════════════════════════════
elif page == "Quant Scanner":
    st.title("L2 — Quantitative Scanner")
    st.caption("5 factors · S&P 500 + tech universe + crypto · macro-gated activation")

    col1, col2 = st.columns([3, 1])
    with col2:
        min_score = st.slider("Min composite score", 0, 90, 60)
        show_crypto = st.checkbox("Include crypto", value=True)
        run_scan = st.button("Run Scanner", type="primary")

    if run_scan or "scanner_df" not in st.session_state:
        # Get macro mode first
        if "macro_data" not in st.session_state:
            from macro_gate import run as macro_run
            st.session_state["macro_data"] = macro_run()
        macro_mode = st.session_state["macro_data"]["mode"]

        with st.spinner(f"Scanning universe in {macro_mode} mode..."):
            from scanner.run_scanner import run as scanner_run
            df = scanner_run(macro_mode=macro_mode, min_score=min_score)
            if not show_crypto and not df.empty:
                df = df[df["asset_type"] != "crypto"]
            st.session_state["scanner_df"] = df

    df = st.session_state.get("scanner_df", pd.DataFrame())

    macro_data = st.session_state.get("macro_data", {})
    mode = macro_data.get("mode", "UNKNOWN")
    color = macro_data.get("color", "#888")

    col1.markdown(
        f"**Macro Mode:** <span style='color:{color};font-weight:700;'>{mode}</span> &nbsp;·&nbsp; "
        f"**{len(df)} candidates** above score {min_score}",
        unsafe_allow_html=True,
    )

    if df.empty:
        if mode == "DEFENSIVE":
            st.error("Scanner disabled — macro is DEFENSIVE. Protect capital.")
        else:
            st.info("No candidates found. Lower the min score or refresh.")
        st.stop()

    # Summary stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Candidates", len(df))
    c2.metric("Tech/AI Plays", int(df["is_tech"].sum()) if "is_tech" in df.columns else "—")
    c3.metric("Avg Score", f"{df['composite'].mean():.1f}")
    c4.metric("Crypto", int((df["asset_type"] == "crypto").sum()) if "asset_type" in df.columns else "—")

    st.markdown("---")

    # Color-coded table
    def style_score(val):
        if val >= 75:
            return "background-color: #0d2a1a; color: #00ff88"
        elif val >= 60:
            return "background-color: #0d1a2a; color: #88ccff"
        elif val >= 45:
            return "background-color: #2a200d; color: #ffaa00"
        return "background-color: #2a0d0d; color: #ff4444"

    display_cols = ["ticker", "price", "change_pct", "composite", "momentum", "volume",
                    "rel_strength", "w52_proximity", "short_interest", "asset_type"]
    display_cols = [c for c in display_cols if c in df.columns]

    styled = df[display_cols].style.map(style_score, subset=["composite"])
    st.dataframe(styled, use_container_width=True, height=500)

    # ── Position Sizing for top candidates ────────────────────────────────
    st.markdown("---")
    st.subheader("Position Sizing — How Much to Put In")

    from allocation import deployment_allocation, position_sizes, get_atr_pct
    alloc = deployment_allocation(
        total_capital=st.session_state.get("total_capital", 50000),
        macro_mode=macro_mode,
        macro_score=macro_data.get("composite", 50),
    )

    top_candidates = df.head(st.session_state.get("max_positions", 8)).copy()
    candidates_list = []
    for _, row in top_candidates.iterrows():
        atr = get_atr_pct(row["ticker"])
        candidates_list.append({
            "ticker": row["ticker"],
            "blended_score": row["composite"],
            "price": row["price"],
            "atr_pct": atr,
            "recommendation": "",
            "is_tech": row.get("is_tech", False),
        })

    sized = position_sizes(
        candidates=candidates_list,
        deploy_amt=alloc["deploy_amt"],
        max_positions=st.session_state.get("max_positions", 8),
        risk_per_trade_pct=st.session_state.get("risk_per_trade", 2.0),
        total_capital=st.session_state.get("total_capital", 50000),
    )

    if sized:
        size_df = pd.DataFrame(sized)
        size_df.index += 1

        def style_action(val):
            colors = {"ADD": "#0d2a1a", "HOLD": "#0d1a2a", "TRIM 25%": "#2a200d",
                      "TRIM 50%": "#2a1500", "EXIT": "#2a0d0d"}
            return f"background-color:{colors.get(val,'')}"

        cols_to_show = ["ticker", "entry_price", "shares", "position_value",
                        "stop_price", "stop_pct", "dollar_risk", "risk_pct_of_capital", "alloc_pct"]
        cols_to_show = [c for c in cols_to_show if c in size_df.columns]

        rename = {
            "entry_price": "Entry $",
            "shares": "Shares",
            "position_value": "Position $",
            "stop_price": "Stop $",
            "stop_pct": "Stop %",
            "dollar_risk": "$ at Risk",
            "risk_pct_of_capital": "% Capital at Risk",
            "alloc_pct": "% of Deploy",
        }
        st.dataframe(
            size_df[cols_to_show].rename(columns=rename),
            use_container_width=True,
        )
        total_deployed = size_df["position_value"].sum()
        total_risk = size_df["dollar_risk"].sum()
        st.markdown(
            f"**Total deployed:** ${total_deployed:,.0f} &nbsp;·&nbsp; "
            f"**Total $ at risk:** ${total_risk:,.0f} &nbsp;·&nbsp; "
            f"**Cash remaining:** ${alloc['total_capital'] - total_deployed:,.0f}",
            unsafe_allow_html=True,
        )

    # Factor breakdown chart for top 15
    st.markdown("---")
    st.subheader("Factor Breakdown — Top 15")
    top15 = df.head(15)
    factor_cols = [c for c in ["momentum", "volume", "rel_strength", "w52_proximity", "short_interest"] if c in top15.columns]
    fig = go.Figure()
    colors_factors = ["#88ccff", "#00ff88", "#ffaa00", "#ff88cc", "#aa88ff"]
    for i, factor in enumerate(factor_cols):
        fig.add_trace(go.Bar(
            name=factor.replace("_", " ").title(),
            x=top15["ticker"],
            y=top15[factor],
            marker_color=colors_factors[i % len(colors_factors)],
        ))
    fig.update_layout(
        barmode="group", height=350,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#ccc", xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222", range=[0, 100]),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 3 — CLAUDE ANALYST
# ════════════════════════════════════════════════════════════════════════════
elif page == "Claude Analyst":
    st.title("L3 — Claude Analyst")
    st.caption("Fundamental quality · 60% quant / 40% AI blend · rank delta = alpha signal")

    col1, col2 = st.columns([3, 1])
    with col2:
        max_analyze = st.slider("Max stocks to analyze", 5, 30, 15)
        run_analysis = st.button("Run Analysis", type="primary")

    if run_analysis or "blended_df" not in st.session_state:
        if "scanner_df" not in st.session_state or st.session_state["scanner_df"].empty:
            if "macro_data" not in st.session_state:
                from macro_gate import run as macro_run
                st.session_state["macro_data"] = macro_run()
            from scanner.run_scanner import run as scanner_run
            st.session_state["scanner_df"] = scanner_run(macro_mode=st.session_state["macro_data"]["mode"])

        with st.spinner(f"Analyzing top {max_analyze} candidates with Claude..."):
            from analyst.blender import blend
            blended = blend(st.session_state["scanner_df"], max_analyze=max_analyze)
            st.session_state["blended_df"] = blended

    blended = st.session_state.get("blended_df", pd.DataFrame())

    if blended.empty:
        st.info("No analysis data. Run the scanner first, then run analysis.")
        st.stop()

    col1.markdown(f"**{len(blended)} candidates analyzed** — green glow = upgraded by AI, red = downgraded")

    # Rank delta highlights
    upgraded = blended[blended["rank_delta"] >= 3] if "rank_delta" in blended.columns else pd.DataFrame()
    downgraded = blended[blended["rank_delta"] <= -3] if "rank_delta" in blended.columns else pd.DataFrame()

    if not upgraded.empty:
        st.success(f"AI upgrades (quant underrated): **{', '.join(upgraded['ticker'].tolist())}**")
    if not downgraded.empty:
        st.warning(f"AI downgrades (quant overrated): **{', '.join(downgraded['ticker'].tolist())}**")

    st.markdown("---")

    # Main blended table
    display_cols = ["ticker", "quant_score", "fund_score", "blended_score",
                    "recommendation", "conviction", "rank_delta", "rank_flag"]
    display_cols = [c for c in display_cols if c in blended.columns]

    def color_rec(val):
        colors = {"BUY": "background-color:#0d2a1a;color:#00ff88",
                  "HOLD": "background-color:#2a200d;color:#ffaa00",
                  "AVOID": "background-color:#2a0d0d;color:#ff4444"}
        return colors.get(val, "")

    styled = blended[display_cols].style.map(color_rec, subset=["recommendation"] if "recommendation" in display_cols else [])
    st.dataframe(styled, use_container_width=True, height=400)

    # Expandable detail per stock
    st.markdown("---")
    st.subheader("Individual Analysis")
    for _, row in blended.head(10).iterrows():
        analysis = row.get("analysis", {})
        if not analysis:
            continue
        rec = analysis.get("recommendation", "")
        with st.expander(
            f"{'🟢' if rec == 'BUY' else '🟡' if rec == 'HOLD' else '🔴'} {row['ticker']} — "
            f"Blended: {row['blended_score']:.0f} | {rec} {'●' * analysis.get('conviction', 0)}"
        ):
            c1, c2 = st.columns(2)
            dims = [
                ("earnings_quality", "Earnings Quality"),
                ("growth_trajectory", "Growth Trajectory"),
                ("balance_sheet", "Balance Sheet"),
                ("margin_trends", "Margin Trends"),
                ("red_flags", "Red Flags"),
            ]
            for i, (key, label) in enumerate(dims):
                dim = analysis.get(key, {})
                if dim:
                    with (c1 if i % 2 == 0 else c2):
                        s = dim.get("score", 5) * 10
                        st.markdown(f"**{label}:** {dim.get('score', '—')}/10")
                        st.progress(s / 100)
                        st.caption(dim.get("rationale", ""))

            st.markdown(f"**Summary:** {analysis.get('summary', '')}")
            if analysis.get("key_risk"):
                st.markdown(f"**Key Risk:** {analysis.get('key_risk')}")

            fins = analysis.get("financials", {})
            if fins:
                st.markdown("**Financials:**")
                fin_cols = {
                    "revenue_growth_yoy": "Revenue Growth YoY",
                    "gross_margin": "Gross Margin",
                    "operating_margin": "Op. Margin",
                    "debt_to_equity": "D/E Ratio",
                    "return_on_equity": "ROE",
                    "forward_pe": "Forward P/E",
                    "analyst_upside_pct": "Analyst Upside",
                }
                fin_data = {v: fins.get(k) for k, v in fin_cols.items() if fins.get(k) is not None}
                if fin_data:
                    st.dataframe(
                        pd.DataFrame([fin_data]),
                        use_container_width=True,
                        hide_index=True,
                    )


# ════════════════════════════════════════════════════════════════════════════
# PAGE 4 — WATCHLIST
# ════════════════════════════════════════════════════════════════════════════
elif page == "Positions":
    st.title("Open Positions & Add/Trim Signals")
    st.caption("Track what you own · get told when to add, trim, or exit")

    from allocation import add_trim_signals, deployment_allocation

    # ── Add a position ─────────────────────────────────────────────────────
    with st.expander("+ Add / Update Position", expanded=len(st.session_state.get("positions", [])) == 0):
        c1, c2, c3, c4, c5 = st.columns(5)
        new_ticker   = c1.text_input("Ticker").upper().strip()
        new_shares   = c2.number_input("Shares", min_value=0.01, value=10.0, step=1.0)
        new_entry    = c3.number_input("Entry Price $", min_value=0.01, value=100.0, step=0.5)
        new_stop     = c4.number_input("Stop Price $", min_value=0.01, value=90.0, step=0.5)
        new_score    = c5.number_input("Score at Entry", min_value=0.0, max_value=100.0, value=70.0, step=1.0)
        if st.button("Add Position") and new_ticker:
            if "positions" not in st.session_state:
                st.session_state["positions"] = []
            # Update if exists
            existing = [p for p in st.session_state["positions"] if p["ticker"] != new_ticker]
            existing.append({
                "ticker": new_ticker,
                "shares": new_shares,
                "entry_price": new_entry,
                "stop_price": new_stop,
                "entry_score": new_score,
            })
            st.session_state["positions"] = existing
            st.success(f"Added {new_ticker}")

    positions = st.session_state.get("positions", [])

    if not positions:
        st.info("No positions yet. Add your first position above.")
        st.stop()

    # Fetch current prices
    import yfinance as yf
    live_positions = []
    for pos in positions:
        try:
            hist = yf.Ticker(pos["ticker"]).history(period="2d")
            current_price = float(hist["Close"].iloc[-1]) if not hist.empty else pos["entry_price"]
        except Exception:
            current_price = pos["entry_price"]
        live_positions.append({**pos, "current_price": round(current_price, 2)})

    # Get add/trim signals
    macro_data = st.session_state.get("macro_data", {})
    scanner_df = st.session_state.get("blended_df", st.session_state.get("scanner_df"))
    signals = add_trim_signals(
        positions=live_positions,
        scanner_df=scanner_df,
        macro_score=macro_data.get("composite", 50),
        macro_mode=macro_data.get("mode", "NORMAL"),
    )

    # ── Summary metrics ────────────────────────────────────────────────────
    total_value   = sum(p["current_price"] * p["shares"] for p in live_positions)
    total_cost    = sum(p["entry_price"]   * p["shares"] for p in live_positions)
    total_pnl     = total_value - total_cost
    total_capital = st.session_state.get("total_capital", 50000)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Positions", len(positions))
    c2.metric("Total Invested", f"${total_cost:,.0f}")
    c3.metric("Current Value", f"${total_value:,.0f}", f"${total_pnl:+,.0f}")
    c4.metric("Cash Remaining", f"${total_capital - total_cost:,.0f}",
              f"{(total_capital - total_cost)/total_capital*100:.0f}% of capital")

    st.markdown("---")

    # ── Action cards ───────────────────────────────────────────────────────
    for sig in signals:
        color = sig["action_color"]
        pnl_color = "#00ff88" if sig["pnl_pct"] >= 0 else "#ff4444"

        with st.container():
            st.markdown(
                f"""
                <div style='background:#1e2130;border-radius:10px;padding:16px;margin-bottom:12px;
                            border-left:4px solid {color};'>
                    <div style='display:flex;justify-content:space-between;align-items:center;'>
                        <div>
                            <span style='font-size:20px;font-weight:800;color:#fff;'>{sig['ticker']}</span>
                            &nbsp;
                            <span style='background:{color};color:#000;padding:3px 10px;border-radius:4px;
                                         font-weight:700;font-size:13px;'>{sig['action']}</span>
                        </div>
                        <div style='text-align:right;'>
                            <span style='font-size:18px;font-weight:700;color:{pnl_color};'>
                                {sig['pnl_pct']:+.1f}%
                            </span>
                            &nbsp;
                            <span style='font-size:13px;color:{pnl_color};'>
                                (${sig['pnl_dollars']:+,.0f})
                            </span>
                        </div>
                    </div>
                    <div style='margin-top:8px;display:grid;grid-template-columns:repeat(5,1fr);gap:8px;'>
                        <div style='font-size:11px;color:#aaa;'>Entry<br><span style='color:#fff;font-size:13px;'>${sig['entry_price']:.2f}</span></div>
                        <div style='font-size:11px;color:#aaa;'>Current<br><span style='color:#fff;font-size:13px;'>${sig['current_price']:.2f}</span></div>
                        <div style='font-size:11px;color:#aaa;'>Stop<br><span style='color:#ff4444;font-size:13px;'>${sig['stop_price']:.2f}</span></div>
                        <div style='font-size:11px;color:#aaa;'>To Stop<br><span style='color:#ffaa00;font-size:13px;'>{sig['distance_to_stop_pct']:.1f}%</span></div>
                        <div style='font-size:11px;color:#aaa;'>Shares<br><span style='color:#fff;font-size:13px;'>{sig['shares']:.0f}</span></div>
                    </div>
                    <div style='margin-top:8px;font-size:12px;color:#aaa;'>
                        <span style='color:#888;'>Reason:</span> {sig['reason']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Remove position ────────────────────────────────────────────────────
    st.markdown("---")
    remove = st.multiselect("Remove closed positions", [p["ticker"] for p in positions])
    if remove:
        st.session_state["positions"] = [p for p in positions if p["ticker"] not in remove]
        st.rerun()


elif page == "Watchlist":
    st.title("Watchlist & Positions")
    st.caption("Track your tech/AI/robotics focus names · add positions manually")

    DEFAULT_WATCHLIST = [
        "NVDA", "AMD", "MSFT", "GOOGL", "META", "PLTR", "IONQ", "TSLA",
        "AVGO", "TSM", "AMZN", "ARM", "SMCI", "RKLB", "RGTI",
    ]

    if "watchlist" not in st.session_state:
        st.session_state["watchlist"] = DEFAULT_WATCHLIST.copy()

    # Add/remove tickers
    col1, col2 = st.columns([3, 1])
    with col1:
        new_ticker = st.text_input("Add ticker to watchlist", placeholder="e.g. CRWD").upper().strip()
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add") and new_ticker:
            if new_ticker not in st.session_state["watchlist"]:
                st.session_state["watchlist"].append(new_ticker)

    remove = st.multiselect("Remove from watchlist", st.session_state["watchlist"])
    if remove:
        st.session_state["watchlist"] = [t for t in st.session_state["watchlist"] if t not in remove]

    st.markdown("---")

    if st.button("Refresh Watchlist Data", type="primary") or "watchlist_df" not in st.session_state:
        tickers = st.session_state["watchlist"]
        rows = []
        with st.spinner("Loading watchlist..."):
            for ticker in tickers:
                try:
                    t = yf.Ticker(ticker)
                    hist = t.history(period="3mo")
                    info = t.info or {}
                    if hist.empty:
                        continue
                    price = hist["Close"].iloc[-1]
                    prev = hist["Close"].iloc[-2]
                    change = (price / prev - 1) * 100
                    high52 = hist["Close"].rolling(min(252, len(hist))).max().iloc[-1]
                    low52 = hist["Close"].rolling(min(252, len(hist))).min().iloc[-1]
                    ema10 = hist["Close"].ewm(span=10).mean().iloc[-1]
                    ema50 = hist["Close"].ewm(span=50).mean().iloc[-1]
                    trend = "↑ Above" if ema10 > ema50 else "↓ Below"
                    rows.append({
                        "Ticker": ticker,
                        "Price": round(price, 2),
                        "Change %": round(change, 2),
                        "EMA Signal": trend,
                        "52W High": round(high52, 2),
                        "52W Low": round(low52, 2),
                        "% from High": round((price / high52 - 1) * 100, 1),
                        "Mkt Cap": info.get("marketCap", ""),
                        "Sector": info.get("sector", ""),
                    })
                except Exception:
                    continue
        st.session_state["watchlist_df"] = pd.DataFrame(rows)

    wdf = st.session_state.get("watchlist_df", pd.DataFrame())
    if not wdf.empty:
        def style_change(val):
            if isinstance(val, float):
                return "color:#00ff88" if val > 0 else "color:#ff4444"
            return ""

        def style_ema(val):
            if "Above" in str(val):
                return "color:#00ff88"
            return "color:#ff4444"

        styled = wdf.style.map(style_change, subset=["Change %", "% from High"]) \
                          .map(style_ema, subset=["EMA Signal"])
        st.dataframe(styled, use_container_width=True, height=450)

        # Mini charts for top picks
        st.markdown("---")
        st.subheader("Price Charts — Top 6")
        top6 = st.session_state["watchlist"][:6]
        cols = st.columns(3)
        for i, ticker in enumerate(top6):
            with cols[i % 3]:
                hist = yf.Ticker(ticker).history(period="6mo")
                if hist.empty:
                    continue
                ema10 = hist["Close"].ewm(span=10).mean()
                ema50 = hist["Close"].ewm(span=50).mean()
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], name="Price",
                                         line=dict(color="#88ccff", width=1.5)))
                fig.add_trace(go.Scatter(x=hist.index, y=ema10, name="EMA10",
                                         line=dict(color="#00ff88", width=1, dash="dot")))
                fig.add_trace(go.Scatter(x=hist.index, y=ema50, name="EMA50",
                                         line=dict(color="#ffaa00", width=1, dash="dot")))
                fig.update_layout(
                    title=ticker, height=200,
                    margin=dict(l=0, r=0, t=30, b=0),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#ccc", showlegend=False,
                    xaxis=dict(gridcolor="#1a1a2a", showticklabels=False),
                    yaxis=dict(gridcolor="#1a1a2a"),
                )
                st.plotly_chart(fig, use_container_width=True)
