import os
import sys

from database import (
    create_tables, get_all_saccos, get_all_routes, search_routes,
    get_route_fares, get_latest_fare, insert_fare, insert_route,
    route_exists, export_routes_to_csv
)
from seed_data import seed_database
from weather_api import get_weather, get_fare_alert, is_rainy, validate_kenyan_city, KENYAN_TOWNS
from scraper import SCRAPE_URL, scrape_route_data, write_csv, load_csv, extract_fare_amount, clean_route_text
from models import SACCO, Route, Fare

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def hr(title):
    print()
    print("=" * 52)
    print(f"  {title}")
    print("=" * 52)

def pause():
    input("\nPress Enter to continue...")

def _route_type_filter():
    print()
    print("  Filter by:")
    print("  [1] Local routes (Nairobi only)")
    print("  [2] Long-distance routes")
    print("  [3] All routes")
    choice = input("  Select: ").strip()
    if choice == "1":
        return "local"
    elif choice == "2":
        return "long_distance"
    return None

def view_routes():
    rt = _route_type_filter()
    label = "ALL" if rt is None else ("LOCAL" if rt == "local" else "LONG-DISTANCE")
    routes = get_all_routes(rt)
    if not routes:
        print(f"No {label.lower()} routes found. Use option 9 to seed the database.")
        return

    hr(f"{label} MATATU ROUTES")
    print(f"{'ID':<4} {'Route':<18} {'From':<18} {'To':<18} {'SACCO':<24} {'Fare Min':<10} {'Fare Max':<10}")
    print("-" * 102)
    for db_id, route_number, start, end, name, code, fmin, fmax, rtype in routes:
        sacco_display = f"{name} ({code})"
        fmin_s = f"KSh {fmin}" if fmin else "N/A"
        fmax_s = f"KSh {fmax}" if fmax else "N/A"
        print(f"{db_id:<4} {route_number:<18} {start:<18} {end:<18} {sacco_display:<24} {fmin_s:<10} {fmax_s:<10}")

    print()
    print("--- Latest Fares ---")
    for db_id, route_number, start, end, name, code, *_ in routes:
        latest = get_latest_fare(db_id)
        if latest:
            amount, date, _ = latest
            print(f"  Route {route_number}: KSh {amount} (as of {date})")
        else:
            print(f"  Route {route_number}: No fare data")

def search_routes_menu():
    term = input("Search by route number, location, or SACCO: ").strip()
    if not term:
        print("Please enter a search term.")
        return

    rt = _route_type_filter()
    label = "ALL" if rt is None else ("LOCAL" if rt == "local" else "LONG-DISTANCE")
    results = search_routes(term, rt)
    if not results:
        print(f"No results found for '{term}' ({label}).")
        return

    hr(f"SEARCH RESULTS ({label}): '{term}'")
    for db_id, route_number, start, end, name, code, fmin, fmax, rtype in results:
        sacco_display = f"{name} ({code})"
        fm = f"  [KSh {fmin} - KSh {fmax}]" if fmin and fmax else ""
        print(f"  Route {route_number}: {start} -> {end} [{sacco_display}]{fm}")

def route_details():
    rt = _route_type_filter()
    label = "ALL" if rt is None else ("LOCAL" if rt == "local" else "LONG-DISTANCE")
    routes = get_all_routes(rt)
    if not routes:
        print(f"No {label.lower()} routes. Seed the database first.")
        return

    print(f"Available routes ({label}):")
    for db_id, route_number, start, end, name, code, fmin, fmax, rtype in routes:
        fare_range = f" [KSh {fmin}-{fmax}]" if fmin and fmax else ""
        print(f"  [{db_id}] Route {route_number}: {start} -> {end}{fare_range}")

    try:
        choice = int(input("\nEnter route ID: "))
    except ValueError:
        print("Invalid input. Enter a number.")
        return

    selected = None
    for r in routes:
        if r[0] == choice:
            selected = r
            break

    if not selected:
        print("Invalid route ID.")
        return

    db_id, route_number, start, end, name, code, fmin, fmax, rtype = selected

    hr(f"ROUTE {route_number}: {start} -> {end}")
    print(f"  SACCO: {name} ({code})")
    print(f"  Type: {rtype.replace('_', ' ').title()}")
    fmin_s = f"KSh {fmin}" if fmin else "N/A"
    fmax_s = f"KSh {fmax}" if fmax else "N/A"
    print(f"  Fare Min: {fmin_s}")
    print(f"  Fare Max: {fmax_s}")
    print()

    fares = get_route_fares(db_id)
    if fares:
        print("  Fare History:")
        for fare_id, amount, date, weather in fares:
            weather_str = f" ({weather})" if weather else ""
            print(f"    KSh {amount} - {date}{weather_str}")
    else:
        print("  No fare records for this route.")

