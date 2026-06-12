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
#    Each key from a different Gmail account gets its own daily limit.
#    3 keys × 4 models = ~240 requests/day FREE.
#
#    Get free keys at: https://aistudio.google.com/apikey
# ─────────────────────────────────────────────
API_KEYS = [
    "",    # ← Key 1 (required): paste your first Gemini key here
    "",    # ← Key 2 (optional): from a different Gmail account
    "",    # ← Key 3 (optional): from another Gmail account
]

# ─────────────────────────────────────────────
# 📊 ANALYTICS — Log every search to Google Sheets
#    Set up instructions in GLUTEN_FREE_SPREE_SUMMARY.txt
# ─────────────────────────────────────────────
SHEET_WEBHOOK = ""   # ← Paste your Google Apps Script webhook URL here

def log_search(dish_name, country, dietary, source="search"):
    """Silently log search to Google Sheets. Never breaks the app if it fails."""
    if not SHEET_WEBHOOK:
        return
    try:
        from datetime import datetime
        requests.post(SHEET_WEBHOOK, json={
            "dish": dish_name,
            "country": country,
            "dietary": ", ".join(dietary) if dietary else "None",
            "source": source,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }, timeout=3)
    except Exception:
        pass

COUNTRIES = [
    "🌍 Choose your country from the dropdown",
    "🇦🇫 Afghanistan", "🇦🇱 Albania", "🇩🇿 Algeria", "🇦🇩 Andorra",
    "🇦🇴 Angola", "🇦🇬 Antigua and Barbuda", "🇦🇷 Argentina", "🇦🇲 Armenia",
    "🇦🇺 Australia", "🇦🇹 Austria", "🇦🇿 Azerbaijan", "🇧🇸 Bahamas",
    "🇧🇭 Bahrain", "🇧🇩 Bangladesh", "🇧🇧 Barbados", "🇧🇾 Belarus",
    "🇧🇪 Belgium", "🇧🇿 Belize", "🇧🇯 Benin", "🇧🇹 Bhutan",
    "🇧🇴 Bolivia", "🇧🇦 Bosnia and Herzegovina", "🇧🇼 Botswana", "🇧🇷 Brazil",
    "🇧🇳 Brunei", "🇧🇬 Bulgaria", "🇧🇫 Burkina Faso", "🇧🇮 Burundi",
    "🇰🇭 Cambodia", "🇨🇲 Cameroon", "🇨🇦 Canada", "🇨🇻 Cape Verde",
    "🇨🇫 Central African Republic", "🇹🇩 Chad", "🇨🇱 Chile", "🇨🇳 China",
    "🇨🇴 Colombia", "🇰🇲 Comoros", "🇨🇬 Congo", "🇨🇩 Congo (DRC)",
    "🇨🇷 Costa Rica", "🇭🇷 Croatia", "🇨🇺 Cuba", "🇨🇾 Cyprus",
    "🇨🇿 Czech Republic", "🇩🇰 Denmark", "🇩🇯 Djibouti", "🇩🇲 Dominica",
    "🇩🇴 Dominican Republic", "🇪🇨 Ecuador", "🇪🇬 Egypt", "🇸🇻 El Salvador",
    "🇬🇶 Equatorial Guinea", "🇪🇷 Eritrea", "🇪🇪 Estonia", "🇸🇿 Eswatini",
    "🇪🇹 Ethiopia", "🇫🇯 Fiji", "🇫🇮 Finland", "🇫🇷 France",
    "🇬🇦 Gabon", "🇬🇲 Gambia", "🇬🇪 Georgia", "🇩🇪 Germany",
    "🇬🇭 Ghana", "🇬🇷 Greece", "🇬🇩 Grenada", "🇬🇹 Guatemala",
    "🇬🇳 Guinea", "🇬🇼 Guinea-Bissau", "🇬🇾 Guyana", "🇭🇹 Haiti",
    "🇭🇳 Honduras", "🇭🇰 Hong Kong", "🇭🇺 Hungary", "🇮🇸 Iceland",
    "🇮🇳 India", "🇮🇩 Indonesia", "🇮🇷 Iran", "🇮🇶 Iraq",
    "🇮🇪 Ireland", "🇮🇱 Israel", "🇮🇹 Italy", "🇨🇮 Ivory Coast",
    "🇯🇲 Jamaica", "🇯🇵 Japan", "🇯🇴 Jordan", "🇰🇿 Kazakhstan",
    "🇰🇪 Kenya", "🇰🇮 Kiribati", "🇰🇼 Kuwait", "🇰🇬 Kyrgyzstan",
    "🇱🇦 Laos", "🇱🇻 Latvia", "🇱🇧 Lebanon", "🇱🇸 Lesotho",
    "🇱🇷 Liberia", "🇱🇾 Libya", "🇱🇮 Liechtenstein", "🇱🇹 Lithuania",
    "🇱🇺 Luxembourg", "🇲🇴 Macau", "🇲🇬 Madagascar", "🇲🇼 Malawi",
    "🇲🇾 Malaysia", "🇲🇻 Maldives", "🇲🇱 Mali", "🇲🇹 Malta",
    "🇲🇭 Marshall Islands", "🇲🇷 Mauritania", "🇲🇺 Mauritius", "🇲🇽 Mexico",
    "🇲🇩 Moldova", "🇲🇨 Monaco", "🇲🇳 Mongolia", "🇲🇪 Montenegro",
    "🇲🇦 Morocco", "🇲🇿 Mozambique", "🇲🇲 Myanmar", "🇳🇦 Namibia",
    "🇳🇷 Nauru", "🇳🇵 Nepal", "🇳🇱 Netherlands", "🇳🇿 New Zealand",
    "🇳🇮 Nicaragua", "🇳🇪 Niger", "🇳🇬 Nigeria", "🇰🇵 North Korea",
    "🇲🇰 North Macedonia", "🇳🇴 Norway", "🇴🇲 Oman", "🇵🇰 Pakistan",
    "🇵🇼 Palau", "🇵🇸 Palestine", "🇵🇦 Panama", "🇵🇬 Papua New Guinea",
    "🇵🇾 Paraguay", "🇵🇪 Peru", "🇵🇭 Philippines", "🇵🇱 Poland",
    "🇵🇹 Portugal", "🇶🇦 Qatar", "🇷🇴 Romania", "🇷🇺 Russia",
    "🇷🇼 Rwanda", "🇰🇳 Saint Kitts and Nevis", "🇱🇨 Saint Lucia",
    "🇻🇨 Saint Vincent", "🇼🇸 Samoa", "🇸🇲 San Marino",
    "🇸🇹 Sao Tome and Principe", "🇸🇦 Saudi Arabia", "🇸🇳 Senegal",
    "🇷🇸 Serbia", "🇸🇨 Seychelles", "🇸🇱 Sierra Leone", "🇸🇬 Singapore",
    "🇸🇰 Slovakia", "🇸🇮 Slovenia", "🇸🇧 Solomon Islands", "🇸🇴 Somalia",
    "🇿🇦 South Africa", "🇰🇷 South Korea", "🇸🇸 South Sudan", "🇪🇸 Spain",
    "🇱🇰 Sri Lanka", "🇸🇩 Sudan", "🇸🇷 Suriname", "🇸🇪 Sweden",
    "🇨🇭 Switzerland", "🇸🇾 Syria", "🇹🇼 Taiwan", "🇹🇯 Tajikistan",
    "🇹🇿 Tanzania", "🇹🇭 Thailand", "🇹🇱 Timor-Leste", "🇹🇬 Togo",
    "🇹🇴 Tonga", "🇹🇹 Trinidad and Tobago", "🇹🇳 Tunisia", "🇹🇷 Turkey",
    "🇹🇲 Turkmenistan", "🇹🇻 Tuvalu", "🇺🇬 Uganda", "🇺🇦 Ukraine",
    "🇦🇪 United Arab Emirates", "🇬🇧 United Kingdom", "🇺🇸 United States",
    "🇺🇾 Uruguay", "🇺🇿 Uzbekistan", "🇻🇺 Vanuatu", "🇻🇦 Vatican City",
    "🇻🇪 Venezuela", "🇻🇳 Vietnam", "🇾🇪 Yemen", "🇿🇲 Zambia", "🇿🇼 Zimbabwe",
]

DIETARY_TAGS = [
    "None",
    # ── Lifestyle / Diet ──
    "Vegetarian",
    "Vegan",
    "Pescatarian",
    "Fruitarian",
    "Raw Food",
    "Keto",
    "Paleo",
    "Carnivore",
    "Low-FODMAP",
    "Whole30",
    "AIP (Autoimmune Protocol)",
    "Mediterranean",
    "DASH (Heart-Healthy)",
    "High-Protein",
    "Low-Carb",
    "Low-Fat",
    "Low-Sodium",
    "Low-Sugar / Diabetic-Friendly",
    "Anti-Inflammatory",
    "Low-Oxalate (Kidney-Friendly)",
    "GERD-Friendly (Low Acid)",
    "PKU (Low Phenylalanine)",
    "Renal Diet",
    # ── Religious / Cultural ──
    "Halal",
    "Kosher",
    "Jain (No Onion/Garlic/Root Veg)",
    "Sattvic",
    "Buddhist Vegetarian",
    # ── Top 14 Allergens (US FDA + EU) ──
    "Dairy-Free",
    "Lactose-Free",
    "Egg-Free",
    "Peanut-Free",
    "Nut-Free (Tree Nuts)",
    "Soy-Free",
    "Fish-Free",
    "Shellfish-Free",
    "Sesame-Free",
    "Mustard-Free",
    "Celery-Free",
    "Lupin-Free",
    "Mollusk-Free",
    # ── Other Allergies ──
    "Corn-Free",
    "Coconut-Free",
    "Nightshade-Free",
    "Legume-Free",
    "Garlic-Free",
    "Onion-Free",
    "Citrus-Free",
    "Berry-Free",
    "Mushroom-Free",
    "Alpha-Gal (No Red Meat)",
    "Latex-Fruit Allergy (No Banana/Avocado/Kiwi)",
    # ── Intolerances / Sensitivities ──
    "Fructose-Free",
    "Histamine-Free",
    "Sulfite-Free",
    "Salicylate-Free",
    "MSG-Free / Glutamate-Free",
    "Caffeine-Free",
    "Alcohol-Free (In Cooking)",
]

# ─────────────────────────────────────────────
# CSS - Sage Green Palette Makeover
# ─────────────────────────────────────────────
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Outfit:wght@300;400;500;600&display=swap');

:root {
  --ink:       #2D2319;
  --ink-mid:   #5C4B3A;
  --ink-soft:  #8B7D6B;
  --bg:        #FFF9F0;
  --bg2:       #FFF3E6;
  --border:    #E8DDD0;
  --green:     #D4603A;
  --green-l:   #FFE8D6;
  --green-d:   #B84A2A;
  --amber:     #C17817;
  --amber-l:   #FEF3E2;
  --red-l:     #FCE4EC;
  --red:       #C62828;
  --card:      #FFFFFF;
  --shadow:    0 4px 20px rgba(0,0,0,0.06);
  --shadow-lg: 0 8px 30px rgba(0,0,0,0.10);
  --r:         14px;
  /* Pastel section colors */
  --pastel-blue:   #DCEEFB;
  --pastel-pink:   #FFE0D6;
  --pastel-green:  #DEF2D6;
  --pastel-blue-b: #A8D4F0;
  --pastel-pink-b: #F5B8A8;
  --pastel-green-b:#B8DBA8;
  --pastel-yellow:  #FFF2D6;
  --pastel-yellow-b:#FFE0A0;
}

