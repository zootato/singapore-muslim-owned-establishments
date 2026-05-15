# Singapore Muslim-Owned Establishments

Lightweight scraper to collect the "Muslim Owned" directory data from
https://www.muslimownedsg.com/explore/

## What this repo contains

- `scraper.py` — AJAX-powered scraper using `requests` + `beautifulsoup4` that fetches MyListing search results and extracts place name, URL, category, and category type.
- `requirements.txt` — minimal Python dependencies.
- `data/establishments.json` — scraped output.

## Quickstart

1. Create a venv and install deps:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

2. Run the scraper and save output:

```bash
python scraper.py --out data/establishments.json --max-pages 10
```

3. If needed, update selectors in `parse_results()` to match future layout changes.

## Notes

- This scraper uses the site’s AJAX `get_listings` action and parses the returned HTML.
- Places under restaurants/cafes are classified as `food`; other categories are classified as `service`.
- The scraper also visits individual record pages to capture address, latitude/longitude, telephone, email, price range, opening hours, tags, and description when available.
- For larger crawls, respect the site’s terms of service and rate-limit requests.
- Current output is closer to bot compatibility because it now includes address and coordinates, but the bot may still need cuisine or halal-type fields for full integration.
