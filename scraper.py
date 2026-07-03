import requests
import re
import csv
import os

SCRAPE_URL = "https://nairobipostalcode.org/nairobi-matatu-routes/"
CSV_FILE = "scraped_routes.csv"

def _clean(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&#8211;", "\u2013").replace("&amp;", "&")
    text = text.replace("&nbsp;", " ").replace("\u2013", " \u2013 ")
    return re.sub(r"\s+", " ", text).strip()

def _fetch_page():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }
    resp = requests.get(SCRAPE_URL, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text


def _extract_routes(html):
    routes = []
    pattern = (
        r'<h3[^>]*>(.*?Line.*?Routes.*?)</h3>'
        r'.*?<figure class="wp-block-table">'
        r'(.*?)</figure>'
    )
    tables = re.findall(pattern, html, re.DOTALL)

    for h3, fig in tables:
        line = re.sub(r"<[^>]+>", "", h3).strip()
        tbody = re.search(r"<tbody>(.*?)</tbody>", fig, re.DOTALL)
        if not tbody:
            continue
        rows = re.findall(r"<tr>(.*?)</tr>", tbody.group(1), re.DOTALL)
        for row in rows:
            tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
            if len(tds) >= 2:
                rn = _clean(tds[0])
                dest = _clean(tds[1])
                if rn and dest:
                    routes.append((line, rn, dest))
    return routes


def _extract_sacco_names(html):
    sacco_section = re.search(
        r"Prominent Matatu SACCOs.*?(?=FAQs About|Matatu Fares|<h2)",
        html, re.DOTALL
    )
    if not sacco_section:
        return []
    h3s = re.findall(
        r"<h3[^>]*>(.*?)</h3>", sacco_section.group(0), re.DOTALL
    )
    names = [_clean(h) for h in h3s]
    return [n for n in names if n and "Fare" not in n and "Line" not in n]


def _extract_fares(html):
    fares = {}
    fare_section = re.search(
        r"Matatu Fares in Nairobi.*?(?=FAQs About|<h2)", html, re.DOTALL
    )
    if not fare_section:
        return {}
    section = fare_section.group(0)
    items = re.findall(r"<li>(.*?)</li>", section, re.DOTALL)
    for item in items:
        clean = _clean(item)
        m = re.search(r"Ksh\s*(\d+)\s*\u2013\s*(\d+)", clean, re.IGNORECASE)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            label = clean.split(":")[0].strip().lower() if ":" in clean else ""
            fares[label] = (lo, hi)
    paras = re.findall(
        r"<h3[^>]*>(.*?)</h3>.*?<p>(.*?)</p>", section, re.DOTALL
    )
    for h3, p in paras:
        clean_h3 = _clean(h3)
        clean_p = _clean(p)
        m = re.search(r"Ksh\s*(\d+)\s*\u2013\s*(\d+)", clean_p, re.IGNORECASE)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            fares[clean_h3.lower()] = (lo, hi)
    return fares


def _assign_sacco(destination, line):
    dest_lower = destination.lower()
    for name, code, keywords in SACCO_INFO:
        for kw in keywords:
            if kw in dest_lower:
                return name, code
    if "nairobi cbd" in dest_lower or "city" in dest_lower:
        return "Citi Hoppa", "CH"
    return "NACICO", "NC"


def _assign_fare(destination):
    dest_lower = destination.lower()
    for keywords, lo, hi in FARE_ZONES:
        for kw in keywords:
            if kw in dest_lower:
                return lo, hi
    return UNKNOWN_FARE


def _split_start_end(line, destination):
    dest = destination
    if "\u2013" in dest:
        parts = [p.strip() for p in dest.split("\u2013", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            return parts[0], parts[1]
    return "Nairobi CBD", dest


def scrape_route_data():
    try:
        html = _fetch_page()
    except requests.exceptions.RequestException:
        return None

    raw_routes = _extract_routes(html)
    if not raw_routes:
        return None

    saccos_from_page = _extract_sacco_names(html)
    fare_info = _extract_fares(html)

    results = []
    for line, rn, dest in raw_routes:
        start, end = _split_start_end(line, dest)
        sacco_name, sacco_code = _assign_sacco(dest, line)
        fare_min, fare_max = _assign_fare(dest)

        results.append({
            "line": line.replace(" Routes", "").replace(" (Mixed Routes)", ""),
            "route_number": rn,
            "start": start,
            "end": end,
            "sacco": sacco_name,
            "sacco_code": sacco_code,
            "fare_min": fare_min,
            "fare_max": fare_max,
        })

    return results

def write_csv(data, filepath=CSV_FILE):
    if not data:
        return False
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "line", "route_number", "start", "end",
            "sacco", "sacco_code", "fare_min", "fare_max"
        ])
        w.writeheader()
        w.writerows(data)
    return True

def load_csv(filepath=CSV_FILE):
    if not os.path.exists(filepath):
        return None
    with open(filepath, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def extract_fare_amount(text):
    m = re.search(r"Ksh\s*(\d+)\s*-?\s*(\d*)", text, re.IGNORECASE)
    if m:
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else lo
        return (lo + hi) // 2
    return None

def clean_route_text(text):
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s\-/]", "", text)
    return text.strip()

SITUATIONS_URL = "https://situations.co.ke/matatu-bus-fares-from-nairobi/"

def _fetch_with_retry(url, timeout=30):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def _parse_fare_value(raw):
    raw = raw.replace(",", "").replace("Ksh", "").replace("ksh", "").strip()
    m = re.search(r"(\d+)\s*[-to]*\s*(\d*)", raw)
    if m:
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else lo
        return lo, hi
    return None, None

def scrape_situations_routes():
    try:
        html = _fetch_with_retry(SITUATIONS_URL)
    except requests.exceptions.RequestException:
        return None

    results = []
    blocks = re.findall(
        r'<h2[^>]*class="wp-block-heading"[^>]*>(.*?)</h2>'
        r'.*?<figure[^>]*class="wp-block-table"[^>]*>'
        r'(.*?)</figure>',
        html, re.DOTALL
    )

    for h2, fig in blocks:
        heading = re.sub(r"<[^>]+>", "", h2).strip()
        m = re.search(r"Fare from Nairobi to (.+)", heading)
        if not m:
            continue
        destination = m.group(1).strip()

        tbody = re.search(r"<tbody>(.*?)</tbody>", fig, re.DOTALL)
        if not tbody:
            continue
        rows = re.findall(r"<tr>(.*?)</tr>", tbody.group(1), re.DOTALL)

        for row in rows:
            tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
            if len(tds) < 2:
                continue
            sacco = re.sub(r"<[^>]+>", "", tds[0]).strip()
            fare_raw = re.sub(r"<[^>]+>", "", tds[-1]).strip()
            if not sacco or not fare_raw:
                continue
            lo, hi = _parse_fare_value(fare_raw)
            if lo is None:
                continue
            results.append({
                "destination": destination,
                "sacco": sacco,
                "fare_min": lo,
                "fare_max": hi or lo,
            })

    return results

ELIMUCENTRE_URL = "https://www.elimucentre.com/registered-matatu-sacco-operating-in-nairobi/"


def scrape_elimucentre_saccos():
    try:
        html = _fetch_with_retry(ELIMUCENTRE_URL)
    except requests.exceptions.RequestException:
        return None

    names = set()
    for m in re.finditer(r'<strong>(.*?)</strong>', html):
        text = m.group(1).strip()
        text = re.sub(r'<[^>]+>', '', text)
        if re.match(r'^\d+\.?\s', text):
            name = re.sub(r'^\d+\.?\s*', '', text).strip()
            if name and ('SACCO' in name.upper() or 'TRANSPORT' in name.upper()):
                names.add(name)

    if not names:
        for m in re.finditer(r'(?:^|\n)\s*(\d+)\.\s+([A-Z][A-Za-z0-9\s&/\-]+?)(?:\s*[–\-~]\s|\s*-\s|\.\s)', html):
            name = m.group(2).strip()
            if name and ('SACCO' in name.upper() or 'TRANSPORT' in name.upper()):
                names.add(name)

    return sorted(names) if names else None
