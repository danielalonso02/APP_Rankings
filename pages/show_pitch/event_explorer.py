#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Event Explorer - Detailed Event Visualization
Filter and explore all match events: Passes, Offsides, Duels, Fouls, Cards
With proper tooltips showing player name and time
"""
import streamlit as st
from utils import util
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler
from mplsoccer import Pitch
import base64
import io
from datetime import datetime
from matplotlib.patches import FancyArrowPatch
from matplotlib.colors import to_rgba
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

ruta_opta_f40 = os.path.join(BASE_DIR, "data_femeni", "raw", "f40", "f40-squad-102.xml")
ruta_opta_f42 = os.path.join(BASE_DIR, "data_femeni", "raw", "f42", "f42-903-2025-results.xml")
ruta_excel_players = os.path.join(BASE_DIR, "data_femeni", "players_relations.xlsx")
ruta_excel_matches = os.path.join(BASE_DIR, "data_femeni", "matches_relations.xlsx")

# Color scheme - Red for home, Blue for away
HOME_COLOR = '#dc2626'  # Red
AWAY_COLOR = '#1e40af'  # Blue

def draw_gradient_arrows(ax, x_start, y_start, x_end, y_end, color=HOME_COLOR, n_segments=20, alpha=0.7):
    """Draw arrows with gradient effect from start to end point"""
    base_color = to_rgba(color)
    
    for i in range(len(x_start)):
        x0, y0 = x_start.iloc[i], y_start.iloc[i]
        x1, y1 = x_end.iloc[i], y_end.iloc[i]
        
        for j in range(n_segments):
            t0 = j / n_segments
            t1 = (j + 1) / n_segments
            
            seg_x0 = x0 + t0 * (x1 - x0)
            seg_y0 = y0 + t0 * (y1 - y0)
            seg_x1 = x0 + t1 * (x1 - x0)
            seg_y1 = y0 + t1 * (y1 - y0)
            
            segment_alpha = alpha * (0.3 + 0.7 * t1)
            intensity = 0.4 + 0.6 * t1
            seg_color = (base_color[0] * intensity, 
                        base_color[1] * intensity, 
                        base_color[2] * intensity, 
                        segment_alpha)
            
            if j < n_segments - 1:
                ax.plot([seg_x0, seg_x1], [seg_y0, seg_y1], 
                       color=seg_color, linewidth=2, zorder=2)
            else:
                arrow = FancyArrowPatch((seg_x0, seg_y0), (seg_x1, seg_y1),
                                      arrowstyle='->', mutation_scale=15,
                                      linewidth=2, color=seg_color, zorder=2)
                ax.add_patch(arrow)

def parse_f27_for_network(filepath_f27):
    """Parse F27 file to get pass network data"""
    if not os.path.exists(filepath_f27):
        return None
    
    tree = ET.parse(filepath_f27)
    root = tree.getroot()
    
    pases_data = []
    
    for player in root.findall("Player"):
        passer_id = player.get("player_id")
        passer_name = player.get("player_name")
        passer_x = float(player.get("x"))
        passer_y = float(player.get("y"))
        
        # Iterate over receivers
        for pass_receiver in player.findall("Player"):
            receiver_id = pass_receiver.get("player_id")
            receiver_name = pass_receiver.get("player_name")
            passes = int(pass_receiver.text)
            
            pases_data.append({
                "player_id": int(passer_id),
                "player": passer_name,
                "x": passer_x,
                "y": passer_y,
                "receiver_id": int(receiver_id),
                "receiver": receiver_name,
                "passes": passes
            })
    
    return pd.DataFrame(pases_data)

def create_interactive_pass_network_f27(match_id, team_id, team_name, team_color=HOME_COLOR, min_passes=2):
    """
    Create interactive pass network using F27 data
    """
    # Build F27 file path
    filepath_f27 = os.path.join(BASE_DIR, "data_femeni", "raw", "f27", 
                                f"pass_matrix_903_2025_g{match_id}_t{team_id}.xml")
    
    df_passes = parse_f27_for_network(filepath_f27)
    
    if df_passes is None or len(df_passes) < 5:
        return None
    
    # Filter minimum passes
    df_passes = df_passes[df_passes['passes'] >= min_passes]
    
    if len(df_passes) == 0:
        return None
    
    # Rename existing x, y to x_from, y_from (these are passer positions from F27)
    df_passes = df_passes.rename(columns={'x': 'x_from', 'y': 'y_from'})
    
    # Get unique players and their positions
    player_positions = df_passes.groupby('player_id').agg({
        'x_from': 'mean',
        'y_from': 'mean',
        'player': 'first'
    }).reset_index()
    player_positions = player_positions.rename(columns={'x_from': 'x', 'y_from': 'y'})
    
    # Calculate total involvement
    passes_made = df_passes.groupby('player_id')['passes'].sum().reset_index(name='passes_made')
    passes_received = df_passes.groupby('receiver_id')['passes'].sum().reset_index(name='passes_received')
    passes_received.columns = ['player_id', 'passes_received']
    
    player_positions = player_positions.merge(passes_made, on='player_id', how='left')
    player_positions = player_positions.merge(passes_received, on='player_id', how='left')
    player_positions['total_involvement'] = (
        player_positions['passes_made'].fillna(0) + 
        player_positions['passes_received'].fillna(0)
    )
    
    # Scale node sizes
    min_size, max_size = 20, 50
    if player_positions['total_involvement'].max() > player_positions['total_involvement'].min():
        scaler = MinMaxScaler(feature_range=(min_size, max_size))
        player_positions['node_size'] = scaler.fit_transform(
            player_positions[['total_involvement']]
        )
    else:
        player_positions['node_size'] = (min_size + max_size) / 2
    
    # Create pitch background
    pitch = Pitch(pitch_type="opta", 
                 pitch_color='grass', 
                 line_color='white', 
                 stripe=True,
                 pad_left=5,
                 pad_right=5,
                 pad_top=2,
                 pad_bottom=2,
                 goal_type='box', 
                 goal_alpha=0.8)
    fig_pitch, ax_pitch = pitch.draw(figsize=(15, 10))
    
    buf = io.BytesIO()
    fig_pitch.savefig(buf, format='png', dpi=100, bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    pitch_img = base64.b64encode(buf.read()).decode()
    plt.close(fig_pitch)
    
    # Create Plotly figure
    fig = go.Figure()
    
    # Add pitch background
    fig.add_layout_image(
        dict(
            source=f'data:image/png;base64,{pitch_img}',
            xref="x",
            yref="y",
            x=-5,
            y=102,
            sizex=110,
            sizey=104,
            sizing="stretch",
            opacity=1,
            layer="below"
        )
    )
    
    # Merge to get receiver positions
    df_passes = df_passes.merge(
        player_positions[['player_id', 'x', 'y']], 
        left_on='receiver_id', 
        right_on='player_id',
        how='left',
        suffixes=('', '_receiver')
    )
    # Drop the duplicate player_id column from merge and rename receiver coords
    df_passes = df_passes.drop(columns=['player_id_receiver'])
    df_passes = df_passes.rename(columns={'x': 'x_to', 'y': 'y_to'})
    
    # Remove rows with missing coordinates
    df_passes = df_passes.dropna(subset=['x_from', 'y_from', 'x_to', 'y_to'])
    
    if len(df_passes) == 0:
        return None
    
    # Normalize line widths
    max_passes = df_passes['passes'].max()
    min_passes_val = df_passes['passes'].min()
    if max_passes > min_passes_val:
        df_passes['line_width'] = 1 + ((df_passes['passes'] - min_passes_val) / 
                                        (max_passes - min_passes_val)) * 6
    else:
        df_passes['line_width'] = 4
    
    # Draw edges
    for _, row in df_passes.iterrows():
        # Check bidirectional
        has_reverse = len(df_passes[
            (df_passes['player_id'] == row['receiver_id']) & 
            (df_passes['receiver_id'] == row['player_id'])
        ]) > 0
        
        if has_reverse:
            # Curved line
            x_mid = (row['x_from'] + row['x_to']) / 2
            y_mid = (row['y_from'] + row['y_to']) / 2
            
            dx = row['x_to'] - row['x_from']
            dy = row['y_to'] - row['y_from']
            length = np.sqrt(dx**2 + dy**2)
            if length > 0:
                offset_x = -dy / length * 3
                offset_y = dx / length * 3
            else:
                offset_x, offset_y = 0, 0
            
            t = np.linspace(0, 1, 30)
            curve_x = (
                (1-t)**2 * row['x_from'] + 
                2*(1-t)*t * (x_mid + offset_x) + 
                t**2 * row['x_to']
            )
            curve_y = (
                (1-t)**2 * row['y_from'] + 
                2*(1-t)*t * (y_mid + offset_y) + 
                t**2 * row['y_to']
            )
        else:
            curve_x = [row['x_from'], row['x_to']]
            curve_y = [row['y_from'], row['y_to']]
        
        fig.add_trace(go.Scatter(
            x=curve_x,
            y=curve_y,
            mode='lines',
            line=dict(color=team_color, width=row['line_width']),
            opacity=0.6,
            hoverinfo='skip',
            showlegend=False
        ))
    
    # Draw nodes
    player_positions['surname'] = player_positions['player'].apply(
        lambda x: x.split()[-1] if pd.notna(x) and isinstance(x, str) else ''
    )
    
    fig.add_trace(go.Scatter(
        x=player_positions['x'],
        y=player_positions['y'],
        mode='markers+text',
        marker=dict(
            size=player_positions['node_size'],
            color=team_color,
            line=dict(width=2, color='white')
        ),
        text=player_positions['surname'],
        textposition='middle center',
        textfont=dict(size=9, color='white', family='Arial Black'),
        customdata=player_positions[['player', 'total_involvement']],
        hovertemplate='<b>%{customdata[0]}</b><br>Total pases: %{customdata[1]:.0f}<extra></extra>',
        showlegend=False
    ))

    # --- Dummy Traces for Network Legend ---
    # Legend for Passes (Line Width)
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', 
                             line=dict(color='gray', width=1), 
                             name='Pases: Pocos (Delgada)', showlegend=True, legendgroup='Pases'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', 
                             line=dict(color='gray', width=6), 
                             name='Pases: Muchos (Gruesa)', showlegend=True, legendgroup='Pases'))
    
    # Legend for Participation (Node Size)
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', 
                             marker=dict(size=14, color='gray', line=dict(width=2, color='white')), 
                             name='Participación: Baja (Pequeño)', showlegend=True, legendgroup='Nodos'))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', 
                             marker=dict(size=40, color='gray', line=dict(width=2, color='white')), 
                             name='Participación: Alta (Grande)', showlegend=True, legendgroup='Nodos'))
    # ---------------------------------------
    
    # Add direction of attack arrow/annotation
    fig.add_annotation(
        x=50, y=103,
        text="Dirección de ataque →",
        showarrow=False,
        font=dict(size=14, color='white', family='Arial Black'),
        bgcolor='rgba(0,0,0,0.7)',
        borderpad=8
    )
    
    # Update layout
    fig.update_layout(
        xaxis=dict(range=[-5, 105], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[-2, 105], showgrid=False, zeroline=False, visible=False,
                   scaleanchor="x", scaleratio=0.68),
        height=700,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=60, b=0),
        legend=dict(title="<b>Guía de Lectura</b>", orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
                    bgcolor='rgba(255,255,255,0.8)', bordercolor='black', borderwidth=1),
        hovermode='closest'
    )
    
    return fig

def show_page():
    """Main function for pitch events visualization"""
    
    # Initialize database if needed
    if "db_initialized" not in st.session_state:
        try:
            util.create_player_db(ruta_opta_f40)
            util.calendar(ruta_opta_f42)
            st.session_state.db_initialized = True
        except Exception as e:
            st.error(f"Error al inicializar la base de datos: {e}")

    df_players = pd.read_excel(ruta_excel_players)
    df_matches = pd.read_excel(ruta_excel_matches)

    # ==================== GET MATCH FROM GLOBAL SESSION STATE ====================
    if "global_selected_match_id" not in st.session_state:
        st.error("⚠️ Por favor, selecciona un partido primero")
        return
    
    match = st.session_state.global_selected_match
    match_id = st.session_state.global_selected_match_id
    
    ruta_opta_f24 = os.path.join(BASE_DIR, "data_femeni", "raw", "f24", f"f24-903-2025-{match_id}-eventdetails.xml")

    # Parse match data
    df_events, team_names = util.parse_f24(ruta_opta_f24)
    home_team = team_names["home_team_name"].iloc[0]
    home_id = team_names["home_team_id"].iloc[0]
    away_team = team_names["away_team_name"].iloc[0]
    away_id = team_names["away_team_id"].iloc[0]

    # ==================== PAGE TITLE ====================
    st.markdown("""
        <div class='info-box'>
            <p>Filtra y visualiza eventos específicos del partido: pases, duelos, faltas y más</p>
        </div>
    """, unsafe_allow_html=True)
    
    # ==================== EVENT TYPE SELECTOR ====================
    st.markdown("### Seleccionar tipo de evento")
    col1, col2, col3 = st.columns([1.5, 1.5, 1.5])
    
    with col1:
        # Only essential event types (NO CARDS)
        event_types = {
            1: "Pases",
            2: "Fuera de juego",
            3: "Duelos",
            4: "Faltas",
        }
        
        event_name = st.selectbox(
            "Tipo de Evento",
            options=list(event_types.values()),
            key="event_type_selector"
        )
        
        # Get type_id from selected name
        type_id = [k for k, v in event_types.items() if v == event_name][0]
        
    with col2:
        teams_select = [home_team, away_team, "Ambos"]
        team = st.selectbox("Equipo", teams_select)
    with col3:
        if team == home_team:
            df_jugadoras = df_players[(df_players["team"] == home_team)]
            dict_jugadoras = dict(zip(df_jugadoras["player"], df_jugadoras["player_id"]))
            new_entry = {'Todas': 0}
            sorted_rest = dict(sorted(dict_jugadoras.items()))
            new_dict = {**new_entry, **sorted_rest}
            player = st.selectbox("Jugadora", list(new_dict.keys()))
            player_id = new_dict[player]
        elif team == away_team:
            df_jugadoras = df_players[(df_players["team"] == away_team)]
            dict_jugadoras = dict(zip(df_jugadoras["player"], df_jugadoras["player_id"]))
            new_entry = {'Todas': 0}
            sorted_rest = dict(sorted(dict_jugadoras.items()))
            new_dict = {**new_entry, **sorted_rest}
            player = st.selectbox("Jugadora", list(new_dict.keys()))
            player_id = new_dict[player]
        else:
            player_id = 0

    # ==================== FILTERS FOR PASSES ====================
    if type_id == 1:
        
        third_mapping = {
            1: ("Todo el campo", (0.0, 100.0)),
            2: ("Primer tercio (Defensivo)", (0.0, 33.33)),
            3: ("Segundo tercio (Medio)", (33.33, 66.66)),
            4: ("Último tercio (Ofensivo)", (66.66, 100.0))
        }
        
        col1, spacer, col2 = st.columns([2, 0.1, 1])  # Add a thin spacer column
        
        with col1:
            st.write("##### Análisis de Pases por Tercio")

            sub_col1, sub_col2 = st.columns([1,1])
            
            with sub_col1:
                st.write("**Inicio del pase** (puedes seleccionar múltiples):")
                start_selections = []
                start_1 = st.checkbox("1. Todo el campo", key="start_1")
                start_2 = st.checkbox("2. Primer tercio (Defensivo)", key="start_2")
                start_3 = st.checkbox("3. Segundo tercio (Medio)", key="start_3")
                start_4 = st.checkbox("4. Último tercio (Ofensivo)", key="start_4")
                
                if start_1:
                    start_selections.append(1)
                if start_2:
                    start_selections.append(2)
                if start_3:
                    start_selections.append(3)
                if start_4:
                    start_selections.append(4)
                
                if 1 in start_selections:
                    start_third = (0.0, 100.0)
                elif len(start_selections) == 0:
                    start_third = (0.0, 100.0)
                else:
                    min_val = min([third_mapping[s][1][0] for s in start_selections])
                    max_val = max([third_mapping[s][1][1] for s in start_selections])
                    start_third = (min_val, max_val)
            
            with sub_col2:
                st.write("**Final del pase** (puedes seleccionar múltiples):")
                end_selections = []
                end_1 = st.checkbox("1. Todo el campo", key="end_1")
                end_2 = st.checkbox("2. Primer tercio (Defensivo)", key="end_2")
                end_3 = st.checkbox("3. Segundo tercio (Medio)", key="end_3")
                end_4 = st.checkbox("4. Último tercio (Ofensivo)", key="end_4")
                
                if end_1:
                    end_selections.append(1)
                if end_2:
                    end_selections.append(2)
                if end_3:
                    end_selections.append(3)
                if end_4:
                    end_selections.append(4)
                
                if 1 in end_selections:
                    end_third = (0.0, 100.0)
                elif len(end_selections) == 0:
                    end_third = (0.0, 100.0)
                else:
                    min_val = min([third_mapping[e][1][0] for e in end_selections])
                    max_val = max([third_mapping[e][1][1] for e in end_selections])
                    end_third = (min_val, max_val)

        with spacer:
            # Create vertical divider
            st.markdown("""
                <div style="
                    border-left: 2px solid #e0e0e0;
                    height: 280px;
                    margin: 0 auto;
                "></div>
            """, unsafe_allow_html=True)

        with col2:
            st.write("##### Banda:")
            st.markdown("""
                <div class='info-box'>
                    <p>Filtrar la banda izquierda o derecha del campo con respecto a la dirección de ataque</p>
                </div>
            """, unsafe_allow_html=True)
            sideline_left = st.checkbox('Banda izquierda')
            sideline_right = st.checkbox('Banda derecha')
            
            if sideline_right and sideline_left:
                start_sideline = "Both"
            elif sideline_right:
                start_sideline = "Right"
            elif sideline_left:
                start_sideline = "Left"
            else:
                start_sideline = "None"
        
        st.write("##### Filtro de Tiempo")
        st.markdown("""
                <div class='info-box'>
                    <p>Selecciona el rango de minutos para cada tiempo incluye tiempo de descuento</p>
                </div>
            """, unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("**Primer Tiempo (0-50 min)**")
            first_half_range = st.slider(
                "Minutos del primer tiempo",
                min_value=0.0,
                max_value=50.0,
                value=(0.0, 50.0),
                step=1.0,
                key="first_half"
            )
            
        with col2:
            st.write("**Segundo Tiempo (45-100 min)**")
            second_half_range = st.slider(
                "Minutos del segundo tiempo",
                min_value=45.0,
                max_value=100.0,
                value=(45.0, 100.0),
                step=1.0,
                key="second_half"
            )

    else:
        # For other events
        st.write("#### Análisis por Tercio")
        
        third_mapping = {
            1: ("Todo el campo", (0.0, 100.0)),
            2: ("Primer tercio (Defensivo)", (0.0, 33.33)),
            3: ("Segundo tercio (Medio)", (33.33, 66.66)),
            4: ("Último tercio (Ofensivo)", (66.66, 100.0))
        }
        
        st.write("**Ubicación del evento** (puedes seleccionar múltiples):")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            third_1 = st.checkbox("1. Todo el campo", key="third_1_other")
        with col2:
            third_2 = st.checkbox("2. Primer tercio", key="third_2_other")
        with col3:
            third_3 = st.checkbox("3. Segundo tercio", key="third_3_other")
        with col4:
            third_4 = st.checkbox("4. Último tercio", key="third_4_other")
        
        third_selections = []
        if third_1:
            third_selections.append(1)
        if third_2:
            third_selections.append(2)
        if third_3:
            third_selections.append(3)
        if third_4:
            third_selections.append(4)
        
        if 1 in third_selections:
            start_third = (0.0, 100.0)
        elif len(third_selections) == 0:
            start_third = (0.0, 100.0)
        else:
            min_val = min([third_mapping[s][1][0] for s in third_selections])
            max_val = max([third_mapping[s][1][1] for s in third_selections])
            start_third = (min_val, max_val)
        
        st.write("#### Bandas")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write('Banda:')
            sideline_left = st.checkbox('Banda izquierda', key="sideline_left_other")
            sideline_right = st.checkbox('Banda derecha', key="sideline_right_other")
            
            if sideline_right and sideline_left:
                start_sideline = "Both"
            elif sideline_right:
                start_sideline = "Right"
            elif sideline_left:
                start_sideline = "Left"
            else:
                start_sideline = "None"
        
        st.write("##### Filtro de Tiempo")
        st.write("Selecciona el rango de minutos para cada tiempo (incluye tiempo de descuento)")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("**Primer Tiempo (0-50 min)**")
            first_half_range = st.slider(
                "Minutos del primer tiempo",
                min_value=0.0,
                max_value=50.0,
                value=(0.0, 50.0),
                step=1.0,
                key="first_half_other"
            )
            
        with col2:
            st.write("**Segundo Tiempo (45-100 min)**")
            second_half_range = st.slider(
                "Minutos del segundo tiempo",
                min_value=45.0,
                max_value=100.0,
                value=(45.0, 100.0),
                step=1.0,
                key="second_half_other"
            )

    # Get specific event data
    df_specific_event = df_events[df_events["type_id"] == type_id]
    
    if "time_minutes" not in df_specific_event.columns:
        df_specific_event["time_minutes"] = df_specific_event["min"] + df_specific_event["sec"] / 60

    # ==================== LOAD TEAM LOGOS ====================
    logo_dir = os.path.join(BASE_DIR, "assets", "logos_table")
    
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
    
    home_logo_path = get_team_logo_path(home_team, logo_dir)
    away_logo_path = get_team_logo_path(away_team, logo_dir)
    
    # Convert logos to base64
    home_logo_base64 = None
    away_logo_base64 = None
    
    if home_logo_path and os.path.exists(home_logo_path):
        try:
            with open(home_logo_path, "rb") as img_file:
                home_logo_base64 = base64.b64encode(img_file.read()).decode()
        except:
            pass
    
    if away_logo_path and os.path.exists(away_logo_path):
        try:
            with open(away_logo_path, "rb") as img_file:
                away_logo_base64 = base64.b64encode(img_file.read()).decode()
        except:
            pass
    
    # ==================== TEAM NAMES DISPLAY ====================
    if team == home_team:
        if home_logo_base64:
            st.markdown(f"""
                <div style='text-align: left;'>
                    <img src='data:image/png;base64,{home_logo_base64}' width='60' style='vertical-align: middle; margin-right: 15px;'>
                    <span style='color: {HOME_COLOR}; font-size: 1.8rem; font-weight: bold; vertical-align: middle;'>{home_team}</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"<h3 style='text-align: left; color: {HOME_COLOR};'>{home_team}</h3>", unsafe_allow_html=True)
    elif team == away_team:
        if away_logo_base64:
            st.markdown(f"""
                <div style='text-align: right;'>
                    <span style='color: {AWAY_COLOR}; font-size: 1.8rem; font-weight: bold; vertical-align: middle;'>{away_team}</span>
                    <img src='data:image/png;base64,{away_logo_base64}' width='60' style='vertical-align: middle; margin-left: 15px;'>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"<h3 style='text-align: right; color: {AWAY_COLOR};'>{away_team}</h3>", unsafe_allow_html=True)
    else:
        col_left, col_right = st.columns(2)
        with col_left:
            if home_logo_base64:
                st.markdown(f"""
                    <div style='text-align: left;'>
                        <img src='data:image/png;base64,{home_logo_base64}' width='60' style='vertical-align: middle; margin-right: 15px;'>
                        <span style='color: {HOME_COLOR}; font-size: 1.8rem; font-weight: bold; vertical-align: middle;'>{home_team}</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"<h3 style='text-align: left; color: {HOME_COLOR};'>{home_team}</h3>", unsafe_allow_html=True)
        with col_right:
            if away_logo_base64:
                st.markdown(f"""
                    <div style='text-align: right;'>
                        <span style='color: {AWAY_COLOR}; font-size: 1.8rem; font-weight: bold; vertical-align: middle;'>{away_team}</span>
                        <img src='data:image/png;base64,{away_logo_base64}' width='60' style='vertical-align: middle; margin-left: 15px;'>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"<h3 style='text-align: right; color: {AWAY_COLOR};'>{away_team}</h3>", unsafe_allow_html=True)

    # ==================== PASES VISUALIZATION ====================
    if type_id == 1:
        df_specific_event[["end_x", "end_y"]] = df_specific_event["qualifiers"].apply(util.extract_end_coordinates)
        df_specific_event = util.filter_actions_passes(df_specific_event, start_third, end_third, start_sideline)
        
        # Apply time filter
        first_half_mask = (df_specific_event["time_minutes"] >= first_half_range[0]) & (df_specific_event["time_minutes"] <= first_half_range[1])
        second_half_mask = (df_specific_event["time_minutes"] >= second_half_range[0]) & (df_specific_event["time_minutes"] <= second_half_range[1])
        df_specific_event = df_specific_event[first_half_mask | second_half_mask]
        
        if team == home_team:
            df_specific_event = df_specific_event[df_specific_event["team_name"] == home_team]
            
            if player_id != 0:
                df_specific_event = df_specific_event[df_specific_event["player_id"] == player_id]
            
            # PASS MAP
            st.markdown("#### Mapa de Pases")
            pitch = Pitch(pitch_type="opta", 
                         pitch_color='grass', 
                         line_color='white', 
                         stripe=True,
                         pad_top=10,
                         pad_bottom=2,
                         goal_type='box', 
                         goal_alpha=0.8)
            fig, ax = pitch.draw(figsize=(12, 10))
            
            ax.text(50, 105, "Dirección de ataque →", 
                   ha='center', va='bottom', fontsize=14, fontweight='bold', color='white',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.7))
            
            draw_gradient_arrows(ax, df_specific_event.x, df_specific_event.y,
                               df_specific_event.end_x, df_specific_event.end_y,
                               color=HOME_COLOR, n_segments=20, alpha=0.7)

            st.pyplot(fig, width='stretch')

            # PASS NETWORK
            if player_id == 0:
                st.markdown("#### Red de Pases")
                
                # Info box explaining filters don't apply
                st.markdown("""
                    <div class='info-box'>
                        <p>Nota: Los filtros anteriores (tercios, bandas, tiempo) no afectan la red de pases. La red muestra todas las conexiones de pases del partido completo.</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Display team logo and name
                if home_logo_base64:
                    st.markdown(f"""
                        <div style='text-align: center; margin-bottom: 20px;'>
                            <img src='data:image/png;base64,{home_logo_base64}' width='80' style='display: block; margin: 0 auto 10px auto;'>
                            <span style='color: {HOME_COLOR}; font-size: 1.5rem; font-weight: bold;'>{home_team}</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"<h4 style='text-align: center; color: {HOME_COLOR};'>{home_team}</h4>", unsafe_allow_html=True)
                
                network_fig = create_interactive_pass_network_f27(
                    match_id, home_id, home_team, HOME_COLOR, min_passes=2
                )
                if network_fig:
                    st.plotly_chart(network_fig, width='stretch')
                else:
                    st.info("No hay suficientes conexiones de pases para crear una red")
            
        elif team == away_team:
            df_specific_event = df_specific_event[df_specific_event["team_name"] == away_team]
            df_specific_event["x"] = 100 - df_specific_event["x"]
            df_specific_event["y"] = 100 - df_specific_event["y"]
            df_specific_event["end_x"] = 100 - df_specific_event["end_x"]
            df_specific_event["end_y"] = 100 - df_specific_event["end_y"]
            
            if player_id != 0:
                df_specific_event = df_specific_event[df_specific_event["player_id"] == player_id]
            
            # PASS MAP
            st.markdown("#### Mapa de Pases")
            pitch = Pitch(pitch_type="opta", 
                         pitch_color='grass', 
                         line_color='white', 
                         stripe=True,
                         pad_top=10,
                         pad_bottom=2,
                         goal_type='box', 
                         goal_alpha=0.8)
            fig, ax = pitch.draw(figsize=(12, 10))
            
            ax.text(50, 105, "← Dirección de ataque", 
                   ha='center', va='bottom', fontsize=14, fontweight='bold', color='white',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.7))
            
            draw_gradient_arrows(ax, df_specific_event.x, df_specific_event.y,
                               df_specific_event.end_x, df_specific_event.end_y,
                               color=AWAY_COLOR, n_segments=20, alpha=0.7)

            st.pyplot(fig, width='stretch')

            # PASS NETWORK
            if player_id == 0:
                st.markdown("#### Red de Pases")
                
                # Info box explaining filters don't apply
                st.markdown("""
                    <div class='info-box'>
                        <p>Nota: Los filtros anteriores (tercios, bandas, tiempo) no afectan la red de pases. La red muestra todas las conexiones de pases del partido completo.</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Display team logo and name
                if away_logo_base64:
                    st.markdown(f"""
                        <div style='text-align: center; margin-bottom: 20px;'>
                            <img src='data:image/png;base64,{away_logo_base64}' width='80' style='display: block; margin: 0 auto 10px auto;'>
                            <span style='color: {AWAY_COLOR}; font-size: 1.5rem; font-weight: bold;'>{away_team}</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"<h4 style='text-align: center; color: {AWAY_COLOR};'>{away_team}</h4>", unsafe_allow_html=True)
                
                network_fig = create_interactive_pass_network_f27(
                    match_id, away_id, away_team, AWAY_COLOR, min_passes=2
                )
                if network_fig:
                    st.plotly_chart(network_fig, width='stretch')
                else:
                    st.info("No hay suficientes conexiones de pases para crear una red")
            
        else:
            df_home = df_specific_event[df_specific_event["team_name"] == home_team]
            df_away = df_specific_event[df_specific_event["team_name"] == away_team]
            df_away["x"] = 100 - df_away["x"]
            df_away["y"] = 100 - df_away["y"]
            df_away["end_x"] = 100 - df_away["end_x"]
            df_away["end_y"] = 100 - df_away["end_y"]
            
            # PASS MAP
            st.markdown("#### Mapa de Pases")
            pitch = Pitch(pitch_type="opta", 
                         pitch_color='grass', 
                         line_color='white', 
                         stripe=True,
                         pad_top=10,
                         pad_bottom=2,
                         goal_type='box', 
                         goal_alpha=0.8)
            fig, ax = pitch.draw(figsize=(12, 10))
            
            draw_gradient_arrows(ax, df_home.x, df_home.y,
                               df_home.end_x, df_home.end_y,
                               color=HOME_COLOR, n_segments=20, alpha=0.7)
            draw_gradient_arrows(ax, df_away.x, df_away.y,
                               df_away.end_x, df_away.end_y,
                               color=AWAY_COLOR, n_segments=20, alpha=0.7)
            st.pyplot(fig, width='stretch')
            
            # PASS NETWORKS
            st.markdown("#### Redes de Pases")
            
            # Info box explaining filters don't apply
            st.markdown("""
                <div class='info-box'>
                    <p>Nota: Los filtros anteriores (tercios, bandas, tiempo) no afectan las redes de pases. Las redes muestran todas las conexiones de pases del partido completo.</p>
                </div>
            """, unsafe_allow_html=True)
            
            col_home, col_away = st.columns(2)
            
            with col_home:
                # Display home team logo and name
                if home_logo_base64:
                    st.markdown(f"""
                        <div style='text-align: center; margin-bottom: 20px;'>
                            <img src='data:image/png;base64,{home_logo_base64}' width='80' style='display: block; margin: 0 auto 10px auto;'>
                            <span style='color: {HOME_COLOR}; font-size: 1.5rem; font-weight: bold;'>{home_team}</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"<h5 style='text-align: center; color: {HOME_COLOR};'>{home_team}</h5>", unsafe_allow_html=True)
                
                network_fig_home = create_interactive_pass_network_f27(
                    match_id, home_id, home_team, HOME_COLOR, min_passes=2
                )
                if network_fig_home:
                    st.plotly_chart(network_fig_home, width='stretch')
                else:
                    st.info("No hay suficientes conexiones")
            
            with col_away:
                # Display away team logo and name
                if away_logo_base64:
                    st.markdown(f"""
                        <div style='text-align: center; margin-bottom: 20px;'>
                            <img src='data:image/png;base64,{away_logo_base64}' width='80' style='display: block; margin: 0 auto 10px auto;'>
                            <span style='color: {AWAY_COLOR}; font-size: 1.5rem; font-weight: bold;'>{away_team}</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"<h5 style='text-align: center; color: {AWAY_COLOR};'>{away_team}</h5>", unsafe_allow_html=True)
                
                network_fig_away = create_interactive_pass_network_f27(
                    match_id, away_id, away_team, AWAY_COLOR, min_passes=2
                )
                if network_fig_away:
                    st.plotly_chart(network_fig_away, width='stretch')
                else:
                    st.info("No hay suficientes conexiones")

    # ==================== OTHER EVENTS VISUALIZATION ====================
    else:
        adding = pd.DataFrame()
        if start_sideline != "None":
            adding = util.filter_bands(df_specific_event, start_sideline)
            
        df_specific_event = util.filter_actions(df_specific_event, start_third)
        df_specific_event = pd.concat([df_specific_event, adding], ignore_index=True)
        
        # Apply time filter
        first_half_mask = (df_specific_event["time_minutes"] >= first_half_range[0]) & (df_specific_event["time_minutes"] <= first_half_range[1])
        second_half_mask = (df_specific_event["time_minutes"] >= second_half_range[0]) & (df_specific_event["time_minutes"] <= second_half_range[1])
        df_specific_event = df_specific_event[first_half_mask | second_half_mask]
       
        # Get player names
        df_players_info = df_players[["player_id", "player"]].drop_duplicates()
        df_specific_event = df_specific_event.merge(df_players_info, on="player_id", how="left")
        
        # Format time for display
        df_specific_event["time_display"] = df_specific_event["time_minutes"].apply(
            lambda x: f"{int(x)}:{int((x % 1) * 60):02d}"
        )
        
        if team == home_team:
            df_specific_event = df_specific_event[df_specific_event["team_name"] == home_team]
            if player_id != 0:
                df_specific_event = df_specific_event[df_specific_event["player_id"] == player_id]
            
            pitch = Pitch(pitch_type="opta", 
                         pitch_color='grass', 
                         line_color='white', 
                         stripe=True,
                         pad_left=5,
                         pad_right=5,
                         pad_top=2,
                         pad_bottom=2,
                         goal_type='box', 
                         goal_alpha=0.8)
            fig_pitch, ax_pitch = pitch.draw(figsize=(15, 10))
            
            buf = io.BytesIO()
            fig_pitch.savefig(buf, format='png', dpi=100, bbox_inches='tight', pad_inches=0)
            buf.seek(0)
            pitch_img = base64.b64encode(buf.read()).decode()
            plt.close(fig_pitch)
            
            fig = go.Figure()
            
            # Standard tooltip for all events
            fig.add_trace(go.Scatter(
                x=df_specific_event["x"],
                y=df_specific_event["y"],
                mode='markers',
                marker=dict(
                    size=14,
                    color=HOME_COLOR,
                    line=dict(width=2, color='white')
                ),
                customdata=df_specific_event[['player', 'time_display']],
                hovertemplate='<b>%{customdata[0]}</b><br>Tiempo: %{customdata[1]}<extra></extra>',
                name=home_team
            ))
            
            fig.add_layout_image(
                dict(
                    source=f'data:image/png;base64,{pitch_img}',
                    xref="x",
                    yref="y",
                    x=-5,
                    y=102,
                    sizex=110,
                    sizey=104,
                    sizing="stretch",
                    opacity=1,
                    layer="below"
                )
            )
            
            fig.add_annotation(
                x=50, y=100,
                text="Dirección de ataque →",
                showarrow=False,
                font=dict(size=14, color='white', family='Arial Black'),
                bgcolor='rgba(0,0,0,0.7)',
                borderpad=8
            )
            
            fig.update_layout(
                xaxis=dict(range=[-5, 105], showgrid=False, zeroline=False, visible=False),
                yaxis=dict(range=[-2, 102], showgrid=False, zeroline=False, visible=False,
                           scaleanchor="x", scaleratio=0.68),
                height=700,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                margin=dict(l=0, r=0, t=0, b=0),
                hovermode='closest'
            )

            st.plotly_chart(fig, width='stretch')

        elif team == away_team:
            df_specific_event = df_specific_event[df_specific_event["team_name"] == away_team]
            df_specific_event["x"] = 100 - df_specific_event["x"]
            df_specific_event["y"] = 100 - df_specific_event["y"]
            if player_id != 0:
                df_specific_event = df_specific_event[df_specific_event["player_id"] == player_id]
            
            pitch = Pitch(pitch_type="opta", 
                         pitch_color='grass', 
                         line_color='white', 
                         stripe=True,
                         pad_left=5,
                         pad_right=5,
                         pad_top=2,
                         pad_bottom=2,
                         goal_type='box', 
                         goal_alpha=0.8)
            fig_pitch, ax_pitch = pitch.draw(figsize=(15, 10))
            
            buf = io.BytesIO()
            fig_pitch.savefig(buf, format='png', dpi=100, bbox_inches='tight', pad_inches=0)
            buf.seek(0)
            pitch_img = base64.b64encode(buf.read()).decode()
            plt.close(fig_pitch)
            
            fig = go.Figure()
            
            # Standard tooltip for all events
            fig.add_trace(go.Scatter(
                x=df_specific_event["x"],
                y=df_specific_event["y"],
                mode='markers',
                marker=dict(
                    size=14,
                    color=AWAY_COLOR,
                    line=dict(width=2, color='white')
                ),
                customdata=df_specific_event[['player', 'time_display']],
                hovertemplate='<b>%{customdata[0]}</b><br>Tiempo: %{customdata[1]}<extra></extra>',
                name=away_team
            ))
            
            fig.add_layout_image(
                dict(
                    source=f'data:image/png;base64,{pitch_img}',
                    xref="x",
                    yref="y",
                    x=-5,
                    y=102,
                    sizex=110,
                    sizey=104,
                    sizing="stretch",
                    opacity=1,
                    layer="below"
                )
            )
            
            fig.add_annotation(
                x=50, y=100,
                text="← Dirección de ataque",
                showarrow=False,
                font=dict(size=14, color='white', family='Arial Black'),
                bgcolor='rgba(0,0,0,0.7)',
                borderpad=8
            )
            
            fig.update_layout(
                xaxis=dict(range=[-5, 105], showgrid=False, zeroline=False, visible=False),
                yaxis=dict(range=[-2, 102], showgrid=False, zeroline=False, visible=False,
                           scaleanchor="x", scaleratio=0.68),
                height=700,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                margin=dict(l=0, r=0, t=0, b=0),
                hovermode='closest'
            )

            st.plotly_chart(fig, width='stretch')

        else:
            df_home = df_specific_event[df_specific_event["team_name"] == home_team]
            df_away = df_specific_event[df_specific_event["team_name"] == away_team]
            
            pitch = Pitch(pitch_type="opta", 
                         pitch_color='grass', 
                         line_color='white', 
                         stripe=True,
                         pad_left=5,
                         pad_right=5,
                         pad_top=2,
                         pad_bottom=2,
                         goal_type='box', 
                         goal_alpha=0.8)
            fig_pitch, ax_pitch = pitch.draw(figsize=(15, 10))
            
            buf = io.BytesIO()
            fig_pitch.savefig(buf, format='png', dpi=100, bbox_inches='tight', pad_inches=0)
            buf.seek(0)
            pitch_img = base64.b64encode(buf.read()).decode()
            plt.close(fig_pitch)
            
            fig = go.Figure()
            
            # Standard tooltips for both teams
            fig.add_trace(go.Scatter(
                x=df_home["x"],
                y=df_home["y"],
                mode='markers',
                marker=dict(
                    size=14,
                    color=HOME_COLOR,
                    line=dict(width=2, color='white')
                ),
                customdata=df_home[['player', 'time_display']],
                hovertemplate='<b>' + home_team + '</b><br>%{customdata[0]}<br>Tiempo: %{customdata[1]}<extra></extra>',
                name=home_team
            ))
            
            fig.add_trace(go.Scatter(
                x=df_away["x"],
                y=df_away["y"],
                mode='markers',
                marker=dict(
                    size=14,
                    color=AWAY_COLOR,
                    line=dict(width=2, color='white')
                ),
                customdata=df_away[['player', 'time_display']],
                hovertemplate='<b>' + away_team + '</b><br>%{customdata[0]}<br>Tiempo: %{customdata[1]}<extra></extra>',
                name=away_team
            ))
            
            fig.add_layout_image(
                dict(
                    source=f'data:image/png;base64,{pitch_img}',
                    xref="x",
                    yref="y",
                    x=-5,
                    y=102,
                    sizex=110,
                    sizey=104,
                    sizing="stretch",
                    opacity=1,
                    layer="below"
                )
            )
            
            fig.update_layout(
                xaxis=dict(range=[-5, 105], showgrid=False, zeroline=False, visible=False),
                yaxis=dict(range=[-2, 102], showgrid=False, zeroline=False, visible=False,
                           scaleanchor="x", scaleratio=0.68),
                height=700,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=1.05,
                    xanchor="center",
                    x=0.5,
                    bgcolor='rgba(255,255,255,0.9)',
                    bordercolor='black',
                    borderwidth=1
                ),
                margin=dict(l=0, r=0, t=40, b=0),
                hovermode='closest'
            )

            st.plotly_chart(fig, width='stretch')
    
    # ==================== FOOTER ====================
    st.divider()
    import locale
    try:
        locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
    except:
        pass

    def last_modified(folder_path):
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

    last_update = last_modified(os.path.join(BASE_DIR, "data_femeni", "raw"))
    st.write(f"Última actualización: {last_update} | Fuente de datos: Opta Stats Perform")