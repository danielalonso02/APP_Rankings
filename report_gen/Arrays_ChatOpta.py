#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 15 15:07:23 2025

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
import os
"""

        OPTA DATA
    
"""

def extract_arrays_wyscout2(df_position,parameters_file,player_id_analizing,param_entry,min_minutes):
    df_stats=df_position
    df_stats=df_stats[df_stats["Time Played"]>min_minutes]
    positions=["Goalkeeper","Defender","Midfielder","Forward"]
    parameters = {}
    for position in positions:
        try:
            
            df_positions = pd.read_excel("/Users/julieta/Desktop/APP_Generic_Femeni/report_gen/parameters.xlsx", sheet_name=position)
            
            
            # Crear un diccionario con las claves 'ofensivo' y 'defensivo' y los valores correspondientes
            parameters[position] = {
                "ofensive": df_positions['ofensivo'].dropna().tolist(),  # Convertir la columna 'ofensivo' en lista
                "ofensive es":df_positions['ofensivo es'].dropna().tolist(),
                "defensive": df_positions['defensivo'].dropna().tolist(),  # Convertir la columna 'defensivo' en lista
                "defensive es":df_positions['defensivo es'].dropna().tolist(),
                "of_number":df_positions["PizzaPlot_of"].dropna().tolist()
            }
        except ValueError:
            print(f"Hoja '{position}' no encontrada en el archivo.")
        except Exception as e:
            print(f"Error al leer la hoja '{position}': {e}")

    df_general_stats=df_stats[["player_name","team_name","age","Appearances","Time Played","weight","height","player_id","position"]].copy()
    player_name=df_general_stats[df_general_stats["player_id"]==player_id_analizing]["player_name"].iloc[0]
    general_stats_player=df_general_stats[df_general_stats["player_id"]==player_id_analizing].iloc[0]
    stats_player=df_stats[df_stats["player_id"]==player_id_analizing].iloc[0]
    player_position=general_stats_player["position"]
    df_stats_position=df_stats[(df_stats["position"]==player_position)].copy()
    #print(df_stats_position["general_position"])
    param_ofensive=parameters[player_position]["ofensive"]
    param_of_idioma=parameters[player_position]["ofensive es"]

    param_of_idioma = [item.replace("\\n", "") for item in param_of_idioma]
    param_defensive=parameters[player_position]["defensive"]
    of_number=parameters[player_position]["of_number"]
    param_def_id=parameters[player_position]["defensive es"]
    param_def_id = [item.replace("\\n", "") for item in param_def_id]
    param_ofensive1 = []
    param_ofensive2 = []
    min_array=[]
    max_array=[]
    player_array=[]
    params_array=[]
    all_params=param_ofensive+param_defensive   

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
    df_stats_percentile=calculate_and_assign_percentiles(df_stats_position, parameters[player_position]["defensive"], parameters[player_position]["ofensive"])
    df_stats_percentile=df_stats_percentile[df_stats_percentile["player_id"]==player_id_analizing]


    param_of1_id=[]
    param_of2_id=[]
    for i, param in enumerate(param_ofensive):
        if of_number[i] == 1:
            param_ofensive1.append(param)
        elif of_number[i] == 2:
            param_ofensive2.append(param)
    for i,param in enumerate(param_of_idioma):
        if of_number[i] == 1:
            param_of1_id.append(param)
        elif of_number[i] == 2:
            param_of2_id.append(param)
    if param_entry=="param_of1":
        min_array=df_stats[param_ofensive1].min(axis=0)
        max_array=df_stats[param_ofensive1].max(axis=0)
        average_array=df_stats[param_ofensive1].mean(axis=0)
        player_array=stats_player[param_ofensive1]
        params_array=param_ofensive1
        percentiles_player=df_stats_percentile[param_ofensive1].values.flatten().tolist()
        param_en=param_of1_id
        
    elif param_entry=="param_of2":
        min_array=df_stats[param_ofensive2].min(axis=0)
        max_array=df_stats[param_ofensive2].max(axis=0)
        average_array=df_stats[param_ofensive2].mean(axis=0)
        player_array=stats_player[param_ofensive2]
        params_array=param_ofensive2
        percentiles_player=df_stats_percentile[param_ofensive2].values.flatten().tolist()
        param_en=param_of2_id
    elif param_entry=="param_def":
        min_array=df_stats[param_defensive].min(axis=0)
        max_array=df_stats[param_defensive].max(axis=0)
        average_array=df_stats[param_defensive].mean(axis=0)
        player_array=stats_player[param_defensive]
        params_array=param_defensive
        percentiles_player=df_stats_percentile[param_defensive].values.flatten().tolist()
        param_en=param_def_id
    else:
        min_array=None
        max_array=None
        average_array=None
        player_array=None
        params_array=None
        percentiles_player=None
        param_en=None
        
    return player_array,average_array,player_name,player_position,params_array

