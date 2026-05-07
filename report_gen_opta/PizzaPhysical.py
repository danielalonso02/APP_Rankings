#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  9 12:45:01 2025

@author: julieta
"""

import pandas as pd
import numpy as np
import json
from mplsoccer import Radar, FontManager, grid
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from urllib.request import urlopen
from PIL import Image
from mplsoccer import PyPizza, add_image, FontManager

from highlight_text import fig_text
from matplotlib.lines import Line2D
from scipy.stats import percentileofscore
from colorsys import rgb_to_hls

import unicodedata
import re
import difflib

def pizzaplot_phys(PLAYER_NAME, PLAYER_POSITION, folder_path, color="#FFFFFF"):
    
    # 1. Carga de datos con encoding robusto
    try:
        df_phys = pd.read_csv(f"{folder_path}/SkillCorner-2026-03-30.csv", delimiter=";", encoding="utf-8-sig")
    except:
        try:
            df_phys = pd.read_csv(f"{folder_path}/SkillCorner-2026-03-30.csv", delimiter=";", encoding="latin1")
        except FileNotFoundError:
            print("Error: El archivo no existe.")
            return None, None, None, None, None

    col_name = "Player" if "Player" in df_phys.columns else "Jugador"

    # 2. Función de limpieza extrema (Maneja los caracteres rotos de tus capturas)
    def clean_extreme(text):
        if pd.isna(text): return ""
        text = str(text)
        replacements = {
            'Ã¸': 'O', 'Ã¤': 'A', 'Ã­': 'I', 'Ã©': 'E', 'Ã¡': 'A', 
            'Ã³': 'O', 'Ãº': 'U', 'Ã±': 'N', 'Ã': 'A', 'Â': '', 
            'A¤': 'A', 'A©': 'E', 'A­': 'I', 'A±': 'N', 'Ã¼': 'U'
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        text = text.upper()
        text = re.sub(r'[^A-Z\s]', ' ', text)
        return " ".join(text.split())

    # 3. BUSCADOR INTELIGENTE DE JUGADORA
    target_clean = clean_extreme(PLAYER_NAME)
    nombres_csv = df_phys[col_name].unique()
    match_final = None

    # Prioridad 1: Contención (Caza a Angela Sosa en Angela Sosa Martin)
    for n_csv in nombres_csv:
        n_csv_clean = clean_extreme(n_csv)
        if target_clean in n_csv_clean or n_csv_clean in target_clean:
            match_final = n_csv
            break
    
    # Prioridad 2: Similitud (Fuzzy) si la contención falla
    if not match_final:
        # Creamos una lista de nombres limpios para comparar
        clean_list = [clean_extreme(n) for n in nombres_csv]
        close_matches = difflib.get_close_matches(target_clean, clean_list, n=1, cutoff=0.7)
        if close_matches:
            idx = clean_list.index(close_matches[0])
            match_final = nombres_csv[idx]

    if match_final:
        PLAYER_NAME = match_final # Sincronizamos con el nombre exacto del CSV
    else:
        print(f"ERROR: No se encontró a {PLAYER_NAME} en datos físicos.")
        return None, None, None, None, None

    # 4. Filtrado por posición para percentiles justos
    dictionary_positions = {
        "Delantera": "Center Forward", "Defensa": "Central Defender",
        "Centrocampista ofensivo": "Midfield", "Centrocampista defensivo": "Midfield",
        "Lateral": "Full Back", "Extremo": "Wide Attacker"
    }
    pos_to_filter = dictionary_positions.get(PLAYER_POSITION, PLAYER_POSITION)
    
    if "Position Group" in df_phys.columns:
        df_phys = df_phys[df_phys["Position Group"] == pos_to_filter]
    elif "Position" in df_phys.columns:
        df_phys = df_phys[df_phys["Position"] == pos_to_filter]

    # --- El resto del proceso de percentiles y gráfico sigue igual ---
    columns_pizza = ["PSV-99", "Running Distance P90", "HSR Distance P90",
                     "Sprint Distance P90", "HI Count P90", "Medium Acceleration Count P90",
                     "High Acceleration Count P90", "Medium Deceleration Count P90",
                     "High Deceleration Count P90", "Explosive Acceleration to Sprint Count P90"]

    def calculate_and_assign_percentiles(df, cols):
        df_res = df.copy()
        for col in cols:
            if col in df_res.columns:
                values = df_res[col].values
                df_res[col] = [int(percentileofscore(values, x, kind='rank')) for x in values]
        return df_res

    # Datos reales (Raw)
    player_raw_data = df_phys[df_phys[col_name] == PLAYER_NAME][columns_pizza].values.flatten().tolist()
    player_raw_data = [int(val) for val in player_raw_data]
    
    # Percentiles
    phys_position = calculate_and_assign_percentiles(df_phys, columns_pizza)
    player_df = phys_position[phys_position[col_name] == PLAYER_NAME]
    player_params = player_df[columns_pizza].values.flatten().tolist()
    
    # Medias de la posición
    phys_average = df_phys[columns_pizza].mean().fillna(0).astype(int).tolist()

    # --- Configuración Visual del Gráfico ---
    # (Mantengo tu lógica de colores y PyPizza...)
    color_selection = color.lstrip("#")
    r, g, b = int(color_selection[0:2], 16), int(color_selection[2:4], 16), int(color_selection[4:6], 16)
    h, l, s = rgb_to_hls(r/255.0, g/255.0, b/255.0)
    letter_color = "#000000" if l > 0.5 else "#F2F2F2"

    parameters_show = ["PSV-99", "Distancia corriendo /90", "Distancia corriendo \n a alta intensidad /90",
                       "Distancia a Sprint /90", "Número de actividades \n a alta intensidad /90",
                       "Número de aceleraciones \n medias /90", "Número de \n aceleraciones altas /90",
                       "Número de decelaraciones \n medias /90", "Número de \n decelaraciones altas /90",
                       "Número de aceleraciones \n explosivas a Sprint /90"]

    params_down = [p.replace("\n", "") for p in parameters_show]
    
    fig1 = plt.figure(figsize=(16, 20), facecolor=color)
    ax1 = fig1.add_subplot(111, projection="polar", facecolor=color)

    baker_of = PyPizza(
        params=parameters_show,
        background_color=color,
        straight_line_color="#222222",
        straight_line_lw=1,
        last_circle_lw=1,
        last_circle_color="#222222",
        other_circle_ls="-.",
        other_circle_lw=1
    )

    baker_of.make_pizza(
        player_params,
        ax=ax1,
        color_blank_space="same",
        param_location=112,
        blank_alpha=0.4,
        kwargs_slices=dict(facecolor="#1A78CF", edgecolor="#000000", zorder=1, linewidth=1),
        kwargs_params=dict(color=letter_color, fontsize=24, zorder=5, va="center"),
        kwargs_values=dict(color="#000000", fontsize=18,
                           bbox=dict(edgecolor="#000000", facecolor="#1A78CF", boxstyle="round,pad=0.2", lw=1))
    )

    # Añadir los porcentajes sobre los sectores
    theta1 = np.linspace(0, 2 * np.pi, len(columns_pizza), endpoint=False)
    for i, value in enumerate(player_params):
        ax1.text(theta1[i], value, f"{value}%", color='black', ha='center', va='center', fontsize=18,
                 bbox=dict(edgecolor="000000", facecolor="#7CBAF3", boxstyle="round,pad=0.5", lw=1))

    # Ajustes finales y Leyenda
    legend_labels = [f"{p}: {v} ({a})" for p, v, a in zip(params_down, player_raw_data, phys_average)]
    handles = [Line2D([0], [0], marker='o', color='w', markerfacecolor="#E74C3C", markersize=14, label=l) for l in legend_labels]
    
    legend1 = fig1.legend(handles=handles, loc='lower center', fontsize=18, ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0))
    for text in legend1.get_texts(): text.set_color(letter_color)

    fig_text(0.5, 0.95, f"<Percentil de {PLAYER_NAME} en Liga F> ", size=28, fig=fig1, 
             highlight_textprops=[{"color": '#1A78CF'}], ha="center", color=letter_color)

    output_path1 = f"pizzaplot_fisico_{PLAYER_NAME}_{PLAYER_POSITION}.png"
    fig1.savefig(output_path1, dpi=300, bbox_inches='tight')
    
    return fig1, output_path1, player_raw_data, parameters_show, phys_average
    
    #plt.show()
