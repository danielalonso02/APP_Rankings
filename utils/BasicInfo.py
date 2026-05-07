#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 22 10:55:39 2025

@author: julieta
"""
import pandas as pd
import numpy as np



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
from colorsys import rgb_to_hls
import argparse
class PlayerNotFoundError(Exception):
    pass
def basic_info_player(wyscout_file,player_id_analizing,min_minutos):
   
    try:
        df_stats = pd.read_excel(wyscout_file)
        
        
    except FileNotFoundError:
        print(f"Error: El archivo '{wyscout_file}' no existe.")
        return None,None,None,None, None, None, None, None
    #pongo el player_id para cada jugado, los identificaremos con esto
    #print(f"COLUMNAS: {df_stats.columns}")
    df_stats = df_stats.reset_index(drop=True)
    df_stats["player_id"] = df_stats.index + 2
    #filtramos por minutos jugados la base de datos
    df_stats=df_stats[df_stats["Minutos jugados"]>=min_minutos]
    
    if df_stats.empty:
        print(f"No hay jugadoras con más de {min_minutos} minutos jugados.")

        raise PlayerNotFoundError(f"No hay jugadoras con más de {min_minutos} minutos jugados.")

        #return None

    if player_id_analizing not in df_stats["player_id"].values:
        
        raise PlayerNotFoundError(
            f"La jugadora elegida, {player_id_analizing}, no está en la base de datos o ha jugado menos de {min_minutos}."
        )
       
        #return None
    df_stats.fillna(df_stats.mean(numeric_only=True),inplace=True)
    
    positions_dict={"GK":"portero","LB":"lateral","RB":"lateral","DMF":"defmid","OF":"ofmid",
                    "AMF":"ofmid","LCB":"defensa","RCB":"defensa","LWF":"extremo","RWF":"extremo",
                    "LAMF":"ofmid","RAMF":"ofmid","LCMF":"ofmid","RCMF":"ofmid","CF":"delantero",
                    "CB":"defensa","RW":"extremo","LDMF":"defmid","LW":"extremo","RDMF":"defmid",
                    }
    positions=["portero","defensa","defmid","ofmid","lateral","delantero","extremo"]
    
    
    #con esta funcion se mapean las posiciones especificas a las generales
    def map_positions(positions_str):
        positions = positions_str.split(", ")  
        general_positions = [positions_dict.get(pos, pos) for pos in positions]  
        unique_positions = set(general_positions)  
        return ", ".join(unique_positions)  # Unir las posiciones únicas

    df_stats["general_position"] = df_stats["Posición específica"].apply(map_positions)

    df_stats[['general_position', 'general_position2',"general_position3"]] = df_stats['general_position'].str.split(", ", n=2, expand=True)
    market_value_col = "Valor de mercado (Transfermarkt)" if "Valor de mercado (Transfermarkt)" in df_stats.columns else "Valor de mercado"

    general_stats=df_stats[["player_id","Jugador","Equipo","Equipo durante el período seleccionado","Edad",market_value_col,"Vencimiento contrato","Partidos jugados","Minutos jugados",'general_position', 'general_position2',"general_position3"]].copy()
    
    general_stats_player=general_stats[general_stats["player_id"]==player_id_analizing]
    if general_stats_player.empty:
        raise PlayerNotFoundError(
            f"La jugadora elegida, {player_id_analizing}, no está en la base de datos o ha jugado menos de {min_minutos}."
            )
    player_name=general_stats_player["Jugador"]
    
    player_team=general_stats_player["Equipo"]
    
    loan_team=general_stats_player["Equipo durante el período seleccionado"]
    
    player_age=general_stats_player["Edad"]
    
    player_minutes=general_stats_player["Minutos jugados"]
    player_pos1=general_stats_player["general_position"]
    player_pos2=general_stats_player["general_position2"]
    player_pos3=general_stats_player["general_position3"]
    return (
        player_name.values[0],
        player_team.values[0],
        loan_team.values[0],
        player_age.values[0],
        player_minutes.values[0],
        player_pos1.values[0],
        player_pos2.values[0],
        player_pos3.values[0]
        )   
player_name, player_team, loan_team, player_age, player_minutes, player_pos1, player_pos2, player_pos3=basic_info_player("/Users/danie/Desktop/APP_Generic_Femeni/data/LigaF_wyscout_2025.xlsx",78,100)