import streamlit as st

st.set_page_config(
    page_title="RentWise_Find Your Place in NSW",
    page_icon="🏠",
    layout="wide",
)

st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    #MainMenu, header, footer { visibility: hidden; }
    .block-container { padding-top: 2rem; max-width: 1100px; margin: 0 auto; }
    body, [data-testid="stAppViewContainer"] {
        background-color: #F1F0EA;
        font-family: 'Segoe UI', sans-serif;
    }
    .rw-nav {
        padding-bottom: 20px; margin-bottom: 28px;
        border-bottom: 1px solid #E0DDCF;
    }
    .rw-logo {
        font-size: 1.6rem; font-weight: 800;
        text-decoration: none !important; color: #2D232E !important;
        letter-spacing: -0.5px;
    }
    .rw-slogan {
        font-size: 0.72rem; font-weight: 500;
        color: #534B52; margin-left: 10px;
        letter-spacing: 0; vertical-align: middle;
    }
    /* Hero */
    .rw-hero {
        background: #2D232E; border-radius: 20px;
        padding: 48px; margin-bottom: 20px;
    }
    .rw-hero h1 {
        font-size: 2.6rem; font-weight: 800;
        color: #F1F0EA; line-height: 1.2; margin: 0;
    }
    /* Cards */
    .st-key-home_card_left,
    .st-key-home_card_right {
        background: #FFFFFF !important;
        border: none !important;
        border-radius: 16px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06) !important;
        padding: 8px 12px 14px 12px !important;
        min-height: 260px !important;
    }
    .st-key-home_card_left > div,
    .st-key-home_card_right > div {
        background: transparent !important;
    }
    .rw-card-header {
        display: flex; align-items: center; gap: 10px;
        margin-bottom: 10px;
    }
    .rw-card-header h3 {
        font-size: 1.15rem; font-weight: 700;
        color: #2D232E; margin: 0;
    }
    .rw-card-desc {
        font-size: 0.85rem; color: #534B52;
        line-height: 1.6; margin-top: 8px;
        margin-bottom: 12px; min-height: 72px;
    }
    /* Red buttons */
    [data-testid="stButton"] button {
        color: #FFFFFF !important;
        background: #FF4B4B !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 8px !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        padding: 8px 20px !important;
    }
    [data-testid="stButton"] button:hover {
        background: #e03e3e !important;
        color: #FFFFFF !important;
    }
    /* How it works */
    h3 { font-size: 1.15rem !important; font-weight: 700 !important; color: #2D232E !important; }
    h3 a, h4 a, h3 svg { display: none !important; }
    [data-testid="stHeadingWithActionElements"] a { display: none !important; }
    .rw-how-list {
        color: #534B52; font-size: 0.9rem;
        line-height: 1.65; margin: 0 0 28px 0;
    }
    .rw-how-list p { margin: 0 0 12px 0; }
    /* Stats */
    .rw-stats {
        display: grid; grid-template-columns: repeat(4, 1fr);
        gap: 12px; margin-top: 8px;
    }
    .rw-stat {
        background: transparent; border-radius: 12px;
        padding: 16px; text-align: center;
        border: 1px solid rgba(83,75,82,0.28);
    }
    .rw-stat .num { font-size: 1.1rem; font-weight: 700; color: #2D232E; }
    .rw-stat .lbl { font-size: 0.75rem; color: #534B52; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Navbar ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="rw-nav"><a href="/" class="rw-logo" target="_self">🏠 RentWise'
    '<span class="rw-slogan">Find the right place, not just a place.</span></a></div>',
    unsafe_allow_html=True
)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="rw-hero">
    <h1>Find the right place,<br>not just a place.</h1>
</div>
""", unsafe_allow_html=True)

# ── Two action cards ──────────────────────────────────────────────────────────
left_col, right_col = st.columns(2, gap="large")

with left_col:
    with st.container(key="home_card_left", border=False):
        st.markdown("""
        <div class="rw-card-header">
            <span>🔍</span>
            <h3>Find Your Suburb</h3>
        </div>
        <div class="rw-card-desc">
            Select your lifestyle — Family, Single, or Student — and we rank
            28 Greater Sydney suburbs across safety, transport, schools,
            amenities, and price. Boost the factors that matter most to you.
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:32px'></div>", unsafe_allow_html=True)
        b1l, b1c, b1r = st.columns([1, 2, 1])
        with b1c:
            st.page_link("pages/1_find_suburb.py", label="Find My Suburb →", use_container_width=True)

with right_col:
    with st.container(key="home_card_right", border=False):
        st.markdown("""
        <div class="rw-card-header">
            <span>💰</span>
            <h3>Is This Rent Fair?</h3>
        </div>
        <div class="rw-card-desc">
            Enter a suburb, property type, and number of bedrooms. We compare
            your rent against the market median and tell you if it's a great
            deal, fair, or overpriced.
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:32px'></div>", unsafe_allow_html=True)
        b2l, b2c, b2r = st.columns([1, 2, 1])
        with b2c:
            st.page_link("pages/2_rent_check.py", label="Check My Rent →", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── How it works ──────────────────────────────────────────────────────────────
st.markdown("### How it works")
st.markdown("""
<div class="rw-how-list">
    <p><strong>1. Data Collection</strong><br>
    Rental bonds (NSW Fair Trading), crime stats (BOCSAR), train stations
    (TfNSW GTFS), school ratings (ICSEA), amenities (OpenStreetMap).</p>
    <p><strong>2. Scoring Model</strong><br>
    Each suburb is scored 0–10 across 5 dimensions using Min-Max normalisation.
    Weights are adjusted per persona (Family / Single / Student).</p>
    <p><strong>3. Price Benchmarks</strong><br>
    Median weekly rent is calculated by suburb × bedrooms × property type
    from 600,000+ rental bond lodgements (2024–2025).</p>
</div>
""", unsafe_allow_html=True)

# ── Stats ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="rw-stats">
    <div class="rw-stat"><div class="num">📍 28</div><div class="lbl">Greater Sydney suburbs</div></div>
    <div class="rw-stat"><div class="num">📊 600,000+</div><div class="lbl">Rental records</div></div>
    <div class="rw-stat"><div class="num">🏫 2,161</div><div class="lbl">Schools scored</div></div>
    <div class="rw-stat"><div class="num">🚉 Train</div><div class="lbl">Access mapped</div></div>
</div>
""", unsafe_allow_html=True)