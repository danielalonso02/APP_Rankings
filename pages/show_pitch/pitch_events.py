#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 13 12:35:15 2025

@author: julieta
"""
import streamlit as st
from utils import login
from utils import util
import pandas as pd
import subprocess
import os
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import sys
import traceback
import requests
import json
import glob
import base64
import tempfile
from pathlib import Path
import shlex
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler


from mplsoccer import Radar, FontManager, grid
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup

from urllib.request import urlopen
from PIL import Image, UnidentifiedImageError, ImageDraw
from mplsoccer import PyPizza, add_image, Pitch, VerticalPitch

from highlight_text import fig_text
import xml.etree.ElementTree as ET
from matplotlib.colors import LinearSegmentedColormap
import imageio
from matplotlib.animation import FuncAnimation
from functools import partial
import matplotlib.lines as mlines
import warnings
from highlight_text import ax_text
import cmasher as cmr
import networkx as nx
from matplotlib.colors import to_rgba
import matplotlib.patheffects as path_effects
from matplotlib import rcParams
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.patches import FancyArrowPatch
import igraph as ig
import math
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D
from matplotlib.patches import Circle
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
import mplsoccer
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.image as mpimg

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

ruta_script = os.path.join(BASE_DIR, "report_gen", "Report_2RFEF_FINAL.py")
Report = "Report_2RFEF_FINAL.py"
directorio_logs=os.path.join(BASE_DIR,"logs")
ruta_parameters=os.path.join(BASE_DIR,"report_gen","parameters.xlsx")
ruta_script_pizza=os.path.join(BASE_DIR,"report_gen","PizzaWyscout.py")
ruta_excel=os.path.join(BASE_DIR,"data","2RFEF_wyscout_2024.xlsx")
ruta_excel2=os.path.join(BASE_DIR,"data")
script_report_team=os.path.join(BASE_DIR,"report_gen_teams","Report_Equipo.py")
folder_equipos=os.path.join(BASE_DIR,"report_gen_teams","datos_equipos")
ruta_reports_wyscout=os.path.join(BASE_DIR,"report_gen_teams","wyscout_report")
Report_equipos="Report_Equipo.py"
directorio_base = os.path.dirname(ruta_script)
parameters_route_xlsx=os.path.join(BASE_DIR,"report_gen","parameters.xlsx")
ruta_opta_f40=os.path.join(BASE_DIR,"data_femeni","raw","f40","f40-squad-102.xml")
ruta_opta_f42=os.path.join(BASE_DIR,"data_femeni","raw","f42","f42-903-2025-results.xml")
ruta_excel_players=os.path.join(BASE_DIR,"data_femeni","players_relations.xlsx")
ruta_excel_matches=os.path.join(BASE_DIR,"data_femeni","matches_relations.xlsx")
def extract_end_coordinates(qualifiers):
    end_x = None
    end_y = None
    if isinstance(qualifiers, list):  # Asegurar que la celda contiene una lista
        for item in qualifiers:
            if item.get("qualifier_id") == "140":
                end_x = float(item.get("value", 0))  # Convertir a float si existe
            elif item.get("qualifier_id") == "141":
                end_y = float(item.get("value", 0))
    return pd.Series([end_x, end_y])
def ensure_and_convert_columns(events: pd.DataFrame) -> pd.DataFrame:
    """
    Asegura que ciertas columnas existan en el DataFrame 'events'.
    Si existen, las convierte a numérico con string_to_numeric.
    Si no existen, las crea vacías (NaN).
    Retorna el DataFrame modificado.
    """
    # Lista de columnas a asegurar
    cols = ['min', 'sec', 'x', 'y', '102', '103', '146', '147', 'outcome']

    for col in cols:
        if col in events.columns:
            events[col] = string_to_numeric(events[col])
        else:
            events[col] = 0  # crea columna vacía

    return events
def string_to_numeric(x):
    return pd.to_numeric(x, errors='coerce')

def parse_f70_events(xml_filename):

    import xml.etree.ElementTree as ET
    
    # Define functions to be used

    
    
    ## Pick the Maximum (non-NA) Values
    
    def pick_out_the_maximum_values(qualifier_values):
        
        max_values = []
        for c in range(qualifier_values.shape[1]):
            col_2_test = qualifier_values.iloc[:, c]
            max_val = col_2_test.dropna().iloc[0]
            max_values.append(max_val)
        results_Q = pd.DataFrame([max_values], columns=qualifier_values.columns)
        return results_Q
    
    ## The Main Unpacking Function
    
    def convert_event_node_row(xml_2_spread):
      
        ## convert the info in the event node header into a dataframe 
        results = pd.DataFrame(xml_2_spread['attrs'], index=[0])
    
        ## find the number of qualifiers for this event 
        no_of_qualifiers = len(xml_2_spread['value'])
        
        if no_of_qualifiers > 0:
            ## create a list of qualifiers 
            Qualifier_Unpacked_Step1 = pd.DataFrame()
        
            ## loop through each qualifer and pull out the info then bind it to the results .. above 
            for Q in range(no_of_qualifiers):
                Qualifier_unpacked = xml_2_spread['value'][Q]

                Value = 1 if 'value' not in Qualifier_unpacked.keys() else Qualifier_unpacked["value"]
                temp = pd.DataFrame({"Q": [str(Value)]}, dtype=str)
                temp.columns = [Qualifier_unpacked["qualifier_id"]]
                Qualifier_Unpacked_Step1 = pd.concat([Qualifier_Unpacked_Step1, temp], axis=0, ignore_index=True)
            
            ## keep the maximum values in the dataframe (the only none NA values) return as a 
            ## dataframe for use 
            Qualifier_unpacked_df = pick_out_the_maximum_values(Qualifier_Unpacked_Step1)
        
            results = pd.concat([results, Qualifier_unpacked_df], axis=1)
        
        return results
    
    # Read in the XML File
    pbpParse = ET.parse(xml_filename)
    
    
  
    # Split the XML File
    all_event_nodes = []
    for event in pbpParse.findall('.//Game/Event'):
        event_attrs = event.attrib
        event_values = [child.attrib for child in list(event)]
        all_event_nodes.append({'attrs': event_attrs, 'value': event_values})
  
    # Convert all events and store in a dataframe
    events = pd.concat([convert_event_node_row(e) for e in all_event_nodes], ignore_index=True)
      
    
    # Add player names to events
    players = {}
    player_name = None
    for i, team in enumerate(pbpParse.findall('.//Team')):
        team_code = int(team.get('uID')[1:])
        players[f'team{i+1}_code'] = team_code
        players[f'playert{i+1}'] = [{'code': int(player.get('uID')[1:]), 'position': player.get('Position'), 'name': player.find('.//PersonName/First').text + ' ' + player.find('.//PersonName/Last').text} for player in team.findall('Player')]
    
    for idx, event in events.iterrows():
        team_code = event['team_id']
        j = 1 if team_code == str(players[f'team{1}_code']) else 2
        for player in players[f'playert{j}']:
            if player['code'] == int(event['player_id']):
                player_name = player['name']
                break
        events.at[idx, 'player_name'] = player_name

    # Convert strings to numerics

    events = ensure_and_convert_columns(events)
    return events 
def parse_f73_possesionchain(filepath_f73):
    if not filepath_f73 or not os.path.exists(filepath_f73):
        print("Error: El archivo especificado no existe.")
        return None
    tree = ET.parse(filepath_f73)
    root = tree.getroot()
    data=[]
    game = root.find("Game")
    game_data = {attr: game.attrib[attr] for attr in game.attrib}
    df_game = pd.DataFrame([game_data])
    team_names=df_game[["home_team_id","home_team_name","away_team_id","away_team_name"]]
    home_team=team_names["home_team_name"][0]
    home_id=team_names["home_team_id"][0]
    away_team=team_names["away_team_name"][0]
    away_id=team_names["away_team_id"][0]

    
    
    # Extraer eventos
    event_list = []
    for event in game.findall("Event"):
        event_data = {attr: event.attrib[attr] for attr in event.attrib}

        qualifiers = []
        for qualifier in event.findall("Q"):
            qualifiers.append({attr: qualifier.attrib[attr] for attr in qualifier.attrib})

        event_data["qualifiers"] = qualifiers  
        event_list.append(event_data)
        
    df_events = pd.DataFrame(event_list)
    df_events=df_events.drop(["last_modified","version"],axis=1)
    df_events["keypass"]=df_events["keypass"].fillna(0)
    df_events[['id', 'event_id', 'type_id', 'period_id', 'min', 'sec', 'team_id','outcome', 'x', 'y','player_id','keypass', 'sequence_id', 'possession_id']]=df_events[['id',
                                                                                                                                                                                                                                                                                                    'event_id', 'type_id', 'period_id', 'min', 'sec', 'team_id','outcome', 'x', 'y',"player_id",'keypass', 'sequence_id', 'possession_id']].astype(float)
    df_events["time_minutes"] = df_events["min"] + df_events["sec"] / 60  
    df_events[["timestamp", "timestamp_utc"]] = df_events[["timestamp", "timestamp_utc"]].apply(pd.to_datetime)
    teams = pd.concat([
    team_names[['home_team_id', 'home_team_name']].rename(columns={'home_team_id': 'team_id', 'home_team_name': 'team_name'}),
    team_names[['away_team_id', 'away_team_name']].rename(columns={'away_team_id': 'team_id', 'away_team_name': 'team_name'})
    ]).drop_duplicates()
    teams["team_id"]=teams["team_id"].astype(float)
    
    df_events = df_events.merge(teams, on="team_id", how="left")
    team1, team2 = df_events.team_name.unique()
    df_pass=df_events[df_events["type_id"]==1]
    df_pass=df_pass[df_pass["outcome"]==1]
    
    def extract_end_coordinates(qualifiers):
        end_x = None
        end_y = None
        if isinstance(qualifiers, list):  # Asegurar que la celda contiene una lista
            for item in qualifiers:
                if item.get("qualifier_id") == "140":
                    end_x = float(item.get("value", 0))  # Convertir a float si existe
                elif item.get("qualifier_id") == "141":
                    end_y = float(item.get("value", 0))
        return pd.Series([end_x, end_y])
    
    # Aplicamos la función y creamos nuevas columnas
    df_pass[["end_x", "end_y"]] = df_pass["qualifiers"].apply(extract_end_coordinates)

    df_pass=df_pass[["x","y","end_x","end_y","team_id","team_name","possession_id","type_id","time_minutes"]]
    #me quedo solo con las que pertenecen a un 

    df_pass=df_pass[df_pass["possession_id"].notna()]
    
    return df_pass,team_names
def parse_f24(file_path_24):
    if not os.path.exists(file_path_24):
        print(f"Error: El archivo '{file_path_24}' no existe.")
        return None, None
    
    tree = ET.parse(file_path_24)
    root = tree.getroot()
 
   
    game = root.find("Game")
    game_data = {attr: game.attrib[attr] for attr in game.attrib}
    df_game = pd.DataFrame([game_data])
    team_names = df_game[["home_team_id", "home_team_name", "away_team_id", "away_team_name"]]
    
    event_list = []
    for event in game.findall("Event"):
        event_data = {attr: event.attrib[attr] for attr in event.attrib} 
        qualifiers = [{attr: qualifier.attrib[attr] for attr in qualifier.attrib} for qualifier in event.findall("Q")]
        event_data["qualifiers"] = qualifiers  
        event_list.append(event_data)
    
    df_events = pd.DataFrame(event_list).drop(["last_modified", "version"], axis=1)
    df_events["keypass"] = df_events["keypass"].fillna(0)
    df_events = df_events.astype({"id": float, "event_id": float, "type_id": float, "period_id": float,
                                  "min": float, "sec": float, "team_id": float, "outcome": float,
                                  "x": float, "y": float, "player_id": float, "keypass": float})
    
    teams = pd.concat([
        team_names[['home_team_id', 'home_team_name']].rename(columns={'home_team_id': 'team_id', 'home_team_name': 'team_name'}),
        team_names[['away_team_id', 'away_team_name']].rename(columns={'away_team_id': 'team_id', 'away_team_name': 'team_name'})
    ]).drop_duplicates().astype({"team_id": float})
    
    df_events = df_events.merge(teams, on="team_id", how="left")
    df_events[["timestamp", "timestamp_utc"]] = df_events[["timestamp", "timestamp_utc"]].apply(pd.to_datetime)
    df_events["first_qualifier_id"] = df_events["qualifiers"].apply(lambda q: q[0]["qualifier_id"] if q else None).astype(float)
    return df_events,team_names

def get_goals(file_path_24):
    df_events,team_names=parse_f24(file_path_24)
    goals=df_events[df_events["type_id"]==16]
    home_id=team_names["home_team_id"].iloc[0]
    away_id=team_names["away_team_id"].iloc[0]
    goals["local_goals"] = (goals["team_id"] == int(home_id)).cumsum()
    goals["visitor_goals"] = (goals["team_id"] == int(away_id)).cumsum()
    print(goals.columns)
    home_goals = (goals["team_id"] == int(home_id)).sum()
    away_goals = (goals["team_id"] == int(away_id)).sum()
    goals["resultado"] = goals["local_goals"].astype(str) + "-" + goals["visitor_goals"].astype(str)
    goals["time_minutes"] = goals["min"] + goals["sec"] / 60
    goals=goals[["time_minutes","resultado"]]
    
    return goals,home_goals,away_goals

def show_page():
    if "db_initialized" not in st.session_state:
        try:
            #st.write("Running create_player_db...")
            util.create_player_db(ruta_opta_f40)
            #st.write("Running calendar...")
            util.calendar(ruta_opta_f42)
            st.session_state.db_initialized = True
            #st.success("DB initialized!")
        except Exception as e:
            st.error(f"Error initializing DB: {e}")

    df_players=pd.read_excel(ruta_excel_players)
    df_matches=pd.read_excel(ruta_excel_matches)
    directorio_equipos=os.path.join(BASE_DIR,"report_gen_teams","datos_equipos")

    # Asegura existencia de la carpeta de logs
    os.makedirs(directorio_logs, exist_ok=True)



    matches_dict=dict(zip(df_matches["game"],df_matches["matchcode"]))
    match=st.selectbox("Partido",list(matches_dict.keys()))
    match_id=matches_dict[match]
    ruta_opta_f24=os.path.join(BASE_DIR,"data_femeni","raw","f24",f"f24-903-2025-{match_id}-eventdetails.xml")

    def parse_f24_cached(file_path_24):
        return util.parse_f24(file_path_24)
    df_events, team_names = util.parse_f24(ruta_opta_f24)
    #st.write(team_names)
    home_team=team_names["home_team_name"].iloc[0]
    home_id=team_names["home_team_id"].iloc[0]
    away_team=team_names["away_team_name"].iloc[0]
    away_id=team_names["away_team_id"].iloc[0]


    col1, col2, col3, col4 = st.columns([1.5,1.5,1.5,1.5])
    with col1:
        type_id = util.select_data_opta()
    with col2:
        teams_select=[home_team,away_team,"Ambos"]
        team=st.selectbox("Equipo",teams_select)
    with col3:
        if team==home_team:
            df_jugadoras=df_players[(df_players["team"]==home_team) ]
            lista_jugadoras=df_jugadoras["player"].tolist()
            dict_jugadoras=dict(zip(df_jugadoras["player"],df_jugadoras["player_id"]))
            new_entry = {'Todas': 0}
            sorted_rest = dict(sorted(dict_jugadoras.items()))
            new_dict = {**new_entry, **sorted_rest}
            player=st.selectbox("Jugadora",list(new_dict.keys()))
            player_id=new_dict[player]
        elif team==away_team:
            df_jugadoras=df_players[(df_players["team"]==away_team)]
            lista_jugadoras=df_jugadoras["player"].tolist()
            dict_jugadoras=dict(zip(df_jugadoras["player"],df_jugadoras["player_id"]))
            new_entry = {'Todas': 0}
            sorted_rest = dict(sorted(dict_jugadoras.items()))
            new_dict = {**new_entry, **sorted_rest}
            player=st.selectbox("Jugadora",list(new_dict.keys()))
            player_id=new_dict[player]
        else:
            df_jugadoras=df_players[(df_players["team"]==home_team) | (df_players["team"]==away_team)]
            player_id=0
            

    def stringify(i:int = 0) -> str:
        return slider_strings[i-1]
    if type_id==1:
        st.write("## Tercio de comienzo y fin de los pases")
        col1,col2=st.columns([1,1])
        slider_values = [1,2,3,4]
        slider_strings = ["Todo el campo","Primer tercio", "Segundo tercio", "Último tercio"]
        
        with col1:
            
            start_third=st.slider("Principio del pase",min_value=0.0,
                                  max_value=100.0,value=(0.0,100.0),step=33.33)

            
        with col2:
            
            end_third=st.slider("Fin del pase",min_value=0.0,
                                  max_value=100.0,value=(0.0,100.0),step=33.33)


        st.write("## Bandas")
        col1,col2=st.columns([1,1])
        slider_values2 = [1,2,3]
        slider_strings= ["Sin bandas","Banda izquierda", "Banda derecha"]
        
        with col1:
            st.write('Banda:')
            sideline_left = st.checkbox('Banda izquierda')
            sideline_right = st.checkbox('Banda derecha')
            
            if sideline_right==True and sideline_left==True:
                start_sideline="Both"
            elif sideline_right==True:
                start_sideline="Right"
            elif sideline_left==True:
                start_sideline="Left"
            else:
                start_sideline="None"

    else:
        col1,col2=st.columns([1,1])
        slider_values = [1,2,3,4]
        slider_strings = ["Todo el campo","Primer tercio", "Segundo tercio", "Último tercio"]
        with col1:
            start_third=st.slider("Principio del pase",min_value=0.0,
                                  max_value=100.0,value=(0.0,100.0),step=33.33)
        st.write("## Bandas")
        col1,col2=st.columns([1,1])
        slider_values2 = [1,2,3]
        slider_strings= ["Sin bandas","Banda izquierda", "Banda derecha"]
        
        with col1:
            st.write('Banda:')
            sideline_left = st.checkbox('Banda izquierda')
            sideline_right = st.checkbox('Banda derecha')
            
            if sideline_right==True and sideline_left==True:
                start_sideline="Both"
            elif sideline_right==True:
                start_sideline="Right"
            elif sideline_left==True:
                start_sideline="Left"
            else:
                start_sideline="None"

                

    st.markdown(f"# <font color='blue'>{home_team} </font> vs <font color='red'>{away_team}</font>",unsafe_allow_html=True)
    
    if type_id!=16:
        df_specific_event=df_events[df_events["type_id"]==type_id]

    if type_id==1:
        df_specific_event[["end_x", "end_y"]] = df_specific_event["qualifiers"].apply(util.extract_end_coordinates)
        df_specific_event=util.filter_actions_passes(df_specific_event,start_third,end_third,start_sideline)
        if team==home_team:
            df_specific_event=df_specific_event[df_specific_event["team_name"]==home_team]
            
            
            
            if player_id!=0:
                df_specific_event=df_specific_event[df_specific_event["player_id"]==player_id]
                
            pitch = Pitch(pitch_type="opta", pad_bottom=0.5, goal_type='box', goal_alpha=0.8)
            fig, ax = pitch.draw(figsize=(12, 10))
            pitch.arrows(df_specific_event.x, df_specific_event.y,
                      df_specific_event.end_x, df_specific_event.end_y,
                      width=2,headwidth=10, headlength=10,
                      color='blue', ax=ax, label='passes')
            #ax.arrow(40, -2, 20, 0, head_width=2, head_length=2, fc='black', ec='black')
            ax.text(50, -5, "Dirección de ataque →", ha='center', va='top', fontsize=12, fontweight='bold')

            st.pyplot(fig)
            
        elif team==away_team:
            df_specific_event=df_specific_event[df_specific_event["team_name"]==away_team]
            df_specific_event["x"]=100-df_specific_event["x"]
            df_specific_event["y"]=100-df_specific_event["y"]
            df_specific_event["end_x"]=100-df_specific_event["end_x"]
            df_specific_event["end_y"]=100-df_specific_event["end_y"]
            if player_id!=0:
                df_specific_event=df_specific_event[df_specific_event["player_id"]==player_id]
            pitch = Pitch(pitch_type="opta", pad_bottom=0.5, goal_type='box', goal_alpha=0.8)
            fig, ax = pitch.draw(figsize=(12, 10))
            pitch.arrows(df_specific_event.x, df_specific_event.y,
                      df_specific_event.end_x, df_specific_event.end_y,
                      width=2,headwidth=10, headlength=10,
                      color='red', ax=ax, label='passes')
            #ax.arrow(40, -2, 20, 0, head_width=2, head_length=2, fc='black', ec='black')
            ax.text(50, -5, "⬅️ Dirección de ataque ", ha='center', va='top', fontsize=12, fontweight='bold')

            st.pyplot(fig)
        else:
            df_home=df_specific_event[df_specific_event["team_name"]==home_team]
            df_away=df_specific_event[df_specific_event["team_name"]==away_team]
            df_away["x"]=100-df_away["x"]
            df_away["y"]=100-df_away["y"]
            df_away["end_x"]=100-df_away["end_x"]
            df_away["end_y"]=100-df_away["end_y"]
            pitch = Pitch(pitch_type="opta", pad_bottom=0.5, goal_type='box', goal_alpha=0.8)
            fig, ax = pitch.draw(figsize=(12, 10))
            pitch.arrows(df_home.x, df_home.y,
                      df_home.end_x, df_home.end_y,
                      width=2,headwidth=10, headlength=10,
                      color='blue', ax=ax, label='passes')
            pitch.arrows(df_away.x, df_away.y,
                      df_away.end_x, df_away.end_y,
                      width=2,headwidth=10, headlength=10,
                      color='red', ax=ax, label='passes')
            st.pyplot(fig)
            
    elif type_id==16:
        goals,home_goals,away_goals=get_goals(ruta_opta_f24)
        filepath_f70=f"{BASE_DIR}/data_femeni/raw/f70/f70-903-2025-{match_id}-expectedgoals.xml"
        events=parse_f70_events(filepath_f70)
        shot_events = events[events['type_id'].isin(['13', '14', '15', '16'])]
        shot_events["team_id"]=shot_events["team_id"].astype(int)
        shot_events["time_minutes"]=shot_events["min"]+shot_events["sec"]/60
        shot_events["321"]=shot_events["321"].astype(float)

        shot_events=shot_events[["time_minutes","team_id","321"]]
        shot_events_home=shot_events[shot_events["team_id"]==int(home_id)]
        shot_events_away=shot_events[shot_events["team_id"]==int(away_id)]

        shot_events_home["cumulative"]=shot_events_home["321"].cumsum()
        shot_events_away["cumulative"]=shot_events_away["321"].cumsum()
        total_xg_home=shot_events_home["cumulative"].max()
        total_xg_away=shot_events_away["cumulative"].max()
        
        shot_events = events[events['type_id'].isin(['13', '14', '15', '16'])]
        shot_events["type_id"]=shot_events["type_id"].astype(int)
        shot_events["321"]=shot_events["321"].astype(float)
        ####
        ruta_opta_f73=os.path.join(BASE_DIR,"data_femeni","raw","f73",f"f73-903-2025-{match_id}-possessions.xml")
        df_pass,team_names=parse_f73_possesionchain(ruta_opta_f73)
        home_team=team_names["home_team_name"].iloc[0]
        away_team=team_names["away_team_name"].iloc[0]
        home_id=team_names["home_team_id"].iloc[0]
        away_id=team_names["away_team_id"].iloc[0]
        ####

        mask = shot_events["team_id"] == (home_id)
        shot_events.loc[mask, "x"] = 100 - shot_events.loc[mask, "x"]
        shot_events.loc[mask, "y"] = 100 - shot_events.loc[mask, "y"]

        scaler = MinMaxScaler(feature_range=(100, 500))  # tamaño mínimo 50, máximo 300
        shot_events["321"] = scaler.fit_transform(shot_events[["321"]])

        df_miss=shot_events[shot_events["type_id"]==13]
        df_post=shot_events[shot_events["type_id"]==14]
        df_blocked=shot_events[shot_events["type_id"]==15]
        df_goals=shot_events[shot_events["type_id"]==16]



        pitch = Pitch(pitch_type="opta",pad_bottom=0.5, goal_type='box', goal_alpha=0.8)  
        fig, ax = pitch.draw(figsize=(12, 10))  

        pitch.scatter(df_miss.x, df_miss.y,  
                      s=df_miss["321"], c='red', edgecolors='black', marker='o', ax=ax, label="Fuera",alpha=0.6)
        pitch.scatter(df_post.x, df_post.y,  
                      s=df_post["321"], c='orange', edgecolors='black', marker='o', ax=ax, label="Palo",alpha=0.6)
        pitch.scatter(df_blocked.x, df_blocked.y,  
                      s=df_blocked["321"], c='yellow', edgecolors='black', marker='o', ax=ax, label="Bloqueado",alpha=0.6)
        pitch.scatter(df_goals.x, df_goals.y,  
                      s=df_goals["321"], c='green', edgecolors='black', marker='*', ax=ax, label="Gol",alpha=0.6)

        ax.legend(loc="upper right", fontsize=12)
        ax.text(x=25,y=90,s=f"{home_goals} - {home_team} (xG={total_xg_home:.2f})",size=18, color="black",
                 va='center', ha='center')
        ax.text(x=75,y=90,s=f"{away_goals} - {away_team} (xG={total_xg_away:.2f})",size=18, color="black",
                 va='center', ha='center')
        ax.legend(loc="lower right")
        st.markdown("### Posición en el campo de las ocaciones de gol (xG)")
        st.pyplot(fig)
        
        ##########
        st.markdown("### Finalización de las ocaciones de gol (xG): Tiros a puerta")
        
        events = parse_f70_events(filepath_f70)
        shot_events = events[events['type_id'].isin(['13', '14', '15', '16'])]
        shot_events["type_id"] = shot_events["type_id"].astype(int)
        shot_events["321"] = shot_events["321"].astype(float)

        shot_events["end_location_x"] = 100
        shot_events["end_location_y"] = shot_events["102"].astype(float)
        shot_events["end_location_z"] = shot_events["103"].astype(float)

        shot_events['outcome_name'] = np.where(shot_events['type_id'] == 16, 'Goal', 'Miss')

        scaler = MinMaxScaler(feature_range=(100, 500))
        shot_events["321"] = scaler.fit_transform(shot_events[["321"]])

        df_shots = shot_events[['end_location_y', 'end_location_z', 'outcome_name', "321", "team_id"]].copy()
        df_shots["team_id"] = df_shots["team_id"].astype(int)
        print("DF SHOTS")
        print(df_shots["321"])

        home_id = int(home_id)
        away_id = int(away_id)
       
        df_home = df_shots[df_shots["team_id"] == home_id]
        df_away = df_shots[df_shots["team_id"] == away_id]
       
        fig, axs = plt.subplots(2, 1,figsize=(8,8))  # 1 row, 2 columns

        for ax, df_team, team_name in zip(axs, [df_home, df_away], ["Home", "Away"]):
            goals = df_team[df_team["outcome_name"] == "Goal"]
            miss = df_team[df_team["outcome_name"] != "Goal"]

            ax.set_xlim(35, 65)
            ax.set_ylim(0, 90)
            goal_y = 0
            goal_height = 40
            goal_left = 44.2
            goal_right = 55.8

            img=mpimg.imread(f"{BASE_DIR}/forwards_analisis/goal.jpg")
            ax.imshow(
                img,
                extent=[goal_left-0.3, goal_right+0.3, goal_y, goal_y + goal_height+2.3],  # position & scale
                aspect='auto',  # stretch to fit area
                zorder=0  # put it behind the rectangles
            )

            # Goal coordinates


            # # Draw goal posts
            # ax.plot([goal_left, goal_left], [goal_y, goal_y + goal_height], color='black', linewidth=2)
            # ax.plot([goal_right, goal_right], [goal_y, goal_y + goal_height], color='black', linewidth=2)
            # ax.plot([goal_left, goal_right], [goal_y + goal_height, goal_y + goal_height], color='black', linewidth=2)

            # Scatter goals and misses
            ax.scatter(goals.end_location_y, goals.end_location_z,
                       s=goals["321"], c='red', edgecolors='black', marker='o', label="Goal", alpha=0.6)
            ax.scatter(miss.end_location_y, miss.end_location_z,
                       s=miss["321"], c='blue', edgecolors='black', marker='o', label="Miss", alpha=0.6)

            # Remove ticks and spines
            ax.set_xticks([])
            ax.set_yticks([])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            if team_name=="Home":
                ax.set_title(f"{home_team} tiros a puerta frente a {away_team} \n\nGoles: {home_goals} \n\nxG:{total_xg_home:.2f}",loc="left")
            elif team_name=="Away":
                ax.set_title(f"{away_team} tiros a puerta frente a {home_team} \n\nGoles: {away_goals} \n\nxG:{total_xg_away:.2f}",loc="left")
            # ax.legend()

       
        plt.tight_layout()
        st.pyplot(fig)

    elif type_id!=1 and type_id!=16:
        adding=pd.DataFrame()
        if start_sideline!="None":
            adding=util.filter_bands(df_specific_event,start_sideline)
            
        df_specific_event=util.filter_actions(df_specific_event,start_third)
        df_specific_event = pd.concat([df_specific_event, adding], ignore_index=True)
       
        if team==home_team:
            df_specific_event=df_specific_event[df_specific_event["team_name"]==home_team]
            if player_id!=0:
                df_specific_event=df_specific_event[df_specific_event["player_id"]==player_id]
                
            pitch = Pitch(pitch_type="opta", pad_bottom=0.5, goal_type='box', goal_alpha=0.8)
            fig, ax = pitch.draw(figsize=(12, 10))
            ax.set_ylim(-10, 100)
            ax.scatter(df_specific_event["x"], df_specific_event["y"], color="blue", s=120, label=home_team)
            #ax.arrow(40, -2, 20, 0, head_width=2, head_length=2, fc='black', ec='black')
            ax.text(50, -5, "Dirección de ataque →", ha='center', va='top', fontsize=12, fontweight='bold')

            st.pyplot(fig)
            
        elif team==away_team:
            df_specific_event=df_specific_event[df_specific_event["team_name"]==away_team]
            df_specific_event["x"]=100-df_specific_event["x"]
            df_specific_event["y"]=100-df_specific_event["y"]
            if player_id!=0:
                df_specific_event=df_specific_event[df_specific_event["player_id"]==player_id]
                
            pitch = Pitch(pitch_type="opta", pad_bottom=0.5, goal_type='box', goal_alpha=0.8)
            fig, ax = pitch.draw(figsize=(12, 10))
            ax.scatter(df_specific_event["x"], df_specific_event["y"], color="red", s=120, label=home_team)
            #ax.arrow(60, -2, -20, 0, head_width=2, head_length=2, fc='black', ec='black')
            ax.text(50, -5, "⬅️ Dirección de ataque ", ha='center', va='top', fontsize=12, fontweight='bold')

            st.pyplot(fig)
        else:
            df_home=df_specific_event[df_specific_event["team_name"]==home_team]
            df_away=df_specific_event[df_specific_event["team_name"]==away_team]
            pitch = Pitch(pitch_type="opta", pad_bottom=0.5, goal_type='box', goal_alpha=0.8)
            fig, ax = pitch.draw(figsize=(12, 10))
            ax.scatter(df_home["x"], df_home["y"], color="blue", s=120, label=home_team)
            ax.scatter(df_away["x"], df_away["y"], color="red", s=120, label=away_team)
            st.pyplot(fig)
    
    
    
            
    st.divider()
    import locale
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")

    def last_modified(folder_path):
        latest_mod = 0
        for root, _, files in os.walk(folder_path):
            for f in files:
                file_path = os.path.join(root, f)
                mod_time = os.path.getmtime(file_path)
                latest_mod = max(latest_mod, mod_time)
        fecha = datetime.fromtimestamp(latest_mod)
        return fecha.strftime("%-d de %B")

    last_update=last_modified(f"{BASE_DIR}/data_femeni/raw")

    st.write(f"Última actualización: {last_update} | Fuente de datos: Opta Stats Perform")

