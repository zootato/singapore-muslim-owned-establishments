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
import re
from typing import Optional, List

BASE_URL = "https://www.muslimownedsg.com/explore/"
HEADERS = {"User-Agent": "makcik-fatimah-scraper/1.0 (+https://github.com/zootato)"}


def get_ajax_info():
    """Return (ajax_url, ajax_nonce) discovered from the Explore page."""
    r = requests.get(BASE_URL + '?type=place&sort=latest', headers=HEADERS, timeout=20)
    text = r.text
    ajax_url = None
    nonce = None
    m = re.search(r'mylisting_ajax_url"\s*:\s*"([^"]+)"', text)
    if m:
        ajax_url = m.group(1).replace('\\/', '/')
    # fallback to known path
    if not ajax_url:
        ajax_url = '?mylisting-ajax=1'
    # find ajax_nonce in CASE27 or other objects
    m2 = re.search(r'ajax_nonce"\s*:\s*"([0-9a-fA-F]+)"', text)
    if m2:
        nonce = m2.group(1)
    else:
        m3 = re.search(r'ajax_nonce"\s*:\s*"([^"]+)"', text)
        if m3:
            nonce = m3.group(1)
    return ajax_url, nonce


def ajax_request(ajax_url, filters: dict, nonce: Optional[str]):
    """Call MyListing `get_listings` action and return listing HTML."""
    # build base URL
    if ajax_url.startswith('/'):
        base = BASE_URL.rstrip('/') + ajax_url
    elif ajax_url.startswith('?'):
        base = BASE_URL.rstrip('/') + '/' + ajax_url.lstrip('/')
    else:
        base = ajax_url

    sep = '&' if '?' in base else '?'
    if nonce:
        url = f"{base}{sep}action=get_listings&security={nonce}"
    else:
        url = f"{base}{sep}action=get_listings"

    # serialize filters as form_data[...] like jQuery would
    params = {'listing_type': 'place'}
    for k, v in filters.items():
        params[f'form_data[{k}]'] = v

    hdrs = dict(HEADERS)
    hdrs.update({'X-Requested-With': 'XMLHttpRequest', 'Referer': BASE_URL})

    try:
        r = requests.get(url, params=params, headers=hdrs, timeout=20)
    except Exception:
        return ''

    # try parse JSON response
    try:
        j = r.json()
        if isinstance(j, dict):
            html = j.get('html')
            if html:
                return html
            # WordPress wp_send_json_success() wraps payload under 'data'
            data = j.get('data') or j.get('results')
            if isinstance(data, str):
                return data
            if isinstance(data, dict):
                return data.get('html', '')
            return ''
    except Exception:
        pass

    return r.text or ''


def _clean_text(value):
    if not value:
        return ''
    return BeautifulSoup(str(value), 'html.parser').get_text(' ', strip=True)


def _load_jsonld(html):
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            raw = script.string
            if not raw:
                continue
            data = json.loads(raw)
        except Exception:
            continue

        if isinstance(data, dict) and data.get('@type') == 'LocalBusiness':
            return data
        if isinstance(data, dict) and '@graph' in data:
            for item in data['@graph']:
                if isinstance(item, dict) and item.get('@type') == 'LocalBusiness':
                    return item
    return {}


def _extract_categories(soup):
    cats = []
    for el in soup.select('.block-type-categories .category-name, .block-type-categories li a span'):
        name = el.get_text(strip=True)
        if name:
            cats.append(name)
    if cats:
        return '; '.join(dict.fromkeys(cats))
    # fallback: generic category anchors
    for el in soup.select('a[href*="/category/"]'):
        name = el.get_text(strip=True)
        if name:
            cats.append(name)
    return '; '.join(dict.fromkeys(cats))


def _extract_tags(soup):
    return [el.get_text(strip=True) for el in soup.select('.block-type-tags li a span') if el.get_text(strip=True)]


def _extract_description(soup):
    block = soup.select_one('.block-type-text.block-field-job_description .pf-body')
    if block:
        return _clean_text(block)
    ld = _load_jsonld(str(soup))
    return _clean_text(ld.get('description', ''))


