import yfinance as yf

# Default watchlist shown on the dashboard when no specific symbols are requested.
# Add/remove tickers here. Indian NSE stocks need ".NS", BSE needs ".BO", US stocks need no suffix.
DEFAULT_SYMBOLS = ["TCS.NS", "INFY.NS", "HDFCBANK.NS", "RELIANCE.NS", "ICICIBANK.NS"]


def _build_stock_entry(symbol, ticker):
    """Pull live data for one ticker and shape it into the response dict."""
    info = ticker.fast_info  # lightweight, fast live snapshot (no full history call)

    current_price = info.last_price
    previous_close = info.previous_close
    change = current_price - previous_close if previous_close else 0
    change_percent = (change / previous_close * 100) if previous_close else 0

    # Trend based on 1-month average vs current price
    hist = ticker.history(period="1mo")
    avg_price = hist["Close"].mean() if not hist.empty else current_price
    trend = "Bullish" if current_price > avg_price else "Bearish"

    # yfinance's .info is slower but has the display name; fall back gracefully
    try:
        name = ticker.info.get("shortName") or ticker.info.get("longName") or symbol
    except Exception:
        name = symbol

    return {
        "symbol": symbol,
        "name": name,
        "price": round(float(current_price), 2),
        "previousClose": round(float(previous_close), 2) if previous_close else None,
        "change": round(float(change), 2),
        "changePercent": round(float(change_percent), 2),
        "dayHigh": round(float(info.day_high), 2) if info.day_high else None,
        "dayLow": round(float(info.day_low), 2) if info.day_low else None,
        "volume": int(info.last_volume) if info.last_volume else None,
        "currency": info.currency,
        "trend": trend,
    }


def get_stock_suggestions(symbols=None):
    """
    Returns live data for a list of symbols (defaults to DEFAULT_SYMBOLS).
    Skips any symbol that fails instead of crashing the whole request,
    and reports which ones failed.
    """
    symbols = symbols or DEFAULT_SYMBOLS
    results = []
    errors = []

    for s in symbols:
        try:
            ticker = yf.Ticker(s)
            results.append(_build_stock_entry(s, ticker))
        except Exception as e:
            errors.append({"symbol": s, "error": str(e)})
            continue

    return {"stocks": results, "errors": errors}


def get_stock_quote(symbol):
    """Single-symbol live quote. Raises on failure so the route can return a clean 404/502."""
    ticker = yf.Ticker(symbol)
    return _build_stock_entry(symbol, ticker)


def get_stock_history(symbol, period="1mo", interval="1d"):
    """
    Historical OHLCV candles for charting.
    period: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
    interval: 1m,5m,15m,30m,1h,1d,1wk,1mo (intraday intervals only work with short periods)
    """
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period, interval=interval)

    candles = []
    for date, row in hist.iterrows():
        candles.append({
            "date": date.isoformat(),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
        })

    return {"symbol": symbol, "candles": candles}


def search_stocks(query):
    """Symbol lookup for a search bar."""
    search_result = yf.Search(query, max_results=8)
    return [
        {
            "symbol": q.get("symbol"),
            "name": q.get("shortname") or q.get("longname"),
            "exchange": q.get("exchange"),
            "type": q.get("quoteType"),
        }
        for q in search_result.quotes
        if q.get("symbol")
    ]
