# NaiFare

A Nairobi Matatu Fare & Route Tracker. Scrapes real route data from [Nairobi Postal Code](https://nairobipostalcode.org/nairobi-matatu-routes/), stores it in SQLite, and provides both a terminal CLI and a Streamlit web UI to browse routes, track fare history, and get weather-based fare alerts.

## Features

- **View & Search** — browse all 97 matatu routes across 6 SACCOs, search by route number, location, or SACCO name
- **Fare Ranges** — each route shows its minimum and maximum fare from the source data
- **Fare History** — record and track fare changes over time with weather context
- **Weather Alerts** — live weather via OpenWeatherMap with fare surge warnings on rainy days
- **Web Scraping** — fetch live route data from nairobipostalcode.org and seed the database
- **Dual Interface** — use the terminal CLI or the Streamlit web app

## Project Structure

| File | Purpose |
|------|---------|
| `database.py` | SQLite schema & CRUD operations |
| `scraper.py` | Web scraper for nairobipostalcode.org |
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
| 1 | View all routes with fare ranges |
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

## Data Source

Routes and fares are scraped from [Nairobi Postal Code](https://nairobipostalcode.org/nairobi-matatu-routes/), which covers all lettered matatu lines (A–Z) operating in Nairobi. The scraper extracts:

- **route tables** (A through Z lines) — 97 routes with route numbers and destinations
- **SACCOs** — Super Metro, Citi Hoppa, Double M, Compliant MOA, NACICO, Kenya Mpya
- **Fare ranges** — short, medium, and long distance fare bands

## Database Schema

```
saccos (id, name, code)
routes (id, route_number, start_point, end_point, sacco_id, fare_min, fare_max)
fares  (id, route_id, amount, date, weather_condition)
```