def weather_check():
    city = input("Enter city (default Nairobi): ").strip() or "Nairobi"
    matched = validate_kenyan_city(city)
    if not matched:
        print(f"'{city}' is not a recognized Kenyan town.")
        print("Valid towns:", ", ".join(sorted(KENYAN_TOWNS)))
        return
    city = matched
    print(f"\nFetching weather for {city}...")

    weather = get_weather(city)

    if weather:
        hr(f"WEATHER: {weather['city'].upper()}")
        print(f"  Temperature: {weather['temperature']:.1f} C")
        print(f"  Condition: {weather['description'].title()}")
        print(f"  Humidity: {weather['humidity']}%")
        print()
        print(f"  {get_fare_alert(weather)}")

        if is_rainy(weather):
            print()
            print("  Routes likely affected:")
            for db_id, rid, start, end, name, code, *_ in get_all_routes()[:5]:
                print(f"    Route {rid}: {start} -> {end}")
    else:
        print("Could not fetch live weather. Using demo data...")
        demo = {
            "city": city, "temperature": 22.5,
            "description": "light rain", "humidity": 78,
            "condition": "Rain"
        }
        print(get_fare_alert(demo))


def add_fare():
    rt = _route_type_filter()
    label = "ALL" if rt is None else ("LOCAL" if rt == "local" else "LONG-DISTANCE")
    routes = get_all_routes(rt)
    if not routes:
        print(f"No {label.lower()} routes. Seed the database first.")
        return

    print(f"Select a route ({label}):")
    for db_id, route_number, start, end, name, code, fmin, fmax, rtype in routes:
        fm = f" [KSh {fmin} - KSh {fmax}]" if fmin and fmax else ""
        print(f"  [{db_id}] Route {route_number}: {start} -> {end} ({name}){fm}")

    try:
        rid = int(input("\nEnter route ID: "))
        amount = int(input("Enter fare amount (KSh): "))
    except ValueError:
        print("Please enter valid numbers.")
        return

    if amount <= 0:
        print("Fare must be a positive number.")
        return

    tag = input("Tag with current weather? (y/n): ").strip().lower()
    weather = None
    if tag == "y":
        w = get_weather("Nairobi")
        if w:
            weather = w["condition"]
            print(f"Weather recorded: {weather}")

    insert_fare(rid, amount, weather=weather)
    print(f"Fare recorded: KSh {amount} for route ID {rid}")


def add_route():
    saccos = get_all_saccos()
    if not saccos:
        print("No SACCOs. Seed the database first.")
        return

    print("Available SACCOs:")
    for sid, name, code in saccos:
        print(f"  [{sid}] {name} ({code})")

    try:
        sid = int(input("\nSelect SACCO ID: "))
    except ValueError:
        print("Invalid input.")
        return

    valid = any(s[0] == sid for s in saccos)
    if not valid:
        print("Invalid SACCO selection.")
        return

    route_number = input("Route number (e.g., 114): ").strip()
    start = input("Starting point: ").strip()
    end = input("Destination: ").strip()

    if not route_number or not start or not end:
        print("All fields are required.")
        return

    print()
    print("Route type:")
    print("  [1] Local (Nairobi area)")
    print("  [2] Long-distance")
    type_choice = input("Select: ").strip()
    route_type = "long_distance" if type_choice == "2" else "local"

    existing = route_exists(route_number, start, end, sid, route_type)
    if existing:
        print("This route already exists in the database.")
        return

    insert_route(route_number, start, end, sid, route_type=route_type)
    print(f"Route {route_number}: {start} -> {end} added! (Type: {route_type})")


