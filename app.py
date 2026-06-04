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
    "gemini-2.5-flash-lite",   # ~20/day free
    "gemini-2.5-flash",        # ~250/day free
]

# ─────────────────────────────────────────────
# 🔑 API KEY — Paste your Gemini key here.
#    Get a free key at: https://aistudio.google.com/apikey
# ─────────────────────────────────────────────
HARDCODED_API_KEY = ""   # ← Paste your key inside the quotes

COUNTRIES = [
    "🌍 Global / International",
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

DIETARY_TAGS = ["None", "Vegan", "Vegetarian", "Dairy-Free", "Nut-Free", "Low-FODMAP", "Keto", "Paleo"]

# ─────────────────────────────────────────────
# CSS - Sage Green Palette Makeover
# ─────────────────────────────────────────────
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Outfit:wght@300;400;500;600&display=swap');

:root {
  --ink:      #1C2A1E;
  --ink-mid:  #3D4F40;
  --ink-soft: #6A7E6E;
  --bg:       #EBF1EC; /* Sage green background */
  --bg2:      #DCE4DC; /* Sidebar background sage */
  --border:   #CCD5CD;
  --green:    #2F5435; /* Forest accent green */
  --green-l:  #E2ECE5;
  --amber:    #B26225;
  --amber-l:  #FDF3EB;
  --red-l:    #FCECEC;
  --red:      #9E2A2B;
  --card:     #FFFFFF;
  --shadow:   0 8px 30px rgba(28,42,30,0.08);
  --r:        14px;
}

/* ── Dark mode: swap colors for users with dark system/browser theme ── */
@media (prefers-color-scheme: dark) {
  :root {
    --ink:      #1C2A1E;
    --ink-mid:  #3D4F40;
    --ink-soft: #6A7E6E;
    --bg:       #EBF1EC;
    --bg2:      #DCE4DC;
    --border:   #CCD5CD;
    --green:    #2F5435;
    --green-l:  #E2ECE5;
    --amber:    #B26225;
    --amber-l:  #FDF3EB;
    --red-l:    #FCECEC;
    --red:      #9E2A2B;
    --card:     #FFFFFF;
    --shadow:   0 8px 30px rgba(28,42,30,0.08);
  }
}

/* Also handle Streamlit's own theme attribute */
[data-theme="dark"] {
    --ink:      #1C2A1E;
    --ink-mid:  #3D4F40;
    --ink-soft: #6A7E6E;
    --bg:       #EBF1EC;
    --bg2:      #DCE4DC;
    --border:   #CCD5CD;
    --green:    #2F5435;
    --green-l:  #E2ECE5;
    --amber:    #B26225;
    --amber-l:  #FDF3EB;
    --red-l:    #FCECEC;
    --red:      #9E2A2B;
    --card:     #FFFFFF;
    --shadow:   0 8px 30px rgba(28,42,30,0.08);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* Prevent black/blank screen while Streamlit loads on mobile */
html, body {
  background-color: #EBF1EC !important;
  color: #1C2A1E !important;
  -webkit-text-size-adjust: 100%;
}
@media (prefers-color-scheme: dark) {
  html, body {
    background-color: #EBF1EC !important;
    color: #1C2A1E !important;
  }
}
.stApp, .main, [data-testid="stAppViewBlockContainer"] {
  background-color: var(--bg) !important;
}
iframe { background-color: var(--card) !important; }

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  font-family: 'Outfit', sans-serif !important;
  color: var(--ink) !important;
}

/* Force ALL Streamlit text to follow our theme variables */
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] span,
[data-testid="stAppViewContainer"] div,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
.stMarkdown, .stMarkdown p {
  color: var(--ink) !important;
}
[data-testid="stExpander"] summary span { color: var(--ink) !important; }
[data-testid="stMetricValue"] { color: var(--green) !important; }
[data-testid="stMetricLabel"] p { color: var(--ink-soft) !important; }

#MainMenu, footer { visibility: hidden; }
/* Hide the header bar entirely — removes the broken "keyboard_double_" icon text */
header[data-testid="stHeader"] { display: none !important; }
[data-testid="stDecoration"] { display: none; }
/* Hide the sidebar collapse button so users can't close it (avoids the broken icon) */
[data-testid="stSidebarCollapseButton"] { display: none !important; }
button[kind="headerNoPadding"] { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--bg2) !important;
  border-right: 1px solid var(--border) !important;
}
/* Scope font to TEXT elements only — wildcard * breaks the Material Icons collapse arrow */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] .stMarkdown { font-family: 'Outfit', sans-serif !important; }
[data-testid="stSidebar"] label { font-size: 0.82rem !important; font-weight: 600 !important; letter-spacing: 0.3px !important; color: var(--ink-soft) !important; text-transform: uppercase !important; }

/* ── Typography ── */
h1, h2, h3 { font-family: 'Cormorant Garamond', serif !important; }
h1 { font-size: 3.2rem !important; font-weight: 700 !important; letter-spacing: -1px; line-height: 1.1 !important; color: var(--green) !important; }

