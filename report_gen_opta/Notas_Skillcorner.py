# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 11:50:55 2026

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
from report_gen_opta.IntentoArrays_Opta import extract_arrays_wyscout
import warnings
from skillcorner.client import SkillcornerClient
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

import unicodedata
import re

import pandas as pd
import numpy as np
import warnings
import unicodedata
import re
import os
from fuzzywuzzy import process # Asegúrate de tenerlo instalado: pip install fuzzywuzzy

warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 

def normalize(x):
    if pd.isna(x): return ""
    x = str(x)
    x = unicodedata.normalize("NFKD", x)
    x = x.encode("ascii", "ignore").decode("ascii")
    x = x.upper()
    x = re.sub(r"\s+", " ", x).strip()
    return x

def notas_fisicas(PLAYER_POSITION, df_position, PLAYER_NAME, parameters_file, min_minutos, folder_path, player_id_analizing):
    try:
        df_phys = pd.read_csv(f"{folder_path}/SkillCorner-2026-03-30.csv", delimiter=";", encoding="latin1")
    except FileNotFoundError:
        print("Error: El archivo no existe.")
        return None, None, None, None

    # 1. Preparación inicial
    df_phys = df_phys.rename(columns={'Player': 'player_name'})
    df_phys['player_name'] = df_phys['player_name'].apply(normalize)
    PLAYER_NAME_NORM = normalize(PLAYER_NAME)

    dictionary_positions = {"Goalkeeper": "goalkeeper", "Defender": "defender", "Midfielder": "midfielder", "Forward": "forward"}
    pos_to_filter = dictionary_positions.get(PLAYER_POSITION, PLAYER_POSITION)

    # Filtrar por posición en el DF físico si las columnas existen
    if "Position Group" in df_phys.columns:
        df_phys = df_phys[df_phys["Position Group"] == pos_to_filter]
    elif "Position" in df_phys.columns:
        df_phys = df_phys[df_phys["Position"] == pos_to_filter]

    # 2. Obtener jugadoras de la misma posición desde Opta
    # (Asumimos que extract_arrays_wyscout funciona correctamente)
    from report_gen_opta.IntentoArrays_Opta import extract_arrays_wyscout
    _, _, _, _, df_all_stats, _, _ = extract_arrays_wyscout(df_position, parameters_file, player_id_analizing, "param_of1", min_minutos)
    
    df_all_stats['player_name'] = df_all_stats['player_name'].apply(normalize)
    stats_player = df_all_stats[df_all_stats["player_id"] == player_id_analizing].iloc[0]
    player_position = stats_player["position"]
    df_stats_position = df_all_stats[df_all_stats["position"] == player_position].copy()
    
    number_of_players_position = len(df_stats_position)
    players_in_pos = df_stats_position[["player_name"]].drop_duplicates().copy()

    # 3. FUZZY MATCHING (Cruce inteligente)
    def find_best_match(name, list_to_search):
        if not list_to_search: return None
        match, score = process.extractOne(name, list_to_search)
        return match if score > 70 else None

    nombres_skillcorner = df_phys['player_name'].tolist()
    players_in_pos['player_name_phys'] = players_in_pos['player_name'].apply(lambda x: find_best_match(x, nombres_skillcorner))

    # 4. MERGE (Cruce de datos)
    columnas_fisicas = ["player_name", "PSV-99", "Running Distance P90", "HSR Distance P90",
                        "Sprint Distance P90", "HI Count P90", "Medium Acceleration Count P90",
                        "High Acceleration Count P90", "Medium Deceleration Count P90",
                        "High Deceleration Count P90", "Explosive Acceleration to Sprint Count P90"]
    
    # Cruzamos usando la columna de match de SkillCorner
    merged_df = pd.merge(
        players_in_pos, 
        df_phys[columnas_fisicas], 
        left_on="player_name_phys", 
        right_on="player_name", 
        how="left",
        suffixes=('', '_phys_extra')
    )

    # 5. CÁLCULO DE SCORES (Normalización y Pesos)
    # Rellenamos vacíos con la mediana para no penalizar en exceso a las no encontradas
    merged_df.fillna(merged_df.median(numeric_only=True), inplace=True)

    # Cargar porcentajes/importancia
    position_excel = dictionary_positions[PLAYER_POSITION]
    percentages = pd.read_excel(f"{BASE_DIR}/report_gen_opta/datoswyscout/physical_percentages.xlsx", sheet_name=position_excel)
    ponderations = percentages.set_index("Datos")["Importancia"].to_dict()

    available_cols = [col for col in merged_df.columns if col in ponderations]
    weights = pd.Series({col: ponderations[col] for col in available_cols})
    
    if weights.sum() != 0:
        weights = weights / weights.sum()

    # ESCALADO CRÍTICO (Scaling 0-1)
    df_scaled = merged_df[weights.index].copy()
    denom = (df_scaled.max() - df_scaled.min()).replace(0, 1)
    df_scaled = (df_scaled - df_scaled.min()) / denom

    # Cálculo Score Final (0-100)
    merged_df["score"] = df_scaled.dot(weights) * 100
    
    # Asegurar rango 0-100 real
    if merged_df["score"].max() != merged_df["score"].min():
        merged_df["score"] = 100 * (merged_df["score"] - merged_df["score"].min()) / (merged_df["score"].max() - merged_df["score"].min())

    # 6. ASIGNACIÓN DE LETRAS Y RANKING
    def get_letter(score):
        if score > 75: return "A"
        if score > 50: return "B"
        if score > 25: return "C"
        return "D"

    merged_df["letter"] = merged_df["score"].apply(get_letter)
    merged_df["Ranking"] = merged_df["score"].rank(method="min", ascending=False).astype(int)

    # 7. RESULTADOS FINALES
    try:
        # Buscamos por el nombre original normalizado (el de Opta)
        player_row = merged_df[merged_df["player_name"] == PLAYER_NAME_NORM].iloc[0]
        
        raw_score = player_row["score"]
        player_letter = player_row["letter"]
        playerranking = player_row["Ranking"]
        
        # Player score final (escala invertida para ranking visual si se requiere)
        player_score_final = int(1 + (number_of_players_position - 1) * (1 - (raw_score / 100)))
        
        return player_score_final, player_letter, number_of_players_position, playerranking

    except Exception as e:
        print(f"Error al procesar jugadora {PLAYER_NAME}: {e}")
        return 0, "-", number_of_players_position, 0
    
    


#notas_tacticas("Portero","/Users/julieta/Desktop/APP_Fuenla/data/2Division_wyscout_2025.xlsx","/Users/julieta/Desktop/APP_Fuenla/report_gen/parameters.xlsx",2,100)



