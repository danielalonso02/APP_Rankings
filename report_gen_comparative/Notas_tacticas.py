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
from IntentoArrays import extract_arrays_wyscout_notas
import warnings
warnings.simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

def notas_tacticas(PLAYER_POSITION,filepath_excel,parameters_file,player_id_analizing,min_minutos):
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
    PLAYER_POSITION = PLAYER_POSITION.lower()
    percentages_file="datoswyscout/wyscout_positions_porcentajes.xlsx"
    dict_excels={"portero":"portero","defensa":"defensa","lateral":"lateral",
                 "centrocampista defensivo":"centrocampista_defensivo",
                 "centrocampista ofensivo":"centrocampista_ofensivo",
                 "extremo":"extremo","delantero":"delantero_centro"}

    position_excel=dict_excels[PLAYER_POSITION]

    excel_path=f"datoswyscout/variables_wyscout_{position_excel}.xlsx"

    df_ponderations=pd.read_excel(excel_path)

    df_ponderations = df_ponderations.rename(columns={0: "ofensive", "0.1": "defensive"})

    df_ponderations = df_ponderations[~((df_ponderations["ofensive"] == 0) & (df_ponderations["defensive"] == 0))]

    _, _, _, _,df_all_stats,_,_ = extract_arrays_wyscout_notas(
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
    df_stats_position[numeric_cols_pos] = (df_stats_position[numeric_cols_pos] - df_stats_position[numeric_cols_pos].min()) / (df_stats_position[numeric_cols_pos].max() - df_stats_position[numeric_cols_pos].min())
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
    #print(of_weights)
    df_stats_position[cols_of] = df_stats_position[cols_of].fillna(0)
    df_stats_position["OF_score"]=df_stats_position[cols_of].dot(of_weights)

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

    for i,row in df_stats_position.iterrows():
        if df_stats_position.loc[i,"DEF_score"]>75:
            df_stats_position.loc[i,"DEF_letter"]="A"
        elif 50<df_stats_position.loc[i,"DEF_score"]<=75:
            df_stats_position.loc[i,"DEF_letter"]="B"
        elif 25<df_stats_position.loc[i,"DEF_score"]<=50:
            df_stats_position.loc[i,"DEF_letter"]="C"
        elif df_stats_position.loc[i,"DEF_score"]<=25:
            df_stats_position.loc[i,"DEF_letter"]="D"


    for i,row in df_stats_position.iterrows():
        if df_stats_position.loc[i,"OF_score"]>75:
            df_stats_position.loc[i,"OF_letter"]="A"
        elif 50<df_stats_position.loc[i,"OF_score"]<=75:
            df_stats_position.loc[i,"OF_letter"]="B"
        elif 25<df_stats_position.loc[i,"OF_score"]<=50:
            df_stats_position.loc[i,"OF_letter"]="C"
        elif df_stats_position.loc[i,"OF_score"]<=25:
            df_stats_position.loc[i,"OF_letter"]="D"

    player_of_score=float(df_stats_position[df_stats_position["player_id"]==player_id_analizing]["OF_score"].iloc[0])
    

    player_def_score=float(df_stats_position[df_stats_position["player_id"]==player_id_analizing]["DEF_score"].iloc[0])
   
    player_of_letter=df_stats_position[df_stats_position["player_id"]==player_id_analizing]["OF_letter"].iloc[0]

    player_def_letter=df_stats_position[df_stats_position["player_id"]==player_id_analizing]["DEF_letter"].iloc[0]

    df_percentages=pd.read_excel(percentages_file)

    df_percentages=df_percentages[["grupo","Defensivo","Ofensivo"]]

    percentages_of=float(df_percentages[df_percentages["grupo"]==position_excel]["Ofensivo"].iloc[0])
    percentages_def=float(df_percentages[df_percentages["grupo"]==position_excel]["Defensivo"].iloc[0])

    df_stats_position["Full_score"]=(percentages_of/100)*df_stats_position["OF_score"]+(percentages_def/100)*df_stats_position["DEF_score"]

    for i,row in df_stats_position.iterrows():
        if df_stats_position.loc[i,"Full_score"]>75:
            df_stats_position.loc[i,"Full_letter"]="A"
        elif 50<df_stats_position.loc[i,"Full_score"]<=75:
            df_stats_position.loc[i,"Full_letter"]="B"
        elif 25<df_stats_position.loc[i,"Full_score"]<=50:
            df_stats_position.loc[i,"Full_letter"]="C"
        elif df_stats_position.loc[i,"Full_score"]<=25:
            df_stats_position.loc[i,"Full_letter"]="D"
    
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
    
    # print(f"FULL SCORE: {player_full_score}")
    # print(f"FULL LETTER: {player_full_letter}")
    return player_of_score,player_of_letter,player_def_score,player_def_letter,player_full_score,player_full_letter,number_of_players_position,Rank_of,Rank_def,Rank_full

# PLAYER_POSITION="Delantero"
# filepath_excel="/Users/julieta/Desktop/WYSCOUT/datoswyscout/espana_3_2025_2025_26_03.xlsx"
# parameters_file="/Users/julieta/Desktop/parameters.xlsx"
# player_id_analizing=522
# min_minutos=600
# of_score,of_letter,def_score,def_letter=notas_tacticas(PLAYER_POSITION,filepath_excel,parameters_file,player_id_analizing,min_minutos)

#player_of_score,player_of_letter,player_def_score,player_def_letter,player_full_score,player_full_letter,number_of_players_position,Rank_of,Rank_def,Rank_full=notas_tacticas("Delantero","/Users/julieta/Downloads/datos_entrada.xlsx","/Users/julieta/Desktop/Creacion_Report_Jugadores/parameters.xlsx",2,600)








