import streamlit as st
import pandas as pd
import os

from database import (
    create_tables, get_all_saccos, get_all_routes, search_routes,
    get_route_fares, get_latest_fare, insert_fare, insert_route,
    route_exists
)
from weather_api import get_weather, get_fare_alert, is_rainy, validate_kenyan_city, KENYAN_TOWNS

create_tables()

st.set_page_config(
    page_title="NaiFare",
    layout="wide",
)

PAGES = [
    "Home",
    "View Routes",
    "Search Routes",
    "Route Details & Fare History",
    "Weather Check & Fare Alert",
    "Add Fare Record",
    "Add New Route",
    "Scrape & Seed Database",
    "Statistics",
]

def _route_type_selector(key="route_type"):
    return st.radio(
        "Route type",
        ["All", "Local", "Long-distance"],
        horizontal=True,
        key=key,
    )

def _resolve_rt(ui_val):
    if ui_val == "Local":
        return "local"
    elif ui_val == "Long-distance":
        return "long_distance"
    return None

def _build_route_row(r):
    db_id, route_number, start, end, name, code, fmin, fmax, rtype = r
    latest = get_latest_fare(db_id)
    return {
        "Route": route_number,
        "From": start,
        "To": end,
        "SACCO": f"{name} ({code})",
        "Type": rtype.replace("_", " ").title(),
        "Fare Min": f"KSh {fmin}" if fmin else "N/A",
        "Fare Max": f"KSh {fmax}" if fmax else "N/A",
        "Latest Fare": f"KSh {latest[0]}" if latest else "N/A",
        "Date": latest[1] if latest else "",
    }

def home():
    st.title("NaiFare")
    st.markdown("**Nairobi Matatu Fare & Route Tracker**")
    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    saccos = get_all_saccos()
    local = get_all_routes("local")
    long_routes = get_all_routes("long_distance")

    with col1:
        st.metric("SACCOs", len(saccos))
    with col2:
        st.metric("Local Routes", len(local))
    with col3:
        st.metric("Long-distance Routes", len(long_routes))
    with col4:
        fare_count = sum(len(get_route_fares(r[0])) for r in local + long_routes)
        st.metric("Fare Records", fare_count)

    st.divider()
    st.markdown("""
    Track matatu fares across Nairobi and beyond. Features:
    - **View & Search** local and long-distance routes
    - **Fare history** with weather context
    - **Weather-based fare alerts**
    - **Add & update** fare records
    - **Export** to CSV
    - **Web scraping** from multiple sources
    """)

def view_routes():
    st.header("All Routes")
    rt = _resolve_rt(_route_type_selector("view_rt"))
    label = "All" if rt is None else ("Local" if rt == "local" else "Long-distance")
    routes = get_all_routes(rt)
    if not routes:
        st.info(f"No {label.lower()} routes found. Go to *Scrape & Seed Database* first.")
        return

    rows = [_build_route_row(r) for r in routes]
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

