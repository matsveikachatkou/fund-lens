# Fund Lens

An automated fund due diligence brief generator for institutional investors.

Given a fund provider URL, Fund Lens scrapes the fund page, downloads the factsheet PDF, extracts structured data, enriches it with live benchmark data anchored to the factsheet date, and generates a professional due diligence brief using GPT-4o.

## Example Output

**Lupus alpha CLO High Quality Invest — Due Diligence Brief**

> The fund invests in a diversified portfolio of investment-grade CLOs with ESG integration, targeting money market +2.5% p.a. 1Y return of 4.26% vs benchmark proxy (IS0R.DE) of 4.46%. 3Y outperformance: 22.03% vs 17.83%. TER: 0.71%. No performance fee.
>
> **Recommendation: Suitable** — consistent performance against targets and low cost structure.

## Design Philosophy

Fund Lens is intentionally conservative. The Analyst Verdict is a **first-pass screening tool** designed to triage funds for deeper human review, not replace the analyst. "Requires Further Due Diligence" is the correct output when data is ambiguous, performance is inconsistent, or costs are elevated — this is not a limitation but a feature. A screening tool that approves every fund is useless.

## Architecture

```
URL Input
    → scraper.py       # fetch HTML links, LLM filters for factsheet/KID/reports
    → scraper.py       # download factsheet PDF
    → parser.py        # pdfplumber extracts text and tables, regex cleans key fields
    → enricher.py      # yFinance pulls benchmark ETF proxy anchored to factsheet date
    → main.ipynb       # GPT-4o assembles structured DD brief with streaming output
    → briefs/          # markdown brief saved with fund name and date
```

## Brief Structure

Each generated brief covers:
- **Fund at a Glance** — AUM, manager, domicile, inception, SFDR classification
- **Investment Strategy** — universe, process, key differentiators
- **Portfolio Characteristics** — style, allocation, net equity exposure
- **Performance** — all periods vs benchmark proxy, anchored to factsheet date
- **Risk Profile** — volatility, Sharpe, max drawdown, VaR 95/99, correlation
- **Costs** — TER, management fee, performance fee, hurdle rate, high-watermark
- **Analyst Verdict** — first-pass suitability assessment with explicit recommendation

## Stack

- Python 3.12
- OpenAI GPT-4o
- pdfplumber — PDF text and table extraction
- requests + BeautifulSoup — HTML scraping
- yFinance — benchmark ETF proxy data anchored to factsheet date
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
    fund_name="Lupus alpha CLO High Quality Invest",
    url="https://www.lupusalpha.com/products/fund/lupus-alpha-clo-high-quality-invest-a/",
    benchmark_hint="clo"
)
```

The `benchmark_hint` is matched against a built-in dictionary of ETF proxies.
Supported hints: `stoxx europe small`, `msci europe small`, `msci europe`,
`stoxx europe 600`, `msci world`, `mdax sdax`, `clo`, `money market`, `credit`,
`eurozone small`, `euro stoxx tmi`.

For funds on JavaScript-heavy sites (e.g. DWS), download the factsheet manually
and use the `local_factsheet_path` parameter to bypass the scraper:

```python
build_brief(
    fund_name="DWS Concept Kaldemorgen",
    url="https://funds.dws.com/en-ie/...",
    benchmark_hint="msci world",
    local_factsheet_path="briefs/DWS_Concept_Kaldemorgen_factsheet.pdf"
)
```

## Limitations

- Geographic and sector allocation data in factsheets is often rendered as charts — not extractable as text by pdfplumber
- Active UCITS funds typically have no ticker — benchmark comparison uses ETF proxies
- Benchmark proxy must be selected manually via `benchmark_hint` — wrong hint produces misleading comparisons
- Some fund provider websites require JavaScript rendering (e.g. DWS) — use `local_factsheet_path` as workaround; Playwright fallback not yet implemented
- Tested primarily on Lupus alpha factsheet format — other providers may require regex adjustments in `parser.py`

## Related Projects

- [equity-lens](https://github.com/matsveikachatkou/equity-lens) — 6-agent CrewAI pipeline for global equity screening
- [edgar-research-rag](https://github.com/matsveikachatkou/edgar-research-rag) — RAG pipeline over SEC EDGAR filings