@media (prefers-color-scheme: dark) {
  :root {
    --ink: #2D2319; --ink-mid: #5C4B3A; --ink-soft: #8B7D6B;
    --bg: #FFF9F0; --bg2: #FFF3E6; --border: #E8DDD0;
    --green: #D4603A; --green-l: #FFE8D6; --card: #FFFFFF;
  }
}
[data-theme="dark"] {
  --ink: #1A1A1A; --bg: #FFFDF7; --bg2: #FFF8F0;
  --border: #E0D8CF; --green: #4A9B6D; --card: #FFFFFF;
}

*, *::before, *::after { box-sizing: border-box; }

html, body {
  background-color: #FFF9F0 !important;
  color: #1A1A1A !important;
  -webkit-text-size-adjust: 100%;
}
html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  font-family: 'Outfit', sans-serif !important;
  color: var(--ink) !important;
}
/* Kill the big empty space at top of page */
[data-testid="stAppViewBlockContainer"], .block-container { padding-top: 1rem !important; }
section[data-testid="stMain"] > div:first-child { padding-top: 0 !important; }



/* Force ALL text dark */
[data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] span,
[data-testid="stAppViewContainer"] div, [data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] li, [data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2, [data-testid="stAppViewContainer"] h3,
.stMarkdown, .stMarkdown p { color: var(--ink) !important; }
[data-testid="stExpander"] summary span { color: var(--ink) !important; }

#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { display: none !important; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }
button[kind="headerNoPadding"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }

/* ── App title ── */
h1 {
  font-family: 'Cormorant Garamond', serif !important;
  font-size: 2.8rem !important;
  font-weight: 700 !important;
  color: var(--green-d) !important;
  letter-spacing: -0.3px !important;
  line-height: 1.1 !important;
  margin-bottom: 0 !important;
}

/* ── Section headers ── */
.sec-hdr {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--green-d);
  border-bottom: 2px solid var(--green);
  padding-bottom: 8px;
  margin: 3rem 0 1.5rem 0;
  letter-spacing: -0.3px;
}

