#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 21 16:02:28 2025

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
import seaborn as sns
from colorsys import rgb_to_hls

def graficas_2D(filepath_excel,player_id_analizing,player_position,min_minutos,folder_skillcorner,color="#FFFFFF"):
    
    
    color_selection=color.lstrip("#")
    r,g,b=int(color_selection[0:2],16),int(color_selection[2:4],16),int(color_selection[4:6],16)
    h,l,s=rgb_to_hls(r/255.0,g/255.0,b/255.0)
    if l>0.5:
        letter_color="#000000"

    else:
        letter_color="#F2F2F2"

    try:
        df_stats = pd.read_excel(filepath_excel)
        
    except FileNotFoundError:
        print(f"Error: El archivo '{filepath_excel}' no existe.")
        return None
    for i,row in df_stats.iterrows():
        df_stats.loc[i,"player_id"]=i+2
    if player_id_analizing not in df_stats["player_id"].values:
        print(f"El jugador {player_id_analizing} no existe en esta base de datos")
        return None
    #filtramos por minutos jugados la base de datos
    df_stats=df_stats[df_stats["Minutos jugados"]>=min_minutos]
    if player_id_analizing not in df_stats["player_id"].values:
        print(f"El jugador {player_id_analizing} no ha jugado {min_minutos} minutos. ")
        return None
    positions_dict={"GK":"portera","LB":"lateral","RB":"lateral","DMF":"defmid","OF":"ofmid",
                    "AMF":"ofmid","LCB":"defensa","RCB":"defensa","LWF":"extremo","RWF":"extremo",
                    "LAMF":"ofmid","RAMF":"ofmid","LCMF":"ofmid","RCMF":"ofmid","CF":"delantera",
                    "CB":"defensa","RW":"extremo","LDMF":"defmid","LW":"extremo","RDMF":"defmid",
                    }
    positions=["portera","defensa","defmid","ofmid","lateral","delantera","extremo"]

    def map_positions(positions_str):
        positions = positions_str.split(", ")  
        general_positions = [positions_dict.get(pos, pos) for pos in positions]  
        unique_positions = set(general_positions)  
        return ", ".join(unique_positions)  # Unir las posiciones únicas

    df_stats["general_position"] = df_stats["Posición específica"].apply(map_positions)
    
    df_stats[['general_position', 'general_position2',"general_position3"]] = df_stats['general_position'].str.split(", ", n=2, expand=True)
    stats_player=df_stats[df_stats["player_id"]==player_id_analizing]
    player_name=stats_player["Jugador"].iloc[0]
    positions_name_dict={"portera":"Portera","defensa":"Defensa","lateral":"Lateral",
                         "defmid":"Centrocampista defensivo","ofmid":"Centrocampista ofensivo",
                         "extremo":"Extremo","delantera":"Delantera"}
    positions_name_dict_inv = {v: k for k, v in positions_name_dict.items()}
    player_position=positions_name_dict_inv[player_position]
   
    df_position=df_stats[(df_stats["general_position"]==player_position) | (df_stats["general_position2"]==player_position) | (df_stats["general_position3"]==player_position)].copy()
    ########################### Goles vs xG por 90
    fig1, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='xG/90', y='Goles/90', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['xG/90'], row['Goles/90'], row['Jugador'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Goles/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['xG/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['xG/90'].values[0]
        y = jugador['Goles/90'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline
        if player_position=="portera":
            
            plt.text(jugador['xG/90'].values[0]+0.0007, jugador['Goles/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
        else:
            
            plt.text(jugador['xG/90'].values[0]+0.006, jugador['Goles/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Goles Esperados (xG)/90',fontsize=15)
    plt.ylabel('Goles/90',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)

    plt.grid(False)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    output_path1=f"xG_{player_name}.png"
    fig1.savefig(output_path1, dpi=300, bbox_inches='tight')
    plt.close(fig1)
    #plt.show()



    ########################## Asistencias/90 vs xA/90
    fig2, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='xA/90', y='Asistencias/90', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['xA/90'], row['Asistencias/90'], row['Jugador'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Asistencias/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['xA/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['xA/90'].values[0]
        y = jugador['Asistencias/90'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline
        if player_position=="portera":
            plt.text(jugador['xA/90'].values[0]+0.0015, jugador['Asistencias/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
        else:
            plt.text(jugador['xA/90'].values[0]+0.008, jugador['Asistencias/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Asistencias Esperadas (xA)/90',fontsize=15)
    plt.ylabel('Asistencias/90',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)

    plt.grid(False)
    plt.tight_layout()
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    output_path2=f"xA_{player_name}.png"
    fig2.savefig(output_path2, dpi=300, bbox_inches='tight')
    plt.close(fig2)
    #plt.show()

    ########################## Jugadas Claves/90 vs Toques en el área de penalty/90 
    fig3, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Toques en el área de penalti/90', y='Jugadas claves/90', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Toques en el área de penalti/90'], row['Jugadas claves/90'], row['Jugador'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Jugadas claves/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['Toques en el área de penalti/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['Toques en el área de penalti/90'].values[0]
        y = jugador['Jugadas claves/90'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline
        if player_position=="portera":
            plt.text(jugador['Toques en el área de penalti/90'].values[0]+0.005, jugador['Jugadas claves/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
        else:   
            plt.text(jugador['Toques en el área de penalti/90'].values[0]+0.1, jugador['Jugadas claves/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Toques en el área de penalti/90',fontsize=15)
    plt.ylabel('Jugadas claves/90',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.grid(False)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    output_path3=f"JugadasClave_{player_name}.png"
    fig3.savefig(output_path3, dpi=300, bbox_inches='tight')
    plt.close(fig3)
    #plt.show()
    ########################## pases en el ultimo tercio/90 vs pases en el ultimo 1/3, %
    fig4, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Precisión pases en el último tercio, %', y='Pases en el último tercio/90', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Precisión pases en el último tercio, %'], row['Pases en el último tercio/90'], row['Jugador'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Pases en el último tercio/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['Precisión pases en el último tercio, %'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['Precisión pases en el último tercio, %'].values[0]
        y = jugador['Pases en el último tercio/90'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline
        if player_position=="portera":  
            plt.text(jugador['Precisión pases en el último tercio, %'].values[0]+1.17, jugador['Pases en el último tercio/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
        else:
            plt.text(jugador['Precisión pases en el último tercio, %'].values[0]+1.17, jugador['Pases en el último tercio/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Precisión pases en el último tercio, %',fontsize=15)
    plt.ylabel('Pases en el último tercio/90',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.grid(False)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    output_path4=f"Ultimotercio_{player_name}.png"
    fig4.savefig(output_path4, dpi=300, bbox_inches='tight')
    plt.close(fig4)
    #plt.show()

    #################### Duelos atacantes/90 vs Duelos atacantes ganados, %

    fig5, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Duelos atacantes ganados, %', y='Duelos atacantes/90', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Duelos atacantes ganados, %'], row['Duelos atacantes/90'], row['Jugador'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Duelos atacantes/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['Duelos atacantes ganados, %'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['Duelos atacantes ganados, %'].values[0]
        y = jugador['Duelos atacantes/90'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline
        if player_position=="portera":  
            plt.text(jugador['Duelos atacantes ganados, %'].values[0]+1.17, jugador['Duelos atacantes/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
        else:
            plt.text(jugador['Duelos atacantes ganados, %'].values[0]+1.17, jugador['Duelos atacantes/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Duelos atacantes ganados, %',fontsize=15)
    plt.ylabel('Duelos atacantes/90',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.grid(False)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    output_path5=f"Duelos_atacantes_{player_name}.png"
    fig5.savefig(output_path5, dpi=300, bbox_inches='tight')
    plt.close(fig5)
    #plt.show()

    #################### Precision de pases cortos+medios vs pases cortos+medios por 90

    fig6, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Pases cortos / medios /90', y='Precisión pases cortos / medios, %', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Pases cortos / medios /90'], row['Precisión pases cortos / medios, %'], row['Jugador'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Precisión pases cortos / medios, %'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['Pases cortos / medios /90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['Pases cortos / medios /90'].values[0]
        y = jugador['Precisión pases cortos / medios, %'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline
        
        if player_position=="portera":  
            plt.text(jugador['Pases cortos / medios /90'].values[0]+0.84, jugador['Precisión pases cortos / medios, %'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
        else:    
            plt.text(jugador['Pases cortos / medios /90'].values[0]+0.88, jugador['Precisión pases cortos / medios, %'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Pases cortos y medios /90',fontsize=15)
    plt.ylabel('Precisión pases cortos y medios, %',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.grid(False)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    output_path6=f"Pases_cortos_medios_{player_name}.png"
    fig6.savefig(output_path6, dpi=300, bbox_inches='tight')
    plt.close(fig6)
    #plt.show()
    ####################### Pases largos /90 vs precisión de pases largos
    fig7, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Pases largos/90', y='Precisión pases largos, %', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Pases largos/90'], row['Precisión pases largos, %'], row['Jugador'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Precisión pases largos, %'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['Pases largos/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['Pases largos/90'].values[0]
        y = jugador['Precisión pases largos, %'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline
        if player_position=="portera":  
            plt.text(jugador['Pases largos/90'].values[0]+0.15, jugador['Precisión pases largos, %'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
        else:
            plt.text(jugador['Pases largos/90'].values[0]+0.15, jugador['Precisión pases largos, %'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Pases largos/90',fontsize=15)
    plt.ylabel('Precisión pases largos, %',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)

    plt.grid(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    output_path7=f"Pases_largos_{player_name}.png"
    fig7.savefig(output_path7, dpi=300, bbox_inches='tight')
    plt.close(fig7)
    #plt.show()

    ########################## pases progresivos
    fig8, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Pases progresivos/90', y='Precisión pases progresivos, %', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Pases progresivos/90'], row['Precisión pases progresivos, %'], row['Jugador'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Precisión pases progresivos, %'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['Pases progresivos/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['Pases progresivos/90'].values[0]
        y = jugador['Precisión pases progresivos, %'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline

        plt.text(jugador['Pases progresivos/90'].values[0]+0.15, jugador['Precisión pases progresivos, %'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                 bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Pases progresivos/90',fontsize=15)
    plt.ylabel('Precisión pases progresivos, %',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.grid(False)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    output_path8=f"Pases_progresivos_{player_name}.png"
    fig8.savefig(output_path8, dpi=300, bbox_inches='tight')
    plt.close(fig8)
    #plt.show()

    ####################### regates
    fig9, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Regates realizados, %', y='Regates/90', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Regates realizados, %'], row['Regates/90'], row['Jugador'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Regates/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['Regates realizados, %'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['Regates realizados, %'].values[0]
        y = jugador['Regates/90'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline

        plt.text(jugador['Regates realizados, %'].values[0]+1.3, jugador['Regates/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                 bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Regates realizados, %',fontsize=15)
    plt.ylabel('Regates/90',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)

    plt.grid(False)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    output_path9=f"Regates_{player_name}.png"
    fig9.savefig(output_path9, dpi=300, bbox_inches='tight')
    plt.close(fig9)
    #plt.show()
    ######################### duelos defensivos
    fig10, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Duelos defensivos ganados, %', y='Duelos defensivos/90', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Duelos defensivos ganados, %'], row['Duelos defensivos/90'], row['Jugador'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Duelos defensivos/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['Duelos defensivos ganados, %'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['Duelos defensivos ganados, %'].values[0]
        y = jugador['Duelos defensivos/90'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline

        plt.text(jugador['Duelos defensivos ganados, %'].values[0]+1.1, jugador['Duelos defensivos/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                 bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Duelos defensivos ganados, %',fontsize=15)
    plt.ylabel('Duelos defensivos/90',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)

    plt.grid(False)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    output_path10=f"Duelos_defensivos_{player_name}.png"
    fig10.savefig(output_path10, dpi=300, bbox_inches='tight')
    plt.close(fig10)
    #plt.show()

    ######################### Interceptaciones
    fig11, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Interceptaciones/90', y='Posesión conquistada después de una interceptación', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Interceptaciones/90'], row['Posesión conquistada después de una interceptación'], row['Jugador'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Posesión conquistada después de una interceptación'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['Interceptaciones/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['Interceptaciones/90'].values[0]
        y = jugador['Posesión conquistada después de una interceptación'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline

        plt.text(jugador['Interceptaciones/90'].values[0]+0.12, jugador['Posesión conquistada después de una interceptación'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                 bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Interceptaciones/90',fontsize=15)
    plt.ylabel('Posesión conquistada después de una interceptación',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.grid(False)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    output_path11=f"Intercepciones_{player_name}.png"
    fig11.savefig(output_path11, dpi=300, bbox_inches='tight')
    plt.close(fig11)
    #plt.show()
    


    output_paths=[output_path1,output_path2,output_path3,output_path4,output_path5,
                  output_path6,output_path7,output_path8,output_path9,output_path10,
                  output_path11]
    return output_paths






