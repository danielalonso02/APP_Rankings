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
import os
import warnings
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
def notas_tacticas(PLAYER_POSITION,filepath_excel,parameters_file,player_id_analizing,min_minutos,pesos_favorito=None):
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
    # Mapeo: posición del informe → hoja en pesos_scouting.xlsx / fila en pesos_scouting_global.xlsx
    MAP_POSICION = {
        "Portera":                  ("Portero",                  "Portero"),
        "Defensa":                  ("Defensa central",           "Defensa central"),
        "Lateral":                  ("Lateral",                   "Lateral"),
        "Centrocampista defensivo": ("Mediocampista defensivo",   "Mediocampista defensivo"),
        "Centrocampista ofensivo":  ("Mediocampista ofensivo",    "Mediocampista ofensivo"),
        "Extremo":                  ("Extremo",                   "Extremo"),
        "Delantera":                ("Delantero",                 "Delantero centro"),
    }
    posicion_hoja, posicion_global = MAP_POSICION.get(
        PLAYER_POSITION, ("Defensa central", "Defensa central")
    )

    # Rutas — mismo directorio base que rankings.py (report_gen_opta/datoswyscout/)
    _base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "report_gen_opta", "datoswyscout")
    ruta_pesos        = os.path.join(_base, "pesos_scouting.xlsx")
    ruta_pesos_macro  = os.path.join(_base, "pesos_scouting_global.xlsx")

    # COL_MAP igual que rankings.py: columna Excel → categoría interna
    COL_MAP = {"ATAQUE": "ofensive", "DEFENSA": "defensive", "TÉCNICA": "tecnico", "FÍSICO": "fisico"}

    # Mapeo: nombre en pesos_scouting.xlsx → columna real en el Excel Wyscout
    RENAME_MAP_WYSCOUT = {
        "Goles /90":                    "Goles/90",
        "xG /90":                       "xG/90",
        "Asistencias /90":              "Asistencias/90",
        "xA /90":                       "xA/90",
        "Remates totales /90":          "Remates/90",
        "Remates a puerta /90":         "Remates/90",
        "Pases clave /90":              "Jugadas claves/90",
        "Regates exitosos /90":         "Regates/90",
        "Centros exitosos /90":         "Centros/90",
        "Toques en área rival /90":     "Toques en el área de penalti/90",
        "Interceptaciones /90":         "Interceptaciones/90",
        "Entradas ganadas /90":         "Entradas/90",
        "Faltas cometidas /90":         "Faltas/90",
        "Faltas recibidas /90":         "Faltas recibidas/90",
        "Faltas recibidad /90":         "Faltas recibidas/90",
        "Pases exitosos /90":           "Pases/90",
        "Pases largos exitosos /90":    "Pases largos/90",
        "Pases en campo rival /90":     "Pases en el último tercio/90",
        "Carries progresivos /90":      "Carreras en progresión/90",
        "Segundas asistencias /90":     "Second assists/90",
        "Balones al hueco /90":         "Pases en profundidad/90",
        "Duelos totales /90":           "Duelos/90",
        "Duelos aéreos totales /90":    "Duelos aéreos en los 90",
        "Duelos ganados /90":           "Duelos ganados, %",
        "Duelos aéreos ganados /90":    "Duelos aéreos ganados, %",
        "Duelos en suelo ganados /90":  "Duelos defensivos/90",
        "Grandes ocasiones creadas /90":"Acciones de ataque exitosas/90",
        "Ocasiones falladas /90":       "Acciones de ataque exitosas/90",
        "Despejes /90":                 "Tiros interceptados/90",
        "Recuperaciones /90":           "Acciones defensivas realizadas/90",
        "Bloqueos /90":                 "Tiros interceptados/90",
        "Pérdidas de balón /90":        "Acciones defensivas realizadas/90",
    }

    def _cargar_pesos_micro(ruta, posicion):
        df_p = pd.read_excel(ruta, sheet_name=posicion)
        df_p.columns = df_p.columns.str.strip()
        df_p["VARIABLE"] = df_p["VARIABLE"].str.strip()
        df_p = df_p.set_index("VARIABLE")
        rows = []
        for col_xlsx, cat in COL_MAP.items():
            if col_xlsx not in df_p.columns:
                continue
            for variable, valor in df_p[col_xlsx].items():
                if pd.notna(valor) and valor != 0:
                    col_wyscout = RENAME_MAP_WYSCOUT.get(variable, variable)
                    rows.append({"Jugador": col_wyscout, cat: float(valor)})
        if not rows:
            return pd.DataFrame(columns=["Jugador", "ofensive", "defensive"])
        df = pd.DataFrame(rows).groupby("Jugador", as_index=False).sum()
        for c in ["ofensive", "defensive", "tecnico", "fisico"]:
            if c not in df.columns:
                df[c] = 0
        return df[~((df["ofensive"] == 0) & (df["defensive"] == 0))]

    def _cargar_pesos_macro(ruta, posicion_desc):
        df_m = pd.read_excel(ruta)
        df_m.columns = df_m.columns.str.strip()
        fila = df_m[df_m["description"] == posicion_desc].iloc[0]
        return {
            "Ofensivo":  float(fila["Ofensivo"]),
            "Defensivo": float(fila["Defensivo"]),
        }

    if pesos_favorito is not None:
        # Usar pesos micro del JSON del favorito (keys: "slider_Ofensivo_Goles /90", etc.)
        micro = pesos_favorito.get("micro", {})
        rows = []
        for key, valor in micro.items():
            parts = key.split("_", 2)
            if len(parts) != 3:
                continue
            categoria = parts[1]   # Ofensivo, Defensivo, Técnico, Físico
            variable  = parts[2]   # nombre en pesos_scouting → traducir a columna Wyscout
            cat_col   = {"Ofensivo": "ofensive", "Defensivo": "defensive",
                         "Técnico": "tecnico", "Físico": "fisico"}.get(categoria)
            if cat_col is None:
                continue
            col_wyscout = RENAME_MAP_WYSCOUT.get(variable, variable)
            rows.append({"Jugador": col_wyscout, cat_col: float(valor)})
        if rows:
            df_ponderations = pd.DataFrame(rows).groupby("Jugador", as_index=False).sum()
            for c in ["ofensive", "defensive", "tecnico", "fisico"]:
                if c not in df_ponderations.columns:
                    df_ponderations[c] = 0
            df_ponderations = df_ponderations[~((df_ponderations["ofensive"] == 0) & (df_ponderations["defensive"] == 0))]
        else:
            df_ponderations = _cargar_pesos_micro(ruta_pesos, posicion_hoja)
    else:
        df_ponderations = _cargar_pesos_micro(ruta_pesos, posicion_hoja)
    
   
    
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
    
    of_list = df_ponderations[df_ponderations['ofensive'] != 0]['Jugador'].tolist()
    
    of_stats=df_all_stats[of_list]

    ponderaciones_OF=df_stats_position

    def_list=df_ponderations[df_ponderations['defensive'] != 0]['Jugador'].tolist()
    

    def_stats=df_all_stats[def_list]

    of_ponderations=df_ponderations.set_index("Jugador")["ofensive"].to_dict()
   

    cols_of=[col for col in df_stats_position.columns if col in of_ponderations]

    of_weights=pd.Series({col: of_ponderations[col] for col in cols_of})
    

    of_weights=of_weights/of_weights.sum()

    df_stats_position["OF_score"]=df_stats_position[cols_of].dot(of_weights)
    #print(df_stats_position["OF_score"])

    min_score=df_stats_position["OF_score"].min()
    max_score=df_stats_position["OF_score"].max()
    
    df_stats_position["OF_score"]=100*(df_stats_position["OF_score"]-min_score)/(max_score - min_score)
    
    #DEFENSIVE
    def_ponderations=df_ponderations.set_index("Jugador")["defensive"].to_dict()

    cols_def=[col for col in df_stats_position.columns if col in def_ponderations]

    def_weights=pd.Series({col: def_ponderations[col] for col in cols_def})

    def_weights=def_weights/def_weights.sum()

    df_stats_position["DEF_score"]=df_stats_position[cols_def].dot(def_weights)

    min_score=df_stats_position["DEF_score"].min()
    max_score=df_stats_position["DEF_score"].max()

    df_stats_position["DEF_score"]=100*(df_stats_position["DEF_score"]-min_score)/(max_score - min_score)
    
    #df_stats_position.to_excel("dfstatsposition.xlsx")
    #hasta aqui vamos bien
    def assign_letter(percentile):
        if percentile > 75:
            return "A"   
        elif percentile > 50:
            return "B"   
        elif percentile > 25:
            return "C"   
        else:
            return "D"  
    
    
    df_stats_position["DEF_percentile"] = df_stats_position["DEF_score"].rank(pct=True) * 100
    
    df_stats_position["DEF_letter"] = df_stats_position["DEF_percentile"].apply(assign_letter)
    
    df_stats_position["OF_percentile"] = df_stats_position["OF_score"].rank(pct=True) * 100
    
    df_stats_position["OF_letter"] = df_stats_position["OF_percentile"].apply(assign_letter)
    
    
    
    # for i,row in df_stats_position.iterrows():
    #     if df_stats_position.loc[i,"DEF_score"]>75:
    #         df_stats_position.loc[i,"DEF_letter"]="A"
    #     elif 50<df_stats_position.loc[i,"DEF_score"]<=75:
    #         df_stats_position.loc[i,"DEF_letter"]="B"
    #     elif 25<df_stats_position.loc[i,"DEF_score"]<=50:
    #         df_stats_position.loc[i,"DEF_letter"]="C"
    #     elif df_stats_position.loc[i,"DEF_score"]<=25:
    #         df_stats_position.loc[i,"DEF_letter"]="D"


    # for i,row in df_stats_position.iterrows():
    #     if df_stats_position.loc[i,"OF_score"]>75:
    #         df_stats_position.loc[i,"OF_letter"]="A"
    #     elif 50<df_stats_position.loc[i,"OF_score"]<=75:
    #         df_stats_position.loc[i,"OF_letter"]="B"
    #     elif 25<df_stats_position.loc[i,"OF_score"]<=50:
    #         df_stats_position.loc[i,"OF_letter"]="C"
    #     elif df_stats_position.loc[i,"OF_score"]<=25:
    #         df_stats_position.loc[i,"OF_letter"]="D"

    player_of_score=float(df_stats_position[df_stats_position["player_id"]==player_id_analizing]["OF_score"].iloc[0])
    

    player_def_score=float(df_stats_position[df_stats_position["player_id"]==player_id_analizing]["DEF_score"].iloc[0])

    player_of_letter=df_stats_position[df_stats_position["player_id"]==player_id_analizing]["OF_letter"].iloc[0]

    player_def_letter=df_stats_position[df_stats_position["player_id"]==player_id_analizing]["DEF_letter"].iloc[0]

    if pesos_favorito is not None and "global" in pesos_favorito:
        glob = pesos_favorito["global"]
        w_of  = float(glob.get("Ofensivo", 0.5))
        w_def = float(glob.get("Defensivo", 0.5))
        total = w_of + w_def if (w_of + w_def) > 0 else 1.0
        percentages_of  = (w_of  / total) * 100
        percentages_def = (w_def / total) * 100
    else:
        # Usar pesos_scouting_global.xlsx igual que rankings.py
        macro = _cargar_pesos_macro(ruta_pesos_macro, posicion_global)
        total = macro["Ofensivo"] + macro["Defensivo"] if (macro["Ofensivo"] + macro["Defensivo"]) > 0 else 1.0
        percentages_of  = (macro["Ofensivo"] / total) * 100
        percentages_def = (macro["Defensivo"] / total) * 100

    df_stats_position["Full_score"]=(percentages_of/100)*df_stats_position["OF_score"]+(percentages_def/100)*df_stats_position["DEF_score"]
    df_stats_position["Full_percentile"] = df_stats_position["Full_score"].rank(pct=True) * 100
    
    df_stats_position["Full_letter"] = df_stats_position["Full_percentile"].apply(assign_letter)

    
    df_stats_position["Rank_of"]=df_stats_position["OF_score"].rank(method="dense", ascending=False).astype(int)
    df_stats_position["Rank_def"]=df_stats_position["DEF_score"].rank(method="dense", ascending=False).astype(int)
    df_stats_position["Rank_full"]=df_stats_position["Full_score"].rank(method="dense", ascending=False).astype(int)
    
    
    player_full_score=float(df_stats_position[df_stats_position["player_id"]==player_id_analizing]["Full_score"].iloc[0])

    player_full_letter=df_stats_position[df_stats_position["player_id"]==player_id_analizing]["Full_letter"].iloc[0]
    
    # player_of_score=int(1+(number_of_players_position-1)*(1-(player_of_score/100)))
    # player_def_score=int(1+(number_of_players_position-1)*(1-(player_def_score/100)))
    # player_full_score=int(1+(number_of_players_position-1)*(1-(player_full_score/100)))
    
    df_stats_position["OF_rank"] = df_stats_position["OF_score"].rank(method='first', ascending=False).astype(int)
    Rank_of=int(df_stats_position[df_stats_position["player_id"] == player_id_analizing]["OF_rank"].iloc[0])
    
    df_stats_position["DEF_rank"] = df_stats_position["DEF_score"].rank(method='first', ascending=False).astype(int)
    Rank_def=int(df_stats_position[df_stats_position["player_id"] == player_id_analizing]["DEF_rank"].iloc[0])
    
    df_stats_position["Full_rank"] = df_stats_position["Full_score"].rank(method='first', ascending=False).astype(int)
    Rank_full= int(df_stats_position[df_stats_position["player_id"] == player_id_analizing]["Full_rank"].iloc[0])
    
    # Rank_of=df_stats_position[df_stats_position["player_id"]==player_id_analizing]["Rank_of"].iloc[0]
    # Rank_def=df_stats_position[df_stats_position["player_id"]==player_id_analizing]["Rank_def"].iloc[0]
    # Rank_full=df_stats_position[df_stats_position["player_id"]==player_id_analizing]["Rank_full"].iloc[0]
    
    
    return player_of_score,player_of_letter,player_def_score,player_def_letter,player_full_score,player_full_letter,number_of_players_position,Rank_of,Rank_def,Rank_full


#notas_tacticas("Portera","/Users/julieta/Desktop/APP_Fuenla/data/2Division_wyscout_2025.xlsx","/Users/julieta/Desktop/APP_Fuenla/report_gen/parameters.xlsx",2,100)



