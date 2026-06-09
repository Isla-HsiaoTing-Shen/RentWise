import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.db import get_connection

st.set_page_config(page_title="RentWise — Is This Rent Fair?", page_icon="💰", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    #MainMenu, header, footer { visibility: hidden; }
    .block-container { padding-top: 1.5rem; max-width: 1100px; margin: 0 auto; }
    body, [data-testid="stAppViewContainer"] { background-color: #F1F0EA; font-family: 'Segoe UI', sans-serif; }
    .rw-nav {
        display: flex; align-items: center;
        padding-bottom: 16px; margin-bottom: 20px;
        border-bottom: 1px solid #E0DDCF;
    }
    .rw-logo {
        font-size: 1.6rem; font-weight: 800; color: #2D232E !important;
        letter-spacing: -0.5px; text-decoration: none !important;
    }
    .rw-slogan {
        font-size: 0.72rem;
        font-weight: 500;
        color: #2D232E;
        margin-left: 8px;
        letter-spacing: 0;
        vertical-align: middle;
    }
    .page-title { color: #2D232E; font-size: 1.7rem; font-weight: 700; margin-bottom: 4px; }
    .page-sub   { color: #534B52; font-size: 0.9rem; margin-bottom: 24px; }
    .input-panel {
        background: #FFFFFF; border-radius: 16px; padding: 20px 32px 20px 32px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06); margin-bottom: 28px;
    }
    /* align button vertically with inputs */
    .input-panel [data-testid="stButton"] {
        margin-top: 24px;
    }
    .input-panel [data-testid="stButton"] button {
        height: 42px; padding: 0 20px !important;
        font-size: 0.9rem !important; font-weight: 600 !important;
        border-radius: 8px !important; white-space: nowrap;
    }
    .verdict {
        border-radius: 16px; padding: 28px 32px; margin-bottom: 24px;
        display: flex; align-items: center; gap: 20px;
    }
    .verdict-cheap  { background: #D4EDDA; border-left: 6px solid #28A745; }
    .verdict-fair   { background: #FFF3CD; border-left: 6px solid #FFC107; }
    .verdict-pricey { background: #F8D7DA; border-left: 6px solid #DC3545; }
    .verdict-icon  { font-size: 2.8rem; }
    .verdict-title { font-size: 1.4rem; font-weight: 700; color: #2D232E; margin-bottom: 4px; }
    .verdict-desc  { font-size: 0.95rem; color: #474448; }
    .stat-box {
        background: #FFFFFF; border-radius: 12px; padding: 20px 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06); text-align: center;
        min-height: 96px; display: flex; flex-direction: column;
        justify-content: center;
    }
    .stat-box .val { font-size: 1.7rem; font-weight: 700; color: #2D232E; }
    .stat-box .lbl { font-size: 0.8rem; color: #534B52; margin-top: 4px; }
    .market-card {
        background: #FFFFFF; border-radius: 16px; padding: 24px 28px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }
</style>
""", unsafe_allow_html=True)

# ── Navbar ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="rw-nav"><a href="/" class="rw-logo" target="_self">🏠 RentWise'
    '<span class="rw-slogan">Find the right place, not just a place.</span></a></div>',
    unsafe_allow_html=True
)
st.markdown('<div class="page-title">💰 Is This Rent Fair?</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Compare your rental price against the suburb\'s market benchmark. Covers all NSW suburbs with rental bond data (2024–2025).</div>', unsafe_allow_html=True)
st.info("⚠️ **Note:** The lowest prices may include individual rooms in share houses (Flat/Unit listings). Use the **median** as the most reliable market reference.")

# ── Functions ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def load_suburbs():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT DISTINCT s.suburb_name
        FROM dbo.rentals r
        JOIN dbo.suburbs s ON r.suburb_id = s.suburb_id
        ORDER BY s.suburb_name
    """, conn)
    return df['suburb_name'].tolist()

@st.cache_data(ttl=300)
def get_benchmark(suburb_name, prop_type, bedrooms):
    conn = get_connection()
    extra_filters = ""
    extra_params  = []
    if prop_type != "Any":
        extra_filters += " AND r.property_type = ?"
        extra_params.append(prop_type)
    if bedrooms != "Any":
        extra_filters += " AND r.bedrooms = ?"
        extra_params.append(int(bedrooms))
    query = f"""
        SELECT r.price_weekly
        FROM dbo.rentals r
        JOIN dbo.suburbs s ON r.suburb_id = s.suburb_id
        WHERE s.suburb_name = ?
        AND r.price_weekly BETWEEN 100 AND 5000
        {extra_filters}
    """
    params = [suburb_name] + extra_params
    df = pd.read_sql(query, conn, params=params)
    if df.empty or len(df) == 0:
        return None
    prices = df['price_weekly'].dropna()
    return {
        'total_listings': len(prices),
        'min_rent':       int(prices.min()),
        'max_rent':       int(prices.max()),
        'avg_rent':       float(prices.mean()),
        'p25':            float(prices.quantile(0.25)),
        'median_rent':    float(prices.quantile(0.50)),
        'p75':            float(prices.quantile(0.75)),
    }

@st.cache_data(ttl=300)
def get_breakdown(suburb_name, prop_type, bedrooms):
    conn = get_connection()
    extra_filters = ""
    params = [suburb_name]
    if prop_type != "Any":
        extra_filters += " AND r.property_type = ?"
        params.append(prop_type)
    if bedrooms != "Any":
        extra_filters += " AND r.bedrooms = ?"
        params.append(int(bedrooms))
    query = f"""
        SELECT r.bedrooms, r.property_type,
               COUNT(*) AS listings,
               AVG(CAST(r.price_weekly AS FLOAT)) AS avg_rent,
               MIN(r.price_weekly) AS min_rent,
               MAX(r.price_weekly) AS max_rent
        FROM dbo.rentals r
        JOIN dbo.suburbs s ON r.suburb_id = s.suburb_id
        WHERE s.suburb_name = ?
        AND r.price_weekly BETWEEN 100 AND 5000
        AND r.bedrooms IS NOT NULL
        {extra_filters}
        GROUP BY r.bedrooms, r.property_type
        ORDER BY r.bedrooms, r.property_type
    """
    return pd.read_sql(query, conn, params=params)

# ── Input ─────────────────────────────────────────────────────────────────────
suburb_list = load_suburbs()

with st.container():
    c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
    with c1:
        suburb = st.selectbox("Suburb", suburb_list)
    with c2:
        prop_type = st.selectbox("Property type", ["Any", "apartment", "house", "townhouse", "other"])
    with c3:
        bedrooms = st.selectbox("Bedrooms", ["Any", 1, 2, 3, 4, 5])
    with c4:
        your_rent = st.number_input("Your weekly rent ($)", min_value=50, max_value=10000, value=500, step=10)
    with c5:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        check = st.button("Check my rent", type="primary")

# ── Results ───────────────────────────────────────────────────────────────────
if check:
    result = get_benchmark(suburb, prop_type, bedrooms)

    if result is None or result.get('total_listings', 0) == 0:
        st.warning("Not enough data for this combination. Try selecting 'Any' for property type or bedrooms.")
        st.stop()

    median   = float(result['median_rent'])
    p25      = float(result['p25'])
    p75      = float(result['p75'])
    avg      = float(result['avg_rent'])
    total    = int(result['total_listings'])
    diff     = your_rent - median
    diff_pct = (diff / median) * 100

    if your_rent <= p25:
        verdict_class = "verdict-cheap"
        verdict_icon  = "🎉"
        verdict_title = "Great deal — below market"
        verdict_desc  = f"Your rent is ${abs(diff):,.0f}/week ({abs(diff_pct):.0f}%) below the suburb median. You're in the cheapest 25% of listings."
    elif your_rent <= median:
        verdict_class = "verdict-cheap"
        verdict_icon  = "✅"
        verdict_title = "Good value — at or below median"
        if abs(diff) < 1:
            verdict_desc = f"Your rent is exactly at the suburb median of ${median:,.0f}/week."
        else:
            verdict_desc = f"Your rent is ${abs(diff):,.0f}/week ({abs(diff_pct):.0f}%) below the suburb median. Solid value for this area."
    elif your_rent <= p75:
        verdict_class = "verdict-fair"
        verdict_icon  = "⚖️"
        verdict_title = "Fair — around market rate"
        verdict_desc  = f"Your rent is ${diff:,.0f}/week ({diff_pct:.0f}%) above the median but within the normal range for this suburb."
    else:
        verdict_class = "verdict-pricey"
        verdict_icon  = "⚠️"
        verdict_title = "Pricey — above market"
        verdict_desc  = f"Your rent is ${diff:,.0f}/week ({diff_pct:.0f}%) above the suburb median. You may be able to negotiate or find better value nearby."

    st.markdown(f"""
    <div class="verdict {verdict_class}">
        <div class="verdict-icon">{verdict_icon}</div>
        <div>
            <div class="verdict-title">{verdict_title}</div>
            <div class="verdict-desc">{verdict_desc}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    stat_items = [
        (f"${your_rent:,}",   "Your rent"),
        (f"${median:,.0f}",   "⭐ Market median"),
        (f"${p25:,.0f}",      "💚 Cheapest 25% pay under"),
        (f"${p75:,.0f}",      "🔴 Top 25% pay over"),
    ]
    cols = st.columns(len(stat_items))
    for col, (val, lbl) in zip(cols, stat_items):
        col.markdown(f"""<div class="stat-box">
            <div class="val">{val}</div><div class="lbl">{lbl}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    breakdown = get_breakdown(suburb, prop_type, bedrooms)
    if not breakdown.empty:
        breakdown['bedrooms'] = breakdown['bedrooms'].astype(int)
        breakdown['avg_rent'] = breakdown['avg_rent'].round(0).astype(int)
        breakdown = breakdown.rename(columns={
            'bedrooms': 'Bedrooms', 'property_type': 'Type',
            'listings': 'Listings', 'avg_rent': 'Avg Rent/wk',
            'min_rent': 'Min', 'max_rent': 'Max'
        })
        st.markdown(f"""<div class="market-card">
            <h4>📊 Rent breakdown — {suburb}{f' · {prop_type}' if prop_type != 'Any' else ''}{f' · {bedrooms}BR' if bedrooms != 'Any' else ''}</h4>
        </div>""", unsafe_allow_html=True)
        st.dataframe(breakdown, use_container_width=True, hide_index=True)
        st.caption("Source: NSW Fair Trading rental bond lodgements 2024–2025")

        