def fetch_detail(url):
    try:
        r = requests.get(url, headers={**HEADERS, 'Referer': BASE_URL}, timeout=20)
        r.raise_for_status()
    except Exception:
        return {
            'address': '',
            'latitude': '',
            'longitude': '',
            'telephone': '',
            'email': '',
            'price_range': '',
            'opening_hours': [],
            'same_as': [],
            'tags': [],
            'description': '',
        }

    html = r.text
    soup = BeautifulSoup(html, 'html.parser')
    ld = _load_jsonld(html)

    address = ''
    if isinstance(ld.get('address'), dict):
        address = ld['address'].get('address', '') or ld['address'].get('streetAddress', '') or ''
    elif isinstance(ld.get('address'), str):
        address = ld['address']

    geo = ld.get('geo', {})
    latitude = str(geo.get('latitude')) if geo else ''
    longitude = str(geo.get('longitude')) if geo else ''

    telephone = ld.get('telephone', '') or ''
    email = ld.get('email', '') or ''
    price_range = ld.get('priceRange', '') or ''
    opening_hours = ld.get('openingHours', []) or []
    same_as = ld.get('sameAs', []) or []
    if isinstance(same_as, str):
        same_as = [same_as]

    category = _extract_categories(soup)
    tags = _extract_tags(soup)
    description = _extract_description(soup)

    return {
        'address': address,
        'latitude': latitude,
        'longitude': longitude,
        'telephone': telephone,
        'email': email,
        'price_range': price_range,
        'opening_hours': opening_hours,
        'same_as': same_as,
        'tags': tags,
        'description': description,
        'category': category,
    }


def parse_results(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    seen = set()

    # Primary containers used by MyListing's explore response
    containers = soup.select('.lf-item-container, .lf-item, .listing-preview, .listing-card, .c27-grid-item, .listing-item')
    if not containers:
        # fallback to anchors
        for a in soup.select("a[href*='/place/'], a[href*='/places/']"):
            href = a.get('href')
            if not href:
                continue
            url = urljoin(BASE_URL, href)
            name = a.get_text(strip=True) or (a.get('title') or '')
            key = (name, url)
            if key in seen:
                continue
            seen.add(key)
            items.append({'name': name, 'url': url, 'category': '', 'category_type': 'service'})
        return items

    for el in containers:
        a = el.find('a', href=True)
        if not a:
            continue
        url = urljoin(BASE_URL, a['href'])
        title_el = el.find(['h1', 'h2', 'h3', 'h4']) or a
        name = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)

        # category detection from data attributes or category links
        cat = el.get('data-category') or el.get('data-category-text') or ''
        if not cat:
            cat_el = el.select_one('.listing__categories a, .cats a, .listing-cats a, .listing-category a, .cat, .category a')
            if cat_el:
                cat = cat_el.get_text(strip=True)

        cat_lower = (cat or '').lower()
        if any(k in cat_lower for k in ('restaurant', 'restaurants', 'cafe', 'cafes', 'food', 'eat')):
            ctype = 'food'
        else:
            ctype = 'service'

        key = (name, url)
        if key in seen:
            continue
        seen.add(key)
        items.append({'name': name, 'url': url, 'category': cat, 'category_type': ctype})

    return items


def _classify_type(category: str, tags: List[str]):
    text = (category or '') + ' ' + ' '.join(tags or [])
    text = text.lower()
    for keyword in ('restaurant', 'restaurants', 'cafe', 'cafes', 'food', 'eat', 'dining', 'bistro', 'bakery', 'coffee'):
        if re.search(rf'\b{re.escape(keyword)}\b', text):
            return 'food'
    return 'service'


def scrape(max_pages=10, delay=1.0, fetch_details=True, detail_delay=0.2):
    results = []
    ajax_url, nonce = get_ajax_info()
    filters = {'page': 0, 'preserve_page': False, 'search_keywords': '', 'category': '', 'region': '', 'tags': '', 'sort': 'latest'}
    page = 0
    while page < max_pages:
        filters['page'] = page
        html = ajax_request(ajax_url, filters, nonce)
        if not html or html.strip() == '':
            print(f'Page {page}: empty response, stopping')
            break

        items = parse_results(html)
        if not items:
            print(f'Page {page}: no items parsed, stopping')
            break

        if fetch_details:
            for item in items:
                detail = fetch_detail(item['url'])
                item.update(detail)
                if detail.get('category'):
                    item['category'] = detail['category']
                item['category_type'] = _classify_type(item.get('category', ''), item.get('tags', []))
                time.sleep(detail_delay)
        else:
            for item in items:
                item['category_type'] = _classify_type(item.get('category', ''), [])

        results.extend(items)
        print(f'Page {page}: found {len(items)} items')
        page += 1
        time.sleep(delay)

    # dedupe by url
    seen = set()
    dedup = []
    for it in results:
        if it['url'] in seen:
            continue
        seen.add(it['url'])
        dedup.append(it)

    return dedup


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="data/establishments.json")
    p.add_argument("--max-pages", type=int, default=20)
    p.add_argument("--delay", type=float, default=0.5)
    p.add_argument("--detail-delay", type=float, default=0.2)
    p.add_argument("--no-details", action='store_true', help="Skip fetching individual record pages")
    args = p.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    data = scrape(
        max_pages=args.max_pages,
        delay=args.delay,
        fetch_details=not args.no_details,
        detail_delay=args.detail_delay,
    )
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(data)} records to {args.out}")


if __name__ == "__main__":
    main()
