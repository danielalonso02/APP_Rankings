#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 24 12:55:39 2025

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
        WYSCOUT DATA
"""

def extract_arrays_wyscout2(wyscout_file,parameters_file,player_id_analizing,param_entry,min_minutes):
    
    if not os.path.exists(wyscout_file):
        print(f"El fichero {wyscout_file} no existe.")
        return None
    if not os.path.exists(parameters_file):
        print(f"El fichero {parameters_file} no existe.")
        return None
    df_stats=pd.read_excel(wyscout_file)
    for i,row in df_stats.iterrows():
        df_stats.loc[i,"player_id"]=i+2
    df_stats=df_stats[df_stats["Minutos jugados"]>min_minutes]
    positions_dict={"GK":"portero","LB":"lateral","RB":"lateral","DMF":"defmid","OF":"ofmid",
                     "AMF":"ofmid","LCB":"defensa","RCB":"defensa","LWF":"extremo","RWF":"extremo",
                     "LAMF":"ofmid","RAMF":"ofmid","LCMF":"ofmid","RCMF":"ofmid","CF":"delantero",
                     "CB":"defensa","RW":"extremo","LDMF":"defmid","LW":"extremo","RDMF":"defmid",
                     "RWB":"lateral","LWB":"lateral"
                     }

    positions=["portero","defensa","defmid","ofmid","lateral","delantero","extremo"]
    parameters = {}
    for position in positions:
        try:
            df_position = pd.read_excel(parameters_file, sheet_name=position)

            # Crear un diccionario con las claves 'ofensive' y 'defensive' y los valores correspondientes
            parameters[position] = {
                "ofensive": df_position['ofensivo'].dropna().tolist(),  # Convertir la columna 'ofensivo' en lista
                "defensive": df_position['defensivo'].dropna().tolist(),  # Convertir la columna 'defensivo' en lista
                "of_number": df_position["PizzaPlot_of"].dropna().tolist(),
                "ofensive_es":df_position['ofensivo es'].dropna().tolist(),
                "defensive_es":df_position['defensivo es'].dropna().tolist(),
            }
        except Exception as e:
            print(f"Error al procesar la posición {position}: {e}")
        except ValueError:
            print(f"Hoja '{position}' no encontrada en el archivo.")
    #con esta funcion se mapean las posiciones especificas a las generales
    def map_positions(positions_str):
        positions = positions_str.split(", ")  
        general_positions = [positions_dict.get(pos, pos) for pos in positions]  
        unique_positions = set(general_positions)  
        return ", ".join(unique_positions)  # Unir las posiciones únicas

    df_stats["general_position"] = df_stats["Posición específica"].apply(map_positions)
    #aqui terminamos de mapear las posiciones
    df_stats[['general_position', 'general_position2',"general_position3"]] = df_stats['general_position'].str.split(", ", n=2, expand=True)
    df_stats.fillna(df_stats.mean(numeric_only=True),inplace=True)
    df_stats["general_position2"] = df_stats["general_position2"].fillna("None")
    df_stats["general_position3"] = df_stats["general_position3"].fillna("None")

    df_general_stats=df_stats[["Jugador","Equipo","Equipo durante el período seleccionado","Edad","Valor de mercado","Vencimiento contrato","Partidos jugados","Minutos jugados","player_id",'general_position', 'general_position2',"general_position3"]].copy()
    general_stats_player=df_general_stats[df_general_stats["player_id"]==player_id_analizing].iloc[0]
    stats_player=df_stats[df_stats["player_id"]==player_id_analizing].iloc[0]
    player_position=general_stats_player["general_position"]
    player_name=general_stats_player["Jugador"]
    df_stats_position=df_stats[(df_stats["general_position"]==player_position) | (df_stats["general_position2"]==player_position) | (df_stats["general_position3"]==player_position)].copy()
    df_stats_position_nums=df_stats_position.copy()
    #print(df_stats_position["general_position"])
    param_ofensive=parameters[player_position]["ofensive"]
    param_of_idioma=parameters[player_position]["ofensive_es"]
    
    param_of_idioma = [item.replace("\\n", "") for item in param_of_idioma]
    param_defensive=parameters[player_position]["defensive"]
    of_number=parameters[player_position]["of_number"]
    param_def_id=parameters[player_position]["defensive_es"]
    param_def_id = [item.replace("\\n", "") for item in param_def_id]
    param_ofensive1 = []
    param_ofensive2 = []
    min_array=[]
    max_array=[]
    player_array=[]
    params_array=[]
    all_params=param_ofensive+param_defensive   
    # Dividir los parámetros ofensivos según el valor de of_number
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
    
    ####
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
        average_array=df_stats_position_nums[param_ofensive1].mean(axis=0)
        player_array=stats_player[param_ofensive1]
        params_array=param_ofensive1
        percentiles_player=df_stats_percentile[param_ofensive1].values.flatten().tolist()
        param_en=param_of1_id
        
    elif param_entry=="param_of2":
        min_array=df_stats[param_ofensive2].min(axis=0)
        max_array=df_stats[param_ofensive2].max(axis=0)
        average_array=df_stats_position_nums[param_ofensive2].mean(axis=0)
        player_array=stats_player[param_ofensive2]
        params_array=param_ofensive2
        percentiles_player=df_stats_percentile[param_ofensive2].values.flatten().tolist()
        param_en=param_of2_id
    elif param_entry=="param_def":
        min_array=df_stats[param_defensive].min(axis=0)
        max_array=df_stats[param_defensive].max(axis=0)
        average_array=df_stats_position_nums[param_defensive].mean(axis=0)
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


# min_of2, max_of2, player_of2, param_of2, df_all ,percentiles_of2,paramof2_en= extract_arrays_wyscout(
#     "/Users/julieta/Desktop/WYSCOUT/datoswyscout/espana_3_2025_2025_26_03.xlsx","/Users/julieta/Desktop/parameters_en.xlsx",
#     262,
#     "param_of2",500
# )