/* ── Buttons ── */
div.stButton > button[kind="primary"],
button[kind="primaryFormSubmit"],
div.stFormSubmitButton > button,
[data-testid="stFormSubmitButton"] > button {
  background: var(--green) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 10px !important;
  font-family: 'Outfit', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.92rem !important;
  padding: 0.6rem 1.6rem !important;
  letter-spacing: 0.2px;
  transition: all 0.18s ease !important;
}
div.stButton > button[kind="primary"]:hover,
button[kind="primaryFormSubmit"]:hover,
div.stFormSubmitButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
  background: #1C3321 !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(47,84,53,0.3) !important;
}
div.stButton > button:not([kind="primary"]) {
  background: var(--card) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 10px !important;
  font-family: 'Outfit', sans-serif !important;
  font-weight: 500 !important;
  font-size: 0.85rem !important;
  color: var(--ink-mid) !important;
  transition: all 0.15s ease !important;
}
div.stButton > button:not([kind="primary"]):hover { border-color: var(--green) !important; color: var(--green) !important; }

/* ── Inputs ── */
div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] > div > div {
  border-radius: 10px !important;
  border-color: var(--border) !important;
  background: #FFFFFF !important;
  color: #1C2A1E !important;
  font-family: 'Outfit', sans-serif !important;
}

/* ══════════════════════════════════════════════════════
   FORCE ALL WIDGETS LEGIBLE — overrides dark mode
   ══════════════════════════════════════════════════════ */

/* Text inputs, textareas, number inputs */
input, textarea, [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
  background-color: #FFFFFF !important;
  color: #1C2A1E !important;
  caret-color: #1C2A1E !important;
}

