# enricher.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

BENCHMARK_PROXIES = {
    "stoxx europe small": "EXSH.DE",
    "msci europe small": "IEUS",
    "msci europe": "IMEU.AS",
    "stoxx europe 600": "EXSA.DE",
    "msci world": "IWDA.AS",
    "mdax": "EXS3.DE",
    "sdax": "EXS3.DE",
    "mdax sdax": "EXS3.DE",
    "default": "EXSH.DE"
}

def get_benchmark_ticker(benchmark_hint: str) -> str:
    hint = benchmark_hint.lower()
    for key, ticker in BENCHMARK_PROXIES.items():
        if key in hint:
            return ticker
    return BENCHMARK_PROXIES["default"]


def fetch_benchmark_performance(ticker: str, as_of_date: str = None) -> dict:
    try:
        etf = yf.Ticker(ticker)
        hist = etf.history(period="6y")
        hist = hist.dropna(subset=["Close"])

        if hist.empty:
            return {"error": f"No data for ticker {ticker}"}

        # anchor to factsheet date if provided
        if as_of_date:
            try:
                anchor = pd.Timestamp(
                    datetime.strptime(as_of_date, "%d.%m.%Y")
                ).tz_localize(hist.index.tz)
                hist_to_anchor = hist[hist.index <= anchor]
                if hist_to_anchor.empty:
                    return {"error": "No data up to factsheet date"}
                now_date = hist_to_anchor.index[-1]
                now_price = hist_to_anchor["Close"].iloc[-1]
            except Exception as e:
                print(f"Date anchoring failed: {e}, falling back to latest")
                now_date = hist.index[-1]
                now_price = hist["Close"].iloc[-1]
        else:
            now_date = hist.index[-1]
            now_price = hist["Close"].iloc[-1]

        one_year_ago = now_date - timedelta(days=365)
        three_years_ago = now_date - timedelta(days=3*365)

        hist_1y = hist[hist.index >= one_year_ago]
        hist_3y = hist[hist.index >= three_years_ago]

        if hist_1y.empty or hist_3y.empty:
            return {"error": "Insufficient history"}

        price_1y = hist_1y["Close"].iloc[0]
        price_3y = hist_3y["Close"].iloc[0]

        perf_1y = ((now_price - price_1y) / price_1y) * 100
        perf_3y = ((now_price - price_3y) / price_3y) * 100

        return {
            "ticker": ticker,
            "current_price": round(float(now_price), 2),
            "performance_1y_pct": round(float(perf_1y), 2),
            "performance_3y_pct": round(float(perf_3y), 2),
            "data_as_of": now_date.strftime("%Y-%m-%d")
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_fund_ticker_data(ticker: str) -> dict:
    try:
        fund = yf.Ticker(ticker)
        info = fund.info
        if not info or "shortName" not in info:
            return {"error": "No ticker data found"}
        return {
            "name": info.get("shortName", ""),
            "aum": info.get("totalAssets", "N/A"),
            "ter": info.get("annualReportExpenseRatio", "N/A"),
            "ytd_return": info.get("ytdReturn", "N/A"),
            "category": info.get("category", "N/A")
        }
    except Exception as e:
        return {"error": str(e)}


def enrich(benchmark_hint: str = "", fund_ticker: str = "", as_of_date: str = None) -> dict:
    result = {}
    ticker = get_benchmark_ticker(benchmark_hint)
    print(f"Fetching benchmark data for: {ticker} anchored to {as_of_date or 'latest'}")
    result["benchmark"] = fetch_benchmark_performance(ticker, as_of_date=as_of_date)
    if fund_ticker:
        print(f"Fetching fund ticker data for: {fund_ticker}")
        result["fund"] = fetch_fund_ticker_data(fund_ticker)
    return result


def format_enrichment_for_llm(enrichment: dict) -> str:
    lines = ["## Market Context (via yFinance)\n"]
    bm = enrichment.get("benchmark", {})
    if "error" not in bm:
        lines.append(f"**Benchmark Proxy ({bm.get('ticker', '')}) — anchored to factsheet date:**")
        lines.append(f"- 1Y Performance: {bm.get('performance_1y_pct', 'N/A')}%")
        lines.append(f"- 3Y Performance: {bm.get('performance_3y_pct', 'N/A')}%")
        lines.append(f"- Data as of: {bm.get('data_as_of', 'N/A')}")
    else:
        lines.append(f"Benchmark data unavailable: {bm.get('error')}")

    fund = enrichment.get("fund", {})
    if fund and "error" not in fund:
        lines.append(f"\n**Fund Data ({fund.get('name', '')}):**")
        lines.append(f"- AUM: {fund.get('aum', 'N/A')}")
        lines.append(f"- TER: {fund.get('ter', 'N/A')}")
        lines.append(f"- YTD Return: {fund.get('ytd_return', 'N/A')}")

    return "\n".join(lines)


if __name__ == "__main__":
    enrichment = enrich(benchmark_hint="stoxx europe small", as_of_date="29.05.2026")
    print(format_enrichment_for_llm(enrichment))