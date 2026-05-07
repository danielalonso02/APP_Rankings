# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 11:50:55 2026

@author: danie
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  6 10:23:55 2025

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
from IntentoArrays import extract_arrays_wyscout
import warnings
from skillcorner.client import SkillcornerClient
import os
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
def notas_fisicas(PLAYER_POSITION,filepath_excel,PLAYER_NAME,parameters_file,min_minutos,folder_path,player_id_analizing,pesos_fisicos=None):
    """
    

    Parameters
    ----------
    PLAYER_POSITION : es la posición en valor final (como se muestra en el informe)
    filepath_excel : file de wyscout full de la liga que estamos analizando
    parameters_file : file de parametros generico
    player_id_analizing : id del jugador que analizamos
    min_minutos : minimo de minutos que vamos a querer filtrar

    Returns
    -------
    None.

    """
    
    dictionary_positions={"Portera":"portera","Defensa":"defensa","Lateral":"lateral",
                 "Centrocampista defensivo":"centrocampista_defensivo",
                 "Centrocampista ofensivo":"centrocampista_ofensivo",
                 "Extremo":"extremo","Delantera":"delantera"}

    position_excel=dictionary_positions[PLAYER_POSITION]

    # Mapa: nombre en español (key del JSON) → columna del CSV SkillCorner
    MAPEO_FISICO = {
        "Velocidad máx. (PSV-99)":               "PSV-99",
        "Distancia en sprint /partido":           "Sprint Distance P90",
        "Acciones de alta intensidad /partido":   "HI Count P90",
        "Distancia alta velocidad /partido":      "HSR Distance P90",
        "Aceleraciones altas /partido":           "High Acceleration Count P90",
        "Deceleraciones altas /partido":          "High Deceleration Count P90",
        "Deceleraciones medias /partido":         "Medium Deceleration Count P90",
        "Distancia en carrera /partido":          "Running Distance P90",
        "Aceleraciones medias /partido":          "Medium Acceleration Count P90",
        "Aceleraciones explosivas /partido":      "Explosive Acceleration to Sprint Count P90",
    }

    if pesos_fisicos is not None:
        # Construir dict {col_csv: peso} desde el JSON de favoritos físicos
        # Las keys del JSON son "slider_Velocidad máx. (PSV-99)" → quitar prefijo "slider_"
        raw = {k.replace("slider_", "", 1): v for k, v in pesos_fisicos.items()}
        ponderations = {MAPEO_FISICO[k]: float(v) for k, v in raw.items() if k in MAPEO_FISICO}
        if not ponderations:
            # Fallback a Excel si el JSON no contiene claves reconocidas
            pesos_fisicos = None

    if pesos_fisicos is None:
        # Mismo método que rankings_fisicos_skillcorner.py: una sola hoja, col 0 = métrica, col 1 = peso
        excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "report_gen_opta", "datoswyscout", "physical_percentages.xlsx")
        df_w = pd.read_excel(excel_path)
        dict_pesos_raw = dict(zip(df_w.iloc[:, 0].astype(str), df_w.iloc[:, 1]))
        # Normalizar a [0,1] si los valores vienen en escala 0-100
        ponderations = {k: (float(v) / 100 if float(v) > 1.0 else float(v)) for k, v in dict_pesos_raw.items() if pd.notna(v)}
    
    df_phys=pd.read_csv(f"{folder_path}/LigaF_skillcorner_2025.csv",delimiter=";")
    df_pressure=pd.read_csv(f"{folder_path}/SkillCorner-GI-2026-03-30-5.csv",delimiter=",")
    df_passing=pd.read_csv(f"{folder_path}/SkillCorner-GI-2026-03-30-2.csv",delimiter=",")
    df_offball=pd.read_csv(f"{folder_path}/SkillCorner-GI-2026-03-30.csv",delimiter=",")
    
    # UNIFICACIÓN DE NOMBRES DE COLUMNA
    # Renombramos 'player_short_name' a 'Short Name' en los DataFrames de GI
    for df in [df_phys]:
        if 'Short Name' in df.columns:
            df.rename(columns={'Short Name': 'Jugador'}, inplace=True)
    
    
            
    for df in [df_pressure, df_passing, df_offball]:
        if 'player_short_name' in df.columns:
            df.rename(columns={'player_short_name': 'Jugador'}, inplace=True)
        elif 'Player' in df.columns: # Por si acaso alguno viniera como 'Player'
            df.rename(columns={'Player': 'Jugador'}, inplace=True)
   
    
    _, _, _, _,df_all_stats,_,_ = extract_arrays_wyscout(
        filepath_excel,parameters_file,
        player_id_analizing,
        "param_of1", min_minutos
    )
    
    df_all_stats["general_position2"] = df_all_stats["general_position2"].fillna("None")
    df_all_stats["general_position3"] = df_all_stats["general_position3"].fillna("None")
    stats_player=df_all_stats[df_all_stats["player_id"]==player_id_analizing].iloc[0]
    player_position=stats_player["general_position"]

    
    df_stats_position=df_all_stats[(df_all_stats["general_position"]==player_position) | (df_all_stats["general_position2"]==player_position) | (df_all_stats["general_position3"]==player_position)].copy()
    
    numeric_cols_pos = [col for col in df_stats_position.select_dtypes(include=['number']).columns if col != "player_id"]
    # Apply Min-Max scaling to each numeric column
    #df_stats_position[numeric_cols_pos] = (df_stats_position[numeric_cols_pos] - df_stats_position[numeric_cols_pos].min()) / (df_stats_position[numeric_cols_pos].max() - df_stats_position[numeric_cols_pos].min())
    denom = (df_stats_position[numeric_cols_pos].max() - df_stats_position[numeric_cols_pos].min()).replace(0, 1)
    df_stats_position[numeric_cols_pos] = (df_stats_position[numeric_cols_pos] - df_stats_position[numeric_cols_pos].min()) / denom
    #df_stats_position.to_excel("dfstatsposition.xlsx")
    number_of_players_position=len(df_stats_position)
    
    
    # Obtenemos la lista de nombres (o IDs) de las jugadoras que SÍ son de la misma posición
    players_in_pos = df_stats_position[["Jugador"]].drop_duplicates()

    # Filtramos el dataframe físico para que SOLO contenga a esas jugadoras
    # Esto asegura que el ranking y el min/max del score sea solo entre iguales
    
    # Seleccionamos las columnas necesarias (ahora ya filtrado por posición)
    columnas_fisicas = ["Jugador", "PSV-99","Running Distance P90","HSR Distance P90",
                   "Sprint Distance P90","HI Count P90","Medium Acceleration Count P90",
                   "High Acceleration Count P90","Medium Deceleration Count P90",
                   "High Deceleration Count P90","Explosive Acceleration to Sprint Count P90"]
    
    merged_df = pd.merge(
        players_in_pos, 
        df_phys[columnas_fisicas], 
        on="Jugador", 
        how="inner"
    ).copy()
    
    
    
    # Nos aseguramos de que solo usamos las columnas que existen
    merged_df = merged_df[[col for col in columnas_fisicas if col in merged_df.columns]].copy()


    merged_df.fillna(merged_df.median(numeric_only=True), inplace=True)
    
    
    # merged_df = merged_df.fillna(merged_df.mean(numeric_only=True))


    available_cols = [col for col in merged_df.columns if col in ponderations]
    weights = pd.Series({col: ponderations[col] for col in available_cols})

    # Normalizamos pesos para que sumen 1
    if weights.sum() != 0:
        weights = weights / weights.sum()

    # IMPORTANTE: Alineamos las columnas del DF con el índice de los pesos para evitar el error
    df_to_score = merged_df[weights.index]
    
    # Producto punto (Score base)
    merged_df["score"] = df_to_score.dot(weights)

    # Normalización del score de 0 a 100
    min_score = merged_df["score"].min()
    max_score = merged_df["score"].max()

    if max_score != min_score:
        merged_df["score"] = 100 * (merged_df["score"] - min_score) / (max_score - min_score)
    else:
        merged_df["score"] = 50 # Valor por defecto si todos son iguales

    # --- ASIGNACIÓN DE LETRAS Y RANKING ---
    
    def get_letter(score):
        if score > 75: return "A"
        if score > 50: return "B"
        if score > 25: return "C"
        return "D"
    
    merged_df["letter"] = merged_df["score"].apply(get_letter)
    merged_df["Ranking"] = merged_df["score"].rank(method="dense", ascending=False).astype(int)
    
    
    # Buscar los datos del jugador analizado
    try:
        player_row = merged_df[merged_df["Jugador"] == PLAYER_NAME].iloc[0]
        
        raw_score = player_row["score"]
        player_letter = player_row["letter"]
        playerranking = player_row["Ranking"]
        
        # Invertir el score para que 1 sea el mejor si es lo que buscas, 
        # o mantener el percentil/posición
        player_score_final = int(1 + (number_of_players_position - 1) * (1 - (raw_score / 100)))
        
        return player_score_final, player_letter, number_of_players_position, playerranking

    except IndexError:
        print(f"Error: No se encontró al jugador {PLAYER_NAME} en el CSV físico.")
        return 0, "-", number_of_players_position, 0
    
    


#notas_tacticas("Portero","/Users/julieta/Desktop/APP_Fuenla/data/2Division_wyscout_2025.xlsx","/Users/julieta/Desktop/APP_Fuenla/report_gen/parameters.xlsx",2,100)



