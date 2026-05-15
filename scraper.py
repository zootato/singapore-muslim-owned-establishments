"""Scraper for MuslimOwnedSG places.

Usage:
  python scraper.py --out data/establishments.json

Note: CSS selectors may require tuning if the site changes. This script fetches paginated
search results and extracts basic fields: name, url, and snippet when available.
"""

import argparse
import json
import os
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.muslimownedsg.com/explore/"
HEADERS = {"User-Agent": "makcik-fatimah-scraper/1.0 (+https://github.com/zootato)"}


def fetch_page(params=None):
    resp = requests.get(BASE_URL, params=params or {}, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text


def parse_results(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []

    # Try a few common selectors used by listing sites. Adjust if needed.
    selectors = [
        "a.place-card",
        "div.place-card a",
        ".listing .place a",
        ".result a",
        "a[href*='/place/']",
    ]

    seen = set()
    for sel in selectors:
        for a in soup.select(sel):
            href = a.get("href")
            if not href:
                continue
            url = urljoin(BASE_URL, href)
            name = a.get_text(strip=True)
            if not name:
                # try alt/title
                name = a.get("title") or ""
            key = (name, url)
            if key in seen:
                continue
            seen.add(key)
            items.append({"name": name, "url": url})
        if items:
            break

    # Fallback: look for article/place elements
    if not items:
        for el in soup.select("article, .place, .card"):
            a = el.find("a")
            if not a:
                continue
            href = a.get("href")
            url = urljoin(BASE_URL, href)
            name = a.get_text(strip=True)
            key = (name, url)
            if key in seen:
                continue
            seen.add(key)
            items.append({"name": name, "url": url})

    return items


def scrape(max_pages=10, delay=1.0):
    results = []
    page = 1
    while page <= max_pages:
        params = {"type": "place", "tab": "search-form", "page": page}
        try:
            html = fetch_page(params)
        except Exception as e:
            print(f"Failed to fetch page {page}: {e}")
            break

        items = parse_results(html)
        if not items:
            break

        results.extend(items)
        print(f"Page {page}: found {len(items)} items")
        page += 1
        time.sleep(delay)

    # dedupe by url
    seen = set()
    dedup = []
    for it in results:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        dedup.append(it)

    return dedup


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="data/establishments.json")
    p.add_argument("--max-pages", type=int, default=20)
    p.add_argument("--delay", type=float, default=0.5)
    args = p.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    data = scrape(max_pages=args.max_pages, delay=args.delay)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(data)} records to {args.out}")


if __name__ == "__main__":
    main()