/* Selectbox / dropdown */
[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #1C2A1E !important; }
[data-baseweb="select"] span { color: #1C2A1E !important; }
[data-baseweb="popover"] { background-color: #FFFFFF !important; }
[data-baseweb="popover"] li { color: #1C2A1E !important; }
[data-baseweb="popover"] li:hover { background-color: var(--green-l) !important; }

/* Download buttons — force white bg with dark text */
[data-testid="stDownloadButton"] button,
[data-testid="stDownloadButton"] > button {
  background-color: #FFFFFF !important;
  color: #1C2A1E !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 10px !important;
  font-family: 'Outfit', sans-serif !important;
  font-weight: 500 !important;
}
[data-testid="stDownloadButton"] button:hover {
  background-color: var(--green-l) !important;
  border-color: var(--green) !important;
  color: var(--green) !important;
}

/* Slider — force green track instead of red */
[data-testid="stSlider"] [role="slider"] { background: var(--green) !important; }
[data-testid="stSlider"] [data-baseweb="slider"] div[role="progressbar"] > div { background: var(--green) !important; }
[data-baseweb="slider"] div { background-color: var(--border) !important; }
[data-baseweb="slider"] div[role="progressbar"] > div:first-child { background-color: var(--green) !important; }
[data-baseweb="slider"] [role="slider"] { background-color: var(--green) !important; border-color: var(--green) !important; }
[data-testid="stSlider"] p { color: var(--ink) !important; }

/* Number input */
[data-testid="stNumberInput"] input { background-color: #FFFFFF !important; color: #1C2A1E !important; }
[data-testid="stNumberInput"] button { background-color: #FFFFFF !important; color: #1C2A1E !important; }

/* Radio buttons */
[data-testid="stRadio"] label span { color: #1C2A1E !important; }
[data-testid="stRadio"] div[role="radiogroup"] label { color: #1C2A1E !important; }

/* Checkboxes */
[data-testid="stCheckbox"] label span { color: #1C2A1E !important; }

/* Expander */
[data-testid="stExpander"] { background: #FFFFFF !important; border-color: var(--border) !important; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary span { color: #1C2A1E !important; }
[data-testid="stExpander"] div { color: #1C2A1E !important; }

/* Markdown text inside all containers */
.stMarkdown p, .stMarkdown li, .stMarkdown span { color: #1C2A1E !important; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: var(--green) !important; }

/* ══ WHITE TEXT EXCEPTIONS — elements with dark/green backgrounds ══ */
/* Form submit / primary buttons */
div.stButton > button[kind="primary"],
div.stButton > button[kind="primary"] span,
div.stButton > button[kind="primary"] p,
button[kind="primaryFormSubmit"],
button[kind="primaryFormSubmit"] span,
button[kind="primaryFormSubmit"] p,
div.stFormSubmitButton > button,
div.stFormSubmitButton > button span,
div.stFormSubmitButton > button p,
[data-testid="stFormSubmitButton"] > button,
[data-testid="stFormSubmitButton"] > button span,
[data-testid="stFormSubmitButton"] > button p { color: #FFFFFF !important; }

/* Step number circles */
.step-n, .step-n span, .step-n p, .step-n div { color: #FFFFFF !important; }

/* Brand logo initials */
.brand-logo-placeholder, .brand-logo-placeholder span,
.brand-logo-placeholder p, .brand-logo-placeholder div { color: #FFFFFF !important; }

/* Brand certification badges */
.brand-cert, .brand-cert span, .brand-cert p { color: #FFFFFF !important; }

/* Hero card — all text white */
.recipe-hero h2, .recipe-hero p, .recipe-hero span, .recipe-hero div,
.recipe-hero-text h2, .recipe-hero-text p, .recipe-hero-text span,
.recipe-hero-text div, .recipe-hero-text .hero-sub,
.hero-badge, .hero-badge span { color: #FFFFFF !important; }

/* Natural box / adaptation banner text stays dark */
.natural-box, .natural-box span, .natural-box p { color: var(--green) !important; }
.adapt-banner, .adapt-banner div, .adapt-banner span, .adapt-banner p { color: #1C2A1E !important; }
.adapt-title { color: var(--amber) !important; }

/* Form container background */
[data-testid="stForm"] { background-color: transparent !important; border: none !important; }

/* ── Recipe Hero Card ── */
.recipe-hero {
  position: relative;
  width: 100%;
  background: linear-gradient(135deg, var(--green) 0%, #152618 100%);
  border-radius: var(--r);
  overflow: visible;
  margin: 1.4rem 0 0 0;
  box-shadow: var(--shadow);
  padding: 2.5rem;
  min-height: auto;
  border-left: 6px solid var(--amber);
}
.recipe-hero-text h2 {
  font-family: 'Cormorant Garamond', serif !important;
  font-size: 2.8rem !important;
  font-weight: 700 !important;
  color: #fff !important;
  line-height: 1.15 !important;
}
.recipe-hero-text .hero-sub {
  color: rgba(255,255,255,0.85);
  font-size: 1rem;
  margin-top: 8px;
  font-family: 'Outfit', sans-serif;
  line-height: 1.5;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: normal;
}
.hero-badge {
  display: inline-block;
  background: rgba(255,255,255,0.2);
  backdrop-filter: blur(4px);
  color: #fff;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  padding: 4px 12px;
  border-radius: 100px;
  margin-bottom: 12px;
  border: 1px solid rgba(255,255,255,0.3);
}
.hero-badge-natural { background: var(--amber); border-color: transparent; }

/* ── Meta pills ── */
.meta-strip {
  display: flex; gap: 10px; flex-wrap: wrap;
  margin: 1.1rem 0;
}
.mpill {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 100px;
  padding: 6px 16px;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--ink-mid);
  display: inline-flex; align-items: center; gap: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}

/* ── Difficulty meter ── */
.diff-wrap { display: flex; align-items: center; gap: 10px; margin: 0.4rem 0 1rem; }
.diff-bar { flex: 1; height: 6px; background: var(--border); border-radius: 100px; overflow: hidden; }
.diff-fill { height: 100%; border-radius: 100px; transition: width 0.6s ease; }
.diff-label { font-size: 0.78rem; font-weight: 600; min-width: 56px; }

/* ── Section headers ── */
.sec-hdr {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--green);
  border-bottom: 2px solid var(--green);
  padding-bottom: 5px;
  margin: 1.8rem 0 1rem;
  display: flex; align-items: center; gap: 8px;
}

/* ── Ingredients ── */
.ing-table { width: 100%; border-collapse: collapse; }
.ing-table tr { border-bottom: 1px solid var(--border); }
.ing-table tr:last-child { border-bottom: none; }
.ing-table td { padding: 11px 6px; font-size: 0.9rem; vertical-align: top; }
.ing-amt { font-weight: 600; color: var(--amber); width: 95px; }
.ing-item { color: var(--ink); }
.ing-note-text { font-size: 0.76rem; color: var(--ink-soft); font-style: italic; display: block; margin-top: 1px; }
.swap-chip {
  background: var(--green-l);
  color: var(--green);
  border: 1px solid #B4CDBA;
  border-radius: 6px;
  font-size: 0.68rem;
  font-weight: 700;
  padding: 2px 8px;
  white-space: nowrap;
  vertical-align: middle;
  margin-left: 4px;
}

/* ── Substitution cards ── */
.sub-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 4px solid var(--amber);
  border-radius: 0 var(--r) var(--r) 0;
  padding: 14px 16px;
  margin-bottom: 12px;
  box-shadow: var(--shadow);
}
.sub-head { font-weight: 600; font-size: 0.95rem; color: var(--ink); }
.sub-ratio { font-size: 0.76rem; color: var(--ink-soft); margin-top: 2px; }
.sub-why { font-size: 0.86rem; margin-top: 6px; line-height: 1.5; color: var(--ink-mid); }
.sub-brands { font-size: 0.77rem; color: var(--green); margin-top: 6px; font-weight: 500; }

/* ── Brands Panel ── */
.brands-panel {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 1.2rem;
  box-shadow: var(--shadow);
}
.brand-item {
  display: flex; align-items: flex-start; gap: 12px;
}
.brand-logo-placeholder {
  width: 40px; height: 40px; border-radius: 8px;
  background: var(--green); display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 0.8rem; font-weight: 700; flex-shrink: 0;
}
.brand-name { font-weight: 600; font-size: 0.9rem; color: var(--green); }
.brand-desc { font-size: 0.82rem; color: var(--ink-mid); margin-top: 3px; line-height: 1.45; }
.brand-cert { font-size: 0.7rem; background: var(--green); color: #fff; border-radius: 6px; padding: 1px 7px; margin-left: 6px; font-weight: 600; }

/* ── Gluten danger tags ── */
.g-tag { display: inline-block; background: var(--red-l); border: 1px solid #E2B3B3; color: var(--red); border-radius: 7px; font-size: 0.76rem; padding: 4px 10px; margin: 3px 3px 3px 0; font-weight: 500; }

/* ── Tips ── */
.tip-row { display: flex; gap: 10px; align-items: flex-start; padding: 10px 0; border-bottom: 1px dashed var(--border); font-size: 0.9rem; }
.tip-row:last-child { border-bottom: none; }

/* ── Also try ── */
.try-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 14px 16px;
  cursor: pointer;
  transition: all 0.18s ease;
  text-align: center;
}
.try-card:hover { border-color: var(--green); box-shadow: 0 4px 16px rgba(47,84,53,0.15); transform: translateY(-2px); }

/* ── Info / warn boxes ── */
.warn-box { background: var(--amber-l); border: 1px solid #E5C3A5; border-left: 4px solid var(--amber); border-radius: 10px; padding: 13px 17px; font-size: 0.88rem; color: #6E3A0F; margin: 0.8rem 0; }
.info-box { background: var(--card); border: 1px solid var(--border); border-left: 4px solid var(--green); border-radius: 10px; padding: 13px 17px; font-size: 0.88rem; color: var(--ink); margin: 0.8rem 0; }
.natural-box { background: #E4EFE5; border: 1px solid #B4D3B8; border-radius: 12px; padding: 13px 17px; color: var(--green); font-weight: 600; margin: 0.6rem 0; }

/* ── Interactive Kitchen Hub Components ── */
.interactive-panel {
  background: var(--card);
  border: 1.5px solid var(--border);
  border-radius: var(--r);
  padding: 1.25rem;
  margin-bottom: 1rem;
  box-shadow: var(--shadow);
}
.cooking-done-step {
  text-decoration: line-through;
  opacity: 0.55;
  transition: all 0.2s ease;
}

/* ── Dynamic Layout Styles ── */
[data-testid="stMetricValue"] {
  font-size: 1.1rem !important;
  font-weight: 700 !important;
  color: var(--green) !important;
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: unset !important;
  line-height: 1.3 !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
}
[data-testid="stMetricLabel"] { overflow: visible !important; white-space: normal !important; }

/* ── Metric cards ── */
[data-testid="stMetric"] {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  text-align: center;
  box-shadow: var(--shadow);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
  overflow: visible !important;
  min-height: 90px;
}
[data-testid="stMetric"]:hover { transform: translateY(-2px); box-shadow: 0 8px 22px rgba(47,84,53,0.14); }
[data-testid="stMetric"] > div { overflow: visible !important; }
[data-testid="stMetric"] [data-testid="stMetricValue"] > div { overflow: visible !important; text-overflow: unset !important; }

/* Smooth hover on substitution & brand cards */
.sub-card, .brands-panel { transition: transform 0.18s ease, box-shadow 0.18s ease; }
.sub-card:hover, .brands-panel:hover { transform: translateY(-2px); box-shadow: 0 8px 22px rgba(47,84,53,0.12); }

/* ── Numbered cooking steps ── */
.step-block { display: flex; gap: 14px; align-items: flex-start; margin-bottom: 1.1rem; }
.step-block:last-child { margin-bottom: 0; }
.step-n {
  min-width: 30px; height: 30px; border-radius: 50%;
  background: var(--green); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.82rem; font-weight: 700; flex-shrink: 0; margin-top: 2px;
}
.step-t { font-size: 0.92rem; line-height: 1.65; color: var(--ink); }

/* ── Ingredient emoji ── */
.ing-emoji { font-size: 0.95rem; margin-right: 7px; }

/* ── Perfect pairings cards ── */
.pair-card {
  background: linear-gradient(160deg, var(--card) 0%, var(--green-l) 100%);
  border: 1.5px solid var(--border); border-radius: var(--r);
  padding: 18px 16px; text-align: center; height: 100%;
  transition: all 0.2s ease;
}
.pair-card:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(47,84,53,0.16); border-color: var(--green); }
.pair-icon { font-size: 2rem; margin-bottom: 6px; }
.pair-name { font-family: 'Cormorant Garamond', serif; font-size: 1.2rem; font-weight: 700; color: var(--green); line-height: 1.2; }
.pair-type { font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.7px; color: var(--amber); font-weight: 700; margin-top: 3px; }
.pair-reason { font-size: 0.8rem; color: var(--ink-mid); margin-top: 8px; line-height: 1.5; }

/* ── Dish hero image ── */
.dish-img-wrap {
  width: 100%; height: 320px; border-radius: var(--r);
  overflow: hidden; margin: 1rem 0; box-shadow: var(--shadow);
  border: 1px solid var(--border);
}
.dish-img-wrap img {
  width: 100%; height: 100%; object-fit: cover; display: block;
  transition: transform 0.4s ease;
}
.dish-img-wrap:hover img { transform: scale(1.03); }

/* ── Dietary adaptation banner ── */
.adapt-banner {
  background: linear-gradient(135deg, #F0F7F1 0%, #E6F0E0 100%);
  border: 1px solid var(--green-l);
  border-left: 5px solid var(--amber);
  border-radius: 0 var(--r) var(--r) 0;
  padding: 14px 20px;
  margin: 0.8rem 0;
  display: flex; align-items: flex-start; gap: 12px;
  font-size: 0.9rem; line-height: 1.55;
  color: var(--ink);
}
.adapt-icon { font-size: 1.4rem; flex-shrink: 0; }
.adapt-title { font-weight: 700; color: var(--amber); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }

/* ── Extra time pills ── */
.time-pills { display: flex; gap: 8px; flex-wrap: wrap; margin: 0.5rem 0 0.8rem; }
.time-pill {
  background: var(--card); border: 1px solid var(--border); border-radius: 100px;
  padding: 6px 16px; font-size: 0.82rem; font-weight: 500; color: var(--ink-mid);
  display: inline-flex; align-items: center; gap: 6px;
}
.time-pill-icon { font-size: 1rem; }
</style>
"""

# ─────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────
SYSTEM_INSTRUCTION_TEMPLATE = """You are an expert recipe developer and food scientist who specialises in \
gluten-free cooking. The user is located in: {country}. Tailor ALL ingredient suggestions and brand recommendations \
to what is realistically available in that country.

{dietary_note}

Your job: produce a complete, cookable gluten-free version of the dish that preserves original flavour/texture.
Tailor all quantities and temperatures to the {unit_system} system (e.g. Metric: grams, ml, Celsius; or Imperial: cups, oz, Fahrenheit).

Process:
1. Identify EVERY gluten source (obvious + sneaky: soy sauce, malt vinegar, roux, seitan, spice blends, couscous).
2. For each, choose a substitution matching its FUNCTION (structure/binding/thickening/crisp coating/flavour) — not just "GF flour". Give realistic ratios (GF subs rarely swap 1:1; may need xanthan gum, starch blends).
3. Write complete recipe with real quantities and clear steps.
4. Flag ingredients that are NOT ALWAYS GF (soy sauce, oats, stock, baking powder, spice mixes).
5. Mention cross-contamination risks.
6. For the brands_panel, list 3–5 actual certified gluten-free brands available in {country} that make the most critical substitution ingredients. For each brand include: name, what product, certification body (e.g. GFFS, NFCA, Coeliac UK), and a brief note on where to buy.
7. Suggest 3 "also_try" naturally-GF dishes similar in flavour profile AND from the same cuisine family. \
For example: if the dish is Indian, suggest other Indian GF dishes like dal tadka or rajma. \
If it's Italian, suggest risotto or polenta-based dishes. Do NOT mix cuisines randomly.
8. Suggest 3 "accompaniments" — side dishes, drinks, or extras that pair well with this dish. \
CRITICAL: The accompaniments MUST be culturally and culinarily appropriate for the dish's cuisine. \
For example: roti pairs with dal/raita/sabzi, NOT chicken sausage. Pasta pairs with garlic bread/salad, NOT naan. \
Sushi pairs with miso soup/edamame, NOT coleslaw. Think about what a person from that cuisine's culture would \
actually eat alongside this dish. Each accompaniment must itself be gluten-free or trivially made GF. \
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
  "brands_panel": [{{"brand": string, "product": string, "certification": string, "where_to_buy": string}}],
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
def generate_recipe(dish, api_key, model, country, dietary, base_servings=None, unit_system="Metric"):
    """Generate a recipe. Tries each fallback model before giving up."""
    dietary_note = ""
    if dietary and dietary != "None":
        dietary_note = f"""CRITICAL DIETARY RESTRICTION: The recipe MUST be {dietary}.
This is a hard constraint — it overrides the original dish if there is a conflict.
For example, if the user asks for "Chicken Tikka" but the dietary restriction is "Vegetarian",
you MUST replace the chicken with a vegetarian protein (e.g. paneer, tofu, chickpeas) and
rename the dish accordingly (e.g. "Paneer Tikka" or "Vegetarian Tikka").
NEVER include any ingredient that violates the {dietary} restriction.
Double-check every single ingredient against the {dietary} requirement before including it."""

    system_prompt = SYSTEM_INSTRUCTION_TEMPLATE.format(
        country=country,
        dietary_note=dietary_note,
        unit_system=unit_system
    )

    serving_note = ""
    if base_servings:
        serving_note = f" Make the recipe for {base_servings} servings."

    dietary_user_note = f" IMPORTANT: This must be {dietary}." if dietary and dietary != "None" else ""

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": f"Create a gluten-free recipe for: {dish}.{serving_note}{dietary_user_note}"}]}],
        "generationConfig": {"response_mime_type": "application/json", "temperature": 0.7},
    }

    models_to_try = [model] + [m for m in FALLBACK_MODELS if m != model]
    resp = None
    last_err = None

    for m in models_to_try:
        url = f"{API_BASE}/{m}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, json=payload, timeout=60)
        except requests.exceptions.RequestException as e:
            last_err = RuntimeError(f"Network error: {e}")
            resp = None
            continue

        if resp.status_code == 200:
            break

        try:
            msg = resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            msg = resp.text

        last_err = RuntimeError(f"API error ({resp.status_code}): {msg}")
        resp = None
        continue  # try next model

    if resp is None or resp.status_code != 200:
        raise last_err or RuntimeError("All models at daily limit. Resets at midnight US Pacific time.")

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
    """Safely scale fractions, integer, and decimal amounts of ingredients."""
    import re
    m = re.match(r'^(\d+\.?\d*|\d*/\d+)\s*(.*)', amount_str.strip())
    if not m:
        return amount_str
    num_str, rest = m.group(1), m.group(2)
    try:
        if '/' in num_str:
            n, d = num_str.split('/')
            num = float(n) / float(d)
        else:
            num = float(num_str)
        scaled = num * factor
        if scaled == int(scaled):
            return f"{int(scaled)} {rest}".strip()
        else:
            return f"{scaled:.2g} {rest}".strip()
    except Exception:
        return amount_str

def difficulty_meta(diff_str):
    d = (diff_str or "Medium").strip().title()
    if d == "Easy":   return 33, "#3A5F43", "Easy"
    if d == "Hard":   return 100, "#9E2B2B", "Hard"
    return 66, "#B26225", "Medium"

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
# Page Setup
# ─────────────────────────────────────────────
st.set_page_config(page_title="Gluten-Free Spree", page_icon="🍽️", layout="wide", initial_sidebar_state="expanded")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Sidebar Workspace Controllers
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("<p style='font-family:Cormorant Garamond,serif;font-size:1.75rem;font-weight:700;color:#1C2A1E;margin-bottom:2px;'>Gluten-Free Spree</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.8rem;color:#6A7E6E;margin-bottom:1rem;'>Your gluten-free recipe companion</p>", unsafe_allow_html=True)
    st.divider()

    # API key — loaded silently
    api_key = HARDCODED_API_KEY or ""
    if not api_key:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            api_key = ""

    # Model is set from the constant — no user-facing input
    model = DEFAULT_MODEL

    country_choice = st.radio("📍 Your Country", ["🇮🇳 India", "🌍 Other"], horizontal=True, key="country_radio")
    if country_choice == "🌍 Other":
        other_countries = [c for c in COUNTRIES if "India" not in c]
        country = st.selectbox("Select your country", other_countries, index=0, label_visibility="collapsed", key="country_select")
    else:
        country = "🇮🇳 India"
    dietary = st.selectbox("🥗 Dietary Need", DIETARY_TAGS, index=0, key="dietary_select")
    unit_sys = st.selectbox("📏 Preferred Units", ["Metric (g, ml, °C)", "Imperial (oz, cups, °F)"], index=0, key="unit_select")
    servings = st.slider("🍽️ Servings", 1, 12, 4, key="servings_slider")
    st.divider()

# ─────────────────────────────────────────────
# Main App Header
# ─────────────────────────────────────────────
st.markdown("""
<div style='padding:0.5rem 0 1rem;'>
  <h1>Gluten-Free Spree</h1>
  <p style='color:var(--ink-mid); font-size:1.1rem; margin-top:2px;'>
    Culinary recreation for safe gluten-free dining.
  </p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Search Bar Interface
# ─────────────────────────────────────────────
with st.form("recipe_form", clear_on_submit=False):
    col_input, col_btn = st.columns([5, 1], vertical_alignment="bottom")
    with col_input:
        dish = st.text_input(
            "Enter a dish to recreate gluten-free:",
            placeholder="e.g., Ramen, Chicken Schnitzel, Naan Bread, Croissants, Pasta Carbonara...",
        )
    with col_btn:
        go = st.form_submit_button("✨ Recreate", type="primary", use_container_width=True)

st.markdown(
    "<p style='font-size:0.82rem;color:var(--ink-soft);margin-top:5px;'>"
    "Trending: <em>Gyoza Dumplings · Yorkshire Pudding · Tempura · Sourdough Bread · Tiramisu</em></p>",
    unsafe_allow_html=True,
)
st.divider()

if go:
    if not api_key:
        st.error("⚠️ API key not configured. Please contact the site administrator.")
        st.stop()
    if not dish.strip():
        st.warning("Please type a recipe name first.")
        st.stop()

    with st.spinner(f"Recreating recipe for {dish}..."):
        try:
            # Derive short system metric identifier
            unit_val = "Metric" if "Metric" in unit_sys else "Imperial"
            recipe = generate_recipe(dish.strip(), api_key, model, country, dietary, servings, unit_val)
            st.session_state["recipe"] = recipe
            st.session_state["base_servings"] = recipe.get("servings", servings) or servings
            st.session_state["current_servings"] = servings
        except Exception as e:
            err = str(e)
            if any(x in err for x in ("429", "503", "404", "daily limit", "quota", "overloaded")):
                st.warning(
                    "🕐 **Daily API limit reached.** I tried 4 different models but they're all "
                    "at their daily cap. This resets at **midnight US Pacific time**.\n\n"
                    "**Quick fix:** Create a second free API key with a different Gmail account "
                    "at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) "
                    "and paste it into the `HARDCODED_API_KEY` line in app.py."
                )
            else:
                st.error(f"Error: {err}")
            st.stop()

# ─────────────────────────────────────────────
# Output Recipe Render Engine
# ─────────────────────────────────────────────
if "recipe" in st.session_state:
    recipe = st.session_state["recipe"]
    base_sv = st.session_state.get("base_servings", 4) or 4
    cur_sv  = st.session_state.get("current_servings", base_sv)
    scale   = cur_sv / base_sv if base_sv else 1

    title = recipe.get("dish_name", dish)
    naturally_gf = recipe.get("naturally_gluten_free", False)

    # ── HERO CARD ──
    badge_txt = "Naturally Gluten-Free ✓" if naturally_gf else "Gluten-Free Version"
    badge_cls = "hero-badge hero-badge-natural" if naturally_gf else "hero-badge"
    st.markdown(f"""
    <div class='recipe-hero'>
      <div class='recipe-hero-text'>
        <div class='{badge_cls}'>{badge_txt}</div>
        <h2>{title}</h2>
        <div class='hero-sub'>{recipe.get('summary', '')}</div>
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

    # ── METRICS STRIP ──
    diff_pct, diff_color, diff_label = difficulty_meta(recipe.get("difficulty"))

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

    st.markdown(f"""
    <div class='diff-wrap'>
      <span style='font-size:0.85rem;color:var(--ink-mid);font-weight:600;min-width:70px;'>Difficulty:</span>
      <div class='diff-bar'><div class='diff-fill' style='width:{diff_pct}%;background:{diff_color};'></div></div>
      <span class='diff-label' style='color:{diff_color};'>{diff_label}</span>
    </div>
    """, unsafe_allow_html=True)

    if naturally_gf:
        st.markdown("<div class='natural-box'>✅ This flavor blueprint is naturally gluten-free. Review potential contamination flags below.</div>", unsafe_allow_html=True)

    # ── METRIC CONTROLS & DOWNLOADING ──
    col_sc, col_cp = st.columns([3, 2])
    with col_sc:
        new_sv = st.slider("🍽️ Adjust Servings", 1, 20, int(cur_sv))
        if new_sv != cur_sv:
            st.session_state["current_servings"] = new_sv
            st.rerun()
    with col_cp:
        recipe_text = recipe_to_text(recipe, cur_sv)
        st.download_button("📋 Download Recipe", recipe_text, file_name=f"{title.lower().replace(' ','_')}_recipe.txt", use_container_width=True)

    # ── NATIVE GLUTEN IDENTIFIED RISKS ──
    sources = recipe.get("gluten_sources") or []
    if sources:
        tags = "".join(f"<span class='g-tag'>⚠️ {s}</span>" for s in sources)
        st.markdown(f"<div style='margin:1rem 0;'>{tags}</div>", unsafe_allow_html=True)

    # ── TWO COLUMN MAIN INTERACTIVE WORKSPACE ──
    col_left, col_right = st.columns([2, 3], gap="large")

    with col_left:
        st.markdown("<div class='sec-hdr'>📋 Ingredients Checklist</div>", unsafe_allow_html=True)
        st.write("*Tick off what you already have — the rest becomes your shopping list:*")

        shopping_list = []
        for idx, ing in enumerate(recipe.get("ingredients", [])):
            amount = scale_amount(ing.get("amount", ""), scale) if scale != 1 else ing.get("amount", "")
            item_name = ing.get("item", "")
            emoji = (ing.get("emoji", "") or "🍽️").strip()
            note = f" ({ing.get('note')})" if ing.get("note") else ""
            swap_indicator = " [GF Swap]" if ing.get("swap", False) else ""

            full_line = f"{emoji} {amount} {item_name}{note}{swap_indicator}"

            # Checkbox interactive ingredient tracker
            is_owned = st.checkbox(full_line, key=f"ing_check_{idx}")
            if not is_owned:
                shopping_list.append(f"• {amount} {item_name}{note}{swap_indicator}")

        if shopping_list:
            missing_text = "\n".join(shopping_list)
            st.download_button(
                "🛒 Download Shopping List",
                missing_text,
                file_name="shopping_list.txt",
                help="Saves your un-ticked ingredients to a text file for shopping."
            )

    with col_right:
        st.markdown("<div class='sec-hdr'>👨‍🍳 Cooking Steps</div>", unsafe_allow_html=True)
        steps_html = "".join(
            f"<div class='step-block'><div class='step-n'>{idx}</div><div class='step-t'>{step}</div></div>"
            for idx, step in enumerate(recipe.get("steps", []), 1)
        )
        st.markdown(
            f"<div style='background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:1.4rem 1.6rem;box-shadow:var(--shadow);'>{steps_html}</div>",
            unsafe_allow_html=True,
        )

        # Kitchen Timer — hidden inside expander, JS runs in iframe via st.components
        with st.expander("⏱️ Kitchen Timer — click to open"):
            timer_min = st.number_input("Set minutes:", min_value=1, max_value=180, value=10, step=1, key="timer_mins")
            import streamlit.components.v1 as components
            timer_html = f"""
            <html>
            <head>
            <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">
            <style>
              * {{ margin:0; padding:0; box-sizing:border-box; }}
              body {{ font-family:'Outfit',sans-serif; background:transparent; text-align:center; padding:12px 0; }}
              #display {{ font-size:3.2rem; font-weight:700; color:#2F5435; letter-spacing:3px; margin-bottom:14px; }}
              #display.warn {{ color:#9E2A2B; }}
              .btns {{ display:flex; gap:10px; justify-content:center; }}
              .btn {{ border:none; border-radius:8px; padding:9px 22px; font-weight:600;
                      font-size:0.88rem; cursor:pointer; font-family:'Outfit',sans-serif; transition:all 0.15s; }}
              .btn:hover {{ transform:translateY(-1px); }}
              .btn-start {{ background:#2F5435; color:#fff; }}
              .btn-pause {{ background:#B26225; color:#fff; }}
              .btn-reset {{ background:#fff; color:#2F5435; border:2px solid #CCD5CD; }}
              .btn:disabled {{ opacity:0.4; cursor:default; transform:none; }}
              #done {{ display:none; margin-top:12px; padding:10px; background:#E4EFE5;
                       border-radius:8px; color:#2F5435; font-weight:600; font-size:0.9rem; }}
            </style>
            </head>
            <body>
              <div id="display">{timer_min:02d}:00</div>
              <div class="btns">
                <button class="btn btn-start" id="startBtn" onclick="doStart()">▶ Start</button>
                <button class="btn btn-pause" id="pauseBtn" onclick="doPause()" disabled>⏸ Pause</button>
                <button class="btn btn-reset" id="resetBtn" onclick="doReset()">↺ Reset</button>
              </div>
              <div id="done">🔔 Time's up!</div>
              <script>
                var total = {timer_min}*60, rem = total, iv = null;
                var d = document.getElementById('display');
                var sb = document.getElementById('startBtn');
                var pb = document.getElementById('pauseBtn');
                var dm = document.getElementById('done');
                function show() {{
                  var m=Math.floor(rem/60), s=rem%60;
                  d.textContent=(m<10?'0':'')+m+':'+(s<10?'0':'')+s;
                }}
                function doStart() {{
                  if(iv) return;
                  dm.style.display='none'; d.className='';
                  sb.disabled=true; pb.disabled=false;
                  iv=setInterval(function(){{
                    rem--;show();
                    if(rem<=10&&rem>0) d.className='warn';
                    if(rem<=0){{ clearInterval(iv);iv=null;d.textContent='00:00';
                      dm.style.display='block';sb.disabled=false;pb.disabled=true;
                      sb.textContent='▶ Start'; }}
                  }},1000);
                }}
                function doPause() {{
                  if(iv){{ clearInterval(iv);iv=null;
                    sb.disabled=false;sb.textContent='▶ Resume';pb.disabled=true; }}
                }}
                function doReset() {{
                  clearInterval(iv);iv=null;rem=total;show();
                  d.className='';dm.style.display='none';
                  sb.disabled=false;sb.textContent='▶ Start';pb.disabled=true;
                }}
              </script>
            </body>
            </html>
            """
            components.html(timer_html, height=160)

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
        c_name = country.split(' ', 1)[-1] if country != "🌍 Global / International" else "your region"
        st.markdown(f"<div class='sec-hdr'>🏪 Where to Buy in {c_name}</div>", unsafe_allow_html=True)
        bcols = st.columns(min(len(brands), 3))
        for i, b in enumerate(brands):
            initials = "".join(w[0].upper() for w in b.get("brand", "?").split()[:2])
            c_badge = f"<span class='brand-cert'>{b.get('certification','')}</span>" if b.get('certification') else ""
            html = (
                f"<div class='brand-item'>"
                f"<div class='brand-logo-placeholder'>{initials}</div>"
                f"<div><div class='brand-name'>{b.get('brand','')} {c_badge}</div>"
                f"<div class='brand-desc'><strong>{b.get('product','')}</strong><br>{b.get('where_to_buy','')}</div>"
                f"</div></div>"
            )
            with bcols[i % 3]:
                st.markdown(f"<div class='brands-panel'>{html}</div>", unsafe_allow_html=True)

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
        tips_html = "".join(f"<div class='tip-row'><span>🌿</span><span>{t}</span></div>" for t in tips)
        st.markdown(f"<div style='background:var(--card); border:1px solid var(--border); padding:1rem; border-radius:var(--r);'>{tips_html}</div>", unsafe_allow_html=True)

    bot1, bot2 = st.columns(2)
    with bot1:
        if recipe.get("storage_info"):
            st.markdown(f"<div class='info-box'><strong>🫙 Storage:</strong><br>{recipe.get('storage_info')}</div>", unsafe_allow_html=True)
    with bot2:
        if recipe.get("nutrition_notes"):
            st.markdown(f"<div class='info-box'><strong>🥦 Nutrition Notes:</strong><br>{recipe.get('nutrition_notes')}</div>", unsafe_allow_html=True)

    # ── PERFECT PAIRINGS / ACCOMPANIMENTS ──
    accompaniments = recipe.get("accompaniments") or []
    if accompaniments:
        st.markdown("<div class='sec-hdr'>🍴 Perfect Pairings</div>", unsafe_allow_html=True)
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
                    f"<div class='pair-icon'>{ic}</div>"
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
                if st.button(f"🍴 {at.get('dish','')}", key=f"try_{i}", use_container_width=True):
                    st.session_state["_queued_dish"] = at.get("dish", "")
                    st.rerun()
                st.markdown(f"<p style='font-size:0.8rem; text-align:center; color:var(--ink-soft);'>{at.get('reason','')}</p>", unsafe_allow_html=True)

    if "_queued_dish" in st.session_state:
        qd = st.session_state.pop("_queued_dish")
        if qd and api_key:
            with st.spinner(f"Recreating recipe for {qd}..."):
                try:
                    unit_val = "Metric" if "Metric" in unit_sys else "Imperial"
                    recipe = generate_recipe(qd, api_key, model, country, dietary, servings, unit_val)
                    st.session_state["recipe"] = recipe
                    st.session_state["base_servings"] = recipe.get("servings", servings) or servings
                    st.session_state["current_servings"] = servings
                    st.rerun()
                except Exception as e:
                    err = str(e)
                    if any(x in err for x in ("429", "503", "404", "daily limit", "quota")):
                        st.warning("🕐 Daily API limit reached. Please try again after midnight US Pacific time.")
                    else:
                        st.error(f"Error: {err}")

    # ── DISCLAIMER FOOTER ──
    st.markdown(
        "<div class='info-box' style='font-size:0.79rem;margin-top:1rem;'>ℹ️ AI-generated guidance only, not medical advice. "
        "If you have coeliac disease or serious gluten sensitivity, verify every ingredient label independently "
        "and be vigilant about cross-contamination.</div>",
        unsafe_allow_html=True,
    )
