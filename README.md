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
- The scraper visits each listing's record page to capture richer fields when available: address, latitude/longitude, telephone, email, price range, opening hours, tags, and description.
- The repository includes a small static UI for browsing results at `index.html` and a GitHub Actions workflow that runs the scraper and publishes the repo to the `gh-pages` branch on a schedule (`.github/workflows/scrape-and-pages.yml`).
- The scraper workflow and UI live in this subfolder (`singapore-muslim-owned-establishments`). The Fly deployment workflow was removed from the repository root per request; there is no Fly pipeline in this repo now.
- For larger crawls, respect the site’s terms of service and rate-limit requests (use `--delay` and `--detail-delay`).
- Current output includes address and coordinates and is closer to the bot's needs, but the Mak Cik Fatimah bot may still require additional `cuisine` or `halal_type` fields for full compatibility.

## Local run (example)

Create a venv and run the scraper locally with a short delay between requests:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python scraper.py --out data/establishments.json --max-pages 50 --delay 0.5 --detail-delay 0.2
```

Data is written to `data/establishments.json` and the UI reads that file from `index.html`.
