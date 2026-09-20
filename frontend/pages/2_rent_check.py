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
st.markdown('<div class="page-sub">Compare your weekly rent with the rents on newly lodged rental bonds in the same postcode (NSW Fair Trading, 2024–2025).</div>', unsafe_allow_html=True)
st.info("ℹ️ Rent data is grouped by **postcode**, so suburbs that share a postcode share the same numbers. The figures come from bonds lodged for new tenancies, not from every current tenant.")

# ── Options ───────────────────────────────────────────────────────────────────
# Property type shown on the website -> code used in the bond data
PROPERTY_TYPES = {
    "Flat / Unit": "F",
    "House": "H",
    "Townhouse / Terrace": "T",
}

# Bedroom choices for each property type (edit these lists if you want more or fewer)
BEDROOM_OPTIONS = {
    "Flat / Unit": [0, 1, 2, 3, 4],
    "House": [1, 2, 3, 4, 5, 6],
    "Townhouse / Terrace": [2, 3, 4],
}

def bedroom_label(bedrooms, property_label):
    if bedrooms == 0 and property_label == "Flat / Unit":
        return "Studio (0 bedrooms)"
    if bedrooms == 1:
        return "1 bedroom"
    return f"{bedrooms} bedrooms"

# ── Functions ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def load_suburbs():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT suburb_name, postcode, lga_name
        FROM dbo.postcode_suburb
        WHERE postcode IN (SELECT DISTINCT postcode FROM dbo.rent_stats)
        ORDER BY suburb_name, postcode
    """, conn)
    df["label"] = (df["suburb_name"].str.title() + " — "
                   + df["postcode"].astype(str) + " (" + df["lga_name"] + ")")
    return df

@st.cache_data(ttl=300)
def get_rent_stats(postcode, dwelling_type, bedrooms):
    conn = get_connection()
    return pd.read_sql("""
        SELECT n, median_rent, p25_rent, p75_rent, rent_min, rent_max, tier
        FROM dbo.rent_stats
        WHERE postcode = ? AND dwelling_type = ? AND bedrooms = ?
    """, conn, params=[int(postcode), dwelling_type, int(bedrooms)])

@st.cache_data(ttl=300)
def get_postcode_overview(postcode):
    conn = get_connection()
    return pd.read_sql("""
        SELECT dwelling_type, bedrooms, n, median_rent, p25_rent, p75_rent, tier
        FROM dbo.rent_stats
        WHERE postcode = ? AND tier <> 'insufficient'
        ORDER BY dwelling_type, bedrooms
    """, conn, params=[int(postcode)])

# ── Input ─────────────────────────────────────────────────────────────────────
suburbs_df = load_suburbs()

with st.container():
    c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
    with c1:
        label = st.selectbox("Suburb (you can also type a postcode)", suburbs_df["label"].tolist())
    with c2:
        property_label = st.selectbox("Property type", list(PROPERTY_TYPES.keys()))
    with c3:
        bedrooms = st.selectbox(
            "Bedrooms",
            BEDROOM_OPTIONS[property_label],
            format_func=lambda b: bedroom_label(b, property_label),
        )
    with c4:
        your_rent = st.number_input("Your weekly rent ($)", min_value=50, max_value=10000, value=500, step=10)
    with c5:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        check = st.button("Check my rent", type="primary")

# ── Results ───────────────────────────────────────────────────────────────────
if check:
    selected = suburbs_df[suburbs_df["label"] == label].iloc[0]
    postcode = int(selected["postcode"])
    dwelling_type = PROPERTY_TYPES[property_label]

    # Show which suburbs share this postcode
    names = suburbs_df[suburbs_df["postcode"] == postcode]["suburb_name"].str.title().tolist()
    shown = ", ".join(names[:8])
    if len(names) > 8:
        shown += f" and {len(names) - 8} more"
    st.caption(f"Postcode {postcode} covers: {shown}")

    stats = get_rent_stats(postcode, dwelling_type, bedrooms)
    what = f"{property_label.lower()}, {bedroom_label(bedrooms, property_label).lower()}"

    if stats.empty:
        st.warning(f"No rental bonds were recorded for a {what} in postcode {postcode}.")
    else:
        row = stats.iloc[0]
        n = int(row["n"])
        tier = row["tier"]

        if tier == "insufficient":
            st.warning(f"Not enough data: only {n} rental bonds for a {what} in postcode {postcode}. We need at least 10 to show a result.")
        else:
            median = float(row["median_rent"])
            p25 = float(row["p25_rent"])
            p75 = float(row["p75_rent"])
            rent_min = float(row["rent_min"])
            rent_max = float(row["rent_max"])

            if tier == "full":
                diff = your_rent - median
                diff_pct = (diff / median) * 100
                direction = "above" if diff >= 0 else "below"
                if your_rent <= p25:
                    verdict_class = "verdict-cheap"
                    verdict_icon = "🎉"
                    verdict_title = "Great deal — below the typical range"
                    verdict_desc = f"Your rent is ${abs(diff):,.0f}/week ({abs(diff_pct):.0f}%) below the median. It falls in the cheapest quarter of recent bonds."
                elif your_rent <= p75:
                    verdict_class = "verdict-fair"
                    verdict_icon = "⚖️"
                    verdict_title = "Fair — within the typical range"
                    verdict_desc = f"Your rent is ${abs(diff):,.0f}/week ({abs(diff_pct):.0f}%) {direction} the median. It falls in the middle 50% of recent bonds."
                else:
                    verdict_class = "verdict-pricey"
                    verdict_icon = "⚠️"
                    verdict_title = "Pricey — above the typical range"
                    verdict_desc = f"Your rent is ${abs(diff):,.0f}/week ({abs(diff_pct):.0f}%) above the median. It falls in the most expensive quarter of recent bonds."

                st.markdown(f"""
                <div class="verdict {verdict_class}">
                    <div class="verdict-icon">{verdict_icon}</div>
                    <div>
                        <div class="verdict-title">{verdict_title}</div>
                        <div class="verdict-desc">{verdict_desc}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.info(f"Limited data: this is based on only {n} rental bonds, so we do not give a verdict. Use the numbers below as a rough guide only.")

            stat_items = [
                (f"${your_rent:,}", "Your rent"),
                (f"${median:,.0f}", "⭐ Median rent"),
                (f"${p25:,.0f}", "💚 25% of bonds are below"),
                (f"${p75:,.0f}", "🔴 25% of bonds are above"),
            ]
            cols = st.columns(len(stat_items))
            for col, (val, lbl) in zip(cols, stat_items):
                col.markdown(f"""<div class="stat-box">
                    <div class="val">{val}</div><div class="lbl">{lbl}</div>
                </div>""", unsafe_allow_html=True)

            st.caption(
                f"Based on {n:,} rental bonds lodged in 2024–2025. "
                f"Lowest and highest recorded: \\${rent_min:,.0f} to \\${rent_max:,.0f} "
                f"(extreme values may be unusual listings, so use the median and typical range instead)."
            )

    # Overview of everything we can show for this postcode
    overview = get_postcode_overview(postcode)
    if not overview.empty:
        overview = overview.copy()
        for col in ["median_rent", "p25_rent", "p75_rent"]:
            overview[col] = overview[col].astype(float).round(0).astype(int)
        overview["dwelling_type"] = overview["dwelling_type"].map({
            "F": "Flat / Unit", "H": "House", "T": "Townhouse / Terrace"})
        overview["bedrooms"] = overview["bedrooms"].astype(int)
        overview["tier"] = overview["tier"].map({"full": "Full", "limited": "Limited data"})
        overview = overview.rename(columns={
            "dwelling_type": "Type", "bedrooms": "Bedrooms", "n": "Bonds",
            "median_rent": "Median/wk", "p25_rent": "25% below", "p75_rent": "25% above",
            "tier": "Data",
        })
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""<div class="market-card">
            <h4>📊 All rents in postcode {postcode}</h4>
        </div>""", unsafe_allow_html=True)
        st.dataframe(overview, use_container_width=True, hide_index=True)
        st.caption("Source: NSW Fair Trading rental bond lodgements 2024–2025. Combinations with fewer than 10 bonds are not shown.")