def search_routes_page():
    st.header("Search Routes")
    rt = _resolve_rt(_route_type_selector("search_rt"))
    term = st.text_input("Search by route number, location, or SACCO")
    if term:
        results = search_routes(term, rt)
        if not results:
            st.info(f"No results for '{term}'")
        else:
            rows = []
            for r in results:
                _, route_number, start, end, name, code, fmin, fmax, rtype = r
                rows.append({
                    "Route": route_number,
                    "From": start,
                    "To": end,
                    "SACCO": f"{name} ({code})",
                    "Type": rtype.replace("_", " ").title(),
                    "Fare Min": f"KSh {fmin}" if fmin else "N/A",
                    "Fare Max": f"KSh {fmax}" if fmax else "N/A",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

def route_details():
    st.header("Route Details & Fare History")
    rt = _resolve_rt(_route_type_selector("detail_rt"))
    routes = get_all_routes(rt)
    if not routes:
        st.info("No routes yet. Seed the database first.")
        return

    options = {}
    for r in routes:
        label = f"[{r[1]}] {r[2]} → {r[3]} ({r[4]})"
        if r[6] and r[7]:
            label += f" — Min KSh {r[6]}, Max KSh {r[7]}"
        options[label] = r
    selected_label = st.selectbox("Select a route", list(options.keys()))
    selected = options[selected_label]
    db_id, route_number, start, end, name, code, fmin, fmax, rtype = selected

    st.subheader(f"Route {route_number}: {start} → {end}")
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f"**SACCO:** {name} ({code})")
    col2.markdown(f"**Fare Min:** KSh {fmin}" if fmin else "**Fare Min:** N/A")
    col3.markdown(f"**Fare Max:** KSh {fmax}" if fmax else "**Fare Max:** N/A")
    col4.markdown(f"**Type:** {rtype.replace('_', ' ').title()}")

    fares = get_route_fares(db_id)
    if fares:
        fare_df = pd.DataFrame(
            [
                {"Amount (KSh)": a, "Date": d, "Weather": w or ""}
                for _, a, d, w in fares
            ]
        )
        st.dataframe(fare_df, use_container_width=True, hide_index=True)

        latest = fares[0]
        st.metric("Latest Fare", f"KSh {latest[1]}", help=f"as of {latest[2]}")
    else:
        st.info("No fare records for this route.")

def weather_check():
    st.header("Weather Check & Fare Alert")
    city = st.text_input("City", value="Nairobi",
                         help="Must be a Kenyan town/city")
    if st.button("Check Weather"):
        matched = validate_kenyan_city(city)
        if not matched:
            st.error(f"'{city}' is not a recognized Kenyan town.")
            with st.expander("View valid towns"):
                for t in sorted(KENYAN_TOWNS):
                    st.write(f"- {t}")
            return
        city = matched
        with st.spinner("Fetching weather..."):
            weather = get_weather(city)
        if weather:
            col1, col2, col3 = st.columns(3)
            col1.metric("Temperature", f"{weather['temperature']:.1f} °C")
            col2.metric("Condition", weather["description"].title())
            col3.metric("Humidity", f"{weather['humidity']}%")

            alert = get_fare_alert(weather)
            st.info(alert)

            if is_rainy(weather):
                st.warning("Routes likely affected:")
                for r in get_all_routes()[:5]:
                    st.write(f"- Route {r[1]}: {r[2]} → {r[3]}")
        else:
            st.error("Could not fetch weather. Check your connection.")

def add_fare():
    st.header("Add Fare Record")
    rt = _resolve_rt(_route_type_selector("fare_rt"))
    routes = get_all_routes(rt)
    if not routes:
        st.info("No routes. Seed the database first.")
        return

    options = {}
    for r in routes:
        label = f"[{r[1]}] {r[2]} → {r[3]} ({r[4]})"
        fmin, fmax = r[6], r[7]
        if fmin and fmax:
            label += f" — Min KSh {fmin}, Max KSh {fmax}"
        options[label] = r
    selected_label = st.selectbox("Route", list(options.keys()))
    selected = options[selected_label]

    amount = st.number_input("Fare amount (KSh)", min_value=1, step=5)
    tag_weather = st.checkbox("Tag with current weather")

    if st.button("Record Fare"):
        weather = None
        if tag_weather:
            w = get_weather("Nairobi")
            if w:
                weather = w["condition"]
        insert_fare(selected[0], amount, weather=weather)
        st.success(f"Fare recorded: KSh {amount} for Route {selected[1]}")

def add_route():
    st.header("Add New Route")
    saccos = get_all_saccos()
    if not saccos:
        st.info("No SACCOs yet. Seed the database first.")
        return

    sacco_options = {f"{s[1]} ({s[2]})": s for s in saccos}
    sacco_label = st.selectbox("SACCO", list(sacco_options.keys()))
    sacco = sacco_options[sacco_label]

    route_number = st.text_input("Route number (e.g., 114)")
    start = st.text_input("Starting point")
    end = st.text_input("Destination")

    route_type = "long_distance" if st.radio("Route type", ["Local", "Long-distance"], horizontal=True) == "Long-distance" else "local"

    col1, col2 = st.columns(2)
    fare_min = col1.number_input("Min fare (KSh)", min_value=0, value=50, step=5)
    fare_max = col2.number_input("Max fare (KSh)", min_value=0, value=100, step=5)

    if st.button("Add Route"):
        if not route_number or not start or not end:
            st.error("All fields required.")
        elif route_exists(route_number, start, end, sacco[0], route_type):
            st.warning("This route already exists.")
        else:
            fmin = fare_min if fare_min > 0 else None
            fmax = fare_max if fare_max > 0 else None
            insert_route(route_number, start, end, sacco[0], fmin, fmax, route_type)
            st.success(f"Route {route_number}: {start} → {end} added! (Type: {route_type})")

def scrape_and_seed():
    st.header("Scrape & Seed Database")
    st.markdown("""
    Seeds the database from three sources:
    1. **Nairobi Postal Code** – local Nairobi route numbers & SACCOs
    2. **Situations.co.ke** – long-distance fares from Nairobi
    3. **Elimu Centre** – expanded registered SACCO list
    """)

    if st.button("Scrape & Seed", type="primary"):
        with st.spinner("Scraping and seeding all sources..."):
            from seed_data import seed_database
            counts = seed_database()

        st.success(
            f"Database seeded: {counts['saccos']} SACCOs, "
            f"{counts['routes']} routes, {counts['fares']} fares"
        )

        local = get_all_routes("local")
        long_routes = get_all_routes("long_distance")
        st.info(f"Local routes: {len(local)} | Long-distance routes: {len(long_routes)}")

def statistics():
    st.header("Database Statistics")
    saccos = get_all_saccos()
    local = get_all_routes("local")
    long_routes = get_all_routes("long_distance")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("SACCOs", len(saccos))
    col2.metric("Local Routes", len(local))
    col3.metric("Long-distance Routes", len(long_routes))

    fare_count = sum(len(get_route_fares(r[0])) for r in local + long_routes)
    col4.metric("Fare Records", fare_count)

    if saccos:
        st.subheader("Routes per SACCO")
        data = []
        for sid, name, code in saccos:
            count = sum(1 for r in local + long_routes if r[4] == name)
            data.append({"SACCO": name, "Code": code, "Routes": count})
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

PAGE_FUNCS = {
    "Home": home,
    "View Routes": view_routes,
    "Search Routes": search_routes_page,
    "Route Details & Fare History": route_details,
    "Weather Check & Fare Alert": weather_check,
    "Add Fare Record": add_fare,
    "Add New Route": add_route,
    "Scrape & Seed Database": scrape_and_seed,
    "Statistics": statistics,
}

st.sidebar.title("NaiFare")
st.sidebar.caption("Nairobi Matatu Fare Tracker")
st.sidebar.divider()

selection = st.sidebar.radio("Navigate", PAGES)

st.sidebar.divider()
st.sidebar.markdown("**Data sources**")
st.sidebar.markdown(
    "[Nairobi Postal Code](https://nairobipostalcode.org/nairobi-matatu-routes/)  \n"
    "[Situations.co.ke](https://situations.co.ke/matatu-bus-fares-from-nairobi/)  \n"
    "[Elimu Centre](https://www.elimucentre.com/registered-matatu-sacco-operating-in-nairobi/)"
)

PAGE_FUNCS[selection]()
