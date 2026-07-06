# NaiFare — Nairobi Matatu Fare & Route Tracker
## Presentation Slides

---

## Slide 1: Title Slide

**NaiFare**
Nairobi Matatu Fare & Route Tracker

A data-driven tool for fare transparency in Kenya's matatu industry

Capstone Project — Module 1

---

## Slide 2: Problem Statement

**The Problem**
- Matatu fares fluctuate daily based on weather, demand, and route
- No centralised source of truth for fare information
- Passengers often overcharged, especially during bad weather or political unrest
- Manual tracking is impractical across 350+ routes

**The Solution**
NaiFare scrapes live data from multiple sources, stores it in a structured database, and provides both a terminal CLI and a web UI to browse, search, and track fare history with weather and political context.

---

## Slide 3: Key Features

| Feature | Description |
|---------|-------------|
| **Route Browser** | 97 local + 258 long-distance routes across 79 SACCOs |
| **Fare History** | Track fare changes over time with 22 weather conditions |
| **Weather Alerts** | Live weather + fare surge warnings on rainy days |
| **Political Advisory** | News analysis for travel safety and fare hike prediction |
| **Search** | By route number, location, or SACCO name |
| **Admin Authentication** | Login required for create, update, delete operations |
| **Full CRUD** | Create, Read, Update, Delete routes, fares, and SACCOs |
| **Export** | CSV export for offline analysis |
| **Dual Interface** | Terminal CLI + mobile-responsive Streamlit web app |

---

## Slide 4: Data Sources

Three live web scrapers feed the database:

1. **Nairobi Postal Code**
   - 97 local matatu routes (A–Z lines)
   - Route numbers, destinations, fare bands

2. **Situations.co.ke**
   - 258 long-distance routes
   - Nairobi to Mombasa, Kisumu, Nakuru, Nyeri, Kitale, etc.
   - SACCO operator names and fares

3. **Elimu Centre**
   - 79 registered SACCOs operating in/from Nairobi
   - Comprehensive operator list

---

## Slide 5: Tech Stack

```
┌─────────────────────────────────────┐
│     Streamlit Web UI (mobile-ready) │
├─────────────────────────────────────┤
│        Terminal CLI (Python)        │
├─────────────────────────────────────┤
│     seed_data.py  (orchestrator)    │
├─────────────────────────────────────┤
│ scraper  │ weather  │ political     │
│ .py      │ .api     │ .api          │
├─────────────────────────────────────┤
│        database.py  (SQLite)        │
├─────────────────────────────────────┤
│ requests │ sqlite3 │ pandas │ lxml  │
└─────────────────────────────────────┘
```

- **Python** — core language
- **SQLite** — lightweight embedded database
- **Streamlit** — responsive web UI framework
- **requests** + **re** + **xml** — web scraping and RSS parsing
- **OpenWeatherMap API** — live weather data
- **Google News RSS** — political climate analysis (no API key needed)

---

## Slide 6: Database Schema

```sql
saccos (id, name, code)
routes (id, route_number, start_point, end_point,
        sacco_id, fare_min, fare_max, route_type)
fares  (id, route_id, amount, date, weather_condition)
```

- **route_type**: distinguishes `local` (Nairobi area) from `long_distance` (inter-county)
- **weather_condition**: stored with every fare record — 22 unique conditions
- Foreign keys maintain referential integrity
- Cascade delete: deleting a SACCO removes its routes and fares

---

## Slide 7: Weather-Fare Correlation

Bad weather drives fare hikes — the data proves it:

| Fare Level | Weather Conditions | Story |
|-----------|-------------------|-------|
| Minimum fare | Cloudy, Fair, Hazy, Overcast, Misty, Breezy | Normal conditions, normal price |
| Mid fare | Clear, Breezy, Partly Cloudy, Mild, Fair, Sunny | Still fine, slight variation |
| Mid fare | Windy, Drizzle, Foggy, Squall, Blustery, Showers | Weather worsening, fare creeping up |
| Maximum fare | Rainy, Thunderstorm, Heavy Rain, Stormy, Downpour, Hail | Bad weather = fare hike |

The UI displays a **fare alert** when rain is detected:
> *"RAIN ALERT: Fares may spike today. Plan ahead and carry extra fare."*

Weather tagging defaults to **on** when recording new fares.

---

## Slide 8: Political Climate Advisory

