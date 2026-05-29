import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

# --- CSS for styling ---
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0d0f14;
    --surface: #151820;
    --surface2: #1c2030;
    --border: rgba(255,255,255,0.07);
    --border2: rgba(255,255,255,0.13);
    --text: #eef0f7;
    --muted: #7a8099;
    --green: #22d07a;
    --green-dim: rgba(34,208,122,0.12);
    --amber: #f5a623;
    --amber-dim: rgba(245,166,35,0.12);
    --red: #f04c5a;
    --red-dim: rgba(240,76,90,0.12);
    --blue: #4b9eff;
    --blue-dim: rgba(75,158,255,0.1);
    --accent: #7c6dfa;
    --accent-dim: rgba(124,109,250,0.12);
    --mono: 'Space Mono', monospace;
    --sans: 'DM Sans', sans-serif;
    --radius: 12px;
    --radius-sm: 8px;
  }
  .stApp { background: var(--bg); color: var(--text); font-family: var(--sans); }
  .stMarkdown, p, h1, h2, h3 { color: var(--text); }
  .stButton > button {
    background-color: var(--surface);
    border: 1px solid var(--border2);
    color: var(--text);
    border-radius: 100px;
  }
  .readiness-card, .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    margin-bottom: 20px;
  }
</style>
""", unsafe_allow_html=True)

# --- Data ---
athletes = [
    {'id': 1, 'name': 'Carlos R.', 'initials': 'CR', 'color': '#7c6dfa', 'sport': 'Ciclismo'},
    {'id': 2, 'name': 'Marta G.', 'initials': 'MG', 'color': '#22d07a', 'sport': 'Triatlón'},
    {'id': 3, 'name': 'Diego L.', 'initials': 'DL', 'color': '#f5a623', 'sport': 'Running'},
]

athlete_data = {
    1: {'rmssd': [60, 58, 60, 52, 68, 59, 61, 72], 'sleep': [7.2, 6.8, 7.5, 6.1, 7.8, 7.0, 7.3, 7.0], 'wellness': [4.0, 3.5, 4.25, 2.75, 4.5, 3.75, 3.25, 4.0], 'hrToday': 72, 'sleepTonight': {'deep': 1.4, 'rem': 1.8, 'light': 3.1}, 'wellnessToday': {'sueno': 3, 'dolor': 4, 'estres': 3, 'fatiga': 3}},
    2: {'rmssd': [70, 72, 68, 75, 74, 71, 73, 80], 'sleep': [7.8, 8.0, 7.5, 7.9, 8.2, 7.7, 8.1, 7.9], 'wellness': [4.5, 4.25, 4.0, 4.75, 4.5, 4.25, 4.5, 4.6], 'hrToday': 80, 'sleepTonight': {'deep': 2.1, 'rem': 2.0, 'light': 3.0}, 'wellnessToday': {'sueno': 5, 'dolor': 5, 'estres': 4, 'fatiga': 5}},
    3: {'rmssd': [55, 52, 50, 48, 56, 54, 53, 42], 'sleep': [6.5, 6.0, 6.8, 5.5, 6.9, 6.2, 6.4, 6.0], 'wellness': [3.25, 3.0, 3.5, 2.5, 3.75, 3.25, 3.0, 3.1], 'hrToday': 42, 'sleepTonight': {'deep': 0.9, 'rem': 1.3, 'light': 3.8}, 'wellnessToday': {'sueno': 2, 'dolor': 2, 'estres': 2, 'fatiga': 2}},
}

# --- Logic ---
def calc_readiness(data):
    hist_rmssd = data['rmssd'][:-1]
    today_rmssd = data['rmssd'][-1]
    baseline = np.mean(hist_rmssd) if hist_rmssd else today_rmssd
    if today_rmssd >= baseline: return {'color': 'green', 'label': 'Carga alta'}
    return {'color': 'amber', 'label': 'Carga moderada'}

# --- UI ---
st.title("AtletaOS Dashboard")
athlete_name = st.selectbox("Seleccionar Atleta", [a['name'] for a in athletes])
sel_id = next(a['id'] for a in athletes if a['name'] == athlete_name)
data = athlete_data[sel_id]

st.metric("HRV Hoy", f"{data['rmssd'][-1]} ms")
st.line_chart(data['rmssd'])
st.write("Datos listos para Streamlit Cloud.")
