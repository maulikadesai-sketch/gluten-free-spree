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

COUNTRIES = [
    "🌍 Global / International",
    "🇦🇫 Afghanistan", "🇦🇱 Albania", "🇩🇿 Algeria", "🇦🇩 Andorra", "🇦🇴 Angola", 
    "🇦🇬 Antigua & Barbuda", "🇦🇷 Argentina", "🇦🇲 Armenia", "🇦🇺 Australia", "🇦🇹 Austria", 
    "🇦🇿 Azerbaijan", "🇧🇸 Bahamas", "🇧🇭 Bahrain", "🇧🇩 Bangladesh", "🇧🇧 Barbados", 
    "🇧🇾 Belarus", "🇧🇪 Belgium", "🇧🇿 Belize", "🇧🇯 Benin", "🇧🇹 Bhutan", 
    "🇧🇴 Bolivia", "🇧🇦 Bosnia Herzegovina", "🇧🇼 Botswana", "🇧🇷 Brazil", "🇧🇳 Brunei", 
    "🇧🇬 Bulgaria", "🇧🇫 Burkina Faso", "🇧🇮 Burundi", "🇰🇭 Cambodia", "🇨🇲 Cameroon", 
    "🇨🇦 Canada", "🇨🇻 Cape Verde", "🇨🇫 Central African Rep", "🇹🇩 Chad", "🇨🇱 Chile", 
    "🇨🇳 China", "🇨🇴 Colombia", "🇨🇲 Comoros", "🇨🇬 Congo", "🇨🇷 Costa Rica", 
    "🇭🇷 Croatia", "🇨🇺 Cuba", "🇨🇾 Cyprus", "🇨🇿 Czech Republic", "🇩🇰 Denmark", 
    "🇩🇯 Djibouti", "🇩🇲 Dominica", "🇩🇴 Dominican Republic", "🇪🇨 Ecuador", "🇪🇬 Egypt", 
    "🇸🇻 El Salvador", "🇬🇶 Equatorial Guinea", "🇪🇷 Eritrea", "🇪🇪 Estonia", "🇸🇿 Eswatini", 
    "🇪🇹 Ethiopia", "🇫🇯 Fiji", "🇫🇮 Finland", "🇫🇷 France", "🇬🇦 Gabon", 
    "🇬🇲 Gambia", "🇬🇪 Georgia", "🇩🇪 Germany", "🇬🇭 Ghana", "🇬🇷 Greece", 
    "🇬🇩 Grenada", "🇬🇹 Guatemala", "🇬🇳 Guinea", "🇬🇼 Guinea-Bissau", "🇬🇾 Guyana", 
    "🇭🇹 Haiti", "🇭🇳 Honduras", "🇭🇺 Hungary", "🇮🇸 Iceland", "🇮🇳 India", 
    "🇮🇩 Indonesia", "🇮🇷 Iran", "🇮🇶 Iraq", "🇮🇪 Ireland", "🇮🇱 Israel", 
    "🇮🇹 Italy", "🇯🇲 Jamaica", "🇯🇵 Japan", "🇯🇴 Jordan", "🇰🇿 Kazakhstan", 
    "🇰🇪 Kenya", "🇰展现 Kiribati", "🇰🇵 North Korea", "🇰🇷 South Korea", "🇰🇼 Kuwait", 
    "🇰🇬 Kyrgyzstan", "🇱🇦 Laos", "🇱🇻 Latvia", "🇱🇧 Lebanon", "🇱🇸 Lesotho", 
    "🇱🇷 Liberia", "🇱🇾 Libya", "🇱🇮 Liechtenstein", "🇱🇹 Lithuania", "🇱🇺 Luxembourg", 
    "🇲展现 Madagascar", "🇲🇼 Malawi", "🇲🇾 Malaysia", "🇲展现 Maldives", "🇲🇱 Mali", 
    "🇲🇹 Malta", "🇲🇭 Marshall Islands", "🇲🇷 Mauritania", "🇲🇺 Mauritius", "🇲🇽 Mexico", 
    "🇫🇲 Micronesia", "🇲🇩 Moldova", "🇲🇨 Monaco", "🇲🇳 Mongolia", "🇲🇪 Montenegro", 
    "🇲🇦 Morocco", "🇲🇿 Mozambique", "🇲🇲 Myanmar", "🇳🇦 Namibia", "🇳🇷 Nauru", 
    "🇳🇵 Nepal", "🇳🇱 Netherlands", "🇳🇿 New Zealand", "🇳🇮 Nicaragua", "🇳🇪 Niger", 
    "🇳🇬 Nigeria", "🇲展现 North Macedonia", "🇳🇴 Norway", "🇴🇲 Oman", "🇵🇰 Pakistan", 
    "🇵展现 Palau", "🇵🇸 Palestine", "🇵🇦 Panama", "🇵🇬 Papua New Guinea", "🇵🇾 Paraguay", 
    "🇵🇪 Peru", "🇵🇭 Philippines", "🇵🇱 Poland", "🇵🇹 Portugal", "🇶🇦 Qatar", 
    "🇷🇴 Romania", "🇷🇺 Russia", "🇷🇼 Rwanda", "🇰展现 St Kitts & Nevis", "🇱🇨 St Lucia", 
    "🇻🇨 St Vincent", "🇼🇸 Samoa", "🇸🇲 San Marino", "🇸🇹 Sao Tome", "🇸🇦 Saudi Arabia", 
    "🇸🇳 Senegal", "🇷🇸 Serbia", "🇸🇨 Seychelles", "🇸🇱 Sierra Leone", "🇸🇬 Singapore", 
    "🇸🇰 Slovakia", "🇸🇮 Slovenia", "🇸🇧 Solomon Islands", "🇸🇴 Somalia", "🇿🇦 South Africa", 
    "🇪🇸 Spain", "🇱🇰 Sri Lanka", "🇸🇩 Sudan", "🇸🇷 Suriname", "🇸🇪 Sweden", 
    "🇨🇭 Switzerland", "🇸🇾 Syria", "🇹🇼 Taiwan", "🇹🇯 Tajikistan", "🇹🇿 Tanzania", 
    "🇹🇭 Thailand", "🇹展现 Timor-Leste", "🇹🇬 Togo", "🇹🇴 Tonga", "🇹🇹 Trinidad & Tobago", 
    "🇹🇳 Tunisia", "🇹🇷 Turkey", "🇹🇲 Turkmenistan", "🇹展现 Tuvalu", "🇺🇬 Uganda", 
    "🇺🇦 Ukraine", "🇦🇪 UAE", "🇬🇧 United Kingdom", "🇺🇸 United States", "🇺🇾 Uruguay", 
    "🇺🇿 Uzbekistan", "🇻展现 Vanuatu", "🇻🇪 Venezuela", "🇻🇳 Vietnam", "🇾🇪 Yemen", 
    "🇿🇲 Zambia", "🇿🇼 Zimbabwe"
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

    /* Fixes for mobile display of markdown checkboxes */
    .stMarkdown div ul {
        list-style-type: none;
        padding-left: 0 !important;
    }
    .stMarkdown li {
        display: flex !important;
        align-items: flex-start !important;
        margin-bottom: 0.5rem;
    }
    .stMarkdown li input[type="checkbox"] {
        margin-right: 10px !important;
        margin-top: 4px !important;
        transform: scale(1.1);
        flex-shrink: 0;
    }

    /* Headings */
    h1, h2, h3 {
        color: #1b5e20;
        font-weight: 700;
    }
    
    .recipe-title {
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
        color: #1b5e20;
    }
    
    .meta-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
    }
    
    .meta-item {
        text-align: center;
        border-right: 1px solid var(--border);
    }
    .meta-item:last-child {
        border-right: none;
    }
    .meta-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        color: var(--ink-soft);
        letter-spacing: 0.5px;
    }
    .meta-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--ink);
    }

    /* Buttons & Inputs */
    .stButton>button {
        background-color: var(--accent) !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        border: none !important;
        font-weight: 600 !important;
        width: 100%;
        box-shadow: 0 2px 6px rgba(46,125,50,0.2);
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #1b5e20 !important;
        transform: translateY(-1px);
    }
    
    /* Utility */
    .badge {
        background: #ffe0b2;
        color: #e65100;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-gf {
        background: #c8e6c9;
        color: #1b5e20;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 🛠️ Business Logic / API Helpers
# ─────────────────────────────────────────────
def try_gemini_models(api_key, model_list, prompt_payload):
    """Iterate through models using a single key until one works."""
    headers = {"Content-Type": "application/json"}
    
    for model in model_list:
        url = f"{API_BASE}/{model}:generateContent?key={api_key}"
        try:
            res = requests.post(url, headers=headers, json=prompt_payload, timeout=22)
            if res.status_code == 200:
                return res.json(), model
            elif res.status_code in (429, 404, 503):
                continue # Try next model
        except Exception:
            continue
    return None, None

def call_gemini_api(all_keys, preferred_model, prompt_text):
    """Cycle through multiple API keys and fallback models to maximize free tier uptime."""
    valid_keys = [k.strip() for k in all_keys if k.strip()]
    if not valid_keys:
        raise ValueError("Missing API Key. Please supply at least one Gemini API Key.")

    # Reorder models to try preferred first
    models_to_try = [preferred_model] + [m for m in FALLBACK_MODELS if m != preferred_model]
    
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.3
        }
    }

    # Try every key × model combination
    for key in valid_keys:
        result, working_model = try_gemini_models(key, models_to_try, payload)
        if result:
            try:
                raw_text = result['candidates'][0]['content']['parts'][0]['text']
                return json.loads(raw_text), working_model
            except (KeyError, IndexError, ValueError):
                raise ValueError("The AI model returned an unparseable response layout. Please retry.")
                
    raise RuntimeError("429 / Daily Limit reached across all provided API keys and fallback models.")

def generate_recipe(dish, keys, model, country, dietary, servings, unit_sys):
    diet_str = ", ".join(dietary) if dietary else "None"
    
    prompt = f"""
    You are an expert culinary specialist and a certified allergen/coeliac safety inspector.
    Create a highly detailed, gourmet, structured recipe for: "{dish}".
    
    CRITICAL CONSTRAINT: The recipe MUST BE 100% GLUTEN-FREE. 
    If the traditional recipe contains wheat, rye, barley, soy sauce, or standard flour, you MUST substitute them with safe, explicitly labeled gluten-free alternatives (e.g., 'gluten-free tamari' instead of 'soy sauce', 'certified gluten-free oat flour').
    
    Context Contextual Adjustments:
    - Target Localization/Country Sourcing: {country} (Tailor standard ingredient names, measurements, and terminology to this locale if applicable).
    - Extra Dietary Restrictions: {diet_str} (The recipe must respect these rules in addition to being strictly gluten-free).
    - Target Yield: {servings} servings.
    - Measurement Unit Standard: Use {unit_sys} units primarily.

    Return your output strictly as a valid JSON object matching this schema exactly. Do not wrap it in markdown code blocks, just raw JSON:
    {{
      "dish_name
