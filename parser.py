# parser.py
import pdfplumber

def parse_factsheet(pdf_path: str) -> dict:
    sections = {
        "raw_text": [],
        "tables": []
    }

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            try:
                text = page.extract_text()
                if text:
                    sections["raw_text"].append(f"--- Page {i+1} ---\n{text}")

                tables = page.extract_tables()
                for t, table in enumerate(tables):
                    sections["tables"].append(f"--- Page {i+1}, Table {t+1} ---")
                    for row in table:
                        cleaned = [cell or "" for cell in row]
                        if any(cleaned):
                            sections["tables"].append(" | ".join(cleaned))
            except Exception as e:
                sections["raw_text"].append(f"--- Page {i+1} ERROR: {e} ---")

    return sections


def extract_factsheet_date(sections: dict) -> str:
    """Extract the 'as of' date from the factsheet."""
    import re
    raw = "\n".join(sections["raw_text"])
    # matches patterns like "29.05.2026" or "Stand: 29.05.2026"
    match = re.search(r'(\d{2}\.\d{2}\.\d{4})', raw)
    if match:
        return match.group(1)
    return None


def extract_key_fields(sections: dict) -> str:
    import re
    raw = "\n".join(sections["raw_text"])
    hints = []

    # VaR - extract from the line after the header
    var_match = re.search(
        r'VaR 95 -10 VaR 99 - 10 Sharpe Ratio Max\. Drawdown\s+([\d.]+%)\s+([-\d.]+%)\s+([-\d.]+%)\s+([-\d.]+%)\s+([\d.]+)\s+([-\d.]+%)',
        raw
    )
    if var_match:
        hints.append("## Key Risk Figures (extracted)")
        hints.append(f"- Volatility p.a.: {var_match.group(1)}")
        hints.append(f"- Max Loss 90 days: {var_match.group(2)}")
        hints.append(f"- VaR 95 (10-day, 95% confidence): {var_match.group(3)}")
        hints.append(f"- VaR 99 (10-day, 99% confidence): {var_match.group(4)}")
        hints.append(f"- Sharpe Ratio: {var_match.group(5)}")
        hints.append(f"- Max Drawdown: {var_match.group(6)}")

    # geography note
    hints.append("\n## Note on Geographic/Sector Allocation")
    hints.append("Geographic and sector allocation data is presented as charts in the factsheet and could not be extracted as text. Do not guess these values — write 'Available in factsheet charts only'.")

    return "\n".join(hints)


def format_for_llm(sections: dict) -> str:
    output = "## Extracted Text\n\n"
    output += "\n".join(sections["raw_text"])
    output += "\n\n## Extracted Tables\n\n"
    output += "\n".join(sections["tables"])
    output += "\n\n" + extract_key_fields(sections)
    return output


if __name__ == "__main__":
    path = "briefs/Factsheet.pdf"
    sections = parse_factsheet(path)
    formatted = format_for_llm(sections)
    print(f"Total characters extracted: {len(formatted)}")
    with open("briefs/parser_test_output.txt", "w") as f:
        f.write(formatted)
    print("Output written to briefs/parser_test_output.txt")