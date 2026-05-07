#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shots & xG Analysis Module
Complete shot analysis with xG values, shot maps, xG timeline, and goal mouth visualization
"""

import streamlit as st
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler
from mplsoccer import Pitch
import base64
import io
import xml.etree.ElementTree as ET
from datetime import datetime
import locale

# ==================== UTILITY FUNCTIONS ====================

def string_to_numeric(x):
    """Convert string to numeric, handling errors gracefully"""
    return pd.to_numeric(x, errors='coerce')

def ensure_and_convert_columns(events: pd.DataFrame) -> pd.DataFrame:
    """Ensure columns exist and convert to numeric"""
    cols = ['min', 'sec', 'x', 'y', '102', '103', '146', '147', 'outcome']
    for col in cols:
        if col in events.columns:
            events[col] = string_to_numeric(events[col])
        else:
            events[col] = 0
    return events

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

def load_logo_base64(logo_path):
    """Load and convert logo to base64"""
    if logo_path and os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        except:
            pass
    return None

# ==================== DATA PARSING FUNCTIONS ====================

def parse_f70_events(xml_filename):
    """Parse F70 XML file for xG data"""
    
    def pick_out_the_maximum_values(qualifier_values):
        max_values = []
        for c in range(qualifier_values.shape[1]):
            col_2_test = qualifier_values.iloc[:, c]
            max_val = col_2_test.dropna().iloc[0]
            max_values.append(max_val)
        results_Q = pd.DataFrame([max_values], columns=qualifier_values.columns)
        return results_Q
    
    def convert_event_node_row(xml_2_spread):
        results = pd.DataFrame(xml_2_spread['attrs'], index=[0])
        no_of_qualifiers = len(xml_2_spread['value'])
        
        if no_of_qualifiers > 0:
            Qualifier_Unpacked_Step1 = pd.DataFrame()
            for Q in range(no_of_qualifiers):
                Qualifier_unpacked = xml_2_spread['value'][Q]
                Value = 1 if 'value' not in Qualifier_unpacked.keys() else Qualifier_unpacked["value"]
                temp = pd.DataFrame({"Q": [str(Value)]}, dtype=str)
                temp.columns = [Qualifier_unpacked["qualifier_id"]]
                Qualifier_Unpacked_Step1 = pd.concat([Qualifier_Unpacked_Step1, temp], axis=0, ignore_index=True)
            
            Qualifier_unpacked_df = pick_out_the_maximum_values(Qualifier_Unpacked_Step1)
            results = pd.concat([results, Qualifier_unpacked_df], axis=1)
        
        return results
    
    pbpParse = ET.parse(xml_filename)
    all_event_nodes = []
    for event in pbpParse.findall('.//Game/Event'):
        event_attrs = event.attrib
        event_values = [child.attrib for child in list(event)]
        all_event_nodes.append({'attrs': event_attrs, 'value': event_values})
  
    events = pd.concat([convert_event_node_row(e) for e in all_event_nodes], ignore_index=True)
    
    players = {}
    player_name = None
    for i, team in enumerate(pbpParse.findall('.//Team')):
        team_code = int(team.get('uID')[1:])
        players[f'team{i+1}_code'] = team_code
        players[f'playert{i+1}'] = [{'code': int(player.get('uID')[1:]), 'position': player.get('Position'), 'name': player.find('.//PersonName/First').text + ' ' + player.find('.//PersonName/Last').text} for player in team.findall('Player')]
    
    for idx, event in events.iterrows():
        team_code = event['team_id']
        j = 1 if team_code == str(players[f'team{1}_code']) else 2
        for player in players[f'playert{j}']:
            if player['code'] == int(event['player_id']):
                player_name = player['name']
                break
        events.at[idx, 'player_name'] = player_name

    events = ensure_and_convert_columns(events)
    return events

def parse_f24(file_path_24):
    """Parse F24 XML file for basic match events"""
    if not os.path.exists(file_path_24):
        print(f"Error: El archivo '{file_path_24}' no existe.")
        return None, None
    
    tree = ET.parse(file_path_24)
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
    df_events[["timestamp", "timestamp_utc"]] = df_events[["timestamp", "timestamp_utc"]].apply(pd.to_datetime)
    df_events["first_qualifier_id"] = df_events["qualifiers"].apply(lambda q: q[0]["qualifier_id"] if q else None).astype(float)
    return df_events, team_names

def get_goals(file_path_24):
    """Extract goals and calculate running score"""
    df_events, team_names = parse_f24(file_path_24)
    goals = df_events[df_events["type_id"] == 16]
    home_id = team_names["home_team_id"].iloc[0]
    away_id = team_names["away_team_id"].iloc[0]
    goals["local_goals"] = (goals["team_id"] == int(home_id)).cumsum()
    goals["visitor_goals"] = (goals["team_id"] == int(away_id)).cumsum()
    
    home_goals = (goals["team_id"] == int(home_id)).sum()
    away_goals = (goals["team_id"] == int(away_id)).sum()
    goals["resultado"] = goals["local_goals"].astype(str) + "-" + goals["visitor_goals"].astype(str)
    goals["time_minutes"] = goals["min"] + goals["sec"] / 60
    goals = goals[["time_minutes", "resultado"]]
    
    return goals, home_goals, away_goals

def last_modified(folder_path):
    """Get last modification date of files in folder"""
    latest_mod = 0
    for root, _, files in os.walk(folder_path):
        for f in files:
            file_path = os.path.join(root, f)
            mod_time = os.path.getmtime(file_path)
            latest_mod = max(latest_mod, mod_time)
    fecha = datetime.fromtimestamp(latest_mod)
    try:
        return fecha.strftime("%-d de %B")
    except:
        return fecha.strftime("%d de %B")

# ==================== VISUALIZATION FUNCTIONS ====================

def create_goal_mouth_figure(df_team, team_name, team_color, team_goals, team_xg, team_logo_base64, goal_img_base64):
    """Create interactive goal mouth visualization for a team.
    
    Opta coordinate system for shot end locations:
    - end_location_y (col 102): horizontal position across goal face,
      roughly 36.8–63.2 for on-target (centered at 50).
    - end_location_z (col 103): height in Opta units.
      Ground ≈ 0, crossbar ≈ 33 (proportional: goal is ~3× wider than tall).
    """
    
    # --- Goal boundary constants (Opta coordinates) ---
    GOAL_LEFT = 36.8
    GOAL_RIGHT = 63.2
    GOAL_WIDTH = GOAL_RIGHT - GOAL_LEFT   # 26.4
    GOAL_HEIGHT = GOAL_WIDTH / 3.0         # ~8.8 but z-scale is different
    # In the Opta z-coordinate system, crossbar is at about z≈33
    CROSSBAR_Z = 33.0
    
    fig = go.Figure()
    
    # --- Add goal image as background ---
    if goal_img_base64:
        # The goal.jpg image shows: posts at left/right edges, crossbar at top, ground at bottom.
        # Position it so that the image edges align with the goal boundaries.
        # Image x = left edge, image y = top edge (Plotly convention)
        img_padding_x = 1.5  # small padding so posts aren't clipped
        img_padding_top = 1.0
        fig.add_layout_image(
            dict(
                source=f'data:image/jpeg;base64,{goal_img_base64}',
                xref="x",
                yref="y",
                x=GOAL_LEFT - img_padding_x,
                y=CROSSBAR_Z + img_padding_top,
                sizex=GOAL_WIDTH + 2 * img_padding_x,
                sizey=CROSSBAR_Z + img_padding_top + 2,  # extends to just below ground
                sizing="stretch",
                opacity=1,
                layer="below"
            )
        )
    
    # --- Plot shot markers ---
    goals_team = df_team[df_team["outcome_name"] == "Goal"]
    miss_team = df_team[df_team["outcome_name"] != "Goal"]
    
    # Misses (gray circles)
    if len(miss_team) > 0:
        fig.add_trace(go.Scatter(
            x=miss_team["end_location_y"],
            y=miss_team["end_location_z"],
            mode='markers',
            marker=dict(
                size=miss_team["321_scaled"],
                color='#64748b',
                line=dict(width=1, color='#1e293b'),
                opacity=0.95
            ),
            customdata=miss_team[['xg_display', 'player_name']],
            hovertemplate='<b>Tiro Fuera</b><br>Jugadora: %{customdata[1]}<br>xG: %{customdata[0]}<extra></extra>',
            name='Fuera',
            showlegend=True
        ))
    
    # Goals (team color circles)
    if len(goals_team) > 0:
        fig.add_trace(go.Scatter(
            x=goals_team["end_location_y"],
            y=goals_team["end_location_z"],
            mode='markers',
            marker=dict(
                size=goals_team["321_scaled"],
                color=team_color,
                line=dict(width=1.5, color='#0f172a'),
                opacity=1.0
            ),
            customdata=goals_team[['xg_display', 'player_name']],
            hovertemplate='<b>⚽ GOL</b><br>Jugadora: %{customdata[1]}<br>xG: %{customdata[0]}<extra></extra>',
            name='Gol',
            showlegend=True
        ))
    
    # --- Team logo ---
    if team_logo_base64:
        fig.add_layout_image(
            dict(
                source=f'data:image/png;base64,{team_logo_base64}',
                xref="paper",
                yref="paper",
                x=0.5,
                y=1.20,
                sizex=0.20,
                sizey=0.20,
                xanchor="center",
                yanchor="bottom",
                layer="above"
            )
        )
    
    # --- Team name and stats ---
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.5, y=1.16,
        text=f"<b>{team_name}</b><br>Goles: {team_goals}  |  xG: {team_xg:.2f}",
        showarrow=False,
        font=dict(size=14, color='#1e293b', family='Arial'),
        align='center',
        xanchor='center', yanchor='top'
    )
    
    # --- Layout ---
    fig.update_layout(
        xaxis=dict(range=[GOAL_LEFT - 8, GOAL_RIGHT + 8], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[-3, 70], showgrid=False, zeroline=False, visible=False),
        height=450,
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.02,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='black',
            borderwidth=1
        ),
        margin=dict(l=10, r=10, t=130, b=30),
        hovermode='closest'
    )
    
    return fig

# ==================== MAIN PAGE FUNCTION ====================

def show_page():
    """Display shot analysis page"""
    
    # Info box
    st.markdown("""
        <div class='info-box'>
            <p><strong>Análisis completo de tiros con:</strong>
                <ul style='margin: 0.5rem 0; padding-left: 1.5rem;'>
                    <li>Métricas de Goles Esperados (xG)</li>
                    <li>Posiciones de tiros en el campo</li>
                    <li>Línea de tiempo de xG</li>
                    <li>Precisión en el remate</li>
                </ul>
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # ==================== SETUP ====================
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    if "global_selected_match_id" not in st.session_state:
        st.error("⚠️ Por favor, selecciona un partido primero")
        return
    
    match = st.session_state.global_selected_match
    match_id = st.session_state.global_selected_match_id
    
    # Determine file paths
    ruta_opta_f24_2025 = os.path.join(BASE_DIR, "data_femeni", "raw", "f24", f"f24-903-2025-{match_id}-eventdetails.xml")
    ruta_opta_f24_2024 = os.path.join(BASE_DIR, "data_femeni", "raw", "f24", f"f24-903-2024-{match_id}-eventdetails.xml")
    filepath_f70_2025 = os.path.join(BASE_DIR, "data_femeni", "raw", "f70", f"f70-903-2025-{match_id}-expectedgoals.xml")
    filepath_f70_2024 = os.path.join(BASE_DIR, "data_femeni", "raw", "f70", f"f70-903-2024-{match_id}-expectedgoals.xml")
    
    if os.path.exists(ruta_opta_f24_2025):
        ruta_opta_f24 = ruta_opta_f24_2025
        filepath_f70 = filepath_f70_2025
    elif os.path.exists(ruta_opta_f24_2024):
        ruta_opta_f24 = ruta_opta_f24_2024
        filepath_f70 = filepath_f70_2024
    else:
        st.error(f"⚠️ Archivo no encontrado para el partido {match}")
        st.info(f"Buscando: f24-903-YYYY-{match_id}-eventdetails.xml")
        
        f24_dir = os.path.join(BASE_DIR, "data_femeni", "raw", "f24")
        if os.path.exists(f24_dir):
            with st.expander("🔍 Ver archivos disponibles"):
                available_files = sorted([f for f in os.listdir(f24_dir) if f.endswith('.xml')])
                if available_files:
                    st.write("Archivos F24 disponibles:")
                    for f in available_files[:10]:
                        st.text(f"  • {f}")
                    if len(available_files) > 10:
                        st.text(f"  ... y {len(available_files) - 10} más")
                else:
                    st.warning("No hay archivos F24 en el directorio")
        return
    
    if not os.path.exists(filepath_f70):
        st.error(f"⚠️ Archivo F70 (xG data) no encontrado para el partido {match}")
        st.info(f"Buscando: {os.path.basename(filepath_f70)}")
        return
    
    st.divider()
    
    # ==================== LOAD DATA ====================
    try:
        goals, home_goals, away_goals = get_goals(ruta_opta_f24)
        events = parse_f70_events(filepath_f70)
    except Exception as e:
        st.error(f"⚠️ Error al procesar los datos del partido: {str(e)}")
        with st.expander("Ver detalles del error"):
            import traceback
            st.code(traceback.format_exc())
        return
    
    # Get team info
    _, team_names = parse_f24(ruta_opta_f24)
    home_team = team_names["home_team_name"].iloc[0]
    home_id = int(team_names["home_team_id"].iloc[0])
    away_team = team_names["away_team_name"].iloc[0]
    away_id = int(team_names["away_team_id"].iloc[0])
    
    # Load team logos once
    logo_dir = os.path.join(BASE_DIR, "assets", "logos_table")
    home_logo_base64 = load_logo_base64(get_team_logo_path(home_team, logo_dir))
    away_logo_base64 = load_logo_base64(get_team_logo_path(away_team, logo_dir))
    
    # ==================== PREPARE SHOT DATA ====================
    shot_events = events[events['type_id'].isin(['13', '14', '15', '16'])].copy()
    shot_events["team_id"] = shot_events["team_id"].astype(int)
    shot_events["time_minutes"] = shot_events["min"] + shot_events["sec"] / 60
    shot_events["321"] = shot_events["321"].astype(float)
    
    # Calculate statistics
    shot_events_home = shot_events[shot_events["team_id"] == home_id]
    shot_events_away = shot_events[shot_events["team_id"] == away_id]
    total_xg_home = shot_events_home["321"].sum()
    total_xg_away = shot_events_away["321"].sum()
    home_shots = len(shot_events_home)
    away_shots = len(shot_events_away)
    
    # Shots on target: type 15 (Saved) and 16 (Goal)
    shots_on_target = shot_events[shot_events['type_id'].isin(['15', '16'])]
    home_shots_on_target = len(shots_on_target[shots_on_target["team_id"] == home_id])
    away_shots_on_target = len(shots_on_target[shots_on_target["team_id"] == away_id])
    
    # Flip home team coordinates
    mask = shot_events["team_id"] == home_id
    shot_events.loc[mask, "x"] = 100 - shot_events.loc[mask, "x"]
    shot_events.loc[mask, "y"] = 100 - shot_events.loc[mask, "y"]

    # Scale xG for marker size
    scaler = MinMaxScaler(feature_range=(10, 30))
    shot_events["marker_size"] = scaler.fit_transform(shot_events[["321"]])

    # Separate by team and outcome
    df_home_shots = shot_events[shot_events["team_id"] == home_id].copy()
    df_away_shots = shot_events[shot_events["team_id"] == away_id].copy()
    
    df_home_goals = df_home_shots[df_home_shots['type_id'] == '16'].copy()
    df_home_non_goals = df_home_shots[df_home_shots['type_id'] != '16'].copy()
    df_away_goals = df_away_shots[df_away_shots['type_id'] == '16'].copy()
    df_away_non_goals = df_away_shots[df_away_shots['type_id'] != '16'].copy()

    # Format xG for tooltips
    for df in [df_home_goals, df_home_non_goals, df_away_goals, df_away_non_goals]:
        df["xg_display"] = df["321"].apply(lambda x: f"{x:.3f}")

    # ==================== SHOT MAP ====================
    pitch = Pitch(pitch_type="opta", pitch_color='grass', line_color='white', stripe=True,
                 pad_left=5, pad_right=5, pad_top=2, pad_bottom=2, goal_type='box', goal_alpha=0.8)
    fig_pitch, ax_pitch = pitch.draw(figsize=(15, 10))
    
    buf = io.BytesIO()
    fig_pitch.savefig(buf, format='png', dpi=100, bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    pitch_img = base64.b64encode(buf.read()).decode()
    plt.close(fig_pitch)
    
    fig = go.Figure()
    
    # Add traces for home team
    fig.add_trace(go.Scatter(
        x=df_home_non_goals["x"], y=df_home_non_goals["y"], mode='markers',
        marker=dict(size=df_home_non_goals["marker_size"], color='#1e40af', symbol='circle', line=dict(width=2, color='white')),
        customdata=df_home_non_goals[['xg_display', 'player_name']],
        hovertemplate='<b>' + home_team + '</b><br>Jugadora: %{customdata[1]}<br>xG: %{customdata[0]}<extra></extra>',
        name=home_team, showlegend=True
    ))
    
    if len(df_home_goals) > 0:
        fig.add_trace(go.Scatter(
            x=df_home_goals["x"], y=df_home_goals["y"], mode='markers',
            marker=dict(size=df_home_goals["marker_size"] * 1.5, color='#1e40af', symbol='star', line=dict(width=2, color='white')),
            customdata=df_home_goals[['xg_display', 'player_name']],
            hovertemplate='<b>' + home_team + ' - ⚽ GOL</b><br>Jugadora: %{customdata[1]}<br>xG: %{customdata[0]}<extra></extra>',
            name=home_team + ' (Gol)', showlegend=False
        ))
    
    # Add traces for away team
    fig.add_trace(go.Scatter(
        x=df_away_non_goals["x"], y=df_away_non_goals["y"], mode='markers',
        marker=dict(size=df_away_non_goals["marker_size"], color='#dc2626', symbol='circle', line=dict(width=2, color='white')),
        customdata=df_away_non_goals[['xg_display', 'player_name']],
        hovertemplate='<b>' + away_team + '</b><br>Jugadora: %{customdata[1]}<br>xG: %{customdata[0]}<extra></extra>',
        name=away_team, showlegend=True
    ))
    
    if len(df_away_goals) > 0:
        fig.add_trace(go.Scatter(
            x=df_away_goals["x"], y=df_away_goals["y"], mode='markers',
            marker=dict(size=df_away_goals["marker_size"] * 1.5, color='#dc2626', symbol='star', line=dict(width=2, color='white')),
            customdata=df_away_goals[['xg_display', 'player_name']],
            hovertemplate='<b>' + away_team + ' - ⚽ GOL</b><br>Jugadora: %{customdata[1]}<br>xG: %{customdata[0]}<extra></extra>',
            name=away_team + ' (Gol)', showlegend=False
        ))
    
    # Add pitch background
    fig.add_layout_image(dict(
        source=f'data:image/png;base64,{pitch_img}',
        xref="x", yref="y", x=-5, y=102, sizex=110, sizey=104,
        sizing="stretch", opacity=1, layer="below"
    ))
    
    # Add team logos
    if home_logo_base64:
        fig.add_layout_image(dict(
            source=f'data:image/png;base64,{home_logo_base64}',
            xref="x", yref="y", x=45, y=98, sizex=12, sizey=12,
            xanchor="center", yanchor="top", layer="above"
        ))
    
    if away_logo_base64:
        fig.add_layout_image(dict(
            source=f'data:image/png;base64,{away_logo_base64}',
            xref="x", yref="y", x=55, y=98, sizex=12, sizey=12,
            xanchor="center", yanchor="top", layer="above"
        ))
    
    # Add annotations
    fig.add_annotation(
        x=35, y=90,
        text=f"<br>{home_goals} goles<br>xG: {total_xg_home:.2f}<br>Tiros: {home_shots}<br>({home_shots_on_target} a puerta)",
        showarrow=False, font=dict(size=13, color='white', family='Arial Black'),
        bgcolor='rgba(30, 64, 175, 0.85)', borderpad=8, borderwidth=2, bordercolor='white', align='center'
    )
    
    fig.add_annotation(
        x=65, y=90,
        text=f"<br>{away_goals} goles<br>xG: {total_xg_away:.2f}<br>Tiros: {away_shots}<br>({away_shots_on_target} a puerta)",
        showarrow=False, font=dict(size=13, color='white', family='Arial Black'),
        bgcolor='rgba(220, 38, 38, 0.85)', borderpad=8, borderwidth=2, bordercolor='white', align='center'
    )
    
    # Update layout
    fig.update_layout(
        xaxis=dict(range=[-5, 105], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[-2, 102], showgrid=False, zeroline=False, visible=False),
        height=500,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=1.05, xanchor="center", x=0.5,
                   bgcolor='rgba(255,255,255,0.9)', bordercolor='black', borderwidth=1, font=dict(size=14)),
        margin=dict(l=0, r=0, t=40, b=0), hovermode='closest'
    )

    st.markdown("### Tiros - Posición y xG ")
    st.markdown("""<div class='info-box'><p>⭐ Estrellas = Goles | ⚪ Círculos = Tiros sin gol | Pasa el cursor para ver xG</p></div>""", unsafe_allow_html=True)

    col_pitch, col_stats = st.columns([3, 1])

    with col_pitch:
        st.plotly_chart(fig, width='stretch')

    with col_stats:
        xg_per_shot_home = total_xg_home / home_shots if home_shots > 0 else 0
        xg_per_shot_away = total_xg_away / away_shots if away_shots > 0 else 0
        sot_pct_home = (home_shots_on_target / home_shots * 100) if home_shots > 0 else 0
        sot_pct_away = (away_shots_on_target / away_shots * 100) if away_shots > 0 else 0

        stats_rows = [
            ("⚽ Goles",           home_goals,                                       away_goals),
            ("📊 xG Total",        f"{total_xg_home:.2f}",                           f"{total_xg_away:.2f}"),
            ("🎯 Tiros",           home_shots,                                       away_shots),
            ("🥅 A Puerta",        home_shots_on_target,                             away_shots_on_target),
            ("% A Puerta",         f"{sot_pct_home:.0f}%",                           f"{sot_pct_away:.0f}%"),
            ("xG / Tiro",          f"{xg_per_shot_home:.3f}",                        f"{xg_per_shot_away:.3f}"),
        ]

        rows_html = ""
        for label, home_val, away_val in stats_rows:
            rows_html += f"""
            <tr>
                <td style='text-align:right; padding:6px 8px; font-weight:600; color:#1e40af;'>{home_val}</td>
                <td style='text-align:center; padding:6px 4px; color:#64748b; font-size:0.78rem; white-space:nowrap;'>{label}</td>
                <td style='text-align:left; padding:6px 8px; font-weight:600; color:#dc2626;'>{away_val}</td>
            </tr>"""

        st.markdown(f"""
        <div style='margin-top:60px;'>
            <table style='width:100%; border-collapse:collapse; font-size:0.88rem; font-family:Arial;'>
                <thead>
                    <tr>
                        <th style='text-align:right; padding:6px 8px; border-bottom:2px solid #1e40af; color:#1e40af;'>{home_team}</th>
                        <th style='text-align:center; padding:6px 4px; border-bottom:2px solid #cbd5e1; color:#64748b;'></th>
                        <th style='text-align:left; padding:6px 8px; border-bottom:2px solid #dc2626; color:#dc2626;'>{away_team}</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    
    # ==================== xG TIMELINE ====================
    st.markdown("### Evolución de xG durante el Partido")
    st.markdown("""
        <div class='info-box'>
            <p>⭐ Estrellas = Goles | ⚪ Círculos = Tiros sin gol | Cómo se acumularon las ocasiones de gol a lo largo del tiempo</p>
        </div>
    """, unsafe_allow_html=True)
    
    shot_timeline = events[events['type_id'].isin(['13', '14', '15', '16'])].copy()
    shot_timeline["time_minutes"] = shot_timeline["min"] + shot_timeline["sec"] / 60
    shot_timeline["321"] = shot_timeline["321"].astype(float)
    shot_timeline["team_id"] = shot_timeline["team_id"].astype(int)
    
    # Separate by team
    home_xg_timeline = shot_timeline[shot_timeline["team_id"] == home_id].copy().sort_values("time_minutes")
    away_xg_timeline = shot_timeline[shot_timeline["team_id"] == away_id].copy().sort_values("time_minutes")
    
    home_xg_timeline["cumulative_xg"] = home_xg_timeline["321"].cumsum()
    away_xg_timeline["cumulative_xg"] = away_xg_timeline["321"].cumsum()
    
    # Separate goals from non-goals
    home_goals_timeline = home_xg_timeline[home_xg_timeline['type_id'] == '16'].copy()
    home_non_goals_timeline = home_xg_timeline[home_xg_timeline['type_id'] != '16'].copy()
    away_goals_timeline = away_xg_timeline[away_xg_timeline['type_id'] == '16'].copy()
    away_non_goals_timeline = away_xg_timeline[away_xg_timeline['type_id'] != '16'].copy()
    
    fig_timeline = go.Figure()
    
    # Add home team traces
    fig_timeline.add_trace(go.Scatter(
        x=home_xg_timeline["time_minutes"], y=home_xg_timeline["cumulative_xg"],
        mode='lines', name=home_team, line=dict(color='#1e40af', width=3),
        showlegend=True, hoverinfo='skip'
    ))
    
    fig_timeline.add_trace(go.Scatter(
        x=home_non_goals_timeline["time_minutes"], y=home_non_goals_timeline["cumulative_xg"],
        mode='markers', marker=dict(size=10, color='#1e40af', symbol='circle', line=dict(color='white', width=2)),
        hovertemplate='<b>' + home_team + '</b><br>Minuto: %{x:.1f}<br>xG acumulado: %{y:.2f}<extra></extra>',
        showlegend=False
    ))
    
    if len(home_goals_timeline) > 0:
        fig_timeline.add_trace(go.Scatter(
            x=home_goals_timeline["time_minutes"], y=home_goals_timeline["cumulative_xg"],
            mode='markers', marker=dict(size=20, color='#1e40af', symbol='star', line=dict(color='white', width=2)),
            hovertemplate='<b>' + home_team + ' - ⚽ GOL</b><br>Minuto: %{x:.1f}<br>xG acumulado: %{y:.2f}<extra></extra>',
            showlegend=False
        ))
    
    # Add away team traces
    fig_timeline.add_trace(go.Scatter(
        x=away_xg_timeline["time_minutes"], y=away_xg_timeline["cumulative_xg"],
        mode='lines', name=away_team, line=dict(color='#dc2626', width=3),
        showlegend=True, hoverinfo='skip'
    ))
    
    fig_timeline.add_trace(go.Scatter(
        x=away_non_goals_timeline["time_minutes"], y=away_non_goals_timeline["cumulative_xg"],
        mode='markers', marker=dict(size=10, color='#dc2626', symbol='circle', line=dict(color='white', width=2)),
        hovertemplate='<b>' + away_team + '</b><br>Minuto: %{x:.1f}<br>xG acumulado: %{y:.2f}<extra></extra>',
        showlegend=False
    ))
    
    if len(away_goals_timeline) > 0:
        fig_timeline.add_trace(go.Scatter(
            x=away_goals_timeline["time_minutes"], y=away_goals_timeline["cumulative_xg"],
            mode='markers', marker=dict(size=20, color='#dc2626', symbol='star', line=dict(color='white', width=2)),
            hovertemplate='<b>' + away_team + ' - ⚽ GOL</b><br>Minuto: %{x:.1f}<br>xG acumulado: %{y:.2f}<extra></extra>',
            showlegend=False
        ))
    
    # Add goal markers
    max_y = max(
        home_xg_timeline["cumulative_xg"].max() if len(home_xg_timeline) > 0 else 1,
        away_xg_timeline["cumulative_xg"].max() if len(away_xg_timeline) > 0 else 1
    )
    
    for _, goal in goals.iterrows():
        fig_timeline.add_shape(
            type="line", x0=goal["time_minutes"], x1=goal["time_minutes"],
            y0=0, y1=max_y, line=dict(color="gray", width=1, dash="dash")
        )
        fig_timeline.add_annotation(
            x=goal["time_minutes"], y=max_y * 0.95, text=goal["resultado"],
            showarrow=False, textangle=-90, font=dict(size=10, color="gray")
        )
    
    fig_timeline.update_layout(
        xaxis_title="Tiempo (minutos)", yaxis_title="xG acumulado",
        legend=dict(orientation="h", yanchor="top", y=1.1, xanchor="center", x=0.5,
                   bgcolor='rgba(255,255,255,0.9)', bordercolor='black', borderwidth=1),
        autosize=True, height=400, plot_bgcolor='white', hovermode='closest'
    )
    
    fig_timeline.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='lightgray')
    fig_timeline.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='lightgray')
    
    st.plotly_chart(fig_timeline, width='stretch')
    st.divider()
    
    # ==================== GOAL MOUTH VISUALIZATION ====================
    st.markdown("### Finalización de las ocasiones de gol (xG): Tiros a puerta")
    
    # Prepare goal mouth data
    shot_events_mouth = events[events['type_id'].isin(['13', '14', '15', '16'])].copy()
    shot_events_mouth["type_id"] = shot_events_mouth["type_id"].astype(int)
    shot_events_mouth["321"] = shot_events_mouth["321"].astype(float)
    shot_events_mouth["end_location_y"] = shot_events_mouth["102"].astype(float)
    shot_events_mouth["end_location_z"] = shot_events_mouth["103"].astype(float)
    shot_events_mouth['outcome_name'] = np.where(shot_events_mouth['type_id'] == 16, 'Goal', 'Miss')
    
    scaler_mouth = MinMaxScaler(feature_range=(15, 40))
    shot_events_mouth["321_scaled"] = scaler_mouth.fit_transform(shot_events_mouth[["321"]])
    shot_events_mouth["xg_display"] = shot_events_mouth["321"].apply(lambda x: f"{x:.3f}")
    
    df_shots = shot_events_mouth[['end_location_y', 'end_location_z', 'outcome_name', "321_scaled", "team_id", "321", "player_name", "xg_display"]].copy()
    df_shots["team_id"] = df_shots["team_id"].astype(int)
    
    df_home = df_shots[df_shots["team_id"] == home_id]
    df_away = df_shots[df_shots["team_id"] == away_id]
    
    # Load goal image
    img_path = os.path.join(BASE_DIR, "forwards_analisis", "goal.jpg")
    goal_img_base64 = load_logo_base64(img_path) if os.path.exists(img_path) else None
   
    # Create side-by-side columns
    col1, col2 = st.columns(2)
    
    with col1:
        fig_home = create_goal_mouth_figure(df_home, home_team, '#1e40af', home_goals, total_xg_home, home_logo_base64, goal_img_base64)
        st.plotly_chart(fig_home, width='stretch')

    with col2:
        fig_away = create_goal_mouth_figure(df_away, away_team, '#dc2626', away_goals, total_xg_away, away_logo_base64, goal_img_base64)
        st.plotly_chart(fig_away, width='stretch')
    
    # ==================== FOOTER ====================
    st.divider()
    try:
        locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
    except:
        pass
    
    last_update = last_modified(os.path.join(BASE_DIR, "data_femeni", "raw"))
    st.write(f"Última actualización: {last_update} | Fuente de datos: Opta Stats Perform")