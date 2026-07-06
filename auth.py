import streamlit as st

ADMIN_USER = "admin@test.com"
ADMIN_PASS = "adminpass"


def login(username, password):
    if username == ADMIN_USER and password == ADMIN_PASS:
        st.session_state.authenticated = True
        st.session_state.user = username
        return True
    return False


def logout():
    st.session_state.authenticated = False
    st.session_state.user = None


def is_authenticated():
    return st.session_state.get("authenticated", False)


def require_auth():
    if not is_authenticated():
        st.warning("You must be logged in as admin to access this page.")
        st.page_link("streamlit_app.py", label="Go to Home")
        return False
    return True


ADMIN_PAGES = [
    "Add Fare Record",
    "Add New Route",
    "Manage SACCOs",
    "Scrape & Seed Database",
]
