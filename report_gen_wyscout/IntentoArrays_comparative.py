# -*- coding: utf-8 -*-
"""
Created on Fri Apr 10 12:24:39 2026

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
import os

"""
        WYSCOUT DATA
"""

positions_dict = {
    "GK":"portera","LB":"lateral","RB":"lateral","DMF":"defmid","OF":"ofmid",
    "AMF":"ofmid","LCB":"defensa","RCB":"defensa","LWF":"extremo","RWF":"extremo",
    "LAMF":"ofmid","RAMF":"ofmid","LCMF":"ofmid","RCMF":"ofmid","CF":"delantera",
    "CB":"defensa","RW":"extremo","LDMF":"defmid","LW":"extremo","RDMF":"defmid",
    "RWB":"lateral","LWB":"lateral"
}

def map_positions(positions_str):
    positions = str(positions_str).split(", ")
    general_positions = [positions_dict.get(pos, pos) for pos in positions]
    seen = []
    for p in general_positions:
        if p not in seen:
            seen.append(p)
    return ", ".join(seen)

def load_and_prepare_df(wyscout_file, min_minutes):
    """Carga un Excel de wyscout, asigna IDs y mapea posiciones."""
    df = pd.read_excel(wyscout_file)
    for i, row in df.iterrows():
        df.loc[i, "player_id"] = i + 2
    df = df[df["Minutos jugados"] > min_minutes]
    df["general_position"] = df["Posición específica"].apply(map_positions)
    df[['general_position', 'general_position2', 'general_position3']] = (
        df['general_position'].str.split(", ", n=2, expand=True)
    )
    df.fillna(df.mean(numeric_only=True), inplace=True)
    return df

def get_player_positions(player_row):
    """Devuelve la lista de posiciones generales de una jugadora, sin nulos."""
    cols = ["general_position", "general_position2", "general_position3"]
    return [str(player_row[c]) for c in cols
            if player_row[c] and str(player_row[c]) not in ("None", "nan")]

def calculate_percentiles(df, cols):
    """Calcula percentiles para cada columna dentro del df dado."""
    df_res = df.copy()
    for col in cols:
        values = df[col].values
        df_res[col] = [percentileofscore(values, x, kind='rank') for x in values]
    return df_res


def extract_arrays_wyscout(wyscout_file1, wyscout_file2, parameters_file, player_id1, player_id2,
                           param_entry, min_minutes):
    """
    Extrae arrays comparativos para dos jugadoras.

    Si wyscout_file2 es igual a wyscout_file1, ambas jugadoras vienen
    del mismo Excel (misma liga).
    Si wyscout_file2 es distinto, cada jugadora tiene su propio Excel y los
    percentiles se calculan contra su propia liga.
    """
    same_league = (wyscout_file2 == wyscout_file1)

    # Validar ficheros
    for f in [wyscout_file1, wyscout_file2, parameters_file]:
        if not os.path.exists(f):
            print(f"Error: Fichero no encontrado: {f}")
            return [None] * 9

    # Cargar dataframes
    df1 = load_and_prepare_df(wyscout_file1, min_minutes)
    df2 = load_and_prepare_df(wyscout_file2, min_minutes)

    # Filas de cada jugadora
    p1_matches = df1[df1["player_id"] == player_id1]
    p2_matches = df2[df2["player_id"] == player_id2]

    if p1_matches.empty or p2_matches.empty:
        print(f"Error: No se encontró player_id1={player_id1} o player_id2={player_id2}.")
        return [None] * 9

    player1_row = p1_matches.iloc[0]
    player2_row = p2_matches.iloc[0]

    # Buscar posición compartida
    p1_positions = get_player_positions(player1_row)
    p2_positions = get_player_positions(player2_row)

    shared_position = None
    for pos in p1_positions:
        if pos in p2_positions:
            shared_position = pos
            break

    if not shared_position:
        print(f"[ERROR] COMPARATIVA IMPOSIBLE")
        print(f"  {player1_row['Jugador']} juega de: {p1_positions}")
        print(f"  {player2_row['Jugador']} juega de: {p2_positions}")
        print(f"  No comparten ninguna posición general para comparar percentiles.")
        return [None] * 9

    player_position = shared_position
    print(f"Validado: Comparando a {player1_row['Jugador']} vs {player2_row['Jugador']} en posición {player_position}")

    # Cargar parámetros
    df_p = pd.read_excel(parameters_file, sheet_name=player_position)
    params_config = {
        "ofensive":     df_p['ofensivo'].dropna().tolist(),
        "defensive":    df_p['defensivo'].dropna().tolist(),
        "of_number":    df_p["PizzaPlot_of"].dropna().tolist(),
        "ofensive_es":  [s.replace("\\n", "") for s in df_p['ofensivo es'].dropna().tolist()],
        "defensive_es": [s.replace("\\n", "") for s in df_p['defensivo es'].dropna().tolist()]
    }

    all_cols = list(set(params_config["ofensive"] + params_config["defensive"]))

    # Selección de columnas según param_entry
    param_of1, param_of2, param_of1_es, param_of2_es = [], [], [], []
    for i, p in enumerate(params_config["ofensive"]):
        if params_config["of_number"][i] == 1:
            param_of1.append(p)
            param_of1_es.append(params_config["ofensive_es"][i])
        else:
            param_of2.append(p)
            param_of2_es.append(params_config["ofensive_es"][i])

    if param_entry == "param_of1":
        cols, cols_es = param_of1, param_of1_es
    elif param_entry == "param_of2":
        cols, cols_es = param_of2, param_of2_es
    else:
        cols, cols_es = params_config["defensive"], params_config["defensive_es"]

    # Población de cada liga filtrada por posición compartida
    def filter_by_position(df, pos):
        return df[(df["general_position"] == pos) |
                  (df["general_position2"] == pos) |
                  (df["general_position3"] == pos)].copy()

    df_pos1 = filter_by_position(df1, player_position)
    df_pos2 = filter_by_position(df2, player_position)

    # Percentiles: cada jugadora contra su propia liga
    df_perc1 = calculate_percentiles(df_pos1, all_cols)
    df_perc2 = calculate_percentiles(df_pos2, all_cols)

    p1_perc = df_perc1[df_perc1["player_id"] == player_id1][cols].values.flatten().tolist()
    p2_perc = df_perc2[df_perc2["player_id"] == player_id2][cols].values.flatten().tolist()

    # Valores reales
    p1_val = player1_row[cols]
    p2_val = player2_row[cols]

    # Min/max combinando ambas ligas para escala común en las barras
    # Aplicamos offset a los IDs de df2 para evitar colisiones con df1
    offset = int(df1["player_id"].max()) + 100
    df2_offset = df2.copy()
    df2_offset["player_id"] = df2_offset["player_id"] + offset
    player_id2_combined = player_id2 + offset

    df_stats_combined = pd.concat([df1, df2_offset], ignore_index=True)
    min_arr = df_stats_combined[cols].min()
    max_arr = df_stats_combined[cols].max()

    return min_arr, max_arr, p1_val, p2_val, cols, df_stats_combined, p1_perc, p2_perc, cols_es, player_id2_combined