def export_csv():
    filename = "matatu_routes_export.csv"
    ok = export_routes_to_csv(filename)
    if ok:
        full_path = os.path.abspath(filename)
        print(f"Data exported to: {full_path}")
    else:
        print("No data to export. Seed the database first.")


def scrape_web():
    hr("WEB SCRAPING")
    print(f"Fetching from {SCRAPE_URL} ...")
    data = scrape_route_data()

    if not data:
        print("Could not scrape data (offline or site changed).")
        print("Use option 9 to seed from built-in data.")
        return

    saccos = set(r['sacco'] for r in data)
    print(f"Found {len(data)} local routes across {len(saccos)} SACCOs.")
    ok = write_csv(data)
    if ok:
        print(f"Saved scraped data to scraped_routes.csv")
    print()

    ans = input("Seed the database with this scraped data? (y/n): ").strip().lower()
    if ans == "y":
        counts = seed_db_from_data()
        print(f"Seeded: {counts['saccos']} SACCOs, "
              f"{counts['routes']} routes, {counts['fares']} fares")
    else:
        print("Not seeded. CSV saved for later use via option 9 (seeding reads CSV if present).")


def setup_db():
    hr("DATABASE SETUP")
    print("This will seed the database with Nairobi local routes,")
    print("long-distance routes, and extended SACCO lists.")
    ans = input("Proceed? (y/n): ").strip().lower()
    if ans == "y":
        create_tables()
        counts = seed_database()
        print(f"Seeded: {counts['saccos']} SACCOs, "
              f"{counts['routes']} routes, "
              f"{counts['fares']} fares")
    else:
        print("Cancelled.")


def stats():
    saccos = get_all_saccos()
    local_routes = get_all_routes("local")
    long_routes = get_all_routes("long_distance")

    hr("DATABASE STATISTICS")
    print(f"  SACCOs: {len(saccos)}")
    print(f"  Local routes: {len(local_routes)}")
    print(f"  Long-distance routes: {len(long_routes)}")
    print(f"  Total routes: {len(local_routes) + len(long_routes)}")

    fare_count = 0
    for r in local_routes + long_routes:
        fare_count += len(get_route_fares(r[0]))
    print(f"  Fare records: {fare_count}")

    if saccos:
        print()
        print("  SACCO breakdown:")
        for sid, name, code in saccos:
            count = sum(1 for r in local_routes + long_routes if r[4] == name)
            print(f"    {name} ({code}): {count} routes")


def exit_app():
    hr("THANK YOU")
    print("  Fare transparency matters. Stay informed!")
    sys.exit(0)


MENU = [
    ("View All Routes", view_routes),
    ("Search Routes", search_routes_menu),
    ("Route Details & Fare History", route_details),
    ("Weather Check & Fare Alert", weather_check),
    ("Add Fare Record", add_fare),
    ("Add New Route", add_route),
    ("Export Routes to CSV", export_csv),
    ("Scrape Route Data (Web)", scrape_web),
    ("Setup / Seed Database", setup_db),
    ("Statistics", stats),
    ("Exit", exit_app),
]

create_tables()

while True:
    clear()
    print("=" * 52)
    print("    MATATUMINDER")
    print("    Nairobi Matatu Fare & Route Tracker")
    print("=" * 52)
    print()
    for i, (label, _) in enumerate(MENU, 1):
        print(f"  [{i}] {label}")
    print()

    choice = input("  Select option: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(MENU):
            clear()
            MENU[idx][1]()
            if MENU[idx][0] != "Exit":
                pause()
        else:
            print("  Invalid choice.")
            pause()
    except ValueError:
        print("  Enter a number.")
        pause()
