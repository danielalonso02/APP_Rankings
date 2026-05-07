#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 16 10:36:00 2025

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
import re
from report_gen_opta.utils_report import parse_allf70
import os 
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 
opta_filepath=f"{BASE_DIR}/LigaF_opta_2024.xlsx"
player_id_analizing=176173
#folder_path=f"{BASE_DIR}/data_femeni/raw/f70"
color="#FFFFFF"
min_minutos=500
import pandas as pd
pd.options.mode.chained_assignment = None


def calculate_pizza_values(df_position,position,formulas_filepath):
    #formulas=pd.read_excel("/Users/julieta/Desktop/formulas.xlsx",sheet_name=player_position)
    formulas=pd.read_excel(formulas_filepath,sheet_name=position)
    
    def is_convertible_to_numeric(series):
        # Try converting, return True if any non-NaN result (means convertible)
        return not pd.to_numeric(series, errors='coerce').isna().all()

    for col in df_position.columns:
        if is_convertible_to_numeric(df_position[col]):
            df_position[col] = pd.to_numeric(df_position[col], errors='coerce')
            
            # --- SOLUCIÓN AQUÍ ---
            # Si la columna es de las que deben ser 0 si están vacías:
            columnas_a_cero = ["Goals", "Goles", "Assists", "Penalty Goals", "Goles/90"] 
            
            if col in columnas_a_cero:
                df_position[col] = df_position[col].fillna(0)
            else:
                # Para el resto, si quieres mantener la mediana:
                df_position[col] = df_position[col].fillna(df_position[col].median())
        
    for _, row in formulas.iterrows():
        formula = row['formula']
        variable = row['variable_get']

        # Find all columns used in the formula (assuming they are written without df[])
        cols_in_formula = re.findall(r"'(.*?)'", formula)  # look for 'Duels won', 'Duels', etc.

        # Convert those columns to numeric safely
        for col in cols_in_formula:
            df_position[col] = pd.to_numeric(df_position[col], errors='coerce')
            df_position[col] = df_position[col].fillna(df_position[col].median())

            # Replace column name in formula with df["col"]
            formula = formula.replace(f"'{col}'", f'df_position["{col}"]')

        # Evaluate the formula
        try:
            df_position[variable] = eval(formula)
            #print(f"Successfully calculated {variable}")
        except Exception as e:
            print(f"Error calculating {variable}: {e}")
            print("Formula:", formula)
            print("Column types:", df_position[cols_in_formula].dtypes)
            
    return df_position


#plt.show()


def graficas_2D(opta_filepath,player_id_analizing,min_minutos,year,folder_skillcorner,color="#FFFFFF"):
    df_all_players=pd.read_excel(opta_filepath)
    

    df_all_players=df_all_players[df_all_players["Time Played"]>min_minutos]
    if player_id_analizing not in df_all_players["player_id"].values:
        print(f"Jugadora {player_id_analizing} no encontrada o ha jugado menos de {min_minutos} minutos.")
    player_df=df_all_players[df_all_players["player_id"]==player_id_analizing].copy()


    player_position=player_df["position"].iloc[0]
    df_position=df_all_players[df_all_players["position"]==player_position]
    df_position=calculate_pizza_values(df_position,player_position,"formulas.xlsx")
    folder_path=f"{BASE_DIR}/datos_opta/903/{year}/f70"
    df_xg_all=parse_allf70(folder_path)
    df_xg_all=df_xg_all[df_xg_all["Position"]==player_position].copy()
    df_position=pd.merge(df_position,df_xg_all,left_on="player_id",right_on="PlayerRef",how="left")
    # Rellenamos con 0 las jugadoras que no tienen datos de xG/xA en los archivos f70
    
    # TAPAS LOS HUECOS: Si no hay dato, pon un 0.
    # Esto evita que las jugadoras se vuelvan invisibles en la gráfica.
    df_position["expected_goals"] = df_position["expected_goals"].fillna(0)
    df_position["expected_assists"] = df_position["expected_assists"].fillna(0)
    
    # df_position["expected_goals"] = df_position["expected_goals"].fillna(0)
    # df_position["expected_assists"] = df_position["expected_assists"].fillna(0)
    player_name=player_df["player_name"].iloc[0]
    

    color_selection=color.lstrip("#")
    r,g,b=int(color_selection[0:2],16),int(color_selection[2:4],16),int(color_selection[4:6],16)
    h,l,s=rgb_to_hls(r/255.0,g/255.0,b/255.0)
    if l>0.5:
        letter_color="#000000"

    else:
        letter_color="#F2F2F2"

    ########################### Goles vs xG por 90

    df_position["xG/90"] = df_position.apply(
        lambda row: row["expected_goals"] / row["Time Played"] * 90 if row["Time Played"] > 0 else 0,
        axis=1
    )

    fig1, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='xG/90', y='Goles/90', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['xG/90'], row['Goles/90'], row['player_name'], fontsize=12, alpha=0.3,zorder=2)

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
        if player_position=="portero":
            
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
    ########################## Asistencias/90 vs xA/90


    df_position["xA/90"] = df_position.apply(
        lambda row: row["expected_assists"] / row["Time Played"] * 90 if row["Time Played"] > 0 else 0,
        axis=1
    )
    fig2, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='xA/90', y='Asistencias/90', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['xA/90'], row['Asistencias/90'], row['player_name'], fontsize=12, alpha=0.3,zorder=2)

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
        if player_position=="portero":
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

    ########################## Jugadas Claves/90 vs Toques en el área de penalty/90 
    df_position["Toques en el área de penalti/90"] = df_position.apply(
        lambda row: row["Total Touches In Opposition Box"] / row["Time Played"] * 90 if row["Time Played"] > 0 else 0,
        axis=1
    )


    fig3, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)

    sns.scatterplot(data=df_position, x='Toques en el área de penalti/90', y='Jugadas claves/90', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Toques en el área de penalti/90'], row['Jugadas claves/90'], row['player_name'], fontsize=12, alpha=0.3,zorder=2)

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
        if player_position=="portero":
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

    ########################## pases en el ultimo tercio/90 vs pases en el ultimo 1/3, %
    df_position["Pases en campo rival/90"] = df_position.apply(
        lambda row: (row["Successful Passes Opposition Half"] +row["Unsuccessful Passes Opposition Half"])/ row["Time Played"] * 90 if row["Time Played"] > 0 else 0,
        axis=1
    )
    # print("MAX X")
    # print(df_position['Precisión pases en la zona rival, %'].max())

    fig4, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Precisión pases en la zona rival, %', y='Pases en campo rival/90', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Precisión pases en la zona rival, %'], row['Pases en campo rival/90'], row['player_name'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Pases en campo rival/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['Precisión pases en la zona rival, %'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['Precisión pases en la zona rival, %'].values[0]
        y = jugador['Pases en campo rival/90'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline
        if player_position=="portero":  
            plt.text(jugador['Precisión pases en la zona rival, %'].values[0]+1.17, jugador['Pases en campo rival/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
        else:
            plt.text(jugador['Precisión pases en la zona rival, %'].values[0]+1.17, jugador['Pases en campo rival/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Precisión pases en la zona rival, %',fontsize=15)
    plt.ylabel('Pases en campo rival/90',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.grid(False)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    output_path4=f"Camporival_{player_name}.png"
    fig4.savefig(output_path4, dpi=300, bbox_inches='tight')
    plt.close(fig4)
    #################### Duelos/90 vs Duelos ganados, %

    fig5, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Duelos ganados, %', y='Duelos/90', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Duelos ganados, %'], row['Duelos/90'], row['player_name'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Duelos/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['Duelos ganados, %'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['Duelos ganados, %'].values[0]
        y = jugador['Duelos/90'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline
        if player_position=="portero":  
            plt.text(jugador['Duelos ganados, %'].values[0]+1.17, jugador['Duelos/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
        else:
            plt.text(jugador['Duelos ganados, %'].values[0]+1.17, jugador['Duelos/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Duelos ganados, %',fontsize=15)
    plt.ylabel('Duelos/90',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.grid(False)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    output_path5=f"Duelos_{player_name}.png"
    fig5.savefig(output_path5, dpi=300, bbox_inches='tight')
    plt.close(fig5)
    #plt.show()
    #################### Precision de pases cortos vs pases cortos por 90
    df_position["Precisión pases cortos / medios, %"] = df_position.apply(
        lambda row: ((row["Successful Short Passes"])/ (row["Successful Short Passes"]+row["Unsuccessful Short Passes"]))*100,
        axis=1
    )
    df_position["Pases cortos / medios /90"] = df_position.apply(
        lambda row: (row["Successful Short Passes"] +row["Unsuccessful Short Passes"])/ row["Time Played"] * 90 if row["Time Played"] > 0 else 0,
        axis=1
    )
    fig6, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Pases cortos / medios /90', y='Precisión pases cortos / medios, %', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Pases cortos / medios /90'], row['Precisión pases cortos / medios, %'], row['player_name'], fontsize=12, alpha=0.3,zorder=2)

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
        
        if player_position=="portero":  
            plt.text(jugador['Pases cortos / medios /90'].values[0]+0.84, jugador['Precisión pases cortos / medios, %'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
        else:    
            plt.text(jugador['Pases cortos / medios /90'].values[0]+0.88, jugador['Precisión pases cortos / medios, %'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                     bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Pases cortos /90',fontsize=15)
    plt.ylabel('Precisión pases cortos, %',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.grid(False)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    output_path6=f"Pases_cortos_{player_name}.png"
    fig6.savefig(output_path6, dpi=300, bbox_inches='tight')
    plt.close(fig6)
    #plt.show()
    ####################### Pases largos /90 vs precisión de pases largos
    df_position["Precisión pases largos, %"] = df_position.apply(
        lambda row: ((row["Successful Long Passes"])/ (row["Successful Long Passes"]+row["Unsuccessful Long Passes"]))*100,
        axis=1
    )
    df_position["Pases largos/90"] = df_position.apply(
        lambda row: (row["Successful Long Passes"] +row["Unsuccessful Long Passes"])/ row["Time Played"] * 90 if row["Time Played"] > 0 else 0,
        axis=1
    )
    fig7, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Pases largos/90', y='Precisión pases largos, %', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Pases largos/90'], row['Precisión pases largos, %'], row['player_name'], fontsize=12, alpha=0.3,zorder=2)

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
        if player_position=="portero":  
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
    ########################## pases progresivos
    df_position["Porcentaje de pases progresivos, %"] = df_position.apply(
        lambda row: ((row["Forward Passes"])/ (row["Total Passes"]))*100,
        axis=1
    )
    
    fig8, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Pases progresivos/90', y='Porcentaje de pases progresivos, %', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Pases progresivos/90'], row['Porcentaje de pases progresivos, %'], row['player_name'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Porcentaje de pases progresivos, %'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['Pases progresivos/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['Pases progresivos/90'].values[0]
        y = jugador['Porcentaje de pases progresivos, %'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline

        plt.text(jugador['Pases progresivos/90'].values[0]+0.15, jugador['Porcentaje de pases progresivos, %'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                 bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Pases progresivos/90',fontsize=15)
    plt.ylabel('Porcentaje de pases progresivos, %',fontsize=15)
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
    ####################### regates
    fig9, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Regates realizados, %', y='Regates/90', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Regates realizados, %'], row['Regates/90'], row['player_name'], fontsize=12, alpha=0.3,zorder=2)

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

        plt.text(jugador['Regates realizados, %'].values[0]+1.1, jugador['Regates/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
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
    ######################### recuperaciones/perdidas
    
    fig10, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Recuperaciones/90', y='Pérdidas de posesión/90', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Recuperaciones/90'], row['Pérdidas de posesión/90'], row['player_name'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Pérdidas de posesión/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['Recuperaciones/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['Recuperaciones/90'].values[0]
        y = jugador['Pérdidas de posesión/90'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline

        plt.text(jugador['Recuperaciones/90'].values[0]+0.11, jugador['Pérdidas de posesión/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                 bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Recuperaciones/90',fontsize=15)
    plt.ylabel('Pérdidas de posesión/90',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)

    plt.grid(False)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    output_path10=f"recuperaciones_perdidas_{player_name}.png"
    fig10.savefig(output_path10, dpi=300, bbox_inches='tight')
    plt.close(fig10)
    #plt.show()

    ######################### Interceptaciones
    fig11, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Interceptaciones/90', y='Tiros interceptados/90', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Interceptaciones/90'], row['Tiros interceptados/90'], row['player_name'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Tiros interceptados/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['Interceptaciones/90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['Interceptaciones/90'].values[0]
        y = jugador['Tiros interceptados/90'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline

        plt.text(jugador['Interceptaciones/90'].values[0]+0.11, jugador['Tiros interceptados/90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                 bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Interceptaciones/90',fontsize=15)
    plt.ylabel('Tiros interceptados/90',fontsize=15)
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
    
    ######################### duelos aereos
    fig12, ax = plt.subplots(figsize=(12, 12),facecolor=color)
    ax.set_facecolor(color)
    sns.scatterplot(data=df_position, x='Duelos aéreos ganados, %', y='Duelos aéreos en los 90', s=100, alpha=0.4, color='blue')

    # Nombres de los jugadores (etiquetas)
    for i, row in df_position.iterrows():
        plt.text(row['Duelos aéreos ganados, %'], row['Duelos aéreos en los 90'], row['player_name'], fontsize=12, alpha=0.3,zorder=2)

    # Líneas de referencia (por ejemplo, medias)
    plt.axhline(df_position['Duelos aéreos en los 90'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
    plt.axvline(df_position['Duelos aéreos ganados, %'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)

    # Marcar a Larin (u otro jugador)
    jugador = df_position[df_position['player_id'] == player_id_analizing]
    if not jugador.empty:
        x = jugador['Duelos aéreos ganados, %'].values[0]
        y = jugador['Duelos aéreos en los 90'].values[0]

        plt.scatter(x, y, s=50, color='red', zorder=4)  # small red dot

        plt.scatter(x, y, s=300, facecolors='none', edgecolors='red', linewidths=2, zorder=3)  # bigger red outline

        plt.text(jugador['Duelos aéreos ganados, %'].values[0]+1.1, jugador['Duelos aéreos en los 90'].values[0],player_name, fontsize=12, weight='bold', color='black', 
                 bbox=dict(facecolor='white', edgecolor='black', pad=2), zorder=3)
    # Títulos y etiquetas
    plt.xlabel('Duelos aéreos ganados, %',fontsize=15)
    plt.ylabel('Duelos aéreos/90',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)

    plt.grid(False)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    output_path12=f"Duelos_aereos_{player_name}.png"
    fig12.savefig(output_path12, dpi=300, bbox_inches='tight')
    plt.close(fig12)
    
    
    

    # ------------- GRAFICOS FISICOS 2D -------------
    
    # 1. Carga y normalización inicial
    df_phys = pd.read_csv(f"{folder_skillcorner}/SkillCorner-2026-03-30.csv", delimiter=";")
    col_phys_name = "Player" if "Player" in df_phys.columns else "Jugador"
    
    import unicodedata
    import re
    import difflib
    
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
    
    # --- PROCESO DE ENLACE ---
    
    # Preparamos el nombre que buscamos para el resaltado final
    target_player_clean = clean_extreme(player_name)
    
    # 1. Preparamos los nombres de Opta
    nombres_opta = df_position['player_name'].unique()
    mapeo_final = {}
    
    # 2. Recorremos SkillCorner (Columna 'Player')
    for nombre_sc_original in df_phys[col_phys_name].unique():
        sc_clean = clean_extreme(nombre_sc_original)
        match = None
        
        # Prioridad 1: Contención
        for n_opta in nombres_opta:
            opta_clean = clean_extreme(n_opta)
            if opta_clean in sc_clean or sc_clean in opta_clean:
                match = n_opta
                break
                
        # Prioridad 2: Similitud
        if not match:
            clean_opta_list = [clean_extreme(n) for n in nombres_opta]
            close_matches = difflib.get_close_matches(sc_clean, clean_opta_list, n=1, cutoff=0.7)
            if close_matches:
                idx = clean_opta_list.index(close_matches[0])
                match = nombres_opta[idx]
                
        mapeo_final[nombre_sc_original] = match

    # 3. Aplicamos y Merge
    df_phys['nombre_unificado'] = df_phys[col_phys_name].map(mapeo_final)
    # Eliminamos duplicados para evitar que una jugadora de SC mapee a dos de Opta
    df_phys = df_phys.drop_duplicates(subset=['nombre_unificado'])
    
    df_phys_pos = pd.merge(df_position, df_phys, left_on='player_name', right_on='nombre_unificado', how='inner')
    
    # 4. Función auxiliar corregida
    def save_phys_scatter(df, x_col, y_col, x_label, y_label, filename):
        fig, ax = plt.subplots(figsize=(12, 12), facecolor=color)
        ax.set_facecolor(color)
        
        sns.scatterplot(data=df, x=x_col, y=y_col, s=100, alpha=0.4, color='blue')
        
        # Usamos 'player_name' que es la columna de Opta que ya sabemos que está limpia
        for _, row in df.iterrows():
            plt.text(row[x_col], row[y_col], row["player_name"], fontsize=10, alpha=0.2)
            
        plt.axhline(df[y_col].mean(), color='red', linestyle='--', linewidth=2, alpha=0.6)
        plt.axvline(df[x_col].mean(), color='red', linestyle='--', linewidth=2, alpha=0.6)
        
        # RESALTADO: Buscamos por la columna que acabamos de limpiar
        # Comparamos la versión limpia de player_name con nuestra target_player_clean
        jugador_phys = df[df['player_name'].apply(clean_extreme) == target_player_clean]
        
        if not jugador_phys.empty:
            px, py = jugador_phys[x_col].values[0], jugador_phys[y_col].values[0]
            plt.scatter(px, py, s=350, facecolors='none', edgecolors='red', linewidths=3, zorder=5)
            plt.text(px, py + (df[y_col].max()*0.01), player_name, fontsize=13, weight='bold', 
                     bbox=dict(facecolor='white', edgecolor='red', pad=3), zorder=6, ha='center')
            
            
            
        plt.xlabel(x_label, fontsize=15)
        plt.ylabel(y_label, fontsize=15)
        plt.grid(False)
        sns.despine()
        plt.tight_layout()
        fig.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
    # --- Ejecución de los gráficos ---
    out_phys1 = f"Phys_Volumen_{player_name}.png"
    save_phys_scatter(df_phys_pos, 'Running Distance P90', 'HI Count P90', 
                      'Distancia Total (m) /90', 'Nº Actividades Alta Intensidad /90', out_phys1)
    
    out_phys2 = f"Phys_Velocidad_{player_name}.png"
    save_phys_scatter(df_phys_pos, 'PSV-99', 'Sprint Distance P90', 
                      'Velocidad Máxima (km/h)', 'Distancia en Sprint (m) /90', out_phys2)
    
    out_phys3 = f"Phys_Explosividad_{player_name}.png"
    save_phys_scatter(df_phys_pos, 'High Acceleration Count P90', 'High Deceleration Count P90', 
                      'Aceleraciones Altas /90', 'Deceleraciones Altas /90', out_phys3)
    
    
    output_paths=[output_path1,output_path2,output_path3,output_path4,output_path5,
                  output_path6,output_path7,output_path8,output_path9,output_path10,output_path11,output_path12,
                  out_phys1,out_phys2,out_phys3]
    return output_paths


#graficas_2D("/Users/julieta/Desktop/LigaF_opta_2024.xlsx",246558,min_minutos,color="#FFFFFF")