A new feature that analyses news headlines for political stability:

**How it works:**
1. Fetches recent Kenya headlines from Google News RSS
2. Scans for unrest keywords: protest, strike, riot, violence, curfew, etc.
3. Classifies into: **Stable** / **Uncertain** / **Unstable**
4. Generates travel safety recommendation and fare outlook

**Output example:**
```
Status: UNSTABLE
Political unrest detected. Travel may be affected.
Travel Safety: Avoid non-essential travel.
Fare Outlook: High probability of fare hikes.
```

Falls back to seasonal heuristics (election years, known quiet periods) when RSS is unreachable.

---

## Slide 9: Database Statistics

```
┌──────────────────────────────────────┐
│         DATABASE STATISTICS          │
├──────────────────────────────────────┤
│  SACCOs:                  79         │
│  Local routes:             97         │
│  Long-distance routes:    258         │
│  Total routes:            355         │
│  Fare records:          1,420         │
│  Weather conditions:      22         │
└──────────────────────────────────────┘
```

---

## Slide 10: Full CRUD Matrix

Complete data management across all entities:

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| **Route** | Add New Route form | View / Search pages | Inline edit on details page | Delete button with confirmation |
| **Fare** | Add Fare form (weather defaults on) | Fare history table | Edit amount/weather inline | Delete by date selection |
| **SACCO** | Add SACCO form | View all SACCOs tab | Edit name/code | Delete with cascade |

All CRUD operations available in both CLI and Streamlit interfaces.

---

## Slide 11: How It Works — Scraping Pipeline

```
┌──────────────┐
│  User clicks │
│ "Scrape &    │
│  Seed"       │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│  seed_data.seed_database()           │
├──────────────────────────────────────┤
│  1. Load CSV or scrape local routes  │
│     (nairobipostalcode.org)          │
│  2. Scrape long-distance routes      │
│     (situations.co.ke)               │
│  3. Scrape extended SACCO list       │
│     (elimucentre.com)                │
│  4. Insert with weather data         │
│     (22 conditions by fare level)    │
└──────────────────────────────────────┘
```

No hardcoded fallback data — relies entirely on live scraping.

---

## Slide 12: User Interfaces

**Terminal CLI** (`python3 matatu_tracker.py`)
- 14-option menu-driven navigation
- Route type filter (Local / Long-distance / All)
- Weather check with Kenyan town validation
- Political climate check
- Full CRUD via numbered options

**Streamlit Web App** (`streamlit run streamlit_app.py`)
- 11-page sidebar navigation
- Route type radio filter on browse/search pages
- Mobile-responsive layout
- Inline editing and deletion with confirmation
- Manage SACCOs with 3 tabs
- Political climate with one-click analysis

---

## Slide 13: Kenyan Town Validation

Weather and political features restricted to **Kenyan towns only**:

- 90+ recognised Kenyan towns and cities
- Case-insensitive matching with whitespace trimming
- Helpful error showing valid towns on mismatch

```python
# Example valid entries
Nairobi, Mombasa, Kisumu, Nakuru, Eldoret,
Thika, Malindi, Nyeri, Meru, Kisii, Kakamega,
Kitale, Garissa, Lamu, Kilifi, Naivasha, Narok
```

---

## Slide 14: Future Enhancements

- **Real-time fare reporting** — crowd-sourced fare updates from users
- **Route maps** — visual mapping with Leaflet or Mapbox
- **Fare predictions** — ML model using weather + political data
- **Multi-city support** — extend beyond Nairobi to Mombasa, Kisumu, Nakuru
- **REST API layer** — for third-party integrations
- **Historical analytics** — charts and trends over time
- **Push notifications** — fare hike alerts via SMS or mobile app

---

## Slide 15: Demo

**Live Demo Walkthrough**

1. Launch Streamlit app — home screen with stats
2. Browse local routes (97 routes across 79 SACCOs)
3. Switch to long-distance routes (258 routes)
4. Route details — view fare history with weather
5. Check weather alert for Nairobi
6. Check political climate — one-click analysis
7. Add a fare record (weather tags on by default)
8. Delete a fare record by date
9. Manage SACCOs — add, edit, delete
10. Export to CSV

---

## Slide 16: Thank You

**NaiFare — Nairobi Matatu Fare & Route Tracker**

*"Fare transparency matters. Stay informed!"*

Questions?
