# Fund Lens

An automated fund due diligence brief generator for institutional investors.

Given a fund provider URL, Fund Lens scrapes the fund page, downloads the factsheet PDF, extracts structured data, enriches it with live benchmark data, and generates a professional due diligence brief using GPT-4o.

## Example Output

**Lupus alpha All Opportunities Fund — Due Diligence Brief**

> The fund employs a long-short equity strategy focused on ~2,000 European small and mid-cap securities. 1Y return of 23.90% vs benchmark proxy (EXSH.DE) of 32.16%. VaR 95 (10-day): -4.42%. TER: 2.26%. Recommendation: Requires Further Due Diligence.

## Architecture

```
URL Input
    → scraper.py       # fetch HTML links, LLM filters for factsheet/KID/reports
    → scraper.py       # download factsheet PDF
    → parser.py        # pdfplumber extracts text and tables, regex cleans key fields
    → enricher.py      # yFinance pulls benchmark ETF proxy performance
    → main.ipynb       # GPT-4o assembles structured DD brief with streaming output
    → briefs/          # markdown brief saved with fund name and date
```

## Brief Structure

Each generated brief covers:
- **Fund at a Glance** — AUM, manager, domicile, inception, SFDR classification
- **Investment Strategy** — universe, process, key differentiators
- **Portfolio Characteristics** — style, allocation, net equity exposure
- **Performance** — all periods vs benchmark proxy
- **Risk Profile** — volatility, Sharpe, max drawdown, VaR 95/99, correlation
- **Costs** — TER, management fee, performance fee, hurdle rate, high-watermark
- **Analyst Verdict** — suitability assessment with explicit recommendation

## Stack

- Python 3.12
- OpenAI GPT-4o
- pdfplumber — PDF text and table extraction
- requests + BeautifulSoup — HTML scraping
- yFinance — benchmark ETF proxy data
- python-dotenv — environment management

## Setup

```bash
git clone https://github.com/matsveikachatkou/fund-lens
cd fund-lens
uv sync
cp .env.example .env  # add your OPENAI_API_KEY
```

## Usage

Open `main.ipynb` and run all cells. Edit the final cell to target any fund:

```python
build_brief(
    fund_name="Lupus alpha All Opportunities Fund",
    url="https://www.lupusalpha.com/products/fund/lupus-alpha-all-opportunities-fund-a/",
    benchmark_hint="stoxx europe small"
)
```

The `benchmark_hint` is matched against a built-in dictionary of ETF proxies.
Supported hints: `stoxx europe small`, `msci europe small`, `msci europe`, `stoxx europe 600`, `msci world`.

## Limitations

- Geographic and sector allocation data in factsheets is often rendered as charts — not extractable as text by pdfplumber
- Active UCITS funds typically have no ticker — benchmark comparison uses ETF proxies
- Some fund provider websites require JavaScript rendering — Playwright fallback not yet implemented
- Tested on Lupus alpha factsheet format — other providers may need regex adjustments

## Related Projects

- [equity-lens](https://github.com/matsveikachatkou/equity-lens) — 6-agent CrewAI pipeline for global equity screening
- [edgar-research-rag](https://github.com/matsveikachatkou/edgar-research-rag) — RAG pipeline over SEC EDGAR filings