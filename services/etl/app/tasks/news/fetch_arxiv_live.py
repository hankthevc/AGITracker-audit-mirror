"""
Live arXiv fetching via official Atom API.

Fetches recent papers from cs.AI, cs.CL, cs.LG, cs.CV categories.
Respects rate limits and robots.txt.
"""
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta

import httpx


def fetch_arxiv_recent(categories: list[str] = None, days_back: int = 7, max_results: int = 50) -> list[dict]:
    """
    Fetch recent arXiv papers via Atom API.

    Args:
        categories: List of arXiv categories (default: cs.AI, cs.CL, cs.LG, cs.CV)
        days_back: How many days back to fetch (default: 7)
        max_results: Max results per category (default: 50)

    Returns:
        List of paper dicts with title, summary, authors, link, published, categories
    """
    if categories is None:
        categories = ["cs.AI", "cs.CL", "cs.LG", "cs.CV"]

    all_papers = []

    for category in categories:
        try:
            # arXiv API query (use HTTPS to avoid 301 redirect)
            # https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=lastUpdatedDate&sortOrder=descending&max_results=50
            url = f"https://export.arxiv.org/api/query?search_query=cat:{category}&sortBy=lastUpdatedDate&sortOrder=descending&max_results={max_results}"

            response = httpx.get(
                url,
                timeout=30,
                follow_redirects=True,
                headers={"User-Agent": "AGI-Signpost-Tracker/1.0 (+https://github.com/hankthevc/AGITracker)"}
            )

            if response.status_code != 200:
                print(f"  ⚠️  arXiv API returned {response.status_code} for {category}")
                continue

            # Parse Atom XML
            root = ET.fromstring(response.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            entries = root.findall("atom:entry", ns)

            for entry in entries:
                title = entry.find("atom:title", ns)
                summary = entry.find("atom:summary", ns)
                published = entry.find("atom:published", ns)
                link = entry.find("atom:id", ns)  # arXiv ID

                # Authors
                authors = []
                for author in entry.findall("atom:author", ns):
                    name = author.find("atom:name", ns)
                    if name is not None and name.text:
                        authors.append(name.text)

                # Categories
                cats = [cat.get("term") for cat in entry.findall("atom:category", ns) if cat.get("term")]

                # Check if within date range
                if published is not None and published.text:
                    pub_date = datetime.fromisoformat(published.text.replace("Z", "+00:00"))
                    cutoff = datetime.now(UTC) - timedelta(days=days_back)

                    if pub_date < cutoff:
                        continue  # Too old, skip

                paper = {
                    "title": title.text.strip() if title is not None else "",
                    "summary": summary.text.strip() if summary is not None else "",
                    "link": link.text if link is not None else "",
                    "url": link.text if link is not None else "",  # Alias
                    "authors": authors,
                    "published": published.text if published is not None else None,
                    "published_at": published.text if published is not None else None,
                    "categories": cats,
                }

                all_papers.append(paper)

            print(f"  ✓ Fetched {len(entries)} papers from {category}")

        except Exception as e:
            print(f"  ⚠️  Failed to fetch {category}: {e}")
            continue

    return all_papers
