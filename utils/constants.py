"""
Shared constants for the Liga F Analytics platform.
Centralizes position mappings, team data, and session state defaults.
"""
import time


# ==================== POSITION MAPPINGS ====================

# Maps Wyscout specific positions to general position categories
POSITIONS_DICT = {
    "GK": "portero",
    "LB": "lateral",
    "RB": "lateral",
    "DMF": "defmid",
    "OF": "ofmid",
    "AMF": "ofmid",
    "LCB": "defensa",
    "RCB": "defensa",
    "LWF": "extremo",
    "RWF": "extremo",
    "LAMF": "ofmid",
    "RAMF": "ofmid",
    "LCMF": "ofmid",
    "RCMF": "ofmid",
    "CF": "delantero",
    "CB": "defensa",
    "RW": "extremo",
    "LDMF": "defmid",
    "LW": "extremo",
    "RDMF": "defmid",
    "RWB": "lateral",
    "LWB": "lateral",
}

# Ordered list of general positions
GENERAL_POSITIONS = [
    "portero", "defensa", "defmid", "ofmid",
    "lateral", "delantero", "extremo"
]

# Human-readable position names (Spanish)
POSITIONS_DISPLAY = {
    "portero": "Portero",
    "defensa": "Defensa",
    "lateral": "Lateral",
    "defmid": "Centrocampista defensivo",
    "ofmid": "Centrocampista ofensivo",
    "delantero": "Delantero",
    "extremo": "Extremo",
}


# ==================== TEAM LOGO MAPPINGS ====================

TEAM_LOGO_MAPPINGS = {
    'Alhama': 'Alhama Femenino.png',
    'Athletic': 'Athletic Club Femenino.png',
    'Athletic Club': 'Athletic Club Femenino.png',
    'Atlético': 'Atlético de Madrid Femenino.png',
    'Atletico Madrid Feminino': 'Atlético de Madrid Femenino.png',
    'Badalona': 'Badalona Women.png',
    'Barcelona': 'Barcelona Femenino.png',
    'Deportivo Abanca': 'Deportivo de La Coruña Femenino.png',
    'Deportivo de La Coruña': 'Deportivo de La Coruña Femenino.png',
    'DUX Logroño': 'DUX Logroño Femenino.png',
    'Eibar': 'Eibar Femenino.png',
    'Espanyol': 'Espanyol Femenino.png',
    'Granada': 'Granada Femenino.png',
    'Granada CF': 'Granada Femenino.png',
    'Levante': 'Levante Femenino.png',
    'Logroño': 'DUX Logroño Femenino.png',
    'Madrid CFF': 'Madrid CF Femenino.png',
    'Real Madrid': 'Real Madrid Femenino.png',
    'Real Sociedad': 'Real Sociedad Femenino.png',
    'Sevilla': 'Sevilla Femenino.png',
    'Tenerife': 'Tenerife Femenino.png',
    'Costa Adeje Tenerife': 'Tenerife Femenino.png',
}

# List of all team names (derived from the mappings)
TEAM_NAMES = list(TEAM_LOGO_MAPPINGS.keys())


# ==================== SESSION STATE DEFAULTS ====================

def init_report_session_state(prefix=""):
    """
    Initialize common session state variables for report generation pages.

    Parameters:
        prefix (str): Optional prefix for namespacing (e.g., "porteras_report_").
                       Include trailing underscore if using a prefix.
    """
    import streamlit as st

    defaults = {
        "proceso": None,
        "log_path": "",
        "pid": None,
        "last_log_update": time.time(),
        "inicio_ejecucion": None,
    }
    for key, val in defaults.items():
        full_key = f"{prefix}{key}"
        if full_key not in st.session_state:
            st.session_state[full_key] = val


# ==================== CHAMPIONSHIP / SEASON MAPPINGS ====================

CHAMPIONSHIP_MAP = {
    "2RFEF": "2\u00ba RFEF",
    "1RFEF": "1\u00ba RFEF",
    "2Division": "La Liga 2",
    "LaLiga": "La Liga",
    "LigaF": "Liga F",
}

SEASON_MAP = {
    2022: "22/23",
    2023: "23/24",
    2024: "24/25",
    2025: "25/26",
}


# ==================== POSITION MAPPING UTILITY ====================

def map_positions(positions_str):
    """
    Map a comma-separated string of specific positions to general positions.
    Returns a comma-separated string of unique general positions.
    """
    positions = positions_str.split(", ")
    general_positions = [POSITIONS_DICT.get(pos, pos) for pos in positions]
    unique_positions = set(general_positions)
    return ", ".join(unique_positions)
