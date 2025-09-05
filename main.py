# main.py — Cricbuzz Analytics Dashboard (Single File Version)
# ----------------------------------------------------------
# Streamlit + SQLite Cricket Analytics Dashboard

import streamlit as st
import requests
import pandas as pd
import sqlite3
from contextlib import contextmanager

DB_PATH = "cricdash.db"
API_BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/recent"
API_KEY = "3a40b41654msh37cc2a3ded239eap19e78fjsn1ddc38a24341"  # load from env in production

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS players (
        player_id TEXT PRIMARY KEY,
        full_name TEXT,
        role TEXT,
        batting_style TEXT,
        bowling_style TEXT,
        country TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS matches (
        match_id TEXT PRIMARY KEY,
        status TEXT,
        venue TEXT,
        start_time TEXT,
        result_text TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    with get_conn() as conn:
        conn.executescript(schema)

def api_get(path, params=None):
    headers = {"User-Agent": "cricdash/1.0"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    r = requests.get(f"{API_BASE_URL}/{path.lstrip('/')}", headers=headers, params=params or {}, timeout=10)
    r.raise_for_status()
    return r.json()

st.set_page_config(page_title="CricDash", page_icon="🏏", layout="wide")
st.title("🏏 CricDash — Cricket Analytics Dashboard")
init_db()
st.write("App initialized. Navigate sidebar to explore.")
menu = ["Live", "Players", "SQL Lab", "Admin"]
choice = st.sidebar.radio("Navigate", menu)

if choice == "Live":
    st.header("Live Matches")
    st.info("No live data yet — try integrating API refresh here.")

elif choice == "Players":
    st.header("Player Explorer")
    st.info("Player database will be shown here.")

elif choice == "SQL Lab":
    st.header("SQL Lab (Read-only)")
    st.info("Custom SQL queries coming soon.")

elif choice == "Admin":
    st.header("Admin — CRUD")
    st.info("Add/update players here.")
