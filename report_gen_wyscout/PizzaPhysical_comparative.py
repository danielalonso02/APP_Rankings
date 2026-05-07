# -*- coding: utf-8 -*-
"""
Created on Fri Apr 10 15:36:28 2026

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
from colorsys import rgb_to_hls

def pizzaplot_phys(name1, name2, player_position, folder_path, league= "LIGA F", color="#FFFFFF"):
    
    try:
        df_phys = pd.read_csv(f"{folder_path}/LigaF_skillcorner_2025.csv", delimiter=";")
    except FileNotFoundError:
        print(f"Error: No se encuentra el archivo físico en {folder_path}")
        return None, None
    
    col_name = "Short Name" if "Short Name" in df_phys.columns else "Jugador"
    

    dictionary_positions={"Delantera":"Center Forward","Defensa":"Central Defender",
                          "Centrocampista ofensivo":"Midfield","Centrocampista defensivo":"Midfield",
                          "Lateral":"Full Back","Extremo":"Wide Attacker"}
    
    # Intentamos obtener la posición traducida, si no, usamos la original
    pos_to_filter = dictionary_positions.get(player_position, player_position)
    
    # FILTRADO: En lugar de usar 'Position Group', vamos a filtrar por 
    # la posición que ya conocemos o simplemente procesar el ranking 
    # si ya has filtrado previamente. 
    # Si quieres filtrar el DF físico por posición para que los percentiles sean justos:
        
    # Filtrar por grupo de posición para que los percentiles sean comparativos
    if "Position Group" in df_phys.columns:
        df_phys_filtered = df_phys[df_phys["Position Group"] == pos_to_filter].copy()
    else:
        df_phys_filtered = df_phys.copy()

    columns_pizza=["PSV-99","Running Distance P90","HSR Distance P90",
                   "Sprint Distance P90","HI Count P90","Medium Acceleration Count P90",
                   "High Acceleration Count P90","Medium Deceleration Count P90",
                   "High Deceleration Count P90","Explosive Acceleration to Sprint Count P90"]
    
    # 4. Verificación de que los jugadores existen en el CSV
    has_j1 = name1 in df_phys_filtered[col_name].values
    has_j2 = name2 in df_phys_filtered[col_name].values

    if not has_j1 and not has_j2:
        print(f"Advertencia: Ninguno de los jugadores ({name1}, {name2}) está en los datos físicos.")
        return None, None

    # Si solo uno tiene datos, usar el que existe como "name1" y marcar el otro como None
    if not has_j1:
        print(f"Advertencia: {name1} no está en los datos físicos. Se mostrará solo {name2}.")
        name1, name2 = name2, None
        has_j1, has_j2 = True, False
    elif not has_j2:
        print(f"Advertencia: {name2} no está en los datos físicos. Se mostrará solo {name1}.")
        has_j2 = False

 


    def get_player_percentiles(df, target_name):
        res = []
        for col in columns_pizza:
            val = df[df[col_name] == target_name][col].iloc[0]
            pct = int(percentileofscore(df[col], val, kind='rank'))
            res.append(pct)
        return res

    pct_j1 = get_player_percentiles(df_phys_filtered, name1)
    pct_j2 = get_player_percentiles(df_phys_filtered, name2) if has_j2 else [0] * len(columns_pizza)

    # Datos reales para la leyenda
    real_j1 = df_phys_filtered[df_phys_filtered[col_name] == name1][columns_pizza].values.flatten().astype(int).tolist()
    real_j2 = df_phys_filtered[df_phys_filtered[col_name] == name2][columns_pizza].values.flatten().astype(int).tolist() if has_j2 else [0] * len(columns_pizza)
    phys_average = df_phys_filtered[columns_pizza].mean().fillna(0).astype(int).tolist()
    
    # 5. Configuración Visual
    color_j1, color_j2 = "#1A78CF", "#E74C3C"
    color_selection = color.lstrip("#")
    r, g, b = int(color_selection[0:2], 16), int(color_selection[2:4], 16), int(color_selection[4:6], 16)
    h, l, s = rgb_to_hls(r/255.0, g/255.0, b/255.0)
    letter_color = "#000000" if l > 0.5 else "#F2F2F2"
    
    parameters_show=["PSV-99", "Distancia corriendo /90", "Distancia corriendo \n a alta intensidad /90",
                     "Distancia a Sprint /90","Número de actividades \n a alta intensidad /90",
                     "Número de aceleraciones \n medias /90","Número de \n aceleraciones altas /90",
                     "Número de decelaraciones \n medias /90", "Número de \n decelaraciones altas /90",
                     "Número de aceleraciones \n explosivas a Sprint /90"]

    params_down=["PSV-99", "Distancia corriendo /90", "Distancia corriendo a alta intensidad /90",
                     "Distancia a Sprint /90","Número de actividades a alta intensidad /90",
                     "Número de aceleraciones medias /90","Número de aceleraciones altas /90",
                     "Número de decelaraciones medias /90", "Número de decelaraciones altas /90",
                     "Número de aceleraciones explosivas a Sprint /90"]
    
    
    parameters_show = [label.replace("\\n", "\n") for label in parameters_show if pd.notna(label)]
    fig = plt.figure(figsize=(14, 16), facecolor=color)
    ax = fig.add_subplot(111, projection="polar", facecolor="#7CBAF3")
    fig.subplots_adjust(top=0.85, bottom=0.22)

    # ----- PIZZA PLOT Físco 1-----
    baker = PyPizza(
        params=parameters_show,
        background_color= "#7CBAF3"
        )

    pizza_kwargs = dict(
        values=pct_j1,
        ax=ax,
        kwargs_slices=dict(facecolor=color_j1, edgecolor="#000000", zorder=1, linewidth=1),
        kwargs_params=dict(color=letter_color, fontsize=16, va="center"),
        kwargs_values=dict(color="#000000", fontsize=16, bbox=dict(edgecolor="#000000", facecolor=color_j1, boxstyle="round,pad=0.2")),
    )
    if has_j2:
        pizza_kwargs["compare_values"] = pct_j2
        pizza_kwargs["kwargs_compare_values"] = dict(color="#000000", fontsize=16, bbox=dict(edgecolor="#000000", facecolor=color_j2, boxstyle="round,pad=0.2"))
    baker.make_pizza(**pizza_kwargs)
    
    # --- AJUSTE DE ETIQUETAS PARA EVITAR SUPERPOSICIÓN (solo en modo comparativo) ---
    if has_j2:
        value_texts = [t for t in ax.texts if "%" in t.get_text() or t.get_text().replace('.','',1).isdigit()]
        half = len(value_texts) // 2
        p1_texts = value_texts[:half]
        p2_texts = value_texts[half:]
        for t1, t2 in zip(p1_texts, p2_texts):
            theta, r = t2.get_position()
            t2.set_position((theta - 0.12, r))
            t2.set_ha('right')
            t1.set_ha('left')
        for i, slice_obj in enumerate(ax.patches):
            if i >= len(pct_j2):
                slice_obj.set_facecolor(color_j2)
                slice_obj.set_alpha(0.5)

    # 7. Textos y Leyenda
    if has_j2:
        fig_text(0.5, 0.99, f"Percentiles de <{name1}> y <{name2}> en {league} (Físico)", size=30, fig=fig,
                 highlight_textprops=[{"color": color_j1}, {"color": color_j2}], ha="center", color=letter_color)
        legend_labels1 = [f"{p}: {v1} | {v2}, ({a})" for p, v1, v2, a in zip(parameters_show, real_j1, real_j2, phys_average)]
    else:
        fig_text(0.5, 0.99, f"Percentiles de <{name1}> en {league} (Físico)", size=30, fig=fig,
                 highlight_textprops=[{"color": color_j1}], ha="center", color=letter_color)
        legend_labels1 = [f"{p}: {v1}, ({a})" for p, v1, a in zip(parameters_show, real_j1, phys_average)]

    handles_metrics1 = [
        Line2D([0], [0], marker='o', markeredgecolor=letter_color,
               markerfacecolor="#E74C3C", color='w', markersize=14, label=label)
        for label in legend_labels1
    ]
        
    lg = fig.legend(
        handles=handles_metrics1, 
        loc='lower center', 
        fontsize=14, 
        ncol=2,
        mode=None,        # Para que no intente expandir
        frameon=False, 
        bbox_to_anchor=(0.5, 0.012),
        columnspacing=2,    # Aumenta este valor si las columnas se siguen pisando
        handletextpad=0.5, # Espacio entre el "marcador" y el texto
        alignment='left'
    )
    for t in lg.get_texts(): t.set_color(letter_color)

    output_path = f"comp_fisica_{name1}_{name2}.png".replace(" ", "_")
    fig.savefig(output_path, dpi=300)
    plt.close(fig)

    return fig, output_path, pct_j1, pct_j2, parameters_show, phys_average, real_j1, real_j2