# NaiFare

A Nairobi Matatu Fare & Route Tracker. Scrapes real route data from multiple sources, stores it in SQLite, and provides both a terminal CLI and a Streamlit web UI to browse routes, track fare history, and get weather-based fare alerts.

## Features

- **View & Search** — browse **97 local routes** (Nairobi area) and **250+ long-distance routes** (Nairobi to towns across Kenya), search by route number, location, or SACCO name
- **Fare Ranges** — each route shows its minimum and maximum fare from the source data
- **Fare History** — record and track fare changes over time with weather context
- **Weather Alerts** — live weather via OpenWeatherMap with fare surge warnings on rainy days
- **Web Scraping** — fetch live route data from three sources and seed the database
- **Dual Interface** — use the terminal CLI or the Streamlit web app
- **Filter by Type** — toggle between local routes and long-distance routes

## Project Structure

| File | Purpose |
|------|---------|
| `database.py` | SQLite schema & CRUD operations |
| `scraper.py` | Web scrapers for all data sources |
| `seed_data.py` | Database seeding (CSV → scrape → fallback) |
| `models.py` | Python classes for SACCO, Route, Fare |
| `weather_api.py` | OpenWeatherMap integration |
| `matatu_tracker.py` | Terminal-based CLI application |
| `streamlit_app.py` | Streamlit web application |
| `scraped_routes.csv` | Cached scraped data (auto-generated) |

## Setup

```bash
pip install requests streamlit
```

Run once to seed the database:

```bash
python3 matatu_tracker.py
```

## Usage

### Terminal CLI

```bash
python3 matatu_tracker.py
```

| Option | Description |
|--------|-------------|
| 1 | View all routes (with local/long-distance filter) |
| 2 | Search routes |
| 3 | Route details & fare history |
| 4 | Weather check & fare alerts |
| 5 | Add a fare record |
| 6 | Add a new route |
| 7 | Export routes to CSV |
| 8 | Scrape live data from the web |
| 9 | Seed the database |
| 10 | Database statistics |

### Web UI

```bash
streamlit run streamlit_app.py
```

Opens at `http://localhost:8501`

## Data Sources

Routes, fares, and SACCOs are scraped from three sources:

1. **[Nairobi Postal Code](https://nairobipostalcode.org/nairobi-matatu-routes/)** — all lettered matatu lines (A–Z) operating in Nairobi. Provides 97 local routes with route numbers, destinations, and fare bands.

2. **[Situations.co.ke](https://situations.co.ke/matatu-bus-fares-from-nairobi/)** — long-distance bus and matatu fares from Nairobi to destinations across Kenya (Mombasa, Kisumu, Nakuru, Nyeri, Meru, Kitale, etc.). Each entry includes the SACCO/operator name and fare.

3. **[Elimu Centre](https://www.elimucentre.com/registered-matatu-sacco-operating-in-nairobi/)** — a comprehensive list of ~73 registered SACCOs operating in and from Nairobi.

## Database Schema

```
saccos (id, name, code)
routes (id, route_number, start_point, end_point, sacco_id, fare_min, fare_max, route_type)
fares  (id, route_id, amount, date, weather_condition)
```

The `route_type` column distinguishes `local` (Nairobi area) from `long_distance` (inter-county) routes.
