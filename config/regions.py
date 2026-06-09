# config/regions.py
# ─────────────────────────────────────────────
# Centralised region configuration for RentWise
# To add a new state (e.g. QLD), add a new entry
# to REGIONS and update STATE_CONFIG below.
# ─────────────────────────────────────────────

# ── Target suburbs by region ──────────────────
REGIONS = {
    "NSW": {
        "North":      ["Chatswood", "North Ryde", "Macquarie Park", "Epping", "Eastwood"],
        "West":       ["Parramatta", "Lidcombe", "Auburn", "Granville", "Westmead", "Homebush", "Merrylands"],
        "Inner West": ["Burwood", "Strathfield", "Ashfield", "Campsie", "Rhodes", "Wolli Creek"],
        "South":      ["Mascot", "Zetland", "Waterloo", "Kensington", "Kingsford", "Hurstville"],
        "East":       ["Bondi Junction", "Coogee", "Randwick", "Maroubra"],
    },
    # Future expansion:
    # "QLD": {
    #     "Brisbane CBD": [...],
    #     "South Brisbane": [...],
    # },
}

# ── LGA groupings for filter (used in frontend) ───
LGA_GROUPS = {
    "NSW": {
        "CBD + Inner": ["Sydney", "Inner West", "Canada Bay", "Burwood", "Strathfield", "Canterbury-Bankstown"],
        "North":       ["North Sydney", "Willoughby", "Lane Cove", "Ryde", "Ku-ring-gai", "Hornsby", "Hunters Hill", "Mosman", "Northern Beaches"],
        "West":        ["Parramatta", "Cumberland", "Blacktown", "The Hills Shire", "Fairfield", "Liverpool"],
        "South":       ["Georges River", "Sutherland Shire", "Bayside"],
        "East":        ["Waverley", "Woollahra", "Randwick"],
    },
    # "QLD": { ... }
}

# ── State-level config ─────────────────────────
STATE_CONFIG = {
    "NSW": {
        "score_version": "v2.0",
        "rent_min":      100,
        "rent_max":      5000,
        "amenity_radius_km": 1.5,
    },
    # "QLD": {
    #     "score_version": "v1.0",
    #     "rent_min": 100,
    #     "rent_max": 5000,
    #     "amenity_radius_km": 1.5,
    # },
}

# ── Helper functions ───────────────────────────
def get_all_suburbs(state: str = "NSW") -> list:
    """Return flat list of all target suburbs for a state."""
    suburbs = []
    for region_suburbs in REGIONS[state].values():
        suburbs.extend(region_suburbs)
    return suburbs

def get_lga_list(state: str = "NSW", area: str = None) -> list:
    """Return LGA list for a given area filter."""
    if area is None or area == "All of Greater Sydney":
        return []
    return LGA_GROUPS[state].get(area, [])