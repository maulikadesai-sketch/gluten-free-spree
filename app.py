"""
Gluten-Free Spree — Recipe Generator
------------------------------------------------
Run with:  streamlit run app.py
"""

import json
import math
import random
import requests
import streamlit as st
import urllib.parse
import time

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
DEFAULT_MODEL = "gemini-2.5-flash-lite"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Models to try in order. Each has its own separate free daily quota.
FALLBACK_MODELS = [
    "gemini-2.5-flash-lite",   # primary
    "gemini-2.5-flash",        # fallback 1
    "gemini-2.5-pro",          # fallback 2
    "gemini-3.0-flash",        # fallback 3
]

# ─────────────────────────────────────────────
# 🔑 API KEYS — Add multiple keys for more free quota!
# ─────────────────────────────────────────────
API_KEYS = [
    "",    # ← Key 1 (required): paste your first Gemini key here
    "",    # ← Key 2 (optional): from a different Gmail account
    "",    # ← Key 3 (optional): from another Gmail account
]

COUNTRIES = [
    "🌍 Global / International", "🇦🇫 Afghanistan", "🇦🇱 Albania", "🇩🇿 Algeria", "🇦🇩 Andorra", 
    "🇦🇬 Antigua & Barbuda", "🇦🇷 Argentina", "🇦🇲 Armenia", "🇦🇺 Australia", "🇦🇹 Austria", 
    "🇮🇳 India", "🇮🇹 Italy", "🇫🇷 France", "🇪🇸 Spain", "🇬🇧 United Kingdom", "🇺🇸 United States"
]

DIETARY_OPTIONS = [
    "None / Just Gluten-Free",
    "Vegan",
    "Vegetarian",
    "Dairy-Free",
    "Egg-Free",
    "Nut-Free",
    "Peanut-Free",
    "Soy-Free",
    "Keto",
    "Paleo",
    "Low FODMAP"
]

# ─────────────────────────────────────────────
# 🎨 UI & Layout Styling
# ─────────────────────────────────────────────
st.set_page_config(page_title="Gluten-Free Spree", page_icon="🌾", layout="centered")

st.markdown("""
<style>
    :root {
        --bg-main: #faf9f6;
        --card-bg: #ffffff;
        --accent: #2e7d32;
        --accent-light: #e8f5e9;
        --ink: #2c3e50;
        --ink-soft: #7f8c8d;
        --border: #e0e0e0;
    }
    
    body, .stApp {
        background-color: var(--bg-main);
        color: var(--ink);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Cards & Containers */
    .recipe-card {
        background: var(--card-bg);
        padding: 2.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        border: 1px solid var(--border);
        margin-bottom: 2rem;
    }
    
    .info-box {
        background: var(--accent-light);
        padding: 1.2rem;
        border-radius: 12px;
        border-left: 5px solid var(--accent);
        margin: 1.5rem 0;
    }

    /* Target the container wrapper instead of breaking the inner checkbox flex element */
    div[data-testid="stCheckbox"] {
        background-color: #ffffff;
        padding: 10px 14px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 8px !important;
        width: 100% !important;
    }

    /* Ensure internal alignment stays beautifully centered and
