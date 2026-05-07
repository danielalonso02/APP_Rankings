#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Dec 20, 2025

@author: rishiraj
Match Overview Page - Quick Match Summary with Key Stats
Provides: Score, Key Stats, xG Summary, and Timeline
"""
import streamlit as st
from utils import util
import pandas as pd
import os
import io
import xml.etree.ElementTree as ET
from translations import get_text
from PIL import Image
import base64
import matplotlib.pyplot as plt
import matplotlib.patheffects as mpe
from mplsoccer import Pitch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

ruta_opta_f40 = os.path.join(BASE_DIR, "data_femeni", "raw", "f40", "f40-squad-102.xml")
ruta_opta_f42 = os.path.join(BASE_DIR, "data_femeni", "raw", "f42", "f42-903-2025-results.xml")
ruta_excel_players = os.path.join(BASE_DIR, "data_femeni", "players_relations.xlsx")
ruta_excel_matches = os.path.join(BASE_DIR, "data_femeni", "matches_relations.xlsx")

# Define logo size constants
LOGO_WIDTH = 120  # pixels
LOGO_HEIGHT = 120  # pixels - making it square for consistency

GOLD = "#FFD700"
HOME_COLOR = "#1e40af"
AWAY_COLOR = "#dc2626"

# =============================================================================
# Formation slot → (x, y) coordinate table
# x ∈ [2, 48]: distance from home goal (GK ≈ 4, forward ≈ 48)
# y ∈ [5, 95]: lateral (0 = right touchline, 100 = left)
# Away team mirrors via x_away = 100 − x_home
# =============================================================================
_COORDS: dict = {
    "433": {
        1:  (4, 50), 2:  (22, 13), 5:  (18, 33), 6:  (18, 67), 3:  (22, 87),
        7:  (37, 23), 4:  (37, 50), 8:  (37, 77),
        10: (47, 17), 9:  (47, 50), 11: (47, 83),
    },
    "4231": {
        1:  (4, 50), 2:  (22, 13), 5:  (18, 33), 6:  (18, 67), 3:  (22, 87),
        4:  (32, 37), 8:  (32, 63),
        7:  (43, 17), 10: (43, 50), 11: (43, 83), 9:  (48, 50),
    },
    "442": {
        1:  (4, 50), 2:  (22, 13), 5:  (18, 33), 6:  (18, 67), 3:  (22, 87),
        7:  (38, 12), 4:  (37, 37), 8:  (37, 63), 11: (38, 88),
        9:  (47, 35), 10: (47, 65),
    },
    "4141": {
        1:  (4, 50), 2:  (22, 13), 5:  (18, 33), 6:  (18, 67), 3:  (22, 87),
        4:  (31, 50),
        7:  (40, 13), 8:  (40, 37), 10: (40, 63), 11: (40, 87), 9:  (48, 50),
    },
    "4321": {
        1:  (4, 50), 2:  (22, 13), 5:  (18, 33), 6:  (18, 67), 3:  (22, 87),
        4:  (34, 27), 7:  (34, 50), 8:  (34, 73),
        9:  (44, 30), 10: (47, 50), 11: (44, 70),
    },
    "352": {
        1:  (4, 50), 5:  (17, 23), 6:  (17, 50), 11: (17, 77),
        2:  (30, 10), 4:  (36, 30), 7:  (36, 50), 8:  (36, 70), 3:  (30, 90),
        9:  (47, 35), 10: (47, 65),
    },
    "451": {
        1:  (4, 50), 2:  (22, 13), 5:  (18, 33), 6:  (18, 67), 3:  (22, 87),
        7:  (37, 12), 4:  (37, 30), 8:  (37, 50), 10: (37, 70), 11: (37, 88),
        9:  (47, 50),
    },
    "4411": {
        1:  (4, 50), 2:  (22, 13), 5:  (18, 33), 6:  (18, 67), 3:  (22, 87),
        7:  (37, 12), 4:  (37, 30), 8:  (37, 70), 11: (37, 88),
        10: (44, 50), 9:  (48, 50),
    },
    "343": {
        1:  (4, 50), 5:  (18, 25), 6:  (18, 50), 11: (18, 75),
        2:  (36, 20), 3:  (36, 40), 4:  (36, 60), 10: (36, 80),
        7:  (47, 20), 8:  (47, 50), 9:  (47, 80),
    },
    "3421": {
        1:  (4, 50), 5:  (18, 25), 6:  (18, 50), 8:  (18, 75),
        2:  (33, 12), 4:  (38, 36), 7:  (38, 64), 3:  (33, 88),
        9:  (45, 35), 10: (47, 50), 11: (45, 65),
    },
    "3142": {
        1:  (4, 50), 5:  (17, 25), 6:  (17, 50), 11: (17, 75),
        8:  (29, 50),
        2:  (37, 15), 7:  (37, 35), 4:  (37, 65), 3:  (37, 85),
        9:  (47, 35), 10: (47, 65),
    },
}


def _get_slot_coords(formation: str, slot: int, is_home: bool):
    """Return (x, y) pitch coords for a formation slot; mirrors for away."""
    coords = _COORDS.get(formation, {})
    if slot in coords:
        x, y = coords[slot]
        return (x, y) if is_home else (100 - x, 100 - y)
    # Generic fallback
    if slot == 1:
        x, y = 4, 50
    else:
        x, y = 37, 50
    return (x, y) if is_home else (100 - x, 100 - y)


def _shorten_name(name) -> str:
    """Abbreviate long names: 'Roberto Lewandowski' → 'R. Lewandowski'."""
    if not name or not isinstance(name, str):
        return ''
    name = name.strip()
    parts = name.split()
    if len(parts) == 1 or len(name) <= 14:
        return name
    return f"{parts[0][0]}. {' '.join(parts[1:])}"


def _format_formation(fmt: str) -> str:
    """Format '433' → '4-3-3'."""
    if not fmt or len(fmt) < 2:
        return fmt or ''
    return '-'.join(fmt)


# =============================================================================
# Lineup & substitution parsers
# =============================================================================

def get_player_name_lookup(f40_path: str) -> dict:
    """Build {player_ref_str: full_name} from f40 squad XML."""
    lookup = {}
    if not os.path.exists(f40_path):
        return lookup
    try:
        tree = ET.parse(f40_path)
        root = tree.getroot()
        doc = root.find("SoccerDocument")
        if doc is None:
            return lookup
        for team in doc.findall("Team"):
            for player in team.findall("Player"):
                uid = player.attrib.get("uID", "")
                name_el = player.find("Name")
                if name_el is not None and name_el.text:
                    lookup[uid] = name_el.text.strip()
    except Exception:
        pass
    return lookup


def parse_lineup_f9(f9_path: str, player_lookup: dict) -> dict | None:
    """
    Parse lineup from f9 matchresults XML.

    Returns dict with keys 'home' and 'away', each containing:
        formation (str), starters (list), subs (list)
    Each player dict has: jersey, name, formation_place, is_captain, player_ref
    Returns None if file not found.
    """
    if not os.path.exists(f9_path):
        return None
    try:
        tree = ET.parse(f9_path)
        root = tree.getroot()
        doc = root.find("SoccerDocument")
        md = doc.find("MatchData")
    except Exception:
        return None

    result = {}
    for td in md.findall("TeamData"):
        side = td.attrib.get("Side", "").lower()
        if side not in ("home", "away"):
            continue

        # Formation
        formation = next(
            (s.text for s in td.findall("Stat") if s.attrib.get("Type") == "formation_used"),
            ""
        ) or ""

        starters, subs = [], []
        lineup = td.find("PlayerLineUp")
        if lineup is None:
            result[side] = {"formation": formation, "starters": starters, "subs": subs}
            continue

        for mp in lineup.findall("MatchPlayer"):
            ref = mp.attrib.get("PlayerRef", "")
            jersey = mp.attrib.get("ShirtNumber", "")
            status = mp.attrib.get("Status", "")
            is_captain = mp.attrib.get("Captain", "0") == "1"
            fp = int(next(
                (s.text for s in mp.findall("Stat") if s.attrib.get("Type") == "formation_place"),
                "0"
            ) or "0")
            name = player_lookup.get(ref, ref)

            entry = {
                "jersey": jersey,
                "name": name,
                "formation_place": fp,
                "is_captain": is_captain,
                "player_ref": ref,
            }
            if status == "Start":
                starters.append(entry)
            else:
                subs.append(entry)

        result[side] = {"formation": formation, "starters": starters, "subs": subs}

    return result if result else None


def parse_substitutions(df_events: pd.DataFrame, lineup: dict) -> dict:
    """
    Extract substitution pairs from f24 events.

    type_id 18 = player off, type_id 19 = player on.
    Returns {'home': [...], 'away': [...]} where each item has:
        minute, player_off, jersey_off, player_on, jersey_on
    """
    # Build player_ref → {name, jersey} lookup from lineup
    ref_info = {}
    for side in ("home", "away"):
        if lineup and side in lineup:
            for p in lineup[side].get("starters", []) + lineup[side].get("subs", []):
                ref_info[str(int(float(p["player_ref"].replace("p", "")))
                              if p["player_ref"].startswith("p")
                              else p["player_ref"])] = p

    offs = df_events[df_events["type_id"] == 18].copy()
    ons  = df_events[df_events["type_id"] == 19].copy()

    # Group subs by (team_id, minute)
    subs_by_team: dict = {}
    for _, row in offs.iterrows():
        key = (row["team_id"], row["min"])
        subs_by_team.setdefault(key, {})["off"] = str(int(row["player_id"]))
    for _, row in ons.iterrows():
        key = (row["team_id"], row["min"])
        subs_by_team.setdefault(key, {})["on"] = str(int(row["player_id"]))

    # Determine home vs away team_id from the two distinct teams in events
    home_tid = None
    if not df_events.empty and "team_name" in df_events.columns:
        team_ids_sorted = sorted(df_events["team_id"].unique(), key=float)
        home_tid = float(team_ids_sorted[0]) if len(team_ids_sorted) >= 1 else None

    result = {"home": [], "away": []}
    for (tid, minute), pair in sorted(subs_by_team.items(), key=lambda x: x[0][1]):
        off_ref = pair.get("off", "")
        on_ref  = pair.get("on", "")
        off_info = ref_info.get(off_ref, {})
        on_info  = ref_info.get(on_ref, {})

        entry = {
            "minute":     int(minute),
            "player_off": off_info.get("name", off_ref),
            "player_on":  on_info.get("name", on_ref),
            "jersey_off": off_info.get("jersey", ""),
            "jersey_on":  on_info.get("jersey", ""),
        }
        side = "home" if float(tid) == home_tid else "away"
        result[side].append(entry)

    return result


# =============================================================================
# Lineup pitch image generator
# =============================================================================

def generate_lineup_pitch_image(lineup: dict) -> str | None:
    """
    Render a horizontal mplsoccer pitch with both starting XIs.
    Returns base64-encoded PNG or None on failure.
    """
    if not lineup:
        return None

    home_data = lineup.get("home", {})
    away_data = lineup.get("away", {})
    home_fmt  = home_data.get("formation", "")
    away_fmt  = away_data.get("formation", "")

    fig, ax = plt.subplots(figsize=(15, 7.5), facecolor="#0A0E27")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.90, bottom=0.02)
    ax.set_facecolor("#0A0E27")

    pitch = Pitch(
        pitch_type="opta",
        pitch_color="#3a7d44",
        line_color="white",
        stripe=True,
        stripe_color="#2e6b39",
        goal_type="box",
        goal_alpha=0.85,
        pad_top=5, pad_bottom=5, pad_left=3, pad_right=3,
    )
    pitch.draw(ax=ax)

    fig.text(0.5, 0.97, "Starting XI",
             ha="center", va="top", fontsize=16, color="white", fontweight="bold",
             path_effects=[mpe.withStroke(linewidth=3, foreground="#0A0E27")])

    def _draw_side(players, formation, is_home, dot_color):
        xs, ys, jerseys, names, caps = [], [], [], [], []
        for p in players:
            slot = p.get("formation_place", 0)
            if slot == 0:
                continue
            x, y = _get_slot_coords(formation, slot, is_home)
            xs.append(x); ys.append(y)
            jerseys.append(str(p.get("jersey", "")))
            names.append(p.get("name", ""))
            caps.append(bool(p.get("is_captain", False)))

        if not xs:
            return

        # Glow rings
        pitch.scatter(xs, ys, s=900, c=dot_color, ax=ax,
                      zorder=4, alpha=0.22, edgecolors="none")
        # Main circles
        pitch.scatter(xs, ys, s=650, c=dot_color, ax=ax,
                      zorder=5, alpha=0.95, edgecolors="white", linewidths=1.6)

        for i, (x, y) in enumerate(zip(xs, ys)):
            ax.text(x, y, jerseys[i],
                    ha="center", va="center",
                    fontsize=9, fontweight="bold", color="white", zorder=7)
            ax.text(x, y - 5.2, _shorten_name(names[i]),
                    ha="center", va="top",
                    fontsize=8.5, color="white", zorder=7,
                    path_effects=[mpe.withStroke(linewidth=2.5, foreground="#0A0E27")])
            if caps[i]:
                bx = x + (3.0 if is_home else -3.0)
                by = y + 3.0
                pitch.scatter([bx], [by], s=160, c=GOLD, ax=ax, zorder=8, edgecolors="none")
                ax.text(bx, by, "C",
                        ha="center", va="center",
                        fontsize=5.5, fontweight="bold", color="#0A0E27", zorder=9)

    _draw_side(home_data.get("starters", []), home_fmt, True,  HOME_COLOR)
    _draw_side(away_data.get("starters", []), away_fmt, False, AWAY_COLOR)

    # Formation labels
    for tx, fmt, col in [
        (14, _format_formation(home_fmt), HOME_COLOR),
        (86, _format_formation(away_fmt), AWAY_COLOR),
    ]:
        ax.text(tx, 107, fmt, ha="center", va="bottom",
                fontsize=13, color=col, fontweight="bold",
                path_effects=[mpe.withStroke(linewidth=2.5, foreground="#0A0E27")])

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130,
                facecolor=fig.get_facecolor(), edgecolor="none",
                bbox_inches="tight")
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return img_b64


def parse_match_stats(file_path_f24):
    """Extract match statistics from f24 XML file"""
    if not os.path.exists(file_path_f24):
        return None, None, None
    
    tree = ET.parse(file_path_f24)
    root = tree.getroot()
    
    game = root.find("Game")
    game_data = {attr: game.attrib[attr] for attr in game.attrib}
    df_game = pd.DataFrame([game_data])
    team_names = df_game[["home_team_id", "home_team_name", "away_team_id", "away_team_name"]]
    
    event_list = []
    for event in game.findall("Event"):
        event_data = {attr: event.attrib[attr] for attr in event.attrib} 
        qualifiers = [{attr: qualifier.attrib[attr] for attr in qualifier.attrib} for qualifier in event.findall("Q")]
        event_data["qualifiers"] = qualifiers  
        event_list.append(event_data)
    
    df_events = pd.DataFrame(event_list).drop(["last_modified", "version"], axis=1)
    df_events["keypass"] = df_events["keypass"].fillna(0)
    df_events = df_events.astype({"id": float, "event_id": float, "type_id": float, "period_id": float,
                                  "min": float, "sec": float, "team_id": float, "outcome": float,
                                  "x": float, "y": float, "player_id": float, "keypass": float})
    
    teams = pd.concat([
        team_names[['home_team_id', 'home_team_name']].rename(columns={'home_team_id': 'team_id', 'home_team_name': 'team_name'}),
        team_names[['away_team_id', 'away_team_name']].rename(columns={'away_team_id': 'team_id', 'away_team_name': 'team_name'})
    ]).drop_duplicates().astype({"team_id": float})
    
    df_events = df_events.merge(teams, on="team_id", how="left")
    
    return df_events, team_names, game_data

def has_qualifier(qualifiers, qualifier_id):
    """
    Check if a specific qualifier exists in the qualifiers list
    
    Args:
        qualifiers: List of qualifier dictionaries
        qualifier_id: The qualifier ID to check for (as int or string)
    
    Returns:
        bool: True if qualifier exists, False otherwise
    """
    if not isinstance(qualifiers, list):
        return False
    
    qualifier_str = str(qualifier_id)
    for q in qualifiers:
        if q.get("qualifier_id") == qualifier_str:
            return True
    return False

def calculate_match_stats(df_events, team_names, game_data):
    """
    Calculate key match statistics for both teams
    
    VERIFIED OPTA EVENT TYPES (from official CSV documentation):
    - Type 1: Pass (with qualifiers for special events)
      - Qualifier 6: Corner taken (for corner statistics)
    - Type 2: Offside Pass (for offside statistics)
    - Type 3: Take On (dribbles - used for possession)
    - Type 4: Foul (with Qualifier 13 for foul statistics)
    - Type 13: Miss (shot off target)
    - Type 14: Post (shot hits frame)
    - Type 15: Saved Shot (shot on target, saved)
    - Type 16: Goal
    - Type 17: Card (with qualifiers: 31=Yellow, 32=Second Yellow, 33=Red)
    
    IMPORTANT NOTES:
    - Corners: Type 1 with Qualifier 6 → team_id shows attacking team
    - Fouls: Type 4 with Qualifier 13 → team_id shows team that committed foul
    - Cards: Type 17 with qualifiers 31/32/33
    - Offsides: Type 2 (offside pass events)
    - Possession: Calculated from successful passes (Type 1) + take-ons (Type 3)
    
    Args:
        df_events: DataFrame with all match events
        team_names: DataFrame with team IDs and names
        game_data: Dictionary with game metadata
    
    Returns:
        dict: Statistics for both teams
    """
    home_id = int(team_names["home_team_id"].iloc[0])
    away_id = int(team_names["away_team_id"].iloc[0])
    home_team = team_names["home_team_name"].iloc[0]
    away_team = team_names["away_team_name"].iloc[0]
    
    stats = {
        'home': {'team_name': home_team},
        'away': {'team_name': away_team}
    }
    
    # ==================== GOALS ====================
    # Type 16 = Goal
    goals = df_events[df_events['type_id'] == 16]
    stats['home']['goals'] = len(goals[goals['team_id'] == home_id])
    stats['away']['goals'] = len(goals[goals['team_id'] == away_id])
    
    # ==================== SHOTS ====================
    # Type 13 = Miss (off target)
    # Type 14 = Post (hits frame)
    # Type 15 = Saved Shot (on target, saved/blocked)
    # Type 16 = Goal
    shots = df_events[df_events['type_id'].isin([13, 14, 15, 16])]
    stats['home']['shots'] = len(shots[shots['team_id'] == home_id])
    stats['away']['shots'] = len(shots[shots['team_id'] == away_id])
    
    # ==================== SHOTS ON TARGET ====================
    # Type 15 = Saved Shot (on target)
    # Type 16 = Goal (on target)
    shots_on_target = df_events[df_events['type_id'].isin([15, 16])]
    stats['home']['shots_on_target'] = len(shots_on_target[shots_on_target['team_id'] == home_id])
    stats['away']['shots_on_target'] = len(shots_on_target[shots_on_target['team_id'] == away_id])
    
    # ==================== PASSES ====================
    # Type 1 = Pass (any pass attempted)
    passes = df_events[df_events['type_id'] == 1]
    successful_passes = passes[passes['outcome'] == 1]
    
    home_passes = len(passes[passes['team_id'] == home_id])
    away_passes = len(passes[passes['team_id'] == away_id])
    home_successful = len(successful_passes[successful_passes['team_id'] == home_id])
    away_successful = len(successful_passes[successful_passes['team_id'] == away_id])
    
    stats['home']['passes'] = home_passes
    stats['away']['passes'] = away_passes
    stats['home']['passes_completed'] = home_successful
    stats['away']['passes_completed'] = away_successful
    
    # ==================== POSSESSION ====================
    # STANDARD METHOD: Based on successful passes (Type 1) + Take Ons (Type 3)
    # Type 1 = Pass (with outcome=1 for successful)
    # Type 3 = Take On (dribble attempts)
    
    # Count successful passes
    pass_possession = successful_passes
    
    # Count take-ons (Type 3) - all attempts count for possession
    take_ons = df_events[df_events['type_id'] == 3]
    
    # Combine for total possession events
    home_possession_events = len(pass_possession[pass_possession['team_id'] == home_id]) + len(take_ons[take_ons['team_id'] == home_id])
    away_possession_events = len(pass_possession[pass_possession['team_id'] == away_id]) + len(take_ons[take_ons['team_id'] == away_id])
    total_possession_events = home_possession_events + away_possession_events
    
    if total_possession_events > 0:
        stats['home']['possession'] = (home_possession_events / total_possession_events) * 100
        stats['away']['possession'] = (away_possession_events / total_possession_events) * 100
    else:
        stats['home']['possession'] = 50
        stats['away']['possession'] = 50
    
    # ==================== FOULS COMMITTED ====================
    # Type 4 = Foul Committed
    # IMPORTANT: team_id represents the team that WAS FOULED, not the team that committed the foul!
    # Outcome: 0 = advantage played (no free kick), 1 = free kick awarded
    # We only count fouls that resulted in free kicks (outcome = 1)
    
    foul_events = df_events[df_events['type_id'] == 4].copy()
    
    # Filter by outcome = 1 (fouls that resulted in free kicks)
    fouls_awarded = foul_events[foul_events['outcome'] == 1]
    
    # REVERSED: team_id = team that was fouled
    # So fouls COMMITTED by home = fouls WHERE away was fouled
    stats['home']['fouls'] = len(fouls_awarded[fouls_awarded['team_id'] == away_id])
    stats['away']['fouls'] = len(fouls_awarded[fouls_awarded['team_id'] == home_id])
    
    # ==================== CARDS ====================
    # Type 17 = Card (bookings)
    # Qualifiers distinguish card types:
    # - Qualifier 31 = Yellow Card
    # - Qualifier 32 = Second Yellow (results in red)
    # - Qualifier 33 = Red Card (straight red)
    
    cards = df_events[df_events['type_id'] == 17].copy()
    
    # Yellow Cards: Type 17 WITH qualifier 31
    home_yellows = 0
    away_yellows = 0
    
    for _, row in cards.iterrows():
        if has_qualifier(row['qualifiers'], 31):  # Yellow card
            if row['team_id'] == home_id:
                home_yellows += 1
            elif row['team_id'] == away_id:
                away_yellows += 1
    
    stats['home']['yellow_cards'] = home_yellows
    stats['away']['yellow_cards'] = away_yellows
    
    # Red Cards: Type 17 WITH qualifier 32 (second yellow) OR 33 (straight red)
    home_reds = 0
    away_reds = 0
    
    for _, row in cards.iterrows():
        # Check for second yellow (32) or straight red (33)
        if has_qualifier(row['qualifiers'], 32) or has_qualifier(row['qualifiers'], 33):
            if row['team_id'] == home_id:
                home_reds += 1
            elif row['team_id'] == away_id:
                away_reds += 1
    
    stats['home']['red_cards'] = home_reds
    stats['away']['red_cards'] = away_reds
    
    # ==================== OFFSIDES ====================
    # Type 2 = Offside Pass (attempted pass made to a player who is in an offside position)
    offsides = df_events[df_events['type_id'] == 2]
    stats['home']['offsides'] = len(offsides[offsides['team_id'] == home_id])
    stats['away']['offsides'] = len(offsides[offsides['team_id'] == away_id])
    
    # ==================== CORNERS ====================
    # Type 6 = Corner Awarded - but assigned to DEFENDING team
    # To get corners WON by each team, count corner kicks TAKEN
    # Type 1 (Pass) with Qualifier 6 (Corner taken)
    
    corner_kicks = df_events[df_events['type_id'] == 1].copy()
    
    # Filter for corner kicks (qualifier 6)
    home_corners = 0
    away_corners = 0
    
    for _, row in corner_kicks.iterrows():
        if has_qualifier(row['qualifiers'], 6):  # Corner taken qualifier
            if row['team_id'] == home_id:
                home_corners += 1
            elif row['team_id'] == away_id:
                away_corners += 1
    
    stats['home']['corners'] = home_corners
    stats['away']['corners'] = away_corners
    
    return stats

def create_stat_bar(label, home_value, away_value, max_value, home_color="#1e40af", away_color="#dc2626", show_percentage=False):
    """Create a responsive TV-style stat comparison bar with label."""
    if isinstance(home_value, str):
        home_value = float(home_value.replace('%', ''))
    if isinstance(away_value, str):
        away_value = float(away_value.replace('%', ''))

    if max_value == 0:
        home_pct = 50
        away_pct = 50
    else:
        home_pct = (home_value / max_value) * 50
        away_pct = (away_value / max_value) * 50

    if show_percentage:
        home_display = f"{home_value:.1f}%"
        away_display = f"{away_value:.1f}%"
    else:
        home_display = int(home_value)
        away_display = int(away_value)

    home_weight = "700" if home_value >= away_value else "400"
    away_weight = "700" if away_value >= home_value else "400"

    return f"""
    <div style="margin: 0.25rem 0;">
        <div style="text-align:center; font-size:0.78rem; color:#64748b;
                    font-weight:500; margin-bottom:4px; text-transform:uppercase;
                    letter-spacing:0.06em;">
            {label}
        </div>
        <div style="display:flex; align-items:center; justify-content:center; gap:10px;">
            <div style="width:52px; text-align:right; font-weight:{home_weight};
                        color:{home_color}; font-size:1rem; flex-shrink:0;">
                {home_display}
            </div>
            <div style="flex:1; max-width:520px; display:flex; height:10px;
                        background:#f1f5f9; border-radius:5px; overflow:hidden;
                        position:relative; min-width:80px;">
                <div style="width:50%; display:flex; justify-content:flex-end;">
                    <div style="width:{home_pct * 2}%; background:{home_color};
                                border-radius:5px 0 0 5px; opacity:0.85;"></div>
                </div>
                <div style="position:absolute; left:50%; transform:translateX(-50%);
                            height:100%; width:2px; background:#cbd5e1; z-index:10;"></div>
                <div style="width:50%; display:flex; justify-content:flex-start;">
                    <div style="width:{away_pct * 2}%; background:{away_color};
                                border-radius:0 5px 5px 0; opacity:0.85;"></div>
                </div>
            </div>
            <div style="width:52px; text-align:left; font-weight:{away_weight};
                        color:{away_color}; font-size:1rem; flex-shrink:0;">
                {away_display}
            </div>
        </div>
    </div>
    """

def resize_and_pad_image(image_path, target_width=LOGO_WIDTH, target_height=LOGO_HEIGHT, bg_color=(255, 255, 255, 0)):
    """
    Resize image to fit within target dimensions while maintaining aspect ratio
    and pad to make it exactly target_width x target_height
    
    Args:
        image_path: Path to the image file
        target_width: Target width in pixels
        target_height: Target height in pixels
        bg_color: Background color for padding (RGBA tuple)
    
    Returns:
        base64 encoded string of the processed image
    """
    try:
        img = Image.open(image_path).convert("RGBA")
        
        # Calculate aspect ratio
        img_width, img_height = img.size
        ratio = min(target_width / img_width, target_height / img_height)
        
        # Calculate new dimensions
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        # Resize image maintaining aspect ratio
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create new image with target size and transparent background
        new_img = Image.new("RGBA", (target_width, target_height), bg_color)
        
        # Calculate position to center the image
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        
        # Paste resized image onto center of new image
        new_img.paste(img, (x_offset, y_offset), img if img.mode == 'RGBA' else None)
        
        # Convert to base64
        buffered = io.BytesIO()
        new_img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return img_str
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None

def get_team_logo_path(team_name, logo_directory):
    """Try to find team logo with different naming conventions"""
    clean_name = team_name.strip()
    extensions = ['.png', '.jpg', '.jpeg', '.svg']
    patterns = [
        clean_name,
        clean_name.replace(' ', '_'),
        clean_name.replace(' ', '-'),
        clean_name.replace(' ', ''),
        clean_name.lower(),
        clean_name.lower().replace(' ', '_'),
        clean_name.lower().replace(' ', '-'),
        clean_name.lower().replace(' ', ''),
    ]
    
    for pattern in patterns:
        for ext in extensions:
            potential_path = os.path.join(logo_directory, f"{pattern}{ext}")
            if os.path.exists(potential_path):
                return potential_path
    return None

def show_page():
    """Display match statistics page"""
    
    # Initialize database
    if "db_initialized" not in st.session_state:
        try:
            util.create_player_db(ruta_opta_f40)
            util.calendar(ruta_opta_f42)
            st.session_state.db_initialized = True
        except Exception as e:
            st.error(f"Error al inicializar la base de datos: {e}")
    
    df_players = pd.read_excel(ruta_excel_players)
    df_matches = pd.read_excel(ruta_excel_matches)
    
    # Get match from global session state
    if "global_selected_match_id" not in st.session_state:
        st.error("⚠️ Por favor, selecciona un partido primero")
        return
    
    match_id = st.session_state.global_selected_match_id
    match = st.session_state.global_selected_match
    
    # Build file path
    ruta_opta_f24 = os.path.join(BASE_DIR, "data_femeni", "raw", "f24", f"f24-903-2025-{match_id}-eventdetails.xml")
    
    # Parse match data
    df_events, team_names, game_data = parse_match_stats(ruta_opta_f24)
    
    if df_events is None:
        st.error("⚠️ No se encontraron datos para este partido")
        return
    
    # Calculate stats
    stats = calculate_match_stats(df_events, team_names, game_data)
    
    home_team = stats['home']['team_name']
    away_team = stats['away']['team_name']
    home_goals = stats['home']['goals']
    away_goals = stats['away']['goals']
    
    # ==================== MATCH HEADER WITH LOGOS ====================
    logo_dir = os.path.join(BASE_DIR, "assets", "logos_table")
    home_logo_path = get_team_logo_path(home_team, logo_dir)
    away_logo_path = get_team_logo_path(away_team, logo_dir)

    def _logo_html(name: str, color: str, logo_path) -> str:
        """Return <img> tag or styled initials circle."""
        b64 = resize_and_pad_image(logo_path, 100, 100) if logo_path else None
        if b64:
            return (
                f'<img src="data:image/png;base64,{b64}" '
                f'style="width:clamp(56px,9vw,96px); height:clamp(56px,9vw,96px); '
                f'object-fit:contain; display:block;" />'
            )
        initials = "".join(w[0].upper() for w in name.split()[:2])
        sz = "clamp(56px,9vw,96px)"
        return (
            f'<div style="width:{sz}; height:{sz}; border-radius:50%; '
            f'background:{color}18; border:2px solid {color}; '
            f'display:flex; align-items:center; justify-content:center; '
            f'font-size:clamp(1.1rem,2.5vw,1.8rem); font-weight:700; color:{color};">'
            f'{initials}</div>'
        )

    home_logo_el = _logo_html(home_team, HOME_COLOR, home_logo_path)
    away_logo_el = _logo_html(away_team, AWAY_COLOR, away_logo_path)

    st.html(f"""
    <div style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: clamp(16px,3vw,28px) clamp(12px,2vw,24px);
        background: linear-gradient(135deg, #f0f4ff 0%, #ffffff 45%, #fff0f0 100%);
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        gap: 8px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        margin-bottom: 4px;
    ">
        <!-- Home team -->
        <div style="display:flex; flex-direction:column; align-items:center;
                    flex:1; min-width:0; gap:10px; padding:0 8px;">
            {home_logo_el}
            <div style="color:{HOME_COLOR}; font-size:clamp(0.72rem,1.4vw,1.05rem);
                        font-weight:700; text-align:center; line-height:1.3;
                        word-break:break-word; width:100%;">
                {home_team}
            </div>
        </div>

        <!-- Score -->
        <div style="display:flex; flex-direction:column; align-items:center;
                    flex-shrink:0; gap:2px;">
            <div style="display:flex; align-items:center;
                        gap:clamp(6px,1.5vw,18px);">
                <span style="font-size:clamp(2.4rem,6vw,4.5rem); font-weight:900;
                             color:{HOME_COLOR}; line-height:1;">
                    {home_goals}
                </span>
                <span style="font-size:clamp(1.4rem,3vw,2.4rem); color:#94a3b8;
                             font-weight:300; line-height:1; margin-bottom:4px;">
                    –
                </span>
                <span style="font-size:clamp(2.4rem,6vw,4.5rem); font-weight:900;
                             color:{AWAY_COLOR}; line-height:1;">
                    {away_goals}
                </span>
            </div>
            <div style="font-size:0.65rem; color:#94a3b8; text-transform:uppercase;
                        letter-spacing:0.12em; font-weight:600; margin-top:2px;">
                Full Time
            </div>
        </div>

        <!-- Away team -->
        <div style="display:flex; flex-direction:column; align-items:center;
                    flex:1; min-width:0; gap:10px; padding:0 8px;">
            {away_logo_el}
            <div style="color:{AWAY_COLOR}; font-size:clamp(0.72rem,1.4vw,1.05rem);
                        font-weight:700; text-align:center; line-height:1.3;
                        word-break:break-word; width:100%;">
                {away_team}
            </div>
        </div>
    </div>
    """)

    # ==================== LINEUP SECTION ====================
    ruta_opta_f9 = os.path.join(BASE_DIR, "data_femeni", "raw", "f9", f"srml-903-2025-f{match_id}-matchresults.xml")
    player_lookup = get_player_name_lookup(ruta_opta_f40)
    lineup = parse_lineup_f9(ruta_opta_f9, player_lookup)

    if lineup:
        try:
            pitch_img = generate_lineup_pitch_image(lineup)
        except Exception:
            pitch_img = None

        subs = parse_substitutions(df_events, lineup)

        def _sub_panel_html(subs_list: list, align: str) -> str:
            """Build substitution panel HTML for one team."""
            text_align = "right" if align == "right" else "left"
            rows_html = ""
            for s in subs_list:
                minute = s.get("minute", 0)
                p_off  = _shorten_name(s.get("player_off", ""))
                p_on   = _shorten_name(s.get("player_on", ""))
                rows_html += f"""
                <div style="padding:7px 0; border-bottom:1px solid #f1f5f9; text-align:{text_align};">
                    <div style="color:#b45309; font-size:0.72rem; font-weight:700;
                                letter-spacing:0.03em; margin-bottom:2px;">{minute}'</div>
                    <div style="color:#dc2626; font-size:0.8rem; line-height:1.4;">
                        &#8595; {p_off or '&#8212;'}
                    </div>
                    <div style="color:#16a34a; font-size:0.8rem; font-weight:500; line-height:1.4;">
                        &#8593; {p_on or '&#8212;'}
                    </div>
                </div>"""
            if not rows_html:
                rows_html = f'<div style="color:#94a3b8; font-size:0.78rem; text-align:{text_align}; padding-top:4px;">Sin cambios</div>'
            header_color = HOME_COLOR if align == "left" else AWAY_COLOR
            return f"""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px;
                        padding:14px 16px; height:100%;
                        box-shadow:0 1px 4px rgba(0,0,0,0.04);">
                <div style="color:{header_color}; font-size:0.68rem; font-weight:700;
                            text-transform:uppercase; letter-spacing:0.08em;
                            margin-bottom:10px; text-align:{text_align};
                            padding-bottom:6px; border-bottom:2px solid {header_color}30;">
                    Cambios
                </div>
                {rows_html}
            </div>"""

        col_home, col_pitch, col_away = st.columns([1, 3, 1])

        with col_home:
            st.html(_sub_panel_html(subs.get("home", []), "left"))

        with col_pitch:
            if pitch_img:
                st.html(
                    f'<div style="width:100%; border-radius:10px; overflow:hidden; '
                    f'box-shadow:0 2px 12px rgba(0,0,0,0.12);">'
                    f'<img src="data:image/png;base64,{pitch_img}" '
                    f'style="width:100%; height:auto; display:block;" /></div>'
                )

        with col_away:
            st.html(_sub_panel_html(subs.get("away", []), "right"))

        st.divider()

    # ==================== MATCH STATISTICS ====================
    def _stat(label, h, a, pct=False):
        mx = max(h, a) if max(h, a) > 0 else 1
        return create_stat_bar(label, h, a, mx, show_percentage=pct)

    stats_html = "".join([
        _stat("Posesión",           stats['home']['possession'],     stats['away']['possession'],     pct=True),
        _stat("Tiros Totales",      stats['home']['shots'],          stats['away']['shots']),
        _stat("Tiros a Puerta",     stats['home']['shots_on_target'],stats['away']['shots_on_target']),
        _stat("Pases Completados",  stats['home']['passes_completed'],stats['away']['passes_completed']),
        _stat("Faltas",             stats['home']['fouls'],          stats['away']['fouls']),
        _stat("Tarjetas Amarillas", stats['home']['yellow_cards'],   stats['away']['yellow_cards']),
        _stat("Tarjetas Rojas",     stats['home']['red_cards'],      stats['away']['red_cards']),
        _stat("Fueras de Juego",    stats['home']['offsides'],       stats['away']['offsides']),
        _stat("Saques de Esquina",  stats['home']['corners'],        stats['away']['corners']),
    ])

    st.html(f"""
    <div style="
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.05);
        max-width: 700px;
        margin: 0 auto;
    ">
        <!-- Team name row -->
        <div style="display:flex; justify-content:space-between; align-items:center;
                    margin-bottom:16px; padding-bottom:12px;
                    border-bottom:2px solid #f1f5f9;">
            <span style="color:{HOME_COLOR}; font-weight:700; font-size:0.9rem;
                         text-transform:uppercase; letter-spacing:0.05em;">
                {home_team}
            </span>
            <span style="color:#94a3b8; font-size:0.72rem; font-weight:600;
                         text-transform:uppercase; letter-spacing:0.1em;">
                Estadísticas
            </span>
            <span style="color:{AWAY_COLOR}; font-weight:700; font-size:0.9rem;
                         text-transform:uppercase; letter-spacing:0.05em;">
                {away_team}
            </span>
        </div>
        {stats_html}
    </div>
    """)
    
    st.divider()
    
    # Data source
    import locale
    from datetime import datetime
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
    
    def last_modified(folder_path):
        latest_mod = 0
        for root, _, files in os.walk(folder_path):
            for f in files:
                file_path = os.path.join(root, f)
                mod_time = os.path.getmtime(file_path)
                latest_mod = max(latest_mod, mod_time)
        fecha = datetime.fromtimestamp(latest_mod)
        return fecha.strftime("%-d de %B")
    
    last_update = last_modified(f"{BASE_DIR}/data_femeni/raw")
    st.write(f"Última actualización: {last_update} | Fuente de datos: Opta Stats Perform")