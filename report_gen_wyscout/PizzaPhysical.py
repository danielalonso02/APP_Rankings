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

def pizzaplot_phys(PLAYER_NAME,PLAYER_POSITION,folder_path,color="#FFFFFF"):
    
    df_phys=pd.read_csv(f"{folder_path}/LigaF_skillcorner_2025.csv",delimiter=";")
    
    col_name = "Short Name" if "Short Name" in df_phys.columns else "Jugador"
    

    dictionary_positions={"Delantera":"Center Forward","Defensa":"Central Defender",
                          "Centrocampista ofensivo":"Midfield","Centrocampista defensivo":"Midfield",
                          "Lateral":"Full Back","Extremo":"Wide Attacker"}
    
    # Intentamos obtener la posición traducida, si no, usamos la original
    pos_to_filter = dictionary_positions.get(PLAYER_POSITION, PLAYER_POSITION)
    
    # FILTRADO: En lugar de usar 'Position Group', vamos a filtrar por 
    # la posición que ya conocemos o simplemente procesar el ranking 
    # si ya has filtrado previamente. 
    # Si quieres filtrar el DF físico por posición para que los percentiles sean justos:
        
    if "Position Group" in df_phys.columns:
        df_phys = df_phys[df_phys["Position Group"] == pos_to_filter]
    elif "Position" in df_phys.columns:
        df_phys = df_phys[df_phys["Position"] == pos_to_filter]
    # Si no existen esas columnas, el percentil será sobre toda la liga (menos ideal pero funciona)

    columns_pizza=["PSV-99","Running Distance P90","HSR Distance P90",
                   "Sprint Distance P90","HI Count P90","Medium Acceleration Count P90",
                   "High Acceleration Count P90","Medium Deceleration Count P90",
                   "High Deceleration Count P90","Explosive Acceleration to Sprint Count P90"]
    
    # 4. Verificación de que el jugador existe en el CSV
    if PLAYER_NAME not in df_phys[col_name].values:
        print(f"Advertencia: {PLAYER_NAME} no encontrado en datos físicos.")
        return None, None

    color_selection=color.lstrip("#")
    r,g,b=int(color_selection[0:2],16),int(color_selection[2:4],16),int(color_selection[4:6],16)
    h,l,s=rgb_to_hls(r/255.0,g/255.0,b/255.0)
    if l>0.5:
        letter_color="#000000"
  
    else:
        letter_color="#F2F2F2"
 


    def calculate_and_assign_percentiles(df, cols):
        df_res = df.copy()
        for col in cols:
            if col in df_res.columns:
                values = df_res[col].values
                # Calculamos percentil y convertimos a int inmediatamente
                df_res[col] = [int(percentileofscore(values, x, kind='rank')) for x in values]
        return df_res
    
    player_raw_data = df_phys[df_phys[col_name] == PLAYER_NAME][columns_pizza].values.flatten().tolist()
    # Convertimos a int para quitar decimales (ej: 25.4 -> 25)
    player_raw_data = [int(val) for val in player_raw_data]
    phys_position=calculate_and_assign_percentiles(df_phys,columns_pizza)
    
    player_df = phys_position[phys_position[col_name] == PLAYER_NAME]
    player_params = player_df[columns_pizza].values.flatten().tolist()

    #medias en numeros
    phys_average = df_phys[columns_pizza].mean().fillna(0).astype(int).tolist()
    player_df=phys_position[phys_position["Short Name"]==PLAYER_NAME]
    player_params=player_df[columns_pizza].values.flatten().tolist()
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
    fig1 = plt.figure(figsize=(16, 20), facecolor=color)
    ax1 = fig1.add_subplot(111, projection="polar", facecolor=color)

    # ----- PIZZA PLOT Físco 1-----
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
            bbox=dict(edgecolor="#000000", facecolor="#1A78CF", boxstyle="round,pad=0.2", lw=1)
        )
    )

    theta1 = np.linspace(0, 2 * np.pi, len(columns_pizza), endpoint=False)
    radius1 = [value for value in player_params]

    for i, value in enumerate(player_params):
        ax1.text(
            theta1[i], radius1[i], f"{value}%",
            color='black', ha='center', va='center', fontsize=18,
            bbox=dict(edgecolor="000000", facecolor="#7CBAF3", boxstyle="round,pad=0.5", lw=1)
        )
    params_offset=[True,True,True,True,True,
                   True,True,True,True,True]
    baker_of.adjust_texts(params_offset, offset=-0.30, adj_comp_values=True)


    legend_labels_of1 = [
        f"{param}: {val_real} ({avg})"
        for param, val_real, avg in zip(params_down, player_raw_data, phys_average)
    ]
    handles_of = [
        Line2D([0], [0], marker='o', markeredgecolor=letter_color, color='w',
               markerfacecolor="#E74C3C", markersize=14, label=label)
        for label in legend_labels_of1
        ]
    legend1 = fig1.legend(handles=handles_of, loc='lower center', fontsize=18, ncol=2,
                      frameon=False, bbox_to_anchor=(0.5, 0.0))
    for label in legend1.get_texts():
        label.set_color(letter_color)

    fig_text(0.5, 0.95, f"<Percentil de {PLAYER_NAME} en Liga F> ",
             size=28, fig=fig1, highlight_textprops=[{"color": '#1A78CF'}],
             ha="center", color=letter_color)

    fig1.text(0.5, 0.90,
              f"Liga F, {PLAYER_POSITION} | Temporada 2025/26",
              size=26, ha="center", color=letter_color)
    output_path1=f"pizzaplot_fisico_{PLAYER_NAME}_{PLAYER_POSITION}.png"
    fig1.savefig(output_path1, dpi=300)
    return  fig1, output_path1, player_params,parameters_show,phys_average,player_raw_data
    
    #plt.show()
