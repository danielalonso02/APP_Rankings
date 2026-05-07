#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 21 09:59:43 2025

@author: julieta
"""

#ESTE ES EL CÓDIGO PARA LA PAGINA INICIAL DE LA APP

import streamlit as st
import pandas as pd
import numpy as np
#from matplotlib import pyplot as plt
#from seaborn import sns
#import pymysql
#pymysql.install_as_MySQLdb()
from utils import login
from PIL import Image

st.set_page_config(
    page_title="Web",
    page_icon=":material/sports_and_outdoors:", #el icono
    layout="wide",
    initial_sidebar_state="expanded" ### esto es para que de normal el sidebar este expandido
    )

# Ejecutar login con autenticación persistente
login.generarLogin()

image2=Image.open("assets/Logos/Redes_Logo.png")
scale = 0.32  # 90% of original size
# Compute new size
new_width = int(image2.width * scale)
new_height = int(image2.height * scale)

# Resize with high-quality resampling
image2 = image2.resize((new_width, new_height), Image.LANCZOS)

col1, col2,col3, col4,col5 = st.columns([2, 1.5,1.5,1.5, 2])
with col2:
    st.image("assets/Logos/Redes_Logo.png")
with col3:
    st.image("assets/Logos/URJC_Logo.png")
with col4:
    st.image("assets/Logos/LigaF_Logo.png")
    

st.divider() 
st.markdown("# ⚽ Bienvenidos a la central de análisis de Liga F ")


import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 
weekly_table_path=os.path.join(BASE_DIR,"weekly_table","weekly_table.xlsx")
# Asegura existencia de la carpeta de logs
table_df=pd.read_excel(weekly_table_path)
table_df["team_position"]=table_df.index+1

df_display = pd.DataFrame({
    "Pos": table_df["team_position"],
    "Equipo": [
        f'<img src="{logo}" width="40"> {name}' 
        for logo, name in zip(table_df["logos_path"], table_df["team_name"])
    ],
    "Puntos": table_df["team_score"]
})

# Function to color last two positions
def highlight_positions(pos):
    if pos in df_display["Pos"].iloc[-2:].values:  # last 2
        return 'background-color: red; color: white; font-weight: bold; text-align:center'
    elif pos in [df_display["Pos"].iloc[0]]:  # top 1
        return 'background-color: green; color: white; font-weight: bold; text-align:center'
    elif pos in df_display["Pos"].iloc[1:3].values:  # 2nd & 3rd
        return 'background-color: #90EE90; color: black; font-weight: bold; text-align:center'
    else:
        return 'background-color: white; color: black; font-weight: bold; text-align:center'

# Apply styling
styled_df = (df_display.style
             .applymap(highlight_positions, subset=['Pos'])
             .set_properties(**{'text-align': 'left'}, subset=['Equipo','Puntos'])
             .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
             .hide(axis='index')
            )

# Render in Streamlit
#st.write(styled_df.to_html(escape=False), unsafe_allow_html=True)
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 


col_table, col_text = st.columns([1.5, 2])  # Adjust widths as needed
with col_table:
    st.markdown("## Clasificación temporada actual")
    st.write(styled_df.to_html(escape=False), unsafe_allow_html=True)

with col_text:
    st.markdown("## Bienvenidas a la plataforma de la Liga F")
    st.write("""El fútbol es mucho más que un juego, es un mundo de números, patrones y hallazgos. 
             Esta plataforma proporciona análisis de datos de última generación.
             """)
    st.write("""El fútbol es mucho más que un juego, es un mundo de números, patrones y hallazgos. 
         Esta plataforma proporciona análisis de datos de última generación.
    """)

    st.write("""
    Aquí encontrarás herramientas de **scouting** 🔍 para seguir el rendimiento de nuestras jugadoras, 
    así como posibles fichajes, y de **análisis del rival** 🆚, con el objetivo de preparar cada partido 
    con la máxima información posible 📊.

    Esta plataforma es el punto de encuentro para **mejorar el rendimiento del equipo** 💪, 
    **potenciar el talento** ⭐ y llevar a nuestros clubes a lo más alto 🏆🔥.
    """)
    st.write("""

    Aquí encontrarás herramientas de **scouting** 🔍 para seguir el rendimiento de nuestras jugadoras, así como posibles fichajes, y de **análisis del rival** 🆚, con el objetivo de preparar cada partido con la máxima información posible 📊.

    Esta plataforma es el punto de encuentro para **mejorar el rendimiento del equipo** 💪, **potenciar el talento** ⭐ y llevar a nuestros clubes a lo más alto 🏆🔥. """)





st.markdown("# 🔍 Que puedes hacer en esta plaforma? ")

st.write("""
         📄 **Generador de Informes Individuales** – Genera informes detallados de un jugador, filtrando por liga, posición y minutos jugados.

    📊 **Visualizador de Estadísticas** – Visualiza el rendimiento de un jugador respecto al resto de su posición en la liga, filtrando por mínimo de minutos jugados.

    ⚖️ **Generador de Informes Comparativos** – Compara dos jugadores de la misma posición con estadísticas clave y métricas de desempeño.

    🏟️ **Visualizador de Equipos** – Compara estadísticas de los equipos en una liga mediante gráficos interactivos en 2D.

    🗂️ **Generador de Informe de Equipo** – Crea informes de rivales con estadísticas detalladas del equipo al que se enfrentará.

    🎯 **Visualizador de Partidos** – Visualiza los eventos ocurridos durante un partido, filtrando por equipo o jugadora.

    👩‍💻 **Visualizador de Jugadoras** – Analiza los eventos de una jugadora durante toda la temporada, con posibilidad de filtrar por partido.
    
    🧤💻 **Visualizador de Porteras** - Analiza los tiros recibidos por una portera durante las temporadas 23/24 y 24/25. 
    
    🧤🗂️ **Generador de Informe de Portera** - Genera informes detallados con estadísticas de los tiros que ha recibido cada portera. 
    
    👟💻 **Visualizador de Delanteras** - Analiza los tiros realizados por una delantera durante las temporadas 23/24 y 24/25.
    
    👟🗂️ **Generador de Informe de Delanteras** - Crea informes detallados con estadísticas de los tiros realizados por cada delantera.
    """)
# 📊 Stats Dashboard – Visualize top performers across leagues and filter by age, nationality, or team. Compare up to 3 stats in interactive 2D or 3D charts.
# ⚖️ Player Comparison – Compare any two players side-by-side with your chosen stats using per 90 values or percentile rankings.
# 🔍 Player Scout Report – View detailed profiles including pizza charts and customizable percentile comparisons by position or league.
# 🧬 Player Clone – Find players with similar profiles based on selected attributes and visualize similarities in 2D or 3D space.
# 🕵️‍♂️ Player Profiler – Identify the most suitable role for any player and see how they match global players in that profile.
# 🧠 Player Performance Index – Discover top talent based on curated performance scores like attacking, pressing, and playmaking. Customize the index with your own weight preferences.
# 🗂️ Player Screener – Set your own stat benchmarks to instantly find players who meet your custom criteria. Filter by percentile or raw values and discover hidden gems.


st.write("""### **Accede a las diferentes secciones de la web a través de los siguientes enlaces 👇**
    
    
""")
st.write("")
st.write("")

col1,col2,col3=st.columns(3)
with col1:
    
    st.page_link("pages/dashboard.py", label="👤 Scouting", icon=None)

with col2:
    st.page_link("pages/team_page.py", label="⚽️ Análisis de rival", icon=None)
with col3:
    st.page_link("pages/team_graphs_page.py", label="⚽️ Visualizador de equipos", icon=None)