"""
KameraPh Regalia Profiles: Culturally Calibrated AI Profiles for Philippine Institutions
-----------------------------------------------------------------------------------------
Pre-configured parameters protecting institutional symbols, indigenous weaves, and fabrics:
  1. Standard Toga: Heavy polyester de-crease, collar align, morena blemish smoothing.
  2. UP Sablay: Protects indigenous chevron/baybayin weave; irons Barong/Filipiniana under.
  3. Barong Tagalog: Protects calado/piña embroidery; sharpens Mandarin collar seams.
  4. Filipiniana: Protects butterfly sleeve structure and neckline.
  5. Kindergarten / Elementary: Gentle drape for pastel satin and lace collars.
"""

REGALIA_PROFILES = {
    "standard_toga": {
        "id": "standard_toga",
        "name": "Standard Toga (High School / College)",
        "iron_strength": 0.75,
        "skin_smoothing": 0.65,
        "shine_reduction": 0.35,
        "edge_protection_level": "high",
        "description": "Irons out heavy polyester folds; aligns collar and center ties."
    },
    "up_sablay": {
        "id": "up_sablay",
        "name": "UP Sablay & Indigenous Sash",
        "iron_strength": 0.50,
        "skin_smoothing": 0.65,
        "shine_reduction": 0.30,
        "edge_protection_level": "maximum",
        "description": "Protects geometric indigenous weaves and Baybayin symbols from blur."
    },
    "barong_tagalog": {
        "id": "barong_tagalog",
        "name": "Barong Tagalog (Formal)",
        "iron_strength": 0.60,
        "skin_smoothing": 0.60,
        "shine_reduction": 0.40,
        "edge_protection_level": "maximum",
        "description": "Preserves delicate Piña/Jusi calado embroidery while straightening collar."
    },
    "filipiniana": {
        "id": "filipiniana",
        "name": "Filipiniana (Terno / Maria Clara)",
        "iron_strength": 0.65,
        "skin_smoothing": 0.68,
        "shine_reduction": 0.35,
        "edge_protection_level": "high",
        "description": "Preserves crisp butterfly sleeve silhouettes and embroidered bodices."
    },
    "kinder_pastel": {
        "id": "kinder_pastel",
        "name": "Kindergarten / Pastel Gown",
        "iron_strength": 0.70,
        "skin_smoothing": 0.50,
        "shine_reduction": 0.25,
        "edge_protection_level": "medium",
        "description": "Soft smoothing for satin/cotton gowns and lace ribbons."
    }
}

# Aliases for frontend IDs that differ from backend canonical IDs
REGALIA_ALIASES = {
    "ph_academic_toga": "standard_toga",
    "formal_blazer": "barong_tagalog",
    "suit_and_tie": "barong_tagalog",
    "academic_toga": "standard_toga",
}


def get_regalia_profile(profile_id: str) -> dict:
    """
    Looks up a regalia profile by ID, resolving aliases to canonical IDs.
    Returns the standard_toga profile as fallback if the ID is unknown.
    """
    # Direct match first
    if profile_id in REGALIA_PROFILES:
        return REGALIA_PROFILES[profile_id]

    # Try alias resolution
    canonical = REGALIA_ALIASES.get(profile_id, "standard_toga")
    return REGALIA_PROFILES.get(canonical, REGALIA_PROFILES["standard_toga"])
