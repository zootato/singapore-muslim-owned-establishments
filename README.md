<<<<<<< HEAD

# Singapore Muslim-Owned Establishments

Lightweight scraper to collect the "Muslim Owned" directory data from
https://www.muslimownedsg.com/explore/

## What this repo contains

- `scraper.py` — simple HTML scraper using `requests` + `beautifulsoup4` that paginates search results and extracts place name and URL.
- `requirements.txt` — minimal Python dependencies.

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

3. Review and adjust selectors in `scraper.py` if the site layout changes.

## Notes

- The site markup may change — update CSS selectors in `parse_results()` accordingly.
- For large crawls, respect robots.txt and the site's terms of service.
- If you'd like, I can add a GitHub Action to run this periodically and commit results to the repo.
