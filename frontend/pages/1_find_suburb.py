import streamlit as st
import pandas as pd
import sys
import os
import folium
from streamlit_folium import st_folium

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.db import get_connection

st.set_page_config(page_title="RentWise — Find Your Suburb", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    #MainMenu, header, footer { visibility: hidden; }
    .block-container { padding-top: 1.5rem; }
    body, [data-testid="stAppViewContainer"] {
        background-color: #F1F0EA;
        font-family: 'Segoe UI', sans-serif;
    }
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
    .page-title { color: #2D232E; font-size: 1.7rem; font-weight: 700; margin-bottom: 2px; }
    .page-sub   { color: #534B52; font-size: 0.9rem; margin-bottom: 16px; }
    .filter-panel { margin-bottom: 16px; }
    .persona-desc {
        font-size: 0.88rem;
        color: #474448; margin-top: 8px; line-height: 1.5;
    }
    .boost-block {
        background: #E8E6DF; border-radius: 10px;
        padding: 12px 16px; margin-top: 12px;
    }
    [data-testid="stSelectbox"] label,
    [data-testid="stSlider"] label {
        font-size: 1rem !important; font-weight: 600 !important; color: #2D232E !important;
    }
    [data-testid="stRadio"] > label { font-size: 1rem !important; font-weight: 600 !important; color: #2D232E !important; }
    [data-testid="stRadio"] label { font-size: 0.92rem !important; }

    /* suburb card */
    .s-card {
        background: #FFFFFF; border-radius: 14px;
        padding: 16px 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 10px; cursor: pointer;
        border: 2px solid transparent; transition: border 0.15s;
    }
    .s-card:hover { border-color: #2D232E; }
    .s-card-active { border-color: #2D232E !important; }
    .s-name  { font-size: 1rem; font-weight: 700; color: #2D232E; }
    .s-score { font-size: 1.3rem; font-weight: 800; color: #2D232E; }
    .s-score-lbl { font-size: 0.7rem; color: #534B52; }
    .rank-badge {
        width: 28px; height: 28px; border-radius: 50%;
        background: #2D232E; color: #F1F0EA;
        display: inline-flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.8rem; margin-right: 10px; flex-shrink: 0;
    }
    .rank-1 { background: #C9A84C; }
    .rank-2 { background: #909090; }
    .rank-3 { background: #A0704A; }
    .dim-pill {
        background: #F1F0EA; border-radius: 8px;
        padding: 8px 6px; text-align: center;
    }
    .dim-pill .icon  { font-size: 1rem; }
    .dim-pill .label { font-size: 0.65rem; color: #534B52; margin: 2px 0; }
    .dim-pill .value { font-size: 0.82rem; font-weight: 700; color: #2D232E; }
    .dim-pill .sub   { font-size: 0.62rem; color: #534B52; }
</style>
""", unsafe_allow_html=True)

# ── Navbar ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="rw-nav"><a href="/" class="rw-logo" target="_self">🏠 RentWise'
    '<span class="rw-slogan">Find the right place, not just a place.</span></a></div>',
    unsafe_allow_html=True
)
st.markdown('<div class="page-title">🔍 Find Your Suburb</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Rank suburbs based on what matters most to your lifestyle.</div>', unsafe_allow_html=True)

# ── Data functions ────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_scores(persona_name, lga_group):
    conn = get_connection()
    LGA_GROUPS = {
        "CBD + Inner": ['Sydney', 'Inner West', 'Canada Bay', 'Burwood', 'Strathfield', 'Canterbury-Bankstown'],
        "North":       ['North Sydney', 'Willoughby', 'Lane Cove', 'Ryde', 'Ku-ring-gai', 'Hornsby', 'Hunters Hill', 'Mosman', 'Northern Beaches'],
        "West":        ['Parramatta', 'Cumberland', 'Blacktown', 'The Hills Shire', 'Fairfield', 'Liverpool'],
        "South":       ['Georges River', 'Sutherland Shire', 'Bayside'],
        "East":        ['Waverley', 'Woollahra', 'Randwick'],
    }
    lga_sql = ""
    params = [persona_name, 'v2.0']
    if lga_group != "All of Greater Sydney":
        lgas = LGA_GROUPS.get(lga_group, [])
        if lgas:
            placeholders = ','.join(['?' for _ in lgas])
            lga_sql = f"AND s.lga_name IN ({placeholders})"
            params += lgas
    query = f"""
        SELECT TOP 50
            s.suburb_id, s.suburb_name, s.latitude, s.longitude,
            ss.overall_score, ss.price_score, ss.safety_score,
            ss.transport_score, ss.school_score, ss.amenity_score
        FROM dbo.suburb_scores ss
        JOIN dbo.suburbs s       ON ss.suburb_id  = s.suburb_id
        JOIN dbo.user_profiles p ON ss.profile_id = p.profile_id
        WHERE p.profile_name = ? AND ss.score_version = ?
        {lga_sql}
        ORDER BY ss.overall_score DESC
    """
    return pd.read_sql(query, conn, params=params)

@st.cache_data(ttl=300)
def load_details(suburb_ids_tuple):
    conn = get_connection()
    ids_str = ','.join(str(i) for i in suburb_ids_tuple)
    transport_df = pd.read_sql(f"""
        SELECT suburb_id, station_name, station_dist_km
        FROM dbo.transport_access WHERE suburb_id IN ({ids_str})
    """, conn)
    schools_df = pd.read_sql(f"""
        SELECT suburb_id, school_name, school_type, rating
        FROM dbo.schools WHERE suburb_id IN ({ids_str}) ORDER BY rating DESC
    """, conn)
    amenities_df = pd.read_sql(f"""
        SELECT suburb_id, amenity_type, count
        FROM dbo.amenities WHERE suburb_id IN ({ids_str})
    """, conn)
    rent_df = pd.read_sql(f"""
        SELECT suburb_id,
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_weekly)
                   OVER (PARTITION BY suburb_id) AS median_rent,
               COUNT(*) OVER (PARTITION BY suburb_id) AS listing_count
        FROM dbo.rentals
        WHERE suburb_id IN ({ids_str}) AND price_weekly BETWEEN 100 AND 5000
    """, conn).drop_duplicates(subset=['suburb_id'])

    t_map = transport_df.set_index('suburb_id').to_dict('index')
    s_map = schools_df.groupby('suburb_id').apply(lambda x: x.to_dict('records')).to_dict()
    a_map = amenities_df.groupby('suburb_id').apply(
        lambda x: x.set_index('amenity_type')['count'].to_dict()
    ).to_dict()
    r_map = rent_df.set_index('suburb_id').to_dict('index')
    return t_map, s_map, a_map, r_map

# ── Filters ───────────────────────────────────────────────────────────────────
# Read params from homepage if passed
default_persona = st.query_params.get("persona", "Family")
default_area    = st.query_params.get("area", "All of Greater Sydney")

c1, c2, c3 = st.columns(3)
with c1:
    persona = st.selectbox("Who are you?", ["Family", "Single", "Student"],
                           index=["Family", "Single", "Student"].index(default_persona)
                           if default_persona in ["Family", "Single", "Student"] else 0)
with c2:
    top_n = st.slider("Suburbs to show", 5, 20, 10)
with c3:
    area_options = ["All of Greater Sydney", "CBD + Inner", "North", "West", "South", "East"]
    lga_filter = st.selectbox("Filter by area", area_options,
                              index=area_options.index(default_area)
                              if default_area in area_options else 0)

persona_info = {
    "Family":  "🏡 Prioritises **safety** (30%) and **schools** (35%). Best for families with children.",
    "Single":  "🏙️ Prioritises **price** (35%) and **transport** (30%). Best for professionals who commute.",
    "Student": "🎓 Prioritises **price** (40%) and **transport** (35%). Best for budget-conscious students.",
}
st.markdown(f'<div class="persona-desc">{persona_info[persona]}</div>', unsafe_allow_html=True)

# ── Priority Boost ────────────────────────────────────────────────────────────
st.markdown('<div class="boost-block">', unsafe_allow_html=True)
st.radio(
    "⚡ What matters most to you? (optional boost)",
    ["No boost", "💰 Cheap rent", "🛡️ Safety", "🚉 Transport", "🏫 Schools", "🛒 Amenities"],
    horizontal=True,
    key="boost_radio"
)
st.markdown('</div>', unsafe_allow_html=True)
boost_choice = st.session_state.boost_radio

# ── Base persona weights ──────────────────────────────────────────────────────
BASE_WEIGHTS = {
    "Family":  {'price': 0.20, 'safety': 0.30, 'transport': 0.10, 'school': 0.35, 'amenity': 0.05},
    "Single":  {'price': 0.35, 'safety': 0.10, 'transport': 0.30, 'school': 0.05, 'amenity': 0.20},
    "Student": {'price': 0.40, 'safety': 0.05, 'transport': 0.35, 'school': 0.05, 'amenity': 0.15},
}

def apply_boost(persona, boost_choice):
    weights = BASE_WEIGHTS[persona].copy()
    BOOST = 0.20
    boost_map = {
        "💰 Cheap rent": 'price',
        "🛡️ Safety":     'safety',
        "🚉 Transport":  'transport',
        "🏫 Schools":    'school',
        "🛒 Amenities":  'amenity',
    }
    dim = boost_map.get(boost_choice)
    if dim:
        weights[dim] += BOOST
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}

boosts = [boost_choice == opt for opt in ["💰 Cheap rent", "🛡️ Safety", "🚉 Transport", "🏫 Schools", "🛒 Amenities"]]
final_weights = apply_boost(persona, boost_choice)

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading rankings..."):
    df = load_scores(persona, lga_filter)

if df.empty:
    st.warning("No suburbs found. Try a different area filter.")
    st.stop()

# Apply boost weights to recalculate overall score
df['overall_score'] = (
    df['price_score']     * final_weights['price'] +
    df['safety_score']    * final_weights['safety'] +
    df['transport_score'] * final_weights['transport'] +
    df['school_score']    * final_weights['school'] +
    df['amenity_score']   * final_weights['amenity']
).round(2)
df = df.sort_values('overall_score', ascending=False).reset_index(drop=True)

top_df = df.head(top_n)

with st.spinner("Loading suburb details..."):
    t_map, s_map, a_map, r_map = load_details(tuple(top_df['suburb_id'].tolist()))

# ── Session state for selected suburb ────────────────────────────────────────
if 'selected_idx' not in st.session_state:
    st.session_state.selected_idx = 0

AMENITY_LABELS = {
    'supermarket': '🛒 Supermarket', 'pharmacy': '💊 Pharmacy',
    'hospital': '🏥 Hospital',       'cafe': '☕ Café',
    'gym': '🏋️ Gym',                 'park': '🌳 Park',
    'university': '🎓 University',
}

# ── Left-right layout ─────────────────────────────────────────────────────────
map_col, list_col = st.columns([1.2, 1], gap="large")

# ── Map ───────────────────────────────────────────────────────────────────────
with map_col:
    st.markdown(f"### Top {top_n} suburbs for **{persona}** lifestyle")
    if boost_choice != "No boost":
        st.caption(f"⚡ Boosted: {boost_choice}")
    selected_row = top_df.iloc[st.session_state.selected_idx]
    sel_lat = selected_row['latitude'] if pd.notna(selected_row['latitude']) else -33.87
    sel_lon = selected_row['longitude'] if pd.notna(selected_row['longitude']) else 151.21

    m = folium.Map(location=[sel_lat, sel_lon], zoom_start=13,
                   tiles='CartoDB positron')

    for idx, row in top_df.iterrows():
        if pd.isna(row['latitude']) or pd.isna(row['longitude']):
            continue
        rank = idx + 1
        is_selected = (idx == st.session_state.selected_idx)
        color = '#C9A84C' if rank == 1 else '#909090' if rank == 2 else '#A0704A' if rank == 3 else '#2D232E'
        border = '#000000' if is_selected else color

        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=14 if is_selected else 10,
            color=border,
            weight=3 if is_selected else 1,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            tooltip=f"#{rank} {row['suburb_name']} — {row['overall_score']:.2f}",
            popup=folium.Popup(f"<b>{row['suburb_name']}</b><br>Score: {row['overall_score']:.2f}", max_width=150)
        ).add_to(m)

        folium.Marker(
            location=[row['latitude'], row['longitude']],
            icon=folium.DivIcon(
                html=f'<div style="font-size:9px;font-weight:700;color:white;text-align:center;margin-top:3px;">{rank}</div>',
                icon_size=(20, 20), icon_anchor=(10, 10)
            )
        ).add_to(m)

    st_folium(m, width=None, height=470, returned_objects=[])

# ── Card list ─────────────────────────────────────────────────────────────────
with list_col:
    st.markdown('<div style="height:520px;overflow-y:auto;padding-right:6px;scroll-behavior:smooth;" id="suburb-list">', unsafe_allow_html=True)

    for idx, row in top_df.iterrows():
        rank     = idx + 1
        sid      = row['suburb_id']
        rank_cls = {1: 'rank-1', 2: 'rank-2', 3: 'rank-3'}.get(rank, '')

        transport  = t_map.get(sid, {})
        schools    = s_map.get(sid, [])
        amenities  = a_map.get(sid, {})
        rent_info  = r_map.get(sid, {})

        station_name = transport.get('station_name', 'N/A')
        median_rent  = rent_info.get('median_rent', None)
        rent_text    = f"${median_rent:,.0f}/wk" if median_rent else "No data"
        school_count = len(schools)
        amenity_total = int(sum(amenities.values())) if amenities else 0
        safety_label  = "Very Safe" if row['safety_score'] >= 8 else ("Moderate" if row['safety_score'] >= 5 else "Higher Crime")
        is_selected   = (idx == st.session_state.selected_idx)

        # Select button
        if st.button(f"#{rank}  {row['suburb_name']}  —  {row['overall_score']:.2f} / 10",
                     key=f"select_{idx}",
                     use_container_width=True,
                     type="primary" if is_selected else "secondary"):
            st.session_state.selected_idx = idx
            st.rerun()

        # Mini dimension pills
        p1, p2, p3, p4, p5 = st.columns(5)
        with p1:
            st.markdown(f"""<div class="dim-pill">
                <div class="icon">💰</div><div class="label">Rent</div>
                <div class="value">{rent_text}</div>
            </div>""", unsafe_allow_html=True)
        with p2:
            st.markdown(f"""<div class="dim-pill">
                <div class="icon">🛡️</div><div class="label">Safety</div>
                <div class="value">{row['safety_score']:.1f}</div>
                <div class="sub">{safety_label}</div>
            </div>""", unsafe_allow_html=True)
        with p3:
            sname_short = station_name.replace(' Station', '').replace(' station', '')[:12]
            st.markdown(f"""<div class="dim-pill">
                <div class="icon">🚉</div><div class="label">Station</div>
                <div class="value" style="font-size:0.7rem">{sname_short}</div>
            </div>""", unsafe_allow_html=True)
        with p4:
            st.markdown(f"""<div class="dim-pill">
                <div class="icon">🏫</div><div class="label">Schools</div>
                <div class="value">{school_count}</div>
            </div>""", unsafe_allow_html=True)
        with p5:
            st.markdown(f"""<div class="dim-pill">
                <div class="icon">🛒</div><div class="label">Amenities</div>
                <div class="value">{amenity_total}</div>
            </div>""", unsafe_allow_html=True)

        # Expandable details
        with st.expander(f"Details — {row['suburb_name']}"):
            ec1, ec2 = st.columns(2)
            with ec1:
                st.markdown("**🚉 Nearest Station**")
                st.write(f"{station_name}")
                st.markdown("---")
                st.markdown("**🛒 Amenities within 1.5 km**")
                if amenities:
                    for atype, cnt in sorted(amenities.items(), key=lambda x: -x[1]):
                        if cnt > 0:
                            st.write(f"{AMENITY_LABELS.get(atype, atype)}: **{int(cnt)}**")
            with ec2:
                st.markdown("**🏫 Schools**")
                if schools:
                    for s in schools[:5]:
                        rating_str = f" ({s['rating']:.1f}/10)" if s['rating'] else ""
                        st.write(f"• {s['school_name']}{rating_str}")
                else:
                    st.write("No data")
                st.markdown("---")
                st.markdown("**💰 Rent**")
                st.write(f"Median: **{rent_text}**")
                if rent_info:
                    st.write(f"Based on {int(rent_info.get('listing_count', 0)):,} listings")

        st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ── Download ──────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
csv = top_df.drop(columns=['suburb_id', 'latitude', 'longitude']).to_csv(index=False)
st.download_button("⬇ Download results as CSV", csv, f"rankings_{persona.lower()}.csv", "text/csv")

