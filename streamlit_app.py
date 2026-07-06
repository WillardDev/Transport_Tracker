import streamlit as st
import pandas as pd
import os

from database import (
    create_tables, get_all_saccos, get_all_routes, search_routes,
    get_route_fares, get_latest_fare, insert_fare, insert_route, insert_sacco,
    route_exists, update_route, delete_route, delete_fare, update_fare,
    update_sacco, delete_sacco, export_routes_to_csv
)
from weather_api import get_weather, get_fare_alert, is_rainy, validate_kenyan_city, KENYAN_TOWNS
from political_api import get_political_status
from auth import is_authenticated, require_auth, ADMIN_PAGES

create_tables()

st.set_page_config(
    page_title="NaiFare",
    layout="wide",
)

PAGE_LOGIN = "Admin Login"

PAGES = [
    "Home",
    "View Routes",
    "Search Routes",
    "Route Details & Fare History",
    "Add Fare Record",
    "Add New Route",
    "Manage SACCOs",
    "Political Climate",
    "Scrape & Seed Database",
    "Statistics",
    "Weather Check & Fare Alert",
    PAGE_LOGIN,
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

    if is_authenticated():
        with st.expander("Edit this route"):
            col1, col2 = st.columns(2)
            new_rn = col1.text_input("Route number", value=route_number)
            new_start = col1.text_input("Starting point", value=start)
            new_end = col2.text_input("Destination", value=end)
            new_fmin = col2.number_input("Min fare (KSh)", min_value=0, value=fmin or 0, step=5)
            new_fmax = col1.number_input("Max fare (KSh)", min_value=0, value=fmax or 0, step=5)
            new_rtype = col2.radio("Type", ["local", "long_distance"], index=0 if rtype == "local" else 1)
            if st.button("Update Route"):
                update_route(db_id, route_number=new_rn, start=new_start, end=new_end,
                             fare_min=new_fmin or None, fare_max=new_fmax or None, route_type=new_rtype)
                st.success("Route updated!")
                st.rerun()

    if is_authenticated():
        if st.button("Delete this route and all its fares", type="secondary", use_container_width=True):
            if delete_route(db_id):
                st.success("Route deleted.")
                st.rerun()

    fares = get_route_fares(db_id)
    if fares:
        fare_rows = []
        for fid, a, d, w in fares:
            fare_rows.append({"ID": fid, "Amount (KSh)": a, "Date": d, "Weather": w or ""})
        fare_df = pd.DataFrame(fare_rows)

        st.subheader("Fare Records")
        if is_authenticated():
            with st.expander("Edit a fare record"):
                edit_fid = st.number_input("Fare ID to edit", min_value=1, step=1, key="edit_fid")
                edit_amount = st.number_input("New amount (KSh)", min_value=1, step=5, key="edit_amt")
                edit_weather = st.text_input("Weather condition (optional)", key="edit_wx")
                if st.button("Update Fare"):
                    update_fare(edit_fid, amount=edit_amount, weather=edit_weather or None)
                    st.success("Fare updated!")
                    st.rerun()

        if is_authenticated():
            with st.expander("Delete a fare record by date"):
                unique_dates = sorted(set(f[2] for f in fares), reverse=True)
                del_date = st.selectbox("Select date", unique_dates, key="del_date")
                matching = [(fid, a, d, w) for fid, a, d, w in fares if d == del_date]
                if len(matching) == 1:
                    st.write(f"Fare on {del_date}: KSh {matching[0][1]} ({matching[0][3] or 'no weather'})")
                    if st.button("Delete this fare", key="del_date_btn"):
                        if delete_fare(matching[0][0]):
                            st.success("Fare deleted.")
                            st.rerun()
                elif len(matching) > 1:
                    del_opts = {f"KSh {a} on {d} ({w or 'no weather'})": fid for fid, a, d, w in matching}
                    del_choice = st.selectbox("Which fare?", list(del_opts.keys()), key="del_choice")
                    if st.button("Delete selected fare", key="del_date_btn"):
                        if delete_fare(del_opts[del_choice]):
                            st.success("Fare deleted.")
                            st.rerun()

        fare_df = fare_df.set_index("ID") if "ID" in fare_df.columns else fare_df
        st.dataframe(fare_df, use_container_width=True)

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
    tag_weather = st.checkbox("Tag with current weather", value=True)

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

def manage_saccos():
    st.header("Manage SACCOs")

    tab1, tab2, tab3 = st.tabs(["View SACCOs", "Add SACCO", "Edit / Delete SACCO"])

    with tab1:
        saccos = get_all_saccos()
        if not saccos:
            st.info("No SACCOs yet.")
        else:
            rows = []
            for sid, name, code in saccos:
                route_count = len(get_all_routes())  # rough count
                rows.append({"ID": sid, "Name": name, "Code": code})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with tab2:
        new_name = st.text_input("SACCO name")
        new_code = st.text_input("SACCO code (e.g. SM)")
        if st.button("Add SACCO"):
            if not new_name or not new_code:
                st.error("Both name and code are required.")
            else:
                sid, is_new = insert_sacco(new_name, new_code.upper())
                if is_new:
                    st.success(f"SACCO '{new_name}' added!")
                else:
                    st.warning("SACCO with that code already exists.")

    with tab3:
        saccos = get_all_saccos()
        if not saccos:
            st.info("No SACCOs to edit.")
            return
        opts = {f"{s[1]} ({s[2]})": s for s in saccos}
        selected_label = st.selectbox("Select SACCO", list(opts.keys()), key="sacco_edit")
        selected = opts[selected_label]
        sid, old_name, old_code = selected

        edit_name = st.text_input("Name", value=old_name)
        edit_code = st.text_input("Code", value=old_code)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update SACCO", use_container_width=True):
                if update_sacco(sid, name=edit_name, code=edit_code.upper()):
                    st.success("SACCO updated!")
                    st.rerun()
        with col2:
            if st.button("Delete SACCO and all its routes", type="secondary", use_container_width=True):
                if delete_sacco(sid):
                    st.success("SACCO deleted.")
                    st.rerun()


def political_climate():
    st.header("Political Climate")
    st.caption("Analyses news to assess travel safety and fare outlook.")

    if st.button("Check Now", type="primary"):
        with st.spinner("Fetching and analysing news..."):
            result = get_political_status()

        status = result["status"]
        color = {"stable": "green", "uncertain": "orange", "unstable": "red"}[status]

        st.markdown(f"### Status: :{color}[{status.upper()}]")
        st.info(result["summary"])

        st.metric("Travel Safety", result["safety"])
        st.metric("Fare Outlook", result["fare_outlook"])

        st.caption(f"Source: {result['source']}")

        if result["headlines"]:
            with st.expander("Recent headlines"):
                for h in result["headlines"]:
                    st.write(f"- {h}")


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

def login_page():
    st.header("Admin Login")
    with st.form("login_form"):
        user = st.text_input("Email")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login", use_container_width=True):
            from auth import login
            if login(user, pwd):
                st.session_state.show_login = False
                st.success("Logged in!")
                st.rerun()
            else:
                st.error("Invalid credentials")


PAGE_FUNCS = {
    "Home": home,
    "View Routes": view_routes,
    "Search Routes": search_routes_page,
    "Route Details & Fare History": route_details,
    "Add Fare Record": add_fare,
    "Add New Route": add_route,
    "Manage SACCOs": manage_saccos,
    "Political Climate": political_climate,
    "Scrape & Seed Database": scrape_and_seed,
    "Statistics": statistics,
    "Weather Check & Fare Alert": weather_check,
    PAGE_LOGIN: login_page,
}

st.sidebar.title("NaiFare")
st.sidebar.caption("Nairobi Matatu Fare Tracker")

# Filter pages based on auth
visible_pages = [p for p in PAGES if is_authenticated() or p not in ADMIN_PAGES + [PAGE_LOGIN]]
selection = st.sidebar.radio("Navigate", visible_pages)

st.sidebar.divider()
st.sidebar.markdown("**Data sources**")
st.sidebar.markdown(
    "[Nairobi Postal Code](https://nairobipostalcode.org/nairobi-matatu-routes/)  \n"
    "[Situations.co.ke](https://situations.co.ke/matatu-bus-fares-from-nairobi/)  \n"
    "[Elimu Centre](https://www.elimucentre.com/registered-matatu-sacco-operating-in-nairobi/)"
)

# Top-right auth icon
top_col1, top_col2, top_col3 = st.columns([8, 1, 1])
with top_col3:
    if not is_authenticated():
        if st.button("Login", key="top_login"):
            st.session_state.show_login = True
            st.rerun()
    else:
        st.caption(st.session_state.user.split("@")[0])
        if st.button("Logout", key="top_logout"):
            from auth import logout
            logout()
            st.rerun()
st.divider()

if st.session_state.get("show_login") or selection == PAGE_LOGIN:
    login_page()
elif not is_authenticated() and selection in ADMIN_PAGES:
    require_auth()
else:
    func = PAGE_FUNCS.get(selection)
    if func:
        func()
