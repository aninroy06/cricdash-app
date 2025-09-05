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
API_KEY = st.secrets.get("3a40b41654msh37cc2a3ded239eap19e78fjsn1ddc38a24341", None) # load from env in production

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
     CREATE TABLE IF NOT EXISTS innings (
        innings_id TEXT PRIMARY KEY,
        match_id TEXT,
        batting_team TEXT,
        runs INT,
        wickets INT,
        overs REAL,
        target INT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS player_match_stats (
        match_id TEXT,
        player_id TEXT,
        batting_runs INT,
        batting_balls INT,
        fours INT,
        sixes INT,
        sr REAL,
        bowling_overs REAL,
        bowling_runs INT,
        bowling_wkts INT,
        econ REAL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (match_id, player_id)
    );
    
    """
    with get_conn() as conn:
        conn.executescript(schema)

def api_get(path, params=None):
    if not API_KEY:
        raise ValueError("API_KEY not set. Please configure in Streamlit secrets.")
    headers = {
        "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com",
        "X-RapidAPI-Key": API_KEY,
    }
    r = requests.get(f"{API_BASE_URL}/{path.lstrip('/')}", headers=headers, params=params or {}, timeout=10)
    r.raise_for_status()
    return r.json()

def refresh_matches(mode="live"):
    """Fetch matches (live or recent) from RapidAPI Cricbuzz"""
    if mode == "live":
        data = api_get("matches/v1/live")
    else:
        data = api_get("matches/v1/recent")

    matches = data.get("typeMatches", [])
    with get_conn() as conn:
        for match_type in matches:
            for m in match_type.get("seriesMatches", []):
                wrapper = m.get("seriesAdWrapper", {})
                for match in wrapper.get("matches", []):
                    info = match.get("matchInfo", {})
                    conn.execute("""
                        INSERT OR REPLACE INTO matches (match_id, status, venue, start_time, result_text)
                        VALUES (?,?,?,?,?)
                    """, (
                        info.get("matchId"),
                        info.get("status"),
                        info.get("venueInfo", {}).get("ground"),
                        info.get("startDate"),
                        info.get("statusText"),
                    ))
st.set_page_config(page_title="CricDash", page_icon="🏏", layout="wide")
st.title("🏏 CricDash — Cricket Analytics Dashboard")

init_db()

menu = ["Live", "Players", "SQL Lab", "Admin"]
choice = st.sidebar.radio("Navigate", menu)
    if choice == "Live":
        st.header("Matches")

    match_mode = st.radio("Select match type", ["Live", "Recent"], horizontal=True)

    if st.button("Refresh Data"):
        refresh_matches("live" if match_mode == "Live" else "recent")

    with get_conn() as conn:
        df = pd.read_sql("SELECT * FROM matches ORDER BY start_time DESC", conn)

    if df.empty:
        st.info(f"No {match_mode.lower()} matches found.")
    else:
        st.dataframe(df, use_container_width=True)


    with get_conn() as conn:
        df = pd.read_sql("SELECT * FROM matches ORDER BY start_time DESC", conn)
    if df.empty:
        st.info("No live/scheduled matches.")
    else:
        st.dataframe(df, use_container_width=True)

elif choice == "Players":
    st.header("Player Explorer")
    search = st.text_input("Search Player")
    with get_conn() as conn:
        if search:
            df = pd.read_sql("SELECT * FROM players WHERE full_name LIKE ?", conn, params=(f"%{search}%",))
        else:
            df = pd.read_sql("SELECT * FROM players LIMIT 50", conn)
    st.dataframe(df, use_container_width=True)

elif choice == "SQL Lab":
    st.header("SQL Lab (Read-only)")
    query = st.text_area("Enter SQL", "SELECT * FROM matches LIMIT 10;")
    if st.button("Run Query"):
        try:
            with get_conn() as conn:
                df = pd.read_sql(query, conn)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(str(e))

elif choice == "Admin":
    st.header("Admin — CRUD")

    with st.form("AddPlayer"):
        pid = st.text_input("Player ID")
        name = st.text_input("Full Name")
        role = st.text_input("Role")
        country = st.text_input("Country")
        submitted = st.form_submit_button("Save")
        if submitted and pid:
            with get_conn() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO players (player_id, full_name, role, country)
                    VALUES (?,?,?,?)
                """, (pid, name, role, country))
            st.success("Player saved!")

st.subheader("Players")
    with get_conn() as conn:
        df = pd.read_sql("SELECT * FROM players ORDER BY updated_at DESC LIMIT 50", conn)
    st.dataframe(df, use_container_width=True)
