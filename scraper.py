# scraper.py
import requests
import json
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)
openai = OpenAI()
MODEL = "gpt-4o-mini"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_links(url: str) -> list[str]:
    """Fetch all links from a webpage."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            # convert relative to absolute
            if href.startswith("/"):
                from urllib.parse import urlparse
                base = urlparse(url)
                href = f"{base.scheme}://{base.netloc}{href}"
            if href.startswith("http"):
                links.append(href)
        return list(set(links))  # deduplicate
    except Exception as e:
        print(f"Error fetching links from {url}: {e}")
        return []


link_system_prompt = """
You are provided with a list of links found on a fund provider webpage.
Identify links most relevant for fund due diligence research, such as:
- Factsheet PDFs
- KID / KIID documents
- Fund description or overview pages
- Performance or portfolio pages

Respond in JSON only, exactly like this example:
{
    "documents": [
        {"type": "factsheet", "url": "https://full.url/factsheet.pdf"},
        {"type": "KID", "url": "https://full.url/kid.pdf"},
        {"type": "fund_page", "url": "https://full.url/fund-overview"}
    ]
}

Only include highly relevant links. Do not include login pages, 
privacy policies, social media, or generic navigation links.
"""

def select_relevant_links(url: str) -> dict:
    """Use LLM to filter links relevant for fund research."""
    links = fetch_links(url)
    if not links:
        return {"documents": []}

    print(f"Found {len(links)} total links, filtering with LLM...")

    user_prompt = f"""
Here are links found on the fund page: {url}

Please identify which are relevant for fund due diligence research.
Respond with full URLs in JSON format.

Links:
{chr(10).join(links[:150])}
"""
    # cap at 150 links to stay within token limits

    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )

    result = response.choices[0].message.content
    return json.loads(result)


def fetch_page_text(url: str) -> str:
    """Fetch readable text content from a webpage."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # remove noise
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        print(f"Error fetching page text from {url}: {e}")
        return ""


def download_pdf(url: str, save_path: str) -> bool:
    """Download a PDF from a URL and save locally."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {save_path}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


if __name__ == "__main__":
    test_url = "https://www.lupusalpha.com/products/fund/lupus-alpha-all-opportunities-fund-a/"
    print(f"Scraping: {test_url}\n")
    results = select_relevant_links(test_url)
    print("Relevant documents found:")
    for doc in results.get("documents", []):
        print(f"  [{doc['type']}] {doc['url']}")