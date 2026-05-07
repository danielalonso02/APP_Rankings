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

def pizzaplot_phys(PLAYER_NAME,PLAYER_POSITION,phys_file,color="#FFFFFF"):
    
    try:
       df_phys=pd.read_csv(phys_file,delimiter=";")
        
    except FileNotFoundError:
        print(f"Error: El archivo '{phys_file}' no existe.")
    

    dictionary_positions={"Delantero":"Center Forward","Defensa":"Central Defender",
                          "Centrocampista ofensivo":"Midfield","Centrocampista defensivo":"Midfield",
                          "Lateral":"Full Back","Extremo":"Wide Attacker"}

    position_skillcorner=dictionary_positions[PLAYER_POSITION]
    player_position=df_phys[df_phys["Short Name"]==PLAYER_NAME]["Position Group"].iloc[0]
    if position_skillcorner!=player_position:
        position_skillcorner=player_position
    
    df_phys=df_phys[df_phys["Position Group"]==position_skillcorner]

    columns_pizza=["PSV-99","Running Distance P90","HSR Distance P90",
                   "Sprint Distance P90","HI Count P90","Medium Acceleration Count P90",
                   "High Acceleration Count P90","Medium Deceleration Count P90",
                   "High Deceleration Count P90","Explosive Acceleration to Sprint Count P90"]

    color_selection=color.lstrip("#")
    r,g,b=int(color_selection[0:2],16),int(color_selection[2:4],16),int(color_selection[4:6],16)
    h,l,s=rgb_to_hls(r/255.0,g/255.0,b/255.0)
    if l>0.5:
        letter_color="#000000"
  
    else:
        letter_color="#F2F2F2"
 


    def calculate_and_assign_percentiles(df, *column_lists):

        columns = pd.Series(sum(column_lists, [])).unique().tolist()
        
        # Calcular los percentiles para las columnas 
        for col in columns:
            values = df[col].values  
            percentiles = [
                percentileofscore(values, x, kind='rank') 
                for x in values
            ]
            
            
            df[col] = pd.Series(percentiles).round().astype(int).values
        
        return df
    phys_position=calculate_and_assign_percentiles(df_phys,columns_pizza)

    #medias en numeros
    phys_average=df_phys[columns_pizza].mean().astype(int)
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

    # ----- PIZZA PLOT OFENSIVO 1-----
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
        f"{param}: {value}, ({values})"
        for param, value, values in zip(params_down, player_params, phys_average)
    ]
    handles_of = [
        Line2D([0], [0], marker='o', markeredgecolor=letter_color, color='w',
               markerfacecolor="#E74C3C", markersize=14, label=label)
        for label in legend_labels_of1
        ]
    legend1 = fig1.legend(handles=handles_of, loc='lower center', fontsize=20, ncol=2,
                      frameon=False, bbox_to_anchor=(0.5, 0.0))
    for label in legend1.get_texts():
        label.set_color(letter_color)

    fig_text(0.5, 0.95, f"<Percentil de {PLAYER_NAME} en 1º RFEF> ",
             size=28, fig=fig1, highlight_textprops=[{"color": '#1A78CF'}],
             ha="center", color=letter_color)

    fig1.text(0.5, 0.90,
              f"1º RFEF, {PLAYER_POSITION} | Temporada 2024/25",
              size=26, ha="center", color=letter_color)
    output_path1=f"pizzaplot_fisico_{PLAYER_NAME}_{PLAYER_POSITION}.png"
    fig1.savefig(output_path1, dpi=300)
    return output_path1
    
    #plt.show()
