#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Página inicial de la app de Rankings y Reports de jugadoras.
"""

import os
import streamlit as st

from utils import login
from utils.styles import inject_home_css

# ==================== CONFIGURACIÓN ====================
st.set_page_config(
    page_title="Scouting Analytics",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ocultar menú nativo de la carpeta pages
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none; }
    </style>
""", unsafe_allow_html=True)

inject_home_css()
login.generarLogin()

if "usuario" not in st.session_state:
    st.stop()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==================== LOGOS ====================
st.markdown("<br>", unsafe_allow_html=True)
_, logo_col1, logo_col2, _ = st.columns([2, 1, 1, 2])
with logo_col1:
    st.image(os.path.join(BASE_DIR, "assets", "Logos", "Redes_Logo.png"), use_container_width=True)
with logo_col2:
    st.image(os.path.join(BASE_DIR, "assets", "Logos", "URJC_Logo.png"), use_container_width=True)

# ==================== HEADER ====================
st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
    <div style='text-align: center; margin-bottom: 2.5rem;'>
        <h1 style='color: #1e3a8a; margin-bottom: 0.5rem;'>⚽ Scouting Analytics</h1>
        <p style='color: #64748b; font-size: 1.2rem; margin-top: 0;'>
            Plataforma de rankings y análisis de jugadores de fútbol
        </p>
    </div>
""", unsafe_allow_html=True)

st.divider()

# ==================== DESCRIPCIÓN ====================
_, col_center, _ = st.columns([1, 2, 1])

with col_center:
    st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(59,130,246,0.05) 0%, rgba(118,75,162,0.05) 100%);
                    border-left: 4px solid #3b82f6; border-radius: 8px;
                    padding: 1.8rem 2rem; margin-bottom: 2rem;'>
            <h3 style='color: #1e3a8a; margin-top: 0;'>¿Qué puedes hacer aquí?</h3>
            <p style='color: #475569; font-size: 1rem; line-height: 1.8; margin: 0;'>
                Esta herramienta está diseñada para el análisis de rendimiento de jugadores
                en distintas ligas y competiciones. Desde aquí puedes:
            </p>
            <ul style='color: #475569; font-size: 1rem; line-height: 2; margin-top: 0.8rem;'>
                <li>📊 <b>Rankings por liga</b> — Genera clasificaciones de rendimiento por categoría 
                (ofensivo, defensivo, técnico, físico y global) para cada competición de forma independiente.</li>
                <li>📄 <b>Reports de jugadores</b> — Crea informes detallados de los jugadores que te interesen, 
                con sus métricas, percentiles y visualizaciones comparativas.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

# ==================== FOOTER ====================
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
st.markdown("""
    <div style='text-align: center; color: #94a3b8; font-size: 0.85rem;'>
        <p>Scouting Analytics · Temporada 24/25</p>
    </div>
""", unsafe_allow_html=True)
