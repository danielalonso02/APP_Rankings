#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 21 09:59:43 2025

@author: julieta
@collaborator: rishiraj (multi-language support and UI improvements)
"""

# ESTE ES EL CÓDIGO PARA LA PAGINA INICIAL DE LA APP

import base64
import os

import streamlit as st
import pandas as pd

from utils import login
from utils.styles import inject_home_css, feature_card, section_header, metric_card
from translations import get_text


def get_image_base64(image_path):
    """Convert image file to base64 string for HTML embedding."""
    try:
        if not os.path.exists(image_path):
            st.sidebar.error(f"Image not found: {image_path}")
            return ""

        with open(image_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()

        ext = os.path.splitext(image_path)[1].lower()
        if ext in ['.jpg', '.jpeg']:
            mime_type = 'image/jpeg'
        else:
            mime_type = 'image/png'

        return f"data:{mime_type};base64,{encoded}"

    except Exception as e:
        st.sidebar.error(f"Error loading {image_path}: {e}")
        return ""


# Page configuration
st.set_page_config(
    page_title="Liga F Analytics",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- NUEVO: Ocultar menú nativo de la carpeta pages ---
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

# Inject shared CSS (sidebar + cards + nav cards + metrics)
inject_home_css()

# Execute login with persistent authentication (includes sidebar with logo)
login.generarLogin()

# ==================== HEADER SECTION ====================
st.markdown("<br>", unsafe_allow_html=True)

st.markdown(f"""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1 style='color: #1e3a8a; margin-bottom: 0.5rem;'>{get_text('welcome_title')}</h1>
        <p style='color: #64748b; font-size: 1.2rem; margin-top: 0;'>{get_text('tagline')}</p>
    </div>
""", unsafe_allow_html=True)

st.divider()

# ==================== MAIN CONTENT SECTION ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
weekly_table_path = os.path.join(BASE_DIR, "weekly_table", "weekly_table.xlsx")

table_df = pd.read_excel(weekly_table_path)
table_df["team_position"] = table_df.index + 1


def fix_logo_path(path):
    """Fix logo path to point to correct directory."""
    filename = os.path.basename(path)
    return os.path.join(BASE_DIR, "assets", "logos_table", filename)


table_df["logos_path"] = table_df["logos_path"].apply(fix_logo_path)

def _team_cell(logo_path, name):
    b64 = get_image_base64(logo_path)
    if b64:
        return f'<img src="{b64}" width="35" height="35" style="object-fit: contain; vertical-align: middle; margin-right: 10px;"> <span style="vertical-align: middle;">{name}</span>'
    return name

df_display = pd.DataFrame({
    get_text('table_pos'): table_df["team_position"],
    get_text('table_team'): [
        _team_cell(logo, name)
        for logo, name in zip(table_df["logos_path"], table_df["team_name"])
    ],
    get_text('table_points'): table_df["team_score"]
})


def highlight_positions(pos):
    if pos in df_display[get_text('table_pos')].iloc[-2:].values:
        return 'background-color: #dc2626; color: white; font-weight: bold; text-align:center'
    elif pos == df_display[get_text('table_pos')].iloc[0]:
        return 'background-color: #16a34a; color: white; font-weight: bold; text-align:center'
    elif pos in df_display[get_text('table_pos')].iloc[1:3].values:
        return 'background-color: #86efac; color: black; font-weight: bold; text-align:center'
    else:
        return 'background-color: white; color: black; font-weight: bold; text-align:center'


styled_df = (df_display.style
             .map(highlight_positions, subset=[get_text('table_pos')])
             .set_properties(**{'text-align': 'left'}, subset=[get_text('table_team'), get_text('table_points')])
             .set_table_styles([
                 {'selector': 'th', 'props': [('text-align', 'center'), ('font-weight', 'bold'), ('background-color', '#f1f5f9')]},
                 {'selector': 'td', 'props': [('vertical-align', 'middle'), ('padding', '8px')]}
             ])
             .hide(axis='index'))

col_table, col_spacer, col_text = st.columns([1.3, 0.2, 2])

with col_table:
    st.markdown(f"### {get_text('current_season_table')}")
    st.write(styled_df.to_html(escape=False), unsafe_allow_html=True)

with col_text:
    st.markdown(f"### {get_text('welcome_header')}")
    st.markdown(get_text('mission_statement'))

    st.markdown("<br>", unsafe_allow_html=True)
    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        metric_card("10+", get_text('analysis_tools'))
    with metric_col2:
        metric_card("16", get_text('teams_tracked'))
    with metric_col3:
        metric_card("24/25", get_text('current_season'))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='text-align: center; margin-top: 2rem;'>
            <p style='color: #64748b; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;
                      letter-spacing: 1px; margin-bottom: 1rem;'>
                {get_text('built_by')}
            </p>
        </div>
    """, unsafe_allow_html=True)

    logo_col1, logo_col2, logo_col3 = st.columns(3)
    with logo_col1:
        st.image("assets/Logos/Redes_Logo.png", width="stretch")
    with logo_col2:
        st.image("assets/Logos/URJC_Logo.png", width="stretch")
    with logo_col3:
        st.image("assets/Logos/LigaF_Logo.png", width="stretch")

