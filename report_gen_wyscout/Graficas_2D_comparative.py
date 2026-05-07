# -*- coding: utf-8 -*-
"""
Created on Fri Apr 10 12:52:19 2026

@author: danie
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
import seaborn as sns
from colorsys import rgb_to_hls

def graficas_2D(filepath_excel1, filepath_excel2=None, player_id1=None, player_id2=None, player_position=None, min_minutos=500, folder_skillcorner=None, color="#FFFFFF"):
    
    # Soporte para un solo archivo (misma liga)
    if filepath_excel2 is None:
        filepath_excel2 = filepath_excel1

    # --- CONFIGURACIÓN DE COLORES ---
    color_selection = color.lstrip("#")
    r, g, b = int(color_selection[0:2], 16), int(color_selection[2:4], 16), int(color_selection[4:6], 16)
    h, l, s = rgb_to_hls(r/255.0, g/255.0, b/255.0)
    letter_color = "#000000" if l > 0.5 else "#F2F2F2"

    # --- CARGA DE DATOS ---
    try:
        df_stats1 = pd.read_excel(filepath_excel1)
    except FileNotFoundError:
        print(f"Error: El archivo '{filepath_excel1}' no existe.")
        return None

    try:
        df_stats2 = pd.read_excel(filepath_excel2)
    except FileNotFoundError:
        print(f"Error: El archivo '{filepath_excel2}' no existe.")
        return None

    # Asignar player_id a cada df por separado
    df_stats1["player_id"] = df_stats1.index + 2
    df_stats2["player_id"] = df_stats2.index + 2

    # Filtrado por minutos jugados
    df_stats1 = df_stats1[df_stats1["Minutos jugados"] >= min_minutos]
    df_stats2 = df_stats2[df_stats2["Minutos jugados"] >= min_minutos]

    # Aplicar offset a df_stats2 para evitar colisiones de IDs
    same_league = (filepath_excel1 == filepath_excel2)
    if same_league:
        df_stats = df_stats1.copy()
        player_id2_internal = player_id2
    else:
        offset = int(df_stats1["player_id"].max()) + 100
        df_stats2_offset = df_stats2.copy()
        df_stats2_offset["player_id"] = df_stats2_offset["player_id"] + offset
        player_id2_internal = player_id2 + offset
        df_stats = pd.concat([df_stats1, df_stats2_offset], ignore_index=True)

    # Validación de existencia de ambos jugadores
    if player_id1 not in df_stats["player_id"].values or player_id2_internal not in df_stats["player_id"].values:
        print(f"Error: Uno de los IDs ({player_id1}, {player_id2}) no existe o no tiene suficientes minutos.")
        return None

    # Obtener nombres para las gráficas
    name1 = df_stats[df_stats["player_id"] == player_id1]["Jugador"].iloc[0]
    name2 = df_stats[df_stats["player_id"] == player_id2_internal]["Jugador"].iloc[0]

    # --- GESTIÓN DE POSICIONES (Aquí estaba el error) ---
    
    # Diccionario para convertir el input de consola (ej: "Defensa") a tu clave interna (ej: "defensa")
    # Lo hacemos insensible a mayúsculas usando .lower() más adelante
    positions_name_dict_inv = {
        "portera": "portera", "defensa": "defensa", "lateral": "lateral",
        "centrocampista defensivo": "defmid", "centrocampista ofensivo": "ofmid",
        "extremo": "extremo", "delantera": "delantera"
    }

    # Convertimos el input "Defensa" a "defensa" y buscamos la clave interna
    pos_key_input = player_position.lower().strip()
    pos_key = positions_name_dict_inv.get(pos_key_input)

    if not pos_key:
        print(f"Error: La posición '{player_position}' no está en el mapeo.")
        return None

    print(f"Validado: Comparando a {name1} vs {name2} en posición {pos_key}")

    # --- MAPEO DE POSICIONES EN EL DATAFRAME ---
    positions_dict_wyscout = {
        "GK":"portera","LB":"lateral","RB":"lateral","DMF":"defmid","OF":"ofmid",
        "AMF":"ofmid","LCB":"defensa","RCB":"defensa","LWF":"extremo","RWF":"extremo",
        "LAMF":"ofmid","RAMF":"ofmid","LCMF":"ofmid","RCMF":"ofmid","CF":"delantera",
        "CB":"defensa","RW":"extremo","LDMF":"defmid","LW":"extremo","RDMF":"defmid"
    }

    def map_positions(positions_str):
        if pd.isna(positions_str): return ""
        parts = str(positions_str).split(", ")
        mapped = [positions_dict_wyscout.get(p, p) for p in parts]
        seen = []
        for p in mapped:
            if p not in seen:
                seen.append(p)
        return ", ".join(seen)

    # Crear columnas de posición general para filtrar el scatter
    df_stats["general_position"] = df_stats["Posición específica"].apply(map_positions)
    df_split = df_stats['general_position'].str.split(", ", expand=True)
    
    # Aseguramos que existan 3 columnas aunque el jugador solo tenga una posición
    for col_idx in range(3):
        col_name = f"general_position{col_idx+1}"
        df_stats[col_name] = df_split[col_idx] if col_idx in df_split.columns else None
    
    df_position = df_stats[(df_stats["general_position1"] == pos_key) | 
                           (df_stats["general_position2"] == pos_key) | 
                           (df_stats["general_position3"] == pos_key)].copy()

    # --- FUNCIÓN INTERNA PARA GENERAR SCATTERS COMPARATIVOS ---
    def create_comp_scatter(df, x_col, y_col, x_label, y_label, filename):
        fig, ax = plt.subplots(figsize=(12, 12), facecolor=color)
        ax.set_facecolor(color)
        
        # Fondo: Todos los jugadores de la posición
        sns.scatterplot(data=df, x=x_col, y=y_col, s=100, alpha=0.4, color='grey', ax=ax)
        
        # Nombres de los jugadores (etiquetas)
        for i, row in df.iterrows():
            ax.text(row[x_col], row[y_col], row['Jugador'], 
                    fontsize=8, alpha=0.4, zorder=2, clip_on=True)
        
        # Medias de la posición
        ax.axhline(df[y_col].mean(), color='red', linestyle='--', linewidth=2, alpha=1)
        ax.axvline(df[x_col].mean(), color='red', linestyle='--', linewidth=2, alpha=1)

        # Resaltar Jugador 1 (Azul)
        p1 = df[df["player_id"] == player_id1].iloc[0]
        ax.scatter(p1[x_col], p1[y_col], s=300, color='#1A78CF', edgecolor='black', zorder=5, label=name1)
        ax.text(p1[x_col], p1[y_col]+(df[y_col].std()*0.1), name1, fontsize=12, weight='bold', 
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='#1A78CF'))

        # Resaltar Jugador 2 (Rojo)
        p2 = df[df["player_id"] == player_id2_internal].iloc[0]
        ax.scatter(p2[x_col], p2[y_col], s=300, color='#E74C3C', edgecolor='black', zorder=5, label=name2)
        ax.text(p2[x_col], p2[y_col]+(df[y_col].std()*0.1), name2, fontsize=12, weight='bold', 
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='#E74C3C'))

        ax.set_xlabel(x_label, fontsize=14)
        ax.set_ylabel(y_label, fontsize=14)
        sns.despine()
        plt.tight_layout()
        fig.savefig(filename, dpi=300)
        plt.close(fig)
        return filename
    
    metrics = [
        ('xG/90', 'Goles/90', 'Goles Esperados (xG)/90', 'Goles/90', f"comp_xG_{name1}_{name2}.png"),
        ('xA/90', 'Asistencias/90', 'Asistencias Esperadas (xA)/90', 'Asistencias/90', f"comp_xA_{name1}_{name2}.png"),
        ('Toques en el área de penalti/90', 'Jugadas claves/90', 'Toques área penalti/90', 'Jugadas claves/90', f"comp_Claves_{name1}_{name2}.png"),
        ('Precisión pases en el último tercio, %', 'Pases en el último tercio/90', 'Precisión pases 1/3, %', 'Pases 1/3 /90', f"comp_Tercio_{name1}_{name2}.png"),
        ('Duelos atacantes ganados, %', 'Duelos atacantes/90', 'Duelos atacantes ganados, %', 'Duelos atacantes/90', f"comp_DuelosAt_{name1}_{name2}.png"),
        ('Pases cortos / medios /90', 'Precisión pases cortos / medios, %', 'Pases cortos/medios /90', 'Precisión cortos/medios, %', f"comp_PasesCM_{name1}_{name2}.png"),
        ('Pases largos/90', 'Precisión pases largos, %', 'Pases largos/90', 'Precisión largos, %', f"comp_Largos_{name1}_{name2}.png"),
        ('Pases progresivos/90', 'Precisión pases progresivos, %', 'Pases progresivos/90', 'Precisión progresivos, %', f"comp_Progresivos_{name1}_{name2}.png"),
        ('Regates realizados, %', 'Regates/90', 'Regates realizados, %', 'Regates/90', f"comp_Regates_{name1}_{name2}.png"),
        ('Duelos defensivos ganados, %', 'Duelos defensivos/90', 'Duelos defensivos ganados, %', 'Duelos defensivos/90', f"comp_DuelosDef_{name1}_{name2}.png"),
        ('Interceptaciones/90', 'Posesión conquistada después de una interceptación', 'Interceptaciones/90', 'Posesión tras intercep.', f"comp_Intercep_{name1}_{name2}.png")
    ]

    output_paths = [create_comp_scatter(df_position, *m) for m in metrics]
    
        

    return output_paths






