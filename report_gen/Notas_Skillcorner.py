#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  6 13:52:45 2025

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
from skillcorner.client import SkillcornerClient

def notas_fisicas(PLAYER_POSITION,PLAYER_NAME,parameters_file,min_minutos,folder_path):
    
    percentages_file="/Users/julieta/Desktop/WYSCOUT/physical_percentages.xlsx"
    
    dictionary_positions={"Delantero":"Center Forward","Defensa":"Central Defender",
                          "Centrocampista ofensivo":"Midfield","Centrocampista defensivo":"Midfield",
                          "Lateral":"Full Back","Extremo":"Wide Attacker"}

    position_skillcorner=dictionary_positions[PLAYER_POSITION]


    percentages=pd.read_excel(percentages_file,sheet_name=position_skillcorner)

    df_phys=pd.read_csv(f"{folder_path}/SkillCorner-physical-2025-04-24.csv",delimiter=";")
    df_pressure=pd.read_csv(f"{folder_path}/SkillCorner-pressure-2025-04-24.csv",delimiter=";")
    df_passing=pd.read_csv(f"{folder_path}/SkillCorner-passing-2025-04-24.csv",delimiter=";")
    df_offball=pd.read_csv(f"{folder_path}/SkillCorner-offball-2025-04-24.csv",delimiter=";")
    
    
    
    df_phys[df_phys.select_dtypes(include='number').columns] = df_phys.select_dtypes(include='number').apply(lambda col: col.fillna(col.mean()))

    df_pressure[df_pressure.select_dtypes(include='number').columns] = df_pressure.select_dtypes(include='number').apply(lambda col: col.fillna(col.mean()))

    df_passing[df_passing.select_dtypes(include='number').columns] = df_passing.select_dtypes(include='number').apply(lambda col: col.fillna(col.mean()))


    df_offball[df_offball.select_dtypes(include='number').columns] = df_offball.select_dtypes(include='number').apply(lambda col: col.fillna(col.mean()))
    player_position=df_phys[df_phys["Short Name"]==PLAYER_NAME]["Position Group"].iloc[0]
    if position_skillcorner!=player_position:
        position_skillcorner=player_position
    #print(position_skillcorner)
    df_phys=df_phys[df_phys["Position Group"]==position_skillcorner]
    df_pressure=df_pressure[df_pressure["Position Group"]==position_skillcorner]
    df_passing=df_passing[df_passing["Position Group"]==position_skillcorner]
    df_offball=df_offball[df_offball["Position Group"]==position_skillcorner]


    phys=df_phys[["Short Name","PSV-99", "Distance P90","HI Distance P90", "HI Count P90","Medium Acceleration Count P90","High Acceleration Count P90"]]

    client = SkillcornerClient(username="jmbuldu@gmail.com", password="Complexity01*")
    data = client.get_in_possession_off_ball_runs(params={'competition': 133, 
                                                          'season': 95,
                                                          'playing_time__gte': 60,
                                                          'count_match__gte': 8,
                                                          'average_per': '30_min_tip',
                                                          'group_by': 'player,competition,team,group',
                                                          'run_type': 'all,run_in_behind,run_ahead_of_the_ball,'
                                                                     'support_run,pulling_wide_run,coming_short_run,'
                                                                     'underlap_run,overlap_run,dropping_off_run,'
                                                                     'pulling_half_space_run,cross_receiver_run'})

    df_runs = pd.DataFrame(data)
    df_runs=df_runs[df_runs["group"]==position_skillcorner]

    runs_cols=["short_name",'count_cross_receiver_runs_per_30_min_tip',
        'count_runs_in_behind_per_30_min_tip',
        'count_runs_ahead_of_the_ball_per_30_min_tip',
        'count_overlap_runs_per_30_min_tip',
        'count_underlap_runs_per_30_min_tip',
        'count_support_runs_per_30_min_tip',
        'count_coming_short_runs_per_30_min_tip',
        'count_dropping_off_runs_per_30_min_tip',
        'count_pulling_half_space_runs_per_30_min_tip',
        'count_pulling_wide_runs_per_30_min_tip']

    df_runs=df_runs[runs_cols]

    merged_df = pd.merge(phys, df_runs, left_on="Short Name", right_on="short_name", how="left")

    merged_df.drop("short_name",axis=1,inplace=True)
    merged_df.fillna(merged_df.median(numeric_only=True), inplace=True)
    
    
    # merged_df = merged_df.fillna(merged_df.mean(numeric_only=True))


    ponderations=percentages.set_index("Datos")["Importancia"].to_dict()

    cols=[col for col in merged_df.columns if col in ponderations]

    weights=pd.Series({col: ponderations[col] for col in cols})

    weights=weights/weights.sum()

    merged_df["score"]=merged_df[cols].dot(weights)

    min_score=merged_df["score"].min()
    max_score=merged_df["score"].max()

    merged_df["score"]=100*(merged_df["score"]-min_score)/(max_score - min_score)
    
    number_of_players_position=len(merged_df)
    for i,row in merged_df.iterrows():
        if merged_df.loc[i,"score"]>75:
            merged_df.loc[i,"letter"]="A"
        elif 50<merged_df.loc[i,"score"]<=75:
            merged_df.loc[i,"letter"]="B"
        elif 25<merged_df.loc[i,"score"]<=50:
            merged_df.loc[i,"letter"]="C"
        elif merged_df.loc[i,"score"]<=25:
            merged_df.loc[i,"letter"]="D"
        else:
            merged_df.loc[i,"letter"]="-"
    #print("Se queda pillado aqui?")
    merged_df["score"] = merged_df["score"].replace([np.inf, -np.inf], np.nan)
    merged_df["score"]=merged_df["score"].fillna(0)
    merged_df["Ranking"] = merged_df["score"].rank(method="dense", ascending=False).astype(int)
    # print(merged_df["Short Name"].unique())
    # print(PLAYER_NAME)
    player_score=round(float(merged_df[merged_df["Short Name"]==PLAYER_NAME]["score"].iloc[0]),2)
    player_letter=merged_df[merged_df["Short Name"]==PLAYER_NAME]["letter"].iloc[0]
    player_score=int(1+(number_of_players_position-1)*(1-(player_score/100)))
    playerranking=merged_df[merged_df["Short Name"]==PLAYER_NAME]["Ranking"].iloc[0]

    return player_score,player_letter,number_of_players_position, playerranking