st.markdown("<br><br>", unsafe_allow_html=True)

# ==================== PLATFORM CAPABILITIES SECTION ====================
section_header(get_text('platform_capabilities'))

tab1, tab2, tab3, tab4 = st.tabs([
    get_text('tab_player_analysis'),
    get_text('tab_team_analysis'),
    get_text('tab_match_analysis'),
    get_text('tab_specialized')
])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        feature_card(get_text('feature_individual_reports_title'), get_text('feature_individual_reports_desc'))
        feature_card(get_text('feature_comparative_reports_title'), get_text('feature_comparative_reports_desc'))
    with col2:
        feature_card(get_text('feature_stats_visualizer_title'), get_text('feature_stats_visualizer_desc'))
        feature_card(get_text('feature_player_visualizer_title'), get_text('feature_player_visualizer_desc'))

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        feature_card(get_text('feature_team_visualizer_title'), get_text('feature_team_visualizer_desc'))
    with col2:
        feature_card(get_text('feature_team_report_title'), get_text('feature_team_report_desc'))

with tab3:
    feature_card(get_text('feature_match_visualizer_title'), get_text('feature_match_visualizer_desc'))

with tab4:
    col1, col2 = st.columns(2)
    with col1:
        feature_card(get_text('feature_goalkeeper_title'), get_text('feature_goalkeeper_desc'))
    with col2:
        feature_card(get_text('feature_forward_title'), get_text('feature_forward_desc'))

st.markdown("<br>", unsafe_allow_html=True)

# ==================== NAVIGATION SECTION ====================
section_header(get_text('get_started'))
st.markdown(f"<p style='color: #64748b; font-size: 1.1rem; margin-bottom: 2rem;'>{get_text('get_started_desc')}</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
        <a href="dashboard" target="_self" style="text-decoration: none;">
            <div class='nav-card' style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);'>
                <div class='nav-card-content'>
                    <div class='nav-card-icon'>👤</div>
                    <div class='nav-card-title'>{get_text('nav_scouting_title')}</div>
                    <div class='nav-card-description'>{get_text('nav_scouting_desc')}</div>
                </div>
                <div class='nav-card-button'>
                    🔍 {get_text('nav_scouting_button')}
                </div>
            </div>
        </a>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <a href="team_page" target="_self" style="text-decoration: none;">
            <div class='nav-card' style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);'>
                <div class='nav-card-content'>
                    <div class='nav-card-icon'>🆚</div>
                    <div class='nav-card-title'>{get_text('nav_opponent_title')}</div>
                    <div class='nav-card-description'>{get_text('nav_opponent_desc')}</div>
                </div>
                <div class='nav-card-button'>
                    📊 {get_text('nav_opponent_button')}
                </div>
            </div>
        </a>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <a href="team_graphs_page" target="_self" style="text-decoration: none;">
            <div class='nav-card' style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);'>
                <div class='nav-card-content'>
                    <div class='nav-card-icon'>⚽</div>
                    <div class='nav-card-title'>{get_text('nav_team_viz_title')}</div>
                    <div class='nav-card-description'>{get_text('nav_team_viz_desc')}</div>
                </div>
                <div class='nav-card-button'>
                    📉 {get_text('nav_team_viz_button')}
                </div>
            </div>
        </a>
    """, unsafe_allow_html=True)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
st.markdown(f"""
    <div style='text-align: center; color: #94a3b8; font-size: 0.9rem;'>
        <p>{get_text('footer_text')}</p>
    </div>
""", unsafe_allow_html=True)