/* ── Buttons ── */
div.stButton > button[kind="primary"] {
  background: var(--green) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 10px !important;
  font-family: 'Outfit', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.95rem !important;
  padding: 0.65rem 2rem !important;
  letter-spacing: 0.3px !important;
  transition: all 0.2s ease !important;
}
div.stButton > button[kind="primary"]:hover {
  background: var(--green-d) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 16px rgba(27,107,74,0.25) !important;
}
div.stButton > button[kind="primary"] p,
div.stButton > button[kind="primary"] span,
div.stFormSubmitButton > button p,
div.stFormSubmitButton > button span { color: #FFFFFF !important; }

/* ── Secondary buttons ── */
div.stButton > button:not([kind="primary"]) {
  background: var(--card) !important;
  color: var(--green) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 10px !important;
  font-family: 'Outfit', sans-serif !important;
  font-weight: 500 !important;
  transition: all 0.2s ease !important;
}
div.stButton > button:not([kind="primary"]):hover {
  border-color: var(--green) !important;
  background: var(--green-l) !important;
}

/* ── Download buttons ── */
[data-testid="stDownloadButton"] button {
  background-color: var(--card) !important;
  color: var(--ink) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 10px !important;
  font-family: 'Outfit', sans-serif !important;
  font-weight: 500 !important;
}
[data-testid="stDownloadButton"] button:hover {
  background-color: var(--green-l) !important;
  border-color: var(--green) !important;
}

/* ── Inputs ── */
div[data-testid="stTextInput"] input {
  border-radius: 10px !important;
  border: 1.5px solid var(--border) !important;
  background: var(--card) !important;
  color: var(--ink) !important;
  font-family: 'Outfit', sans-serif !important;
  padding: 0.7rem 1rem !important;
  font-size: 0.95rem !important;
  transition: border-color 0.2s ease !important;
}
div[data-testid="stTextInput"] input:focus {
  border-color: var(--green) !important;
  box-shadow: 0 0 0 3px rgba(27,107,74,0.08) !important;
}

/* ── Select/Dropdown ── */
[data-baseweb="select"] > div {
  background-color: var(--card) !important; color: var(--ink) !important;
  border-radius: 10px !important; border-color: var(--border) !important;
}
[data-baseweb="select"] span { color: var(--ink) !important; }
[data-baseweb="select"] svg { fill: var(--ink) !important; width: 18px !important; height: 18px !important; }
[data-baseweb="select"] input { background: var(--card) !important; color: var(--ink) !important; }
[data-baseweb="popover"], [data-baseweb="popover"] > div,
[data-baseweb="menu"], [data-baseweb="menu"] > div,
[data-baseweb="list"], [data-baseweb="list"] > div { background-color: var(--card) !important; color: var(--ink) !important; }
[data-baseweb="popover"] li, [data-baseweb="menu"] li, [role="option"] { background-color: var(--card) !important; color: var(--ink) !important; }
[data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover, [role="option"]:hover,
[role="option"][aria-selected="true"] { background-color: var(--green-l) !important; }
[data-testid="stSelectbox"] [data-baseweb="select"] > div { background: var(--card) !important; color: var(--ink) !important; }
[data-testid="stMultiSelect"] div { background-color: transparent !important; }
[data-testid="stMultiSelect"] [data-baseweb="select"] > div { background: var(--card) !important; }
[data-testid="stMultiSelect"] input { background: var(--card) !important; color: var(--ink) !important; }

/* ── Tags (multiselect) ── */
[data-baseweb="tag"] {
  background-color: var(--green) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 20px !important;
  font-weight: 500 !important;
}
[data-baseweb="tag"] span { color: #FFFFFF !important; }
[data-baseweb="tag"] svg { fill: #FFFFFF !important; }
[data-baseweb="tag"]:hover { background-color: var(--green-d) !important; }

/* ── Metrics ── */
[data-testid="stMetricValue"] {
  font-size: 1rem !important;
  font-weight: 700 !important;
  color: var(--green) !important;
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: unset !important;
  line-height: 1.3 !important;
  word-wrap: break-word !important;
}
[data-testid="stMetricValue"] div, [data-testid="stMetricValue"] span {
  white-space: normal !important; overflow: visible !important; text-overflow: unset !important;
}
[data-testid="stMetricLabel"] { overflow: visible !important; white-space: normal !important; }
/* ── Metric cards — alternating pastel colors ── */
[data-testid="stMetric"] {
  background: var(--pastel-blue);
  border: 1px solid var(--pastel-blue-b);
  border-radius: var(--r);
  padding: 16px 14px;
  text-align: center;
  box-shadow: var(--shadow);
  overflow: visible !important;
}
/* 2nd and 5th card: pastel yellow */
[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > div:nth-child(2) [data-testid="stMetric"],
[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > div:nth-child(5) [data-testid="stMetric"] {
  background: var(--pastel-yellow) !important;
  border-color: var(--pastel-yellow-b) !important;
}
/* 3rd and 6th card: pastel pink */
[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > div:nth-child(3) [data-testid="stMetric"],
[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > div:nth-child(6) [data-testid="stMetric"] {
  background: var(--pastel-pink) !important;
  border-color: var(--pastel-pink-b) !important;
}
[data-testid="stMetric"] > div, [data-testid="stMetric"] > div > div { overflow: visible !important; }
[data-testid="stMetricValue"] { color: var(--green) !important; }
[data-testid="stMetricLabel"] p { color: var(--ink-soft) !important; }

/* ── Slider ── */
[data-testid="stSlider"] { background: transparent !important; }
[data-testid="stSlider"] > div { background: transparent !important; }
[data-testid="stSlider"] div { background-color: transparent !important; }
[data-baseweb="slider"] div[role="progressbar"] { background-color: var(--border) !important; }
[data-baseweb="slider"] div[role="progressbar"] > div,
[data-baseweb="slider"] div[role="progressbar"] > div:first-child { background-color: var(--green) !important; }
[data-baseweb="slider"] [role="slider"] { background-color: var(--green) !important; border-color: var(--green) !important; }
[data-baseweb="slider"] div[role="slider"] > div { background: transparent !important; border: none !important; box-shadow: none !important; }
[data-baseweb="tooltip"] { background: transparent !important; border: none !important; box-shadow: none !important; }
[data-testid="stSlider"] p { color: var(--ink) !important; }
[data-testid="stElementContainer"]:has([data-testid="stSlider"]) { background: transparent !important; }

/* ── Checkboxes ── */
[data-testid="stCheckbox"] { background: transparent !important; }
[data-testid="stCheckbox"] label { background: transparent !important; cursor: pointer !important; color: var(--ink) !important; }
[data-testid="stCheckbox"] label span { color: var(--ink) !important; }

/* ── Radio ── */
[data-testid="stRadio"] > div { background: transparent !important; }
[data-testid="stRadio"] label { background: transparent !important; color: var(--ink) !important; }

/* ── Expander ── */
[data-testid="stExpander"] { background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: var(--r) !important; }
[data-testid="stExpander"] details { background: var(--card) !important; }
[data-testid="stExpander"] summary { background: var(--card) !important; cursor: pointer !important; }
[data-testid="stExpander"] summary span { color: var(--ink) !important; font-weight: 500 !important; }
[data-testid="stExpander"] summary svg { fill: var(--green) !important; width: 20px !important; height: 20px !important; }
[data-testid="stExpander"] details:not([open]) summary svg { transform: rotate(0deg) !important; }
[data-testid="stExpander"] details[open] summary svg { transform: rotate(180deg) !important; }

/* ── Form ── */
[data-testid="stForm"] { background: transparent !important; border: none !important; padding: 0 !important; }
[data-testid="InputInstructions"], [data-testid="stForm"] small, .stTextInput small,
[data-testid="stForm"] [data-testid="stFormSubmitButton"] + div {
  display: none !important; visibility: hidden !important; height: 0 !important;
}

/* ── Number input ── */
[data-testid="stNumberInput"] input { background: var(--card) !important; color: var(--ink) !important; border-radius: 8px !important; }
[data-testid="stNumberInput"] button { background: var(--card) !important; color: var(--ink) !important; }

/* ── Recipe Hero Card ── */
.recipe-hero {
  position: relative; width: 100%;
  background: linear-gradient(135deg, #2F5435 0%, #152618 100%);
  border-radius: 16px;
  overflow: visible;
  margin: 1.5rem 0 0 0;
  box-shadow: var(--shadow-lg);
  padding: 2.5rem;
  min-height: auto;
}
.recipe-hero-text { position: relative; z-index: 1; }
.recipe-hero-text h2 {
  font-family: 'Cormorant Garamond', serif !important;
  color: #FFFFFF !important;
  font-size: 2rem !important;
  font-weight: 700 !important;
  margin: 0.5rem 0 0 0 !important;
  line-height: 1.15 !important;
}
.recipe-hero-text .hero-sub {
  color: rgba(255,255,255,0.8);
  font-size: 1rem; margin-top: 10px;
  font-family: 'Outfit', sans-serif;
  line-height: 1.6;
  word-wrap: break-word;
}
.hero-badge {
  display: inline-block;
  background: rgba(255,255,255,0.15);
  color: #FFFFFF !important;
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: 20px;
  padding: 4px 14px;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  backdrop-filter: blur(4px);
}
.hero-badge-natural { background: rgba(39,174,96,0.25); border-color: rgba(39,174,96,0.4); }

/* ── Adaptation banner ── */
.adapt-banner {
  background: var(--amber-l); border-left: 4px solid var(--amber);
  border-radius: 0 var(--r) var(--r) 0;
  padding: 14px 18px; margin: 1rem 0;
}
.adapt-title { font-weight: 700; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.5px; color: var(--amber) !important; margin-bottom: 4px; }
.adapt-banner div, .adapt-banner span, .adapt-banner p { color: var(--ink) !important; }
.natural-box {
  background: var(--green-l); border-left: 4px solid var(--green);
  border-radius: 0 var(--r) var(--r) 0;
  padding: 14px 18px; margin: 1rem 0;
  color: var(--green) !important; font-weight: 500;
}

/* ── Time pills ── */
.time-pill {
  display: inline-flex; align-items: center; gap: 5px;
  background: var(--green-l); border: 1px solid rgba(27,107,74,0.15);
  border-radius: 20px; padding: 5px 14px;
  font-size: 0.82rem; margin: 3px 4px;
  color: var(--green-d);
}
.time-pill-icon { font-size: 0.9rem; }

/* ── Steps ── */
.step-block { display: flex; gap: 14px; margin: 22px 0; align-items: flex-start; }
.step-n { min-width: 24px; font-size: 0.95rem; font-weight: 700; color: var(--green); flex-shrink: 0; margin-top: 3px; }
.step-t { font-size: 0.92rem; line-height: 1.8; color: var(--ink); }

/* ── Ingredient emoji ── */
.ing-emoji { font-size: 0.95rem; margin-right: 7px; }

/* ── Pairing cards ── */
.pair-card {
  background: var(--pastel-green);
  border: 1px solid var(--pastel-green-b); border-radius: var(--r);
  padding: 24px 20px; text-align: center; height: 100%;
  box-shadow: var(--shadow);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.pair-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
.pair-icon { font-size: 1.6rem; margin-bottom: 8px; }
.pair-name { font-weight: 700; font-size: 0.95rem; color: var(--green-d); margin: 6px 0 2px; font-family: 'Cormorant Garamond', serif; }
.pair-type { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: var(--green); margin-bottom: 6px; }
.pair-reason { font-size: 0.82rem; color: var(--ink-mid); line-height: 1.65; }

/* ── Brands ── */
.brands-panel {
  background: var(--pastel-green); border: 1px solid var(--pastel-green-b);
  border-radius: var(--r); padding: 20px; margin-bottom: 16px;
  box-shadow: var(--shadow);
}
.brand-item { display: flex; align-items: flex-start; gap: 12px; }
.brand-logo-placeholder {
  width: 40px; height: 40px; border-radius: 10px;
  background: var(--green-l); border: 1px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  color: var(--green); font-size: 0.8rem; font-weight: 700; flex-shrink: 0;
}
.brand-name { font-weight: 600; font-size: 0.9rem; color: var(--green-d); }
.brand-desc { font-size: 0.82rem; color: var(--ink-mid); margin-top: 5px; line-height: 1.65; }
.brand-cert { font-size: 0.7rem; background: var(--green-l); color: var(--green); border: 1px solid rgba(27,107,74,0.15); border-radius: 6px; padding: 1px 8px; margin-left: 6px; font-weight: 600; }

/* ── Gluten tags ── */
.g-tag { display: inline-block; background: var(--red-l); border: 1px solid #E2B3B3; color: var(--red); border-radius: 20px; font-size: 0.76rem; padding: 5px 12px; margin: 3px; font-weight: 500; }

/* ── Substitution cards ── */
.sub-card {
  background: var(--pastel-pink); border: 1px solid var(--pastel-pink-b);
  border-radius: var(--r); padding: 18px; margin-bottom: 14px;
  box-shadow: var(--shadow);
}
.sub-arrow { text-align: center; font-size: 1.2rem; margin: 10px 0; color: var(--green); }
.sub-orig { color: var(--red); font-weight: 600; }
.sub-new { color: var(--green); font-weight: 700; }
.sub-why { font-size: 0.82rem; color: var(--ink-mid); margin-top: 8px; font-style: italic; line-height: 1.65; }
.sub-brands { font-size: 0.8rem; color: var(--ink-soft); margin-top: 5px; }

/* ── Also try buttons ── */
.also-try-btn {
  background: var(--card); border: 1.5px solid var(--border);
  border-radius: 10px; padding: 10px 18px;
  cursor: pointer; font-weight: 500; font-size: 0.88rem;
  transition: all 0.2s ease; color: var(--ink);
}
.also-try-btn:hover { border-color: var(--green); background: var(--green-l); color: var(--green-d); }

/* ── White text on dark backgrounds ── */
div.stButton > button[kind="primary"] p, div.stButton > button[kind="primary"] span,
div.stFormSubmitButton > button p, div.stFormSubmitButton > button span,
[data-testid="stFormSubmitButton"] > button p { color: #FFFFFF !important; }
.recipe-hero h2, .recipe-hero p, .recipe-hero span, .recipe-hero div,
.recipe-hero-text h2, .recipe-hero-text p, .recipe-hero-text span,
.recipe-hero-text div, .recipe-hero-text .hero-sub,
.hero-badge, .hero-badge span { color: #FFFFFF !important; }
.recipe-hero-text .hero-sub { color: rgba(255,255,255,0.8) !important; }
.natural-box, .natural-box span, .natural-box p { color: var(--green) !important; }
.adapt-banner div, .adapt-banner span, .adapt-banner p { color: var(--ink) !important; }
.adapt-title { color: var(--amber) !important; }
.step-n, .step-n span { color: var(--green) !important; }
.brand-logo-placeholder, .brand-logo-placeholder span { color: var(--green) !important; }
.brand-cert, .brand-cert span { color: var(--green) !important; }

/* ── Divider ── */
hr { border-color: var(--border) !important; opacity: 0.5 !important; }


/* ── Decorative cooking elements ── */
.decor-strip {
  text-align: center;
  font-size: 2.5rem;
  letter-spacing: 15px;
  opacity: 0.15;
  margin: 1rem 0;
  user-select: none;
  line-height: 1;
}
.decor-float {
  text-align: center;
  font-size: 4rem;
  opacity: 0.08;
  margin: 0.5rem 0;
  user-select: none;
}

/* Force dropdowns to open downward by ensuring lots of space below every widget */
[data-testid="stAppViewBlockContainer"]::after {
  content: '';
  display: block;
  height: 80vh;
  pointer-events: none;
}
/* ── Content section spacing ── */
.tip-row { padding: 10px 0; line-height: 1.75; font-size: 0.9rem; }
.info-box { padding: 20px; margin: 20px 0; line-height: 1.7; font-size: 0.9rem; border-radius: var(--r); background: var(--pastel-blue); border: 1px solid var(--pastel-blue-b); }

/* ── Mobile spacing — more breathing room on phones ── */
@media (max-width: 768px) {
  .sec-hdr { font-size: 1.2rem; margin: 2rem 0 1.2rem 0; }
  .step-block { padding: 14px 0; }
  .step-t { font-size: 0.95rem; line-height: 1.8; }
  .tip-row { padding: 10px 0; line-height: 1.7; }
  .info-box { padding: 16px !important; margin: 12px 0 !important; line-height: 1.7 !important; font-size: 0.92rem !important; }
  .brands-panel { padding: 14px !important; margin-bottom: 10px !important; }
  .brand-desc { line-height: 1.6 !important; }
  .pair-card { padding: 16px 14px !important; }
  .sub-card { padding: 16px !important; margin-bottom: 10px !important; }
  [data-testid="stMetric"] { padding: 12px 10px; min-height: 80px; }
  [data-testid="stMetricValue"] { font-size: 0.85rem !important; }
  [data-testid="stCheckbox"] label { padding: 6px 0 !important; line-height: 1.6 !important; }
  .natural-box, .adapt-banner { padding: 14px !important; margin: 10px 0 !important; line-height: 1.6 !important; }
  .recipe-hero { padding: 1.5rem !important; }
  .recipe-hero-text h2 { font-size: 1.5rem !important; }
  .recipe-hero-text .hero-sub { font-size: 0.9rem !important; }
}
</style>
"""

# ─────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────

def get_culture_proteins(country_str):
    """Return culture-appropriate protein list based on country."""
    c = country_str.lower()
    
    # Hindu-majority: no beef, no pork
    _HINDU = ["india", "nepal"]
    # Muslim-majority: no pork
    _MUSLIM = ["pakistan", "bangladesh", "afghanistan", "saudi", "uae", "emirates", "qatar", "kuwait", 
               "bahrain", "oman", "iran", "iraq", "jordan", "egypt", "morocco", "tunisia", "algeria", 
               "libya", "sudan", "somalia", "yemen", "syria", "lebanon", "turkey", "indonesia", 
               "malaysia", "brunei", "maldives", "uzbekistan", "turkmenistan", "tajikistan", 
               "kyrgyzstan", "kazakhstan", "azerbaijan", "senegal", "mali", "niger", "mauritania",
               "gambia", "guinea", "sierra leone", "djibouti", "comoros", "palestine"]
    # Jewish: no pork, no shellfish
    _JEWISH = ["israel"]
    # Buddhist (some): vegetarian-leaning but varied
    _NO_BEEF = ["sri lanka", "myanmar", "bhutan"]
    
    base = ["Chicken", "Mutton/Lamb", "Eggs", "Fish"]
    
    if any(h in c for h in _HINDU):
        return base + ["Prawns/Shrimp", "Crab", "Duck", "Turkey"]
    elif any(m in c for m in _MUSLIM):
        return base + ["Beef", "Prawns/Shrimp", "Duck", "Turkey", "Crab", "Salmon", "Tuna"]
    elif any(j in c for j in _JEWISH):
        return base + ["Beef", "Duck", "Turkey", "Salmon", "Tuna"]  # No shellfish
    elif any(b in c for b in _NO_BEEF):
        return base + ["Prawns/Shrimp", "Pork", "Crab", "Duck", "Squid/Calamari"]
    else:
        return base + ["Prawns/Shrimp", "Pork", "Beef", "Crab", "Squid/Calamari", "Duck", "Turkey", "Salmon", "Tuna", "Lobster"]

SYSTEM_INSTRUCTION_TEMPLATE = """You are an expert recipe developer and food scientist who specialises in \
gluten-free cooking. The user is located in: {country}. Tailor ALL ingredient suggestions and brand recommendations \
to what is realistically available in that country.

{dietary_note}

Your job: produce a complete, cookable gluten-free version of the dish that preserves original flavour/texture.
Use spelling conventions appropriate for the user's country: \
for India, UK, Australia use British spellings (flavour, colour, metre, litre, specialise). \
For USA use American spellings (flavor, color, meter, liter, specialize). \
For other countries, default to British spellings. \
IMPORTANT: You must generate a valid recipe for ANY country selected, even less common ones like Afghanistan, \
Mongolia, or smaller nations. Adapt the dish to use locally available ingredients and brands from that country. \
If the dish is not traditional in that country, still provide the recipe but note how it might be adapted locally.
Tailor all quantities and temperatures to the {unit_system} system (e.g. Metric: grams, ml, Celsius; or Imperial: cups, oz, Fahrenheit).

Process:
1. Identify EVERY gluten source that ACTUALLY exists in the traditional/authentic version of this dish. \
Do NOT assume or invent gluten ingredients that are not part of the real recipe. \
RESEARCH the authentic recipe first — use only ingredients that are genuinely part of the dish. \
For example: Parsi dhansak is a lentil and vegetable stew — it does NOT contain cornstarch, wheat flour, or any gluten. \
Soy sauce, wheat noodles, roux, seitan, couscous, regular flour, and malt vinegar ARE common gluten sources. \
Cornstarch, rice flour, besan/chickpea flour, tapioca, and arrowroot are naturally GF — NEVER list these as gluten sources. \
If the dish is naturally gluten-free, clearly state so and provide the authentic recipe with cross-contamination warnings only.
2. For each gluten ingredient, choose a substitution matching its FUNCTION (structure/binding/thickening/crisp coating/flavour) — not just "GF flour". Give realistic ratios (GF subs rarely swap 1:1; may need xanthan gum, starch blends). \
Do NOT substitute ingredients that are already gluten-free. Every ingredient must be accurate and traditionally part of this dish. \
Do not add random ingredients. Do not confuse one dish with another. \
Verify quantities are realistic — a curry for 4 should not need 2 kg of onions or 500g of spice.
3. Write complete recipe with real quantities and clear steps. Each step MUST include specific time durations \
in minutes or hours (e.g. "Sauté onions for 5 minutes", "Bake for 25 minutes at 180°C", "Let rest for 10 minutes"). \
Never use vague timing like "until done" or "for a while" — always give exact minutes.
4. Flag ingredients that are NOT ALWAYS GF (soy sauce, oats, stock, baking powder, spice mixes).
5. Mention cross-contamination risks.
6. For the brands_panel, list 3–5 actual certified gluten-free brands available in {country} that make the most critical substitution ingredients. For each brand include: name, what product, certification body (e.g. GFFS, NFCA, Coeliac UK), a brief note on where to buy, and "fully_gf" set to true if the brand is certified gluten-free, or false if the brand is NOT fully certified GF and may carry contamination risk (e.g. brands that also manufacture wheat products on the same line).
7. Suggest 3 "also_try" naturally-GF dishes similar in flavour profile AND from the same cuisine family. \
For example: if the dish is Indian, suggest other Indian GF dishes like dal tadka or rajma. \
If it's Italian, suggest risotto or polenta-based dishes. Do NOT mix cuisines randomly. \
IMPORTANT: The also_try dishes MUST also comply with all the user's dietary restrictions listed above.
8. Suggest 3 "accompaniments" — side dishes, drinks, or extras that pair well with this dish. \
CRITICAL: Suggest what people ACTUALLY eat with this dish in real life — common, traditional pairings \
that restaurants serve together or families cook together. NOT creative or unusual combinations. \
Examples of CORRECT pairings: \
- Chole → bhature, poori, kulcha, or jeera rice \
- Idli → sambhar, coconut chutney, ghee podi \
- Barfi → nothing as a side (it IS the dessert) — instead suggest what main meal comes BEFORE it \
- Pasta → garlic bread, caesar salad, minestrone soup \
- Sushi → miso soup, edamame, pickled ginger \
- Tacos → guacamole, refried beans, Mexican rice \
If the dish IS a dessert or snack, suggest the MEAL that would precede it, not another snack. \
Think: "What would a restaurant menu show alongside this dish?" or "What does a home cook serve with this?" Each accompaniment must itself be gluten-free AND comply with ALL the user's \
dietary restrictions listed above (e.g. if the user is Vegan, no dairy/meat accompaniments). \
Give name, type (e.g. "Side", "Drink", "Dessert", "Sauce", "Condiment"), and a short reason it pairs well.
9. For EACH ingredient include a single relevant food "emoji" (e.g. 🥚 eggs, 🧈 butter, 🧄 garlic, 🍚 rice, 🧀 cheese). Use 🍽️ if nothing fits.
10. For "calories_per_serving", keep it SHORT like "~420 kcal" (under 12 characters).
11. If the dish requires baking, set "bake_time" (e.g. "25 mins at 180°C"). If it requires marination or resting, set "marination_time" (e.g. "2 hours" or "overnight"). Otherwise set these to null or empty string.
12. Set "total_time" to the overall time from start to finish including prep, cook, bake, marination, and resting. E.g. "1 hour 15 mins" or "3 hours (incl. marination)".
12. If the dish was adapted to meet a dietary restriction (e.g. a chicken dish made vegetarian with paneer), set "dietary_adaptation" to a short explanation like "Originally a chicken dish — adapted to vegetarian using paneer as the protein." If no adaptation was needed, set it to null or empty string.

If naturally GF, set naturally_gluten_free: true, still give full recipe, warn about hidden gluten.

Respond ONLY with valid JSON (no markdown, no backticks):
{{
  "dish_name": string,
  "naturally_gluten_free": boolean,
  "dietary_adaptation": string | null,
  "summary": string,
  "servings": number,
  "prep_time": string,
  "cook_time": string,
  "total_time": string,
  "bake_time": string | null,
  "marination_time": string | null,
  "difficulty": "Easy" | "Medium" | "Hard",
  "calories_per_serving": string,
  "cuisine": string,
  "gluten_sources": [string],
  "ingredients": [{{"item": string, "amount": string, "swap": boolean, "note": string, "emoji": string}}],
  "steps": [string],
  "substitutions": [{{"original": string, "replacement": string, "ratio": string, "reason": string, "local_brands": string}}],
  "brands_panel": [{{"brand": string, "product": string, "certification": string, "where_to_buy": string, "fully_gf": boolean}}],
  "check_labels": [string],
  "tips": [string],
  "storage_info": string,
  "nutrition_notes": string,
  "accompaniments": [{{"name": string, "type": string, "reason": string}}],
  "also_try": [{{"dish": string, "reason": string}}]
}}
"""

# ─────────────────────────────────────────────
# Gemini Helper
# ─────────────────────────────────────────────
def generate_recipe(dish, api_keys, model, country, dietary, base_servings=None, unit_system="Metric"):
    """Generate a recipe. Cycles through every API key × every model before giving up."""
    dietary_note = ""
    dietary_str = ""
    if dietary and len(dietary) > 0:
        dietary_str = ", ".join(dietary)
        dietary_note = f"""CRITICAL DIETARY RESTRICTIONS: The recipe MUST comply with ALL of these: {dietary_str}.
These are hard constraints — they override the original dish if there is a conflict.
For example, if the user asks for "Chicken Tikka" but the restrictions include "Vegetarian",
you MUST replace the chicken with a vegetarian protein (e.g. paneer, tofu, chickpeas) and
rename the dish accordingly (e.g. "Paneer Tikka" or "Vegetarian Tikka").
If the restrictions include "Non-Vegetarian (must include meat/seafood/eggs)", the recipe MUST contain \
meat, poultry, seafood, or eggs as a main ingredient. Do NOT make it vegetarian. \
For example, "Hakka Noodles" with Non-Vegetarian should be "Chicken Hakka Noodles" or "Egg Hakka Noodles", NOT "Vegetable Hakka Noodles".
NEVER include any ingredient that violates ANY of these restrictions: {dietary_str}.
Double-check every single ingredient against ALL restrictions before including it."""

    system_prompt = SYSTEM_INSTRUCTION_TEMPLATE.format(
        country=country,
        dietary_note=dietary_note,
        unit_system=unit_system
    )

    serving_note = ""
    if base_servings:
        serving_note = f" Make the recipe for {base_servings} servings."

    dietary_user_note = f" IMPORTANT: This must comply with: {dietary_str}." if dietary_str else ""

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": f"Create a gluten-free recipe for: {dish}.{serving_note}{dietary_user_note}"}]}],
        "generationConfig": {"response_mime_type": "application/json", "temperature": 0.4, "max_output_tokens": 4096},
    }

    # Ensure api_keys is a list
    if isinstance(api_keys, str):
        api_keys = [api_keys]
    api_keys = [k for k in api_keys if k]  # remove empties

    models_to_try = [model] + [m for m in FALLBACK_MODELS if m != model]
    resp = None
    last_err = None
    combos_tried = 0

    for key in api_keys:
        for m in models_to_try:
            combos_tried += 1
            url = f"{API_BASE}/{m}:generateContent?key={key}"
            try:
                resp = requests.post(url, json=payload, timeout=30)
            except requests.exceptions.RequestException as e:
                last_err = RuntimeError(f"Network error: {e}")
                resp = None
                continue

            if resp.status_code == 200:
                break  # success!

            try:
                msg = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                msg = resp.text

            last_err = RuntimeError(f"API error ({resp.status_code}): {msg}")
            resp = None
            continue  # try next combo

        if resp is not None and resp.status_code == 200:
            break  # done!

    if resp is None or resp.status_code != 200:
        n_keys = len(api_keys)
        raise RuntimeError(
            f"Tried {combos_tried} combinations ({n_keys} key(s) × {len(models_to_try)} models) — "
            f"all at their daily limit. Resets at midnight US Pacific time (1:30 PM IST). "
            f"Add more free API keys from different Gmail accounts to increase your daily quota."
        )

    data = resp.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("No content returned. Try again.")
    
    # Robustly clean up any stray formatting tags around the JSON payload
    text = text.strip()
    if text.startswith("```"):
        first_nl = text.find("\n")
        if first_nl != -1:
            text = text[first_nl:]
        if text.endswith("```"):
            text = text[:-3]
    text = text.strip()
    
    brace = text.find('{')
    if brace > 0:
        text = text[brace:]
    rbrace = text.rfind('}')
    if rbrace != -1 and rbrace < len(text) - 1:
        text = text[:rbrace + 1]
    
    result = json.loads(text)
    if isinstance(result, str):
        result = json.loads(result)
    return result

def scale_amount(amount_str, factor):
    """Scale ingredient amounts to cooking-friendly numbers (whole numbers and halves)."""
    import re
    if not amount_str or factor == 1:
        return amount_str

    def friendly_number(n):
        """Round to cooking-friendly numbers — multiples of 5/10 for large, ¼ for small."""
        if n <= 0:
            return "0"
        # Large numbers: round to nearest 5 (≥50) or 10 (≥100)
        if n >= 100:
            return str(int(round(n / 10) * 10))
        if n >= 20:
            return str(int(round(n / 5) * 5))
        # Medium numbers (5-20): round to whole number
        if n >= 5:
            return str(round(n))
        # Small numbers: round to nearest ¼
        rounded = round(n * 4) / 4
        if rounded == 0:
            rounded = 0.25
        if rounded == int(rounded):
            return str(int(rounded))
        whole = int(rounded)
        frac = rounded - whole
        frac_str = {0.25: "¼", 0.5: "½", 0.75: "¾"}.get(frac, str(frac))
        if whole == 0:
            return frac_str
        return f"{whole}{frac_str}"

    # Handle ranges like "18-24" or "2-3"
    range_match = re.match(r'^(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)\s*(.*)', amount_str.strip())
    if range_match:
        lo = float(range_match.group(1)) * factor
        hi = float(range_match.group(2)) * factor
        rest = range_match.group(3)
        return f"{friendly_number(lo)}-{friendly_number(hi)} {rest}".strip()

    # Handle fractions like "1/4", "1/2", "3/4"
    frac_match = re.match(r'^(\d+)\s*/\s*(\d+)\s*(.*)', amount_str.strip())
    if frac_match:
        num = float(frac_match.group(1)) / float(frac_match.group(2))
        scaled = num * factor
        rest = frac_match.group(3)
        return f"{friendly_number(scaled)} {rest}".strip()

    # Handle single numbers
    m = re.match(r'^(\d+\.?\d*)\s*(.*)', amount_str.strip())
    if not m:
        return amount_str
    try:
        num = float(m.group(1))
        rest = m.group(2)
        scaled = num * factor
        return f"{friendly_number(scaled)} {rest}".strip()
    except Exception:
        return amount_str

# ─────────────────────────────────────────────
# Post-generation gluten safety scan
# ─────────────────────────────────────────────
GLUTEN_BLOCKLIST = [
    "wheat flour", "all-purpose flour", "plain flour", "self-raising flour", "bread flour",
    "cake flour", "semolina", "durum", "spelt", "kamut", "farro", "bulgur", "couscous",
    "barley", "rye", "triticale", "seitan", "vital wheat gluten", "wheat starch",
    "wheat germ", "wheat bran", "wheat berries", "einkorn", "emmer",
    "regular soy sauce", "soy sauce", "malt vinegar", "malt extract", "malt syrup",
    "beer", "lager", "ale", "stout",
    "regular breadcrumbs", "breadcrumbs", "panko", "croutons",
    "regular pasta", "wheat noodles", "udon noodles",
    "flour tortilla", "wheat tortilla", "pita bread", "naan",
    "oreo", "graham cracker",
]

# Items that are OK despite sounding suspicious
GLUTEN_SAFE = [
    "gluten-free", "gf", "rice flour", "almond flour", "coconut flour", "oat flour",
    "tapioca", "cornstarch", "corn flour", "chickpea flour", "besan", "buckwheat",
    "arrowroot", "potato starch", "sorghum", "millet", "teff", "amaranth",
    "tamari", "coconut aminos", "gf soy sauce", "gluten-free soy sauce",
    "rice noodles", "glass noodles", "gf pasta", "gluten-free pasta",
    "gf breadcrumbs", "gluten-free breadcrumbs", "gf panko",
    "corn tortilla", "gf tortilla",
]

def scan_recipe_safety(recipe):
    """Scan all ingredients for potential gluten contamination. Returns list of warnings."""
    warnings = []
    for ing in recipe.get("ingredients", []):
        item = ((ing.get("item", "") or "") + " " + (ing.get("note", "") or "")).lower()
        # Skip if marked as GF swap
        if ing.get("swap", False):
            continue
        # Skip if contains a safe term
        if any(safe in item for safe in GLUTEN_SAFE):
            continue
        # Check against blocklist
        for blocked in GLUTEN_BLOCKLIST:
            if blocked in item:
                warnings.append(f"⚠️ **{ing.get('item', '')}** may contain gluten ({blocked}). Please verify this ingredient is gluten-free before using.")
                break
    return warnings

def recipe_to_text(recipe, servings_label):
    lines = [
        f"GLUTEN-FREE SPREE — {recipe.get('dish_name','').upper()}",
        f"Servings: {servings_label}  |  Prep: {recipe.get('prep_time','')}  |  Cook: {recipe.get('cook_time','')}  |  Total: {recipe.get('total_time','')}",
        "",
        "INGREDIENTS",
    ]
    for ing in recipe.get("ingredients", []):
        swap = " [GF swap]" if ing.get("swap") else ""
        lines.append(f"  {ing.get('amount','')}  {ing.get('item','')}{swap}")
    lines += ["", "METHOD"]
    for i, step in enumerate(recipe.get("steps", []), 1):
        lines.append(f"  {i}. {step}")
    return "\n".join(lines)

# ─────────────────────────────────────────────
# Cached recipe generation — same dish + settings = 0 API calls
# Works across ALL users visiting the site, lasts 24 hours
# ─────────────────────────────────────────────
@st.cache_data(ttl=86400, show_spinner=False)
def cached_generate(keys_str, dish, model, country, dietary_str, unit_system):
    """Cached wrapper. Same dish+country+dietary = 1 API call total across ALL users for 24 hours.
    Servings excluded from cache key — scaling is done client-side."""
    api_keys = [k for k in keys_str.split("|") if k]
    dietary = [d for d in dietary_str.split("|") if d] if dietary_str else []
    return generate_recipe(dish, api_keys, model, country, dietary, 4, unit_system)

# ─────────────────────────────────────────────
# Page Setup
# ─────────────────────────────────────────────
st.set_page_config(page_title="Gluten-Free Spree", page_icon="🍽️", layout="wide", initial_sidebar_state="collapsed")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# API Key — loaded silently in background
# ─────────────────────────────────────────────
# Build list of all available API keys (from code + secrets)
all_api_keys = [k.strip() for k in API_KEYS if k.strip()]
try:
    # Also check secrets for keys (supports GEMINI_API_KEY, GEMINI_API_KEY_1, _2, _3 etc.)
    secret_key = st.secrets.get("GEMINI_API_KEY", "")
    if secret_key and secret_key.strip() not in all_api_keys:
        all_api_keys.append(secret_key.strip())
    for i in range(1, 6):
        sk = st.secrets.get(f"GEMINI_API_KEY_{i}", "")
        if sk and sk.strip() not in all_api_keys:
            all_api_keys.append(sk.strip())
except Exception:
    pass
model = DEFAULT_MODEL

# Load analytics webhook from secrets if available
if not SHEET_WEBHOOK:
    try:
        SHEET_WEBHOOK = st.secrets.get("SHEET_WEBHOOK", "")
    except Exception:
        pass

# ─────────────────────────────────────────────
# Main App Header
# ─────────────────────────────────────────────
st.markdown("""
<div style='padding:0; margin-top:1.5rem; text-align:center;'>
  <h1 style='margin-bottom:6px; font-size:2.8rem; background:linear-gradient(135deg, #D4603A, #C17817); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;'>Gluten-Free Spree</h1>
  <p style='color:#7A7A7A; font-size:0.95rem; margin:0 auto 12px; line-height:1.5; font-style:italic; max-width:800px;'>
    Craving something delicious but need it gluten-free? You're in the right place! Type any dish and we'll recreate it with GF swaps, brand suggestions, and step-by-step instructions tailored to your dietary needs.
  </p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DISH INPUT — first thing users see and type
# ─────────────────────────────────────────────
_default_dish = st.session_state.pop("_new_dish_name", "")
_dish_key = f"dish_input_{hash(_default_dish) if _default_dish else 0}"
dish = st.text_input(
    "🍳 What dish would you like to make gluten-free?",
    value=_default_dish if _default_dish else "",
    placeholder="Type any dish — e.g., Biryani, Pizza, Croissants, Pad Thai...",
    key=_dish_key,
)

# ─────────────────────────────────────────────
# Smart sub-options — AI detects vague dishes dynamically
# ─────────────────────────────────────────────
@st.cache_data(ttl=86400, show_spinner=False)
def get_dish_options(dish_name, keys_str, _v=3):
    """Ask Gemini if dish is vague. If yes, return sub-categories. Cached 24hrs."""
    import json as _j
    api_keys = [k for k in keys_str.split("|") if k]
    prompt = f"""The user typed "{dish_name}" as a dish. Return customization options as JSON.

RULE: Single-word dishes (pizza, pasta, curry, dosa, biryani, soup, salad, burger, sushi, noodles, bread, cake, pie, wrap, taco, steak, kebab, paratha, chaat, momos, risotto, crepe, omelette, smoothie, pancake, dumpling, sandwich, etc.) are ALWAYS generic — return options.
Multi-word specific dishes (chicken tikka masala, pad thai, eggs benedict, etc.) are specific — return {{"specific":true}}.

For generic dishes: return 1-2 JSON keys with 8-10 variations each.
Noodles=Asian(ramen,udon,soba). Pasta=Italian(penne,spaghetti). Never mix.
Examples:
"dosa"->{{"Dosa Type":["Plain Dosa","Masala Dosa","Rava Dosa","Onion Dosa","Mysore Masala","Set Dosa","Neer Dosa","Paper Dosa","Cheese Dosa","Egg Dosa"]}}
"pasta"->{{"Pasta Type":["Penne","Spaghetti","Fusilli","Fettuccine","Rigatoni","Macaroni","Lasagne","Tagliatelle"],"Sauce":["Tomato","Alfredo","Pesto","Carbonara","Arrabbiata","Bolognese","Aglio e Olio","Pink"]}}
"chicken tikka masala"->{{"specific":true}}
JSON only."""
    for key in api_keys[:2]:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=5
            )
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            text = text.strip().strip("`").strip()
            if text.startswith("json"): text = text[4:].strip()
            data = _j.loads(text)
            if data.get("specific"): return None
            return data
        except Exception:
            continue
    return None


# Veg / Non-veg — auto-detect from dish name
_VEG_WORDS = {"veg", "vegetarian", "veggie", "paneer", "tofu", "aloo", "gobhi", "palak", "bhindi", "dal", "chana", "rajma", "sabzi", "gobi", "mushroom veg"}
_NONVEG_WORDS = {"chicken", "mutton", "lamb", "fish", "prawn", "shrimp", "egg", "pork", "beef", "crab", "lobster", "salmon", "tuna", "duck", "turkey", "meat", "non-veg", "nonveg", "non veg", "keema", "seekh", "butter chicken", "tandoori", "rogan josh", "bacon", "ham", "sausage", "pepperoni", "salami", "squid", "calamari"}

_dish_lower = (dish or "").strip().lower()
_SPECIFIC_PROTEINS = {"chicken", "mutton", "lamb", "fish", "prawn", "shrimp", "egg", "pork", "beef", "crab", "lobster", "salmon", "tuna", "duck", "turkey", "bacon", "ham", "sausage", "squid", "calamari", "keema", "seekh"}
_has_specific_protein = any(w in _dish_lower for w in _SPECIFIC_PROTEINS)
_current_country = st.session_state.get("country_radio", "🇮🇳 India")
_detected_veg = None
if any(w in _dish_lower for w in _NONVEG_WORDS) or _dish_lower.startswith("egg "):
    _detected_veg = "nonveg"
elif any(w in _dish_lower.split() for w in _VEG_WORDS) or _dish_lower.startswith("veg ") or "vegetable" in _dish_lower:
    _detected_veg = "veg"

nonveg_proteins = []
if _detected_veg == "veg":
    veg_choice = "🥦 Veg"
    st.markdown("<p style='font-size:0.85rem;color:var(--ink-soft);'>🥦 <em>Detected as vegetarian from dish name</em></p>", unsafe_allow_html=True)
elif _detected_veg == "nonveg":
    veg_choice = "🍗 Non-Veg"
    st.markdown("<p style='font-size:0.85rem;color:var(--ink-soft);'>🍗 <em>Detected as non-vegetarian from dish name</em></p>", unsafe_allow_html=True)
else:
    # Not clear from dish name — show selector
    veg_choice = st.radio("🥗 Food preference", ["🥦 Veg", "🥚 Eggetarian", "🍗 Non-Veg"], horizontal=True, key="veg_radio")
    
    # Non-veg protein selector moved to customization area
    if veg_choice == "🍗 Non-Veg" and dish and dish.strip():
        pass  # Proteins shown in customize section above


dish_extra = ""
if dish and dish.strip():
    dish_lower = dish.strip().lower()
    # Only check for vague dishes (1-2 common words, short names)
    word_count = len(dish_lower.split())
    if word_count <= 2 and len(dish_lower) <= 20:
        keys_for_check = "|".join(all_api_keys)
        if keys_for_check:
            options = get_dish_options(dish_lower, keys_for_check, _v=3)
            
            # Fallback: if AI returns nothing for a single common word, use hardcoded
            if not options and word_count == 1:
                _FB = {
                    "dosa": {"Dosa Type": ["Plain Dosa","Masala Dosa","Rava Dosa","Onion Dosa","Mysore Masala","Set Dosa","Neer Dosa","Paper Dosa","Cheese Dosa","Egg Dosa"]},
                    "paratha": {"Paratha Type": ["Aloo","Gobhi","Paneer","Methi","Mooli","Plain","Laccha"]},
                    "biryani": {"Type": ["Chicken","Mutton","Veg","Egg","Prawn","Paneer","Mushroom"], "Style": ["Hyderabadi","Lucknowi","Kolkata","Malabar"]},
                    "chaat": {"Type": ["Pani Puri","Bhel Puri","Sev Puri","Dahi Puri","Aloo Tikki","Papdi Chaat","Samosa Chaat"]},
                    "curry": {"Style": ["Butter","Tikka Masala","Korma","Vindaloo","Thai Green","Thai Red","Rogan Josh","Saag"], "Protein": ["Chicken","Paneer","Tofu","Lamb","Chickpeas","Veg","Prawns"]},
                    "pizza": {"Crust": ["Thin","Thick","Deep Dish","Neapolitan","Stuffed"], "Topping": ["Margherita","Pepperoni","BBQ Chicken","Veggie","Four Cheese"]},
                    "pasta": {"Type": ["Penne","Spaghetti","Fusilli","Fettuccine","Rigatoni","Macaroni","Lasagne"], "Sauce": ["Tomato","Alfredo","Pesto","Carbonara","Arrabbiata","Bolognese","Pink"]},
                    "noodles": {"Type": ["Ramen","Udon","Soba","Rice Noodles","Hakka","Chow Mein","Vermicelli"], "Style": ["Stir-fried","Soup","Dry","Spicy"]},
                    "soup": {"Type": ["Tomato","Mushroom","Chicken","Minestrone","Corn Chowder","Hot & Sour","Lentil","Pumpkin"]},
                    "salad": {"Type": ["Caesar","Greek","Cobb","Garden","Quinoa","Thai","Caprese"], "Protein": ["Chicken","Tofu","Prawns","Egg","Chickpeas","None"]},
                    "burger": {"Patty": ["Beef","Chicken","Veggie","Paneer","Fish","Lamb"], "Style": ["Classic","Smash","BBQ","Spicy"]},
                    "sandwich": {"Type": ["Club","Grilled Cheese","BLT","Panini","Sub"], "Bread": ["White","Multigrain","Wrap","Sourdough"]},
                    "cake": {"Type": ["Chocolate","Vanilla","Red Velvet","Carrot","Cheesecake","Lemon","Coffee","Black Forest"]},
                    "bread": {"Type": ["Sandwich","Focaccia","Naan","Roti","Pita","Baguette","Sourdough","Banana Bread"]},
                    "sushi": {"Style": ["Maki","Nigiri","Hand Roll","Inside-out","Poke Bowl"], "Filling": ["Salmon","Tuna","Prawn","Avocado","Tofu"]},
                    "taco": {"Filling": ["Chicken","Beef","Fish","Shrimp","Bean","Veggie"], "Shell": ["Hard Shell","Soft Tortilla","Lettuce Wrap"]},
                    "momos": {"Type": ["Steamed","Fried","Tandoori","Gravy","Pan-fried"], "Filling": ["Chicken","Veg","Paneer","Pork","Cheese"]},
                    "kebab": {"Type": ["Seekh","Shami","Tikka","Chapli","Doner","Shawarma"], "Protein": ["Chicken","Lamb","Paneer","Fish","Veg"]},
                    "rice": {"Dish": ["Fried Rice","Biryani","Pulao","Risotto","Jeera Rice","Lemon Rice"], "Protein": ["Veg","Chicken","Egg","Prawn","Paneer"]},
                    "pancake": {"Type": ["American Fluffy","French Crêpes","Banana","Blueberry","Dutch Baby","Japanese Soufflé"]},
                    "omelette": {"Style": ["French","Spanish","Masala","Cheese","Mushroom","Western"]},
                    "smoothie": {"Base": ["Banana","Mango","Berry","Green","Tropical","Chocolate"], "Liquid": ["Milk","Almond Milk","Coconut Milk","Yogurt"]},
                    "dumpling": {"Type": ["Gyoza","Momo","Wonton","Pierogi","Ravioli","Samosa"], "Method": ["Steamed","Pan-fried","Deep-fried","Boiled"]},
                    "steak": {"Cut": ["Ribeye","Sirloin","Tenderloin","T-Bone","Flank"], "Doneness": ["Rare","Medium Rare","Medium","Well Done"]},
                    "wrap": {"Filling": ["Chicken Tikka","Falafel","Paneer","Fish","Veggie & Hummus","Egg"]},
                    "idli": {"Type": ["Plain Idli","Rava Idli","Mini Idli","Masala Idli","Stuffed Idli","Kanchipuram Idli"]},
                    "uttapam": {"Type": ["Onion","Tomato","Mixed Veg","Cheese","Masala","Plain"]},
                    "thali": {"Cuisine": ["North Indian","South Indian","Gujarati","Rajasthani","Bengali","Maharashtrian"]},
                    "cookie": {"Type": ["Chocolate Chip","Oatmeal","Peanut Butter","Shortbread","Snickerdoodle","Double Chocolate","Sugar Cookie"]},
                    "pie": {"Type": ["Apple","Chicken","Shepherd's","Pumpkin","Key Lime","Banoffee","Meat"]},
                }
                options = _FB.get(dish_lower)

            if options and isinstance(options, dict) and not options.get("specific"):
                # Filter out any non-list values (cleanup AI response)
                valid_options = {k: v for k, v in options.items() if isinstance(v, list) and len(v) > 1}
                if valid_options:
                    # Add protein selector as first option if non-veg
                    if veg_choice == "🍗 Non-Veg" and not _has_specific_protein:
                        protein_list = get_culture_proteins(_current_country)
                        valid_options = {"🥩 Non-Veg Protein": protein_list, **valid_options}

                    st.markdown(f"<p style='font-size:0.85rem;color:var(--ink-soft);margin:4px 0;'>🎯 Customize your {dish.strip()}:</p>", unsafe_allow_html=True)
                    cols = st.columns(min(len(valid_options), 3))
                    selections = []
                    for idx, (label, choices) in enumerate(valid_options.items()):
                        with cols[idx % 3]:
                            sel = st.selectbox(f"🍽️ {label}", ["— Choose (optional) —"] + choices[:12], key=f"generic_{dish_lower}_{idx}")
                            if sel != "— Choose (optional) —":
                                selections.append(sel)
                                if label == "🥩 Non-Veg Protein":
                                    nonveg_proteins.append(sel)
                    if selections:
                        dish_extra = " — " + ", ".join(selections)
                elif veg_choice == "🍗 Non-Veg" and not _has_specific_protein:
                    st.markdown(f"<p style='font-size:0.85rem;color:var(--ink-soft);margin:4px 0;'>🎯 Customize your {dish.strip()}:</p>", unsafe_allow_html=True)
                    protein_list = get_culture_proteins(_current_country)
                    sel = st.selectbox("🥩 Non-Veg Protein", ["— Choose (optional) —"] + protein_list, key=f"protein_only_{dish_lower}")
                    if sel != "— Choose (optional) —":
                        nonveg_proteins.append(sel)
                        dish_extra = " — " + sel
            elif veg_choice == "🍗 Non-Veg" and word_count <= 2 and not _has_specific_protein:
                st.markdown(f"<p style='font-size:0.85rem;color:var(--ink-soft);margin:4px 0;'>🎯 Customize your {dish.strip()}:</p>", unsafe_allow_html=True)
                protein_list = get_culture_proteins(_current_country)
                sel = st.selectbox("🥩 Non-Veg Protein", ["— Choose (optional) —"] + protein_list, key=f"protein_spec_{dish_lower}")
                if sel != "— Choose (optional) —":
                    nonveg_proteins.append(sel)
                    dish_extra = " — " + sel

# ─────────────────────────────────────────────
# Settings Panel — country, units
# ─────────────────────────────────────────────
# Location
# Location
country_choice = st.radio("📍 Which country are you in?", ["🇮🇳 India", "🌍 Other"], horizontal=True, key="country_radio")
if country_choice == "🌍 Other":
    other_countries = [c for c in COUNTRIES if "India" not in c]
    country = st.selectbox("Select country", other_countries, index=0, label_visibility="collapsed", key="country_select")
else:
    country = "🇮🇳 India"

# Default servings (adjustable in recipe display area)
servings = st.session_state.get("current_servings", 4)

# Dietary needs
all_dietary = sorted([
    "Vegan", "Pescatarian", "Fruitarian", "Raw Food",
    "Keto", "Paleo", "Carnivore", "Low-FODMAP", "Whole30",
    "AIP (Autoimmune Protocol)", "Mediterranean", "DASH (Heart-Healthy)",
    "High-Protein", "Low-Carb", "Low-Fat", "Low-Sodium",
    "Low-Sugar / Diabetic-Friendly", "Anti-Inflammatory",
    "Low-Oxalate (Kidney-Friendly)", "GERD-Friendly (Low Acid)",
    "PKU (Low Phenylalanine)", "Renal Diet",
    "Halal", "Kosher", "Jain (No Onion/Garlic/Root Veg)", "Sattvic", "Buddhist Vegetarian",
    "Dairy-Free", "Lactose-Free", "Egg-Free", "Peanut-Free",
    "Nut-Free (Tree Nuts)", "Soy-Free", "Fish-Free", "Shellfish-Free",
    "Sesame-Free", "Mustard-Free", "Celery-Free", "Lupin-Free",
    "Mollusk-Free", "Corn-Free", "Coconut-Free", "Nightshade-Free",
    "Legume-Free", "Garlic-Free", "Onion-Free", "Citrus-Free",
    "Berry-Free", "Mushroom-Free", "Alpha-Gal (No Red Meat)",
    "Latex-Fruit Allergy (No Banana/Avocado/Kiwi)",
    "Fructose-Free", "Histamine-Free", "Sulfite-Free",
    "Salicylate-Free", "MSG-Free / Glutamate-Free",
    "Caffeine-Free", "Alcohol-Free (In Cooking)",
])
dietary = st.multiselect("🥗 Any other dietary needs? (Select all that apply)", all_dietary, default=[], key="dietary_select")

# Add Vegetarian if veg toggle is on, Non-Vegetarian if non-veg
if veg_choice == "🥦 Veg" and "Vegetarian" not in dietary:
    dietary = ["Vegetarian"] + list(dietary)
elif veg_choice == "🥚 Eggetarian":
    dietary = ["Eggetarian (vegetarian + eggs only, no meat/fish)"] + list(dietary)
elif veg_choice == "🍗 Non-Veg" and "Non-Vegetarian" not in dietary:
    protein_note = f"Non-Vegetarian (use these proteins: {", ".join(nonveg_proteins)})" if nonveg_proteins else "Non-Vegetarian (must include meat/seafood/eggs)"
    dietary = [protein_note] + list(dietary)

# Units stored in session state, configurable near recipe
if "unit_pref" not in st.session_state:
    st.session_state["unit_pref"] = "Metric (g, ml, °C)"
unit_sys = st.session_state["unit_pref"]

# Make My Recipe button
col_btn_l, col_btn_m, col_btn_r = st.columns([2, 1, 2])
with col_btn_m:
    go = st.button("✨ Make My Recipe!", type="primary", use_container_width=True)

st.markdown("<p style='text-align:center;font-size:1.2rem;letter-spacing:6px;margin:8px 0;opacity:1;'><span style='font-size:2rem;letter-spacing:12px;'>🔪 🧄 🧅 🍋 🌶️ 🧈 🍯 🫚 🌿 🧂 🥄 🍶 🫗 🥣</span></p>", unsafe_allow_html=True)
st.divider()

if go:
    if not all_api_keys:
        st.error("⚠️ API key not configured. Please contact the site administrator.")
        st.stop()
    if not dish.strip():
        st.warning("Please type a recipe name first.")
        st.stop()

    with st.spinner(f"Recreating recipe for {dish}..."):
        try:
            unit_val = "Metric" if "Metric" in unit_sys else "Imperial"
            keys_str = "|".join(all_api_keys)
            dietary_str = "|".join(dietary) if dietary else ""
            full_dish = dish.strip() + dish_extra
            recipe = cached_generate(keys_str, full_dish, model, country, dietary_str, unit_val)
            st.session_state["recipe"] = recipe
            st.session_state["recipe_country"] = country
            st.session_state["base_servings"] = int(recipe.get("servings", 4) or 4)
            st.session_state["current_servings"] = st.session_state.get("current_servings", 4)
            log_search(full_dish, country, dietary, source="search")
        except Exception as e:
            err = str(e)
            if any(x in err for x in ("429", "503", "404", "daily limit", "quota", "overloaded", "combinations")):
                st.warning(
                    "🕐 **Daily API limit reached.** All API keys and models are at their daily cap. "
                    "This resets at **midnight US Pacific time** (1:30 PM IST).\n\n"
                    "**To increase your daily quota for free:** Create additional Gmail accounts, "
                    "get an API key for each at [aistudio.google.com/apikey](https://aistudio.google.com/apikey), "
                    "and add them to Streamlit Secrets. Each key adds ~80 more recipes/day."
                )
            else:
                st.error(f"Error: {err}")
            st.stop()

# ─────────────────────────────────────────────
# Output Recipe Render Engine
# ─────────────────────────────────────────────
if "recipe" in st.session_state:
    recipe = st.session_state["recipe"]
    try:
        base_sv = int(st.session_state.get("base_servings", 4) or 4)
    except (ValueError, TypeError):
        base_sv = 4
    cur_sv = int(st.session_state.get("current_servings", base_sv))
    scale = cur_sv / base_sv if base_sv > 0 else 1

    title = recipe.get("dish_name", dish)
    naturally_gf = recipe.get("naturally_gluten_free", False)

    # ── HERO CARD ──
    badge_txt = "Naturally Gluten-Free ✓" if naturally_gf else "Gluten-Free Version"
    badge_cls = "hero-badge hero-badge-natural" if naturally_gf else "hero-badge"
    st.markdown(f"""
    <div class='recipe-hero'>
      <div class='recipe-hero-text'>
        <div class='{badge_cls}' style='color:#fff !important;'>{badge_txt}</div>
        <h2 style='color:#fff !important;'>{title}</h2>
        <div class='hero-sub' style='color:rgba(255,255,255,0.85) !important;'>{recipe.get('summary', '')}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)




    # ── DIETARY ADAPTATION NOTICE ──
    adaptation = recipe.get("dietary_adaptation") or ""
    if adaptation:
        st.markdown(f"""
        <div class='adapt-banner'>
          <div class='adapt-icon'>🔄</div>
          <div>
            <div class='adapt-title'>Dietary Adaptation</div>
            <div>{adaptation}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── SAFETY SCAN — check for potential gluten ingredients ──
    safety_warnings = scan_recipe_safety(recipe)
    if safety_warnings:
        st.markdown("<div class='sec-hdr' style='color:#C62828;'>🚨 Safety Alert — Potential Gluten Detected</div>", unsafe_allow_html=True)
        for w in safety_warnings:
            st.warning(w)
        st.markdown(
            "<p style='font-size:0.82rem;color:var(--ink-soft);margin-bottom:1rem;'>"
            "These ingredients were flagged by our automated safety scan. "
            "The AI may have included a non-GF ingredient by mistake. Please verify before cooking.</p>",
            unsafe_allow_html=True,
        )

    # ── METRICS STRIP ──
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    with col_m1:
        st.metric("Prep Time", recipe.get("prep_time", "N/A"))
    with col_m2:
        st.metric("Cook Time", recipe.get("cook_time", "N/A"))
    with col_m3:
        st.metric("Total Time", recipe.get("total_time", "N/A"))
    with col_m4:
        st.metric("Est. Calories", recipe.get("calories_per_serving", "N/A"))
    with col_m5:
        st.metric("Cuisine", recipe.get("cuisine", "General"))

    # ── BAKE / MARINATION TIME (shown only when present) ──
    bake_time = recipe.get("bake_time") or ""
    marination_time = recipe.get("marination_time") or ""
    if bake_time or marination_time:
        pills_html = "<div class='time-pills'>"
        if bake_time:
            pills_html += f"<span class='time-pill'><span class='time-pill-icon'>🔥</span><strong>Bake:</strong> {bake_time}</span>"
        if marination_time:
            pills_html += f"<span class='time-pill'><span class='time-pill-icon'>⏳</span><strong>Marination / Rest:</strong> {marination_time}</span>"
        pills_html += "</div>"
        st.markdown(pills_html, unsafe_allow_html=True)

    if naturally_gf:
        st.markdown("<div class='natural-box'>✅ This flavor blueprint is naturally gluten-free. Review potential contamination flags below.</div>", unsafe_allow_html=True)

    # ── DOWNLOAD ──
    recipe_text = recipe_to_text(recipe, cur_sv)

    # ── GLUTEN CONTAMINANTS ──
    sources = recipe.get("gluten_sources") or []
    if sources:
        st.markdown("<div class='sec-hdr' style='margin:1.5rem 0 0.5rem;'>⚠️ Gluten Contaminants</div>", unsafe_allow_html=True)
        tags = "".join(f"<span class='g-tag'>⚠️ {s}</span>" for s in sources)
        st.markdown(f"<div style='margin:0 0 0.5rem;'>{tags}</div>", unsafe_allow_html=True)

    # ── TWO COLUMN MAIN INTERACTIVE WORKSPACE ──
    col_left, col_right = st.columns([2, 3], gap="large")
    _show_timer_left = True
    _timer_val = 5

    with col_left:
        st.markdown("<div class='sec-hdr'>📋 Ingredients Checklist</div>", unsafe_allow_html=True)

        # Adjust servings — directly above ingredients
        new_sv = st.slider("🍽️ How many people are you cooking for?", 1, 20, int(cur_sv), key="adjust_servings_slider")
        if new_sv != cur_sv:
            st.session_state["current_servings"] = new_sv
            st.rerun()

        if scale != 1:
            st.markdown(f"<p style='font-size:0.82rem;color:#B26225;font-weight:600;'>📐 Quantities adjusted for {cur_sv} servings (recipe base: {base_sv})</p>", unsafe_allow_html=True)

        st.write("*What do you need to buy? Tick the items below:*")

        shopping_list = []
        for idx, ing in enumerate(recipe.get("ingredients", [])):
            amount = scale_amount(ing.get("amount", ""), scale) if scale != 1 else ing.get("amount", "")
            item_name = ing.get("item", "")
            emoji = ""  # emojis removed for cleaner look
            note = f" ({ing.get('note')})" if ing.get("note") else ""
            swap_indicator = " [GF Swap]" if ing.get("swap", False) else ""

            full_line = f"{amount} {item_name}{note}{swap_indicator}"

            needs_to_buy = st.checkbox(full_line, key=f"ing_check_{idx}")
            if needs_to_buy:
                shopping_list.append(f"• {amount} {item_name}{note}{swap_indicator}")

        if shopping_list:
            missing_text = "SHOPPING LIST\n" + "\n".join(shopping_list)
            st.download_button(
                "🛒 Download Shopping List",
                missing_text,
                file_name="shopping_list.txt",
                help="Downloads only the ingredients you ticked above."
            )

        # Units preference — below ingredients
        new_unit = st.radio("📏 Units", ["Metric (g, ml, °C)", "Imperial (oz, cups, °F)"], horizontal=True, key="unit_select")
        if new_unit != st.session_state.get("unit_pref"):
            st.session_state["unit_pref"] = new_unit

        # Kitchen Timer — compact, inside left column
        st.markdown("<div class='sec-hdr'>⏱️ Kitchen Timer</div>", unsafe_allow_html=True)
        _timer_val = st.number_input("Set minutes and press Enter:", min_value=1, max_value=180, value=5, step=1, key="timer_left")
        if _timer_val and _timer_val > 0:
            import streamlit.components.v1 as components
            components.html(f"""
            <html><head><style>
              *{{margin:0;padding:0;box-sizing:border-box;}}
              body{{font-family:sans-serif;background:transparent;text-align:center;padding:8px 0;}}
              #d{{font-size:2rem;font-weight:700;color:#D4603A;letter-spacing:2px;margin-bottom:8px;}}
              #d.w{{color:#C62828;}}
              .b{{display:flex;gap:8px;justify-content:center;}}
              .b button{{border:none;border-radius:6px;padding:6px 16px;font-weight:600;font-size:0.8rem;cursor:pointer;}}
              .s{{background:#D4603A;color:#fff;}}.p{{background:#C17817;color:#fff;}}.r{{background:#fff;color:#D4603A;border:1px solid #E8DDD0;}}
              button:disabled{{opacity:0.3;}}
              #dn{{display:none;margin-top:8px;padding:8px;background:#DEF2D6;border-radius:6px;color:#2E7D32;font-weight:700;font-size:0.85rem;}}
            </style></head><body>
              <div id="d">{_timer_val:02d}:00</div>
              <div class="b">
                <button class="s" id="sb" onclick="go()">▶ Start</button>
                <button class="p" id="pb" onclick="pa()" disabled>⏸ Pause</button>
                <button class="r" onclick="re()">↺ Reset</button>
              </div><div id="dn">🔔 Time's up!</div>
              <script>var t={_timer_val}*60,r=t,i=null,d=document.getElementById('d'),s=document.getElementById('sb'),p=document.getElementById('pb'),dn=document.getElementById('dn');
              function sh(){{var m=Math.floor(r/60),sec=r%60;d.textContent=(m<10?'0':'')+m+':'+(sec<10?'0':'')+sec;}}
              function go(){{if(i)return;dn.style.display='none';d.className='';s.disabled=true;p.disabled=false;i=setInterval(function(){{r--;sh();if(r<=10&&r>0)d.className='w';if(r<=0){{clearInterval(i);i=null;d.textContent='00:00';dn.style.display='block';s.disabled=false;p.disabled=true;s.textContent='▶ Start';}}}},1000);}}
              function pa(){{if(i){{clearInterval(i);i=null;s.disabled=false;s.textContent='▶ Resume';p.disabled=true;}}}}
              function re(){{clearInterval(i);i=null;r=t;sh();d.className='';dn.style.display='none';s.disabled=false;s.textContent='▶ Start';p.disabled=true;}}</script>
            </body></html>""", height=120)

    with col_right:
        st.markdown("<div class='sec-hdr'>👨‍🍳 Cooking Steps</div>", unsafe_allow_html=True)
        steps_html = "".join(
            f"<div class='step-block'><div class='step-n'>{idx}.</div><div class='step-t'>{step}</div></div>"
            for idx, step in enumerate(recipe.get("steps", []), 1)
        )
        st.markdown(
            f"<div style='background:var(--pastel-blue);border:1px solid var(--pastel-blue-b);border-radius:var(--r);padding:1.4rem 1.6rem;box-shadow:var(--shadow);'>{steps_html}</div>",
            unsafe_allow_html=True,
        )

        # Download button — bottom right after steps
        col_empty, col_dl, col_rpt = st.columns([2, 1, 1])
        with col_dl:
            st.download_button("📋 Download Recipe", recipe_text, file_name=f"{title.lower().replace(' ','_')}_recipe.txt", use_container_width=True)
        with col_rpt:
            if st.button("🚩 Incorrect Recipe", key="report_btn", use_container_width=True):
                log_search(f"REPORT: {recipe.get('dish_name','unknown')}", country, dietary, source="report")
                st.toast("🙏 Thank you for the feedback! We will work towards correcting this recipe.", icon="✅")



    # Render timer component (works for either position)
    # ── SUBSTITUTION ARCHITECTURE ──
    subs = recipe.get("substitutions") or []
    if subs:
        st.markdown("<div class='sec-hdr'>🔄 What Was Swapped & Why</div>", unsafe_allow_html=True)
        sub_cols = st.columns(2)
        for idx, s in enumerate(subs):
            brands_html = f"<div class='sub-brands'>🛒 Suggested: {s.get('local_brands', '')}</div>" if s.get('local_brands') else ""
            html = (
                f"<div class='sub-card'>"
                f"<div class='sub-head'>**{s.get('original','')}** → <span style='color:var(--amber);'>{s.get('replacement','')}</span></div>"
                f"<div class='sub-ratio'>*Formula Ratio:* {s.get('ratio','')}</div>"
                f"<div class='sub-why'>{s.get('reason','')}</div>"
                f"{brands_html}</div>"
            )
            with sub_cols[idx % 2]:
                st.markdown(html, unsafe_allow_html=True)

    # ── REGIONAL BRANDS AND SOURCING ──
    brands = recipe.get("brands_panel") or []
    if brands:
        r_country = st.session_state.get("recipe_country", country)
        c_name = r_country.split(' ', 1)[-1] if r_country != "🌍 Choose your country from the dropdown" else "your region"
        st.markdown(f"<div class='sec-hdr'>🏪 Recommended Brands in {c_name}</div>", unsafe_allow_html=True)
        bcols = st.columns(min(len(brands), 3))
        for i, b in enumerate(brands):
            initials = "".join(w[0].upper() for w in b.get("brand", "?").split()[:2])
            is_fully_gf = b.get("fully_gf", True)

            if is_fully_gf:
                # Green — certified safe
                logo_style = "color:#D4603A !important;background:#E8F5E9 !important;"
                badge_style = "color:#D4603A !important;background:#E8F5E9 !important;border:1px solid #E0D8CF;"
                card_style = ""
                name_style = "color:#D4603A;"
                desc_style = ""
            else:
                # Amber — contamination risk, entire card amber-tinted
                logo_style = "color:#7A4A1E !important;background:#FDEBD0 !important;border:1px solid #E8A84C;"
                badge_style = "color:#7A4A1E !important;background:#FDEBD0 !important;border:1px solid #E8A84C;"
                card_style = "border:2px solid #E8A84C !important;background:#FFF7ED !important;"
                name_style = "color:#B26225;"
                desc_style = "color:#7A4A1E;"

            c_badge = f"<span class='brand-cert' style='{badge_style}'>{b.get('certification','')}</span>" if b.get('certification') else ""
            risk_label = "" if is_fully_gf else "<div style='font-size:0.75rem;color:#B26225;font-weight:700;margin-top:6px;padding:4px 8px;background:#FDEBD0;border-radius:6px;border:1px solid #E8A84C;'>⚠️ Not fully GF — always check label</div>"
            html = (
                f"<div class='brand-item'>"
                f"<div class='brand-logo-placeholder' style='{logo_style}'>{initials}</div>"
                f"<div><div class='brand-name' style='{name_style}'>{b.get('brand','')} {c_badge}</div>"
                f"<div class='brand-desc' style='{desc_style}'><strong>{b.get('product','')}</strong><br>{b.get('where_to_buy','')}</div>"
                f"{risk_label}"
                f"</div></div>"
            )
            with bcols[i % 3]:
                st.markdown(f"<div class='brands-panel' style='{card_style}'>{html}</div>", unsafe_allow_html=True)

    # ── CRITICAL LABEL ALERT TRACKER ──
    checks = recipe.get("check_labels") or []
    if checks:
        st.markdown(
            f"<div class='warn-box'>⚠️ <strong>Check the label</strong> — buy certified gluten-free versions of: "
            f"{' · '.join(checks)}</div>",
            unsafe_allow_html=True,
        )

    # ── PRO TIPS, STORAGE, NUTRITION ──
    tips = recipe.get("tips") or []
    if tips:
        st.markdown("<div class='sec-hdr'>💡 Tips for Best Results</div>", unsafe_allow_html=True)
        tips_html = "".join(f"<div class='tip-row'><span>{t}</span></div>" for t in tips)
        st.markdown(f"<div style='background:var(--pastel-yellow); border:1px solid var(--pastel-yellow-b); padding:1rem; border-radius:var(--r);'>{tips_html}</div>", unsafe_allow_html=True)

    bot1, bot2 = st.columns(2)
    with bot1:
        if recipe.get("storage_info"):
            st.markdown(f"<div class='info-box' style='background:var(--pastel-blue);border-color:var(--pastel-blue-b);'><strong>🫙 Storage:</strong><br>{recipe.get('storage_info')}</div>", unsafe_allow_html=True)
    with bot2:
        if recipe.get("nutrition_notes"):
            st.markdown(f"<div class='info-box' style='background:var(--pastel-pink);border-color:var(--pastel-pink-b);'><strong>🥦 Nutrition Notes:</strong><br>{recipe.get('nutrition_notes')}</div>", unsafe_allow_html=True)

    # ── PERFECT PAIRINGS / ACCOMPANIMENTS ──
    accompaniments = recipe.get("accompaniments") or []
    if accompaniments:
        st.markdown("<div class='sec-hdr'>🍴 Potential Pairings</div>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-size:0.85rem;color:var(--ink-soft);margin-bottom:0.8rem;'>"
            "Gluten-free sides, drinks and extras that round out the meal.</p>",
            unsafe_allow_html=True,
        )
        type_icons = {
            "side": "🥗", "side dish": "🥗", "drink": "🥤", "beverage": "🥤",
            "dessert": "🍮", "sauce": "🥣", "salad": "🥬", "bread": "🥖",
            "appetizer": "🍢", "starter": "🍢", "soup": "🍲", "wine": "🍷",
        }
        pair_cols = st.columns(len(accompaniments))
        for i, ac in enumerate(accompaniments):
            ic = type_icons.get((ac.get("type", "") or "").lower().strip(), "🍽️")
            with pair_cols[i]:
                st.markdown(
                    f"<div class='pair-card'>"
                    f"<div class='pair-name'>{ac.get('name','')}</div>"
                    f"<div class='pair-type'>{ac.get('type','')}</div>"
                    f"<div class='pair-reason'>{ac.get('reason','')}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # ── ALTERNATIVE NAVIGATIONAL LINKS ──
    also_try = recipe.get("also_try") or []
    if also_try:
        st.markdown("<div class='sec-hdr'>🍽️ Other Dishes You Might Like to Try</div>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-size:0.85rem;color:var(--ink-soft);margin-bottom:0.8rem;'>"
            "Tap any dish to instantly generate its gluten-free recipe.</p>",
            unsafe_allow_html=True,
        )
        try_cols = st.columns(len(also_try))
        for i, at in enumerate(also_try):
            with try_cols[i]:
                st.markdown(f"""<div style='background:var(--pastel-yellow);border:1px solid var(--pastel-yellow-b);
                    border-radius:var(--r);padding:16px;text-align:center;'>
                    <p style='font-weight:600;font-size:0.95rem;color:var(--ink);margin-bottom:6px;'>🍴 {at.get('dish','')}</p>
                    <p style='font-size:0.8rem;color:var(--ink-soft);'>{at.get('reason','')}</p>
                </div>""", unsafe_allow_html=True)
                if st.button(f"Make this →", key=f"try_{i}", use_container_width=True):
                    st.session_state["_queued_dish"] = at.get("dish", "")
                    st.rerun()

    if "_queued_dish" in st.session_state:
        qd = st.session_state.pop("_queued_dish")
        st.session_state["_new_dish_name"] = qd  # Pass to text input on next rerun
        if qd and all_api_keys:
            with st.spinner(f"Recreating recipe for {qd}..."):
                try:
                    unit_val = "Metric" if "Metric" in unit_sys else "Imperial"
                    keys_str = "|".join(all_api_keys)
                    dietary_str = "|".join(dietary) if dietary else ""
                    recipe = cached_generate(keys_str, qd, model, country, dietary_str, unit_val)
                    st.session_state["recipe"] = recipe
                    st.session_state["recipe_country"] = country
                    st.session_state["base_servings"] = int(recipe.get("servings", servings) or servings)
                    st.session_state["current_servings"] = servings
                    log_search(qd, country, dietary, source="also_try")
                    st.session_state["_from_also_try"] = True
                    st.rerun()
                except Exception as e:
                    err = str(e)
                    if any(x in err for x in ("429", "503", "404", "daily limit", "quota")):
                        st.warning("🕐 Daily API limit reached. Please try again after midnight US Pacific time.")
                    else:
                        st.error(f"Error: {err}")

    st.markdown("<p style='text-align:center;font-size:1.3rem;letter-spacing:6px;margin:1.5rem 0 0.5rem;opacity:1;'><span style='font-size:2rem;letter-spacing:12px;'>🍽️ 👨‍🍳 🥄 🍴 🫕 🥘 🍲 🧑‍🍳 🥟 🫔 🥙 🌮 🍕 🍝</span></p>", unsafe_allow_html=True)

    # ── DISCLAIMER FOOTER ──
    if st.session_state.pop("_from_also_try", False):
        st.markdown(
            "<p style='text-align:center;color:#D4603A;font-weight:600;font-size:0.9rem;margin:1.5rem 0 0.5rem;'>⬆️ New recipe loaded! Scroll up to view it.</p>",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<div class='info-box' style='font-size:0.79rem;margin-top:1rem;'>ℹ️ AI-generated guidance only, not medical advice. "
        "If you have coeliac disease or serious gluten sensitivity, verify every ingredient label independently "
        "and be vigilant about cross-contamination.</div>",
        unsafe_allow_html=True,
    )
