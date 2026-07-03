from database import insert_sacco, insert_route, insert_fare, route_exists
from scraper import scrape_route_data, write_csv, load_csv, scrape_situations_routes, scrape_elimucentre_saccos

CSV_FILE = "scraped_routes.csv"

DATES = ["2023-06-01", "2024-01-15", "2025-06-01", "2026-01-15"]


def _get_or_create_sacco(name, code=None):
    if not code:
        words = name.upper().split()
        code = "".join(w[0] for w in words if w)[:4]
    sacco_id, is_new = insert_sacco(name, code)
    return sacco_id, is_new


def _seed_from_csv(rows, route_type='local'):
    counts = {"saccos": 0, "routes": 0, "fares": 0}
    sacco_cache = {}

    for row in rows:
        name = row["sacco"]
        code = row["sacco_code"]
        if name not in sacco_cache:
            sacco_cache[name], is_new = _get_or_create_sacco(name, code)
            if is_new:
                counts["saccos"] += 1

    seen = set()
    for row in rows:
        sacco_id = sacco_cache[row["sacco"]]
        rid = row["route_number"]
        start = row["start"]
        end = row["end"]
        key = (rid, start, end, sacco_id, route_type)
        if key in seen:
            continue
        seen.add(key)

        fare_min = int(row["fare_min"])
        fare_max = int(row["fare_max"])

        existing = route_exists(rid, start, end, sacco_id, route_type)
        if existing:
            route_db_id = existing
        else:
            route_db_id = insert_route(rid, start, end, sacco_id, fare_min, fare_max, route_type)
            counts["routes"] += 1
        mid = (fare_min + fare_max) // 2
        for i, date in enumerate(DATES):
            amount = fare_min if i == 0 else (fare_max if i == 3 else mid)
            insert_fare(route_db_id, amount, date=date)
            counts["fares"] += 1

    return counts


def _seed_long_distance():
    counts = {"saccos": 0, "routes": 0, "fares": 0}

    data = scrape_situations_routes()
    if not data:
        return counts

    sacco_cache = {}
    dest_counters = {}

    for entry in data:
        dest = entry["destination"]
        sacco_name = entry["sacco"]

        if sacco_name not in sacco_cache:
            sacco_cache[sacco_name], is_new = _get_or_create_sacco(sacco_name)
            if is_new:
                counts["saccos"] += 1

        sacco_id = sacco_cache[sacco_name]

        if dest not in dest_counters:
            dest_counters[dest] = 1
        route_number = f"LD-{dest.upper().replace(' ', '')}-{dest_counters[dest]}"
        dest_counters[dest] += 1

        start = "Nairobi"
        end = dest
        fare_min = entry["fare_min"]
        fare_max = entry["fare_max"]

        existing = route_exists(route_number, start, end, sacco_id, 'long_distance')
        if existing:
            route_db_id = existing
        else:
            route_db_id = insert_route(route_number, start, end, sacco_id, fare_min, fare_max, 'long_distance')
            counts["routes"] += 1

        mid = (fare_min + fare_max) // 2
        for i, date in enumerate(DATES):
            amount = fare_min if i == 0 else (fare_max if i == 3 else mid)
            insert_fare(route_db_id, amount, date=date)
            counts["fares"] += 1

    return counts

def _seed_more_saccos():
    names = scrape_elimucentre_saccos()
    if not names:
        return 0

    count = 0
    for name in names:
        try:
            _, is_new = _get_or_create_sacco(name)
            if is_new:
                count += 1
        except Exception:
            pass
    return count

def seed_database():
    total = {"saccos": 0, "routes": 0, "fares": 0}

    csv_rows = load_csv(CSV_FILE)
    if csv_rows:
        c = _seed_from_csv(csv_rows, 'local')
    else:
        scraped = scrape_route_data()
        if scraped:
            write_csv(scraped, CSV_FILE)
            c = _seed_from_csv(scraped, 'local')
        else:
            c = {"saccos": 0, "routes": 0, "fares": 0}

    for k in total:
        total[k] += c[k]

    c = _seed_long_distance()
    for k in total:
        total[k] += c[k]

    extra = _seed_more_saccos()
    total["saccos"] += extra

    return total
