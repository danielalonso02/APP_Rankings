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
import plotly.graph_objects as go
from plotly.subplots import make_subplots


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
    df_events, team_names = parse_f24_cached(ruta_opta_f24)
    home_team=team_names["home_team_name"].iloc[0]
    away_team=team_names["away_team_name"].iloc[0]


    

            

    df_events,team_names=parse_f24(ruta_opta_f24)
    goals,home_goals,away_goals=get_goals(ruta_opta_f24)
    
    df_pass=df_events[df_events["type_id"]==1].copy()
    df_pass[["end_x", "end_y"]] = df_pass["qualifiers"].apply(extract_end_coordinates)
    df_pass["time_minutes"] = df_pass["min"] + df_pass["sec"] / 60
    df_pass=df_pass[["period_id","time_minutes","team_id","x","y","end_x","end_y"]]
    home_id=team_names["home_team_id"].iloc[0]
    away_id=team_names["away_team_id"].iloc[0]
    home_team=team_names["home_team_name"].iloc[0]
    away_team=team_names["away_team_name"].iloc[0]
    df_home_pass = df_pass[df_pass["team_id"] == int(home_id)]
    df_away_pass = df_pass[df_pass["team_id"] == int(away_id)]

    df_home_pass["av_x"]=(df_home_pass["x"]+df_home_pass["end_x"])/2
    df_home_pass["av_y"]=(df_home_pass["y"]+df_home_pass["end_y"])/2

    df_away_pass["av_x"]=(df_away_pass["x"]+df_away_pass["end_x"])/2
    df_away_pass["av_y"]=(df_away_pass["y"]+df_away_pass["end_y"])/2

    df_home_pass=df_home_pass[["period_id","time_minutes","av_x","av_y"]]
    df_away_pass=df_away_pass[["period_id","time_minutes","av_x","av_y"]]

    df_home_pass["rolling_x"] = df_home_pass["av_x"].rolling(30).mean()
    df_home_pass["rolling_y"] = df_home_pass["av_y"].rolling(30).mean()

    df_home_pass=df_home_pass.dropna()

    df_home_x=df_home_pass[["time_minutes","rolling_x"]]
    df_home_x = (
        df_home_pass[["time_minutes", "rolling_x"]]
        .groupby("time_minutes", as_index=False)  # group by minute
        .last()                          # keep the last row for each minute
    )
    df_home_y=df_home_pass[["time_minutes","rolling_y"]]
    df_home_y = (
        df_home_pass[["time_minutes", "rolling_y"]]
        .groupby("time_minutes", as_index=False)  # group by minute
        .last()                          # keep the last row for each minute
    )

    df_away_pass["rolling_x"] = df_away_pass["av_x"].rolling(30).mean()
    df_away_pass["rolling_y"] = df_away_pass["av_y"].rolling(30).mean()
    df_away_pass=df_away_pass.dropna()
    df_away_x=df_away_pass[["time_minutes","rolling_x"]]
    df_away_y=df_away_pass[["time_minutes","rolling_y"]]
    
    
    minutes=np.arange(0, 91)
    
    df_plot1 = (
        pd.concat([
            df_home_pass.assign(team=home_team),
            df_away_pass.assign(team=away_team)
        ])
    )
    
    colors = {home_team: "red", away_team: "blue"}

    # Crear figura
    fig = go.Figure()

    # Añadir líneas de cada equipo
    for team in df_plot1['team'].unique():
        df_team = df_plot1[df_plot1['team'] == team]
        fig.add_trace(go.Scatter(
            x=df_team['time_minutes'],
            y=df_team['rolling_x'],
            mode='lines',
            name=team,
            line=dict(color=colors[team], width=2)
            ))  

    # Línea horizontal en y=50
    fig.add_shape(type="line",
                  x0=0, x1=df_plot1["time_minutes"].max()+2,
                  y0=50, y1=50,
                  line=dict(color="black", width=1, dash="dash"))

    # Líneas verticales y anotaciones para goles
    for _, row in goals.iterrows():
        fig.add_shape(type="line",
                      x0=row["time_minutes"], x1=row["time_minutes"],
                      y0=0, y1=df_plot1['rolling_x'].max(),
                      line=dict(color="gray", width=1, dash="dash"))
        fig.add_annotation(x=row["time_minutes"],
                           y=df_plot1['rolling_x'].max()*0.95,
                           text=row["resultado"],
                           showarrow=False,
                           xanchor='right',
                           yanchor='top',
                           textangle=-90,
                           font=dict(color="black"))

    # Layout
    fig.update_layout(
        xaxis_title="Tiempo (minutos)",
        yaxis_title="Cercanía a la portería Rival",
        xaxis=dict(range=[0, df_plot1["time_minutes"].max()+2]),
        legend=dict(title="Equipo")
        )
    st.markdown("### Cercanía a la portería rival")
    st.plotly_chart(fig,use_container_width=True)
    
    ############## 
    st.markdown("### Lateralidad del juego")
    
    
    colors = {home_team: "red", away_team: "blue"}

    # Crear figura
    fig = go.Figure()

    # Añadir líneas de cada equipo
    for team in df_plot1['team'].unique():
        df_team = df_plot1[df_plot1['team'] == team]
        fig.add_trace(go.Scatter(
            x=df_team['time_minutes'],
            y=df_team['rolling_y'],
            mode='lines',
            name=team,
            line=dict(color=colors[team], width=2)
            ))
        
  
        fig.add_shape(type="line",
                      x0=0, x1=df_plot1["time_minutes"].max()+2,
                      y0=50, y1=50,
                      line=dict(color="black", width=1, dash="dash"))

    # Líneas verticales y anotaciones para goles
    for _, row in goals.iterrows():
        fig.add_shape(type="line",
                      x0=row["time_minutes"], x1=row["time_minutes"],
                      y0=df_plot1['rolling_y'].min()-2, y1=df_plot1['rolling_y'].max()+1,
                      line=dict(color="gray", width=1, dash="dash"))
        fig.add_annotation(x=row["time_minutes"],
                           y=df_plot1['rolling_y'].max()*0.95,
                           text=row["resultado"],
                           showarrow=False,
                           xanchor='right',
                           yanchor='top',
                           textangle=-90,
                           font=dict(color="black"))

    # Anotaciones de bandas
    y_max = df_plot1["rolling_y"].max()
    y_min = df_plot1["rolling_y"].min()

    fig.add_annotation(x=10, y=y_max+2,
                       text="Banda Izquierda",
                       showarrow=False,
                       font=dict(size=12, color="black", family="Arial", weight="bold"),
                       bgcolor="white", bordercolor="black", borderwidth=1, borderpad=4, align="center")

    fig.add_annotation(x=10, y=y_min + (y_max - y_min) * 0.05,
                       text="Banda Derecha",
                       showarrow=False,
                       font=dict(size=12, color="black", family="Arial", weight="bold"),
                       bgcolor="white", bordercolor="black", borderwidth=1, borderpad=4, align="center")

    # Layout
    fig.update_layout(
        xaxis_title="Tiempo (minutos)",
        yaxis_title="Banda Izquierda vs Banda Derecha",
        xaxis=dict(range=[0, df_plot1["time_minutes"].max()+2]),
        yaxis=dict(range=[y_min-2, y_max+3]),
        legend=dict(title="Equipo")
        )
    
    st.plotly_chart(fig,use_container_width=True)
    
    ################
    st.markdown("### Número de pases acumulados a lo largo del partido")
    df_events,team_names=parse_f24(ruta_opta_f24)
    df_pass=df_events[df_events["type_id"]==1].copy()
    df_pass["time_minutes"] = df_pass["min"] + df_pass["sec"] / 60
    df_pass=df_pass[["period_id","time_minutes","team_id","x","y"]]
    df_pass = df_pass.sort_values(by=["time_minutes"]).reset_index(drop=True)
    home_id=team_names["home_team_id"].iloc[0]
    away_id=team_names["away_team_id"].iloc[0]
    home_team=team_names["home_team_name"].iloc[0]
    away_team=team_names["away_team_name"].iloc[0]
    df_home_pass_count = df_pass[df_pass["team_id"] == int(home_id)]
    df_away_pass_count = df_pass[df_pass["team_id"] == int(away_id)]

    df_home_pass_count["cumulative"]=range(1,len(df_home_pass_count)+1)
    df_away_pass_count["cumulative"]=range(1,len(df_away_pass_count)+1)

    df_plot2 = (
        pd.concat([
            df_home_pass_count.assign(team=home_team),
            df_away_pass_count.assign(team=away_team)
        ])
    )

    df_diff = df_home_pass_count[["time_minutes", "cumulative"]].rename(columns={"cumulative": "home"})
    df_diff = df_diff.merge(
        df_away_pass_count[["time_minutes", "cumulative"]].rename(columns={"cumulative": "away"}),
        on="time_minutes",
        how="outer"
    )
    df_diff = df_diff.sort_values("time_minutes").reset_index(drop=True)

    # Forward-fill NaNs
    df_diff["home"] = df_diff["home"].ffill().fillna(0)
    df_diff["away"] = df_diff["away"].ffill().fillna(0)

    # Compute difference
    df_diff["diff_passes"] = df_diff["home"] - df_diff["away"]
    
    colors = {home_team: "red", away_team: "blue"}

    # Crear figura con subplot tipo inset
    fig = make_subplots(
        rows=1, cols=1,
        specs=[[{"secondary_y": False}]],
        # Para añadir un inset, usaremos add_trace con domain
        )

    # Gráfico principal: pases acumulados
    for team in df_plot2['team'].unique():
        df_team = df_plot2[df_plot2['team'] == team]
        fig.add_trace(go.Scatter(
            x=df_team['time_minutes'],
            y=df_team['cumulative'],
            mode='lines',
            name=team,
            line=dict(color=colors[team], width=2)
                ))

    # Líneas verticales y anotaciones para goles en gráfico principal
    for _, row in goals.iterrows():
        fig.add_shape(type="line",
                      x0=row["time_minutes"], x1=row["time_minutes"],
                      y0=0, y1=df_plot2['cumulative'].max(),
                      line=dict(color="gray", width=1, dash="dash"))
        fig.add_annotation(x=row["time_minutes"],
                           y=df_plot2['cumulative'].max()*0.95,
                           text=row["resultado"],
                           showarrow=False,
                           xanchor='right',
                           yanchor='top',
                           textangle=-90,
                           font=dict(color="black"))

    # Ejes principales
    fig.update_xaxes(title_text="Tiempo (minutos)", range=[0, df_plot2["time_minutes"].max()+2])
    fig.update_yaxes(title_text="Pases acumulados")

    # === Inset plot ===
    # Definir inset usando domain
    inset_x0, inset_x1 = 0.10, 0.40
    inset_y0, inset_y1 = 0.65, 0.95

    # Línea de diferencia de pases
    fig.add_trace(go.Scatter(
        x=df_diff['time_minutes'],
        y=df_diff['diff_passes'],
        mode='lines',
        line=dict(color='black', width=1),
        name='Diferencia pases',
        xaxis="x2",
        yaxis="y2"
        ))

    # Líneas verticales y anotaciones para goles en inset
    for _, row in goals.iterrows():
        fig.add_shape(type="line",
                      x0=row["time_minutes"], x1=row["time_minutes"],
                      y0=df_diff['diff_passes'].min(), y1=df_diff['diff_passes'].max(),
                      line=dict(color="gray", width=1, dash="dash"),
                      xref='x2', yref='y2')
        fig.add_annotation(x=row["time_minutes"],
                           y=df_diff['diff_passes'].max()*0.95,
                           text=row["resultado"],
                           showarrow=False,
                           xanchor='right',
                           yanchor='top',
                           textangle=-90,
                           font=dict(color="black"),
                           xref='x2', yref='y2')

    # Definir ejes del inset
    fig.update_layout(
        xaxis2=dict(domain=[inset_x0, inset_x1], anchor='y2'),
        yaxis2=dict(domain=[inset_y0, inset_y1], anchor='x2', title="Diferencia pases"),
        )

    # Layout general
    fig.update_layout(
        legend=dict(title="Equipo", yanchor="bottom", y=0.05, xanchor="right", x=0.95),
        width=1000,
        height=500
        )
    st.plotly_chart(fig,use_container_width=True)


    
    ##### defensive
    st.markdown("### Número de acciones defensivas acumuladas: Faltas, tackles, pases cortados y challenges")
    list_defensive=[4,7,8,45]
    df_defensive=df_events[df_events["type_id"].isin(list_defensive)].copy()

    df_defensive["time_minutes"]=df_defensive["min"] + df_defensive["sec"] / 60

    df_home_def=df_defensive[df_defensive["team_id"] == int(home_id)]
    df_away_def=df_defensive[df_defensive["team_id"] == int(away_id)]

    df_home_def["cumulative"]=range(1,len(df_home_def)+1)
    df_away_def["cumulative"]=range(1,len(df_away_def)+1)
    df_plot1 = (
        pd.concat([
            df_home_def.assign(team=home_team),
            df_away_def.assign(team=away_team)
        ])
    )
    
    # Preparar df_diff
    df_diff = df_home_def[["time_minutes", "cumulative"]].rename(columns={"cumulative": "home"})
    df_diff = df_diff.merge(
        df_away_def[["time_minutes", "cumulative"]].rename(columns={"cumulative": "away"}),
        on="time_minutes", how="outer"
        ).sort_values("time_minutes").reset_index(drop=True)
    df_diff["home"] = df_diff["home"].ffill().fillna(0)
    df_diff["away"] = df_diff["away"].ffill().fillna(0)
    df_diff["diff_def"] = df_diff["home"] - df_diff["away"]

    # Crear figura
    fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": False}]])

    # Gráfico principal: acciones defensivas acumuladas
    for team in df_plot1['team'].unique():
        df_team = df_plot1[df_plot1['team'] == team]
        fig.add_trace(go.Scatter(
            x=df_team['time_minutes'],
            y=df_team['cumulative'],
            mode='lines',
            name=team,
            line=dict(color=colors[team], width=2)
            ))

    # Líneas verticales y anotaciones de goles en gráfico principal
    for _, row in goals.iterrows():
        fig.add_shape(type="line",
                      x0=row["time_minutes"], x1=row["time_minutes"],
                      y0=0, y1=df_plot1['cumulative'].max(),
                      line=dict(color="gray", width=1, dash="dash"))
        fig.add_annotation(x=row["time_minutes"],
                           y=df_plot1['cumulative'].max()*0.95,
                           text=row["resultado"],
                           showarrow=False,
                           xanchor='right',
                           yanchor='top',
                           textangle=-90,
                           font=dict(color="black"))

    # Ejes principales
    fig.update_xaxes(title_text="Tiempo (minutos)", range=[0, df_plot1["time_minutes"].max()+2])
    fig.update_yaxes(title_text="Acciones defensivas acumuladas")

    # === Inset plot ===
    # Definir posición del inset usando domain
    inset_x0, inset_x1 = 0.10, 0.40
    inset_y0, inset_y1 = 0.65, 0.95

    # Línea de diferencia de acciones defensivas
    fig.add_trace(go.Scatter(
        x=df_diff['time_minutes'],
        y=df_diff['diff_def'],
        mode='lines',
        line=dict(color='black', width=1),
        name='Diferencia defensiva',
        xaxis="x2",
        yaxis="y2"
        ))

    # Líneas verticales y anotaciones en inset
    for _, row in goals.iterrows():
        fig.add_shape(type="line",
                      x0=row["time_minutes"], x1=row["time_minutes"],
                      y0=df_diff['diff_def'].min(), y1=df_diff['diff_def'].max(),
                      line=dict(color="gray", width=1, dash="dash"),
                      xref='x2', yref='y2')
        fig.add_annotation(x=row["time_minutes"],
                           y=df_diff['diff_def'].max()*0.95,
                           text=row["resultado"],
                           showarrow=False,
                           xanchor='right',
                           yanchor='top',
                           textangle=-90,
                           font=dict(color="black"),
                           xref='x2', yref='y2')

    # Configurar ejes del inset
    fig.update_layout(
        xaxis2=dict(domain=[inset_x0, inset_x1], anchor='y2'),
        yaxis2=dict(domain=[inset_y0, inset_y1], anchor='x2', title="Diferencia acciones defensivas")
        )

    # Layout general
    fig.update_layout(
        legend=dict(title="Equipo", yanchor="bottom", y=0.05, xanchor="right", x=0.95),
        width=1000,
        height=500
        )
    st.plotly_chart(fig,use_container_width=True)

    ########## 
    st.markdown("### Posición promedio de las acciones defensivas acumuladas")
    
    df_home_def["rolling_x"] = df_home_def["x"].rolling(10).mean()
    df_away_def["rolling_x"] = df_away_def["x"].rolling(10).mean()

    df_plot2 = (
        pd.concat([
            df_home_def.assign(team=home_team),
            df_away_def.assign(team=away_team)
        ])
    )
    fig = go.Figure()

    # Añadir línea por equipo
    for team in df_plot2['team'].unique():
        df_team = df_plot2[df_plot2['team'] == team]
        fig.add_trace(go.Scatter(
            x=df_team['time_minutes'],
            y=df_team['rolling_x'],
           mode='lines',
           name=team,
           line=dict(color=colors[team], width=2)
           ))

    # Línea horizontal central en y=50
    fig.add_shape(type="line",
                  x0=0, x1=df_plot2["time_minutes"].max()+2,
                  y0=50, y1=50,
                  line=dict(color="gray", width=1, dash="dash"))

    # Líneas verticales y anotaciones de goles
    for _, row in goals.iterrows():
        fig.add_shape(type="line",
                      x0=row["time_minutes"], x1=row["time_minutes"],
                      y0=0, y1=df_plot2['rolling_x'].max(),
                      line=dict(color="gray", width=1, dash="dash"))
        fig.add_annotation(x=row["time_minutes"],
                           y=df_plot2['rolling_x'].max()*0.95,
                           text=row["resultado"],
                           showarrow=False,
                           xanchor='right',
                           yanchor='top',
                           textangle=-90,
                           font=dict(color="black"))

    # Layout
    fig.update_layout(
        xaxis_title="Tiempo (minutos)",
        yaxis_title="Situación de la acción defensiva respecto a la portería rival",
        xaxis=dict(range=[0, df_plot2["time_minutes"].max()+2]),
        legend=dict(title="Equipo", x=0.01, y=0.99, xanchor='left', yanchor='top'),
        width=1000,
        height=500
        )
    st.plotly_chart(fig,use_container_width=True)
    
    ##########
    st.markdown("### Ritmo de juego de cada equipo (velocidad del balón)")
    ruta_opta_f73=os.path.join(BASE_DIR,"data_femeni","raw","f73",f"f73-903-2025-{match_id}-possessions.xml")
    #st.write(ruta_opta_f73)
    df_pass,team_names=parse_f73_possesionchain(ruta_opta_f73)

    df_pass["x_diff"]=df_pass.groupby("possession_id")["x"].diff().abs()

    df_pass["t_diff"] = (
        df_pass.groupby("possession_id")["time_minutes"]
               .transform(lambda x: x.iloc[-1] - x.iloc[0])
    )
    sums = (
        df_pass.groupby("possession_id")
        .agg({
            "x_diff": "sum",
            "time_minutes":"last",
            "t_diff":"first",
            "team_id": "first"  
        })
        .reset_index()
    )

    sums.rename(columns={"x_diff": "total_diff"}, inplace=True)

    sums["velocity"]=sums["total_diff"]/sums["t_diff"]
    sums["velocity"] = sums["total_diff"] / (sums["t_diff"] * 60)
    sums_home=sums[sums["team_id"]==int(home_id)]
    sums_away=sums[sums["team_id"]==int(away_id)]
    df_plot3 = (
        pd.concat([
            sums_home.assign(team=home_team),
            sums_away.assign(team=away_team)
        ])
    )
    fig = go.Figure()
    for team in df_plot3['team'].unique():
        df_team = (
            df_plot3[df_plot3['team'] == team]
            .sort_values('time_minutes')       # ordenar por tiempo
            .copy()
            )
        # Rellenar posibles NaN en la velocidad
        df_team['velocity'] = df_team['velocity'].interpolate().ffill().bfill()

        fig.add_trace(go.Scatter(
            x=df_team['time_minutes'],
            y=df_team['velocity'],
            mode='lines',
            name=team,
            line=dict(color=colors[team], width=2),
            connectgaps=True   # 🔥 fuerza la conexión de la línea aunque haya gaps
            ))

    

    # Líneas por equipo
    for team in df_plot3['team'].unique():
        df_team = df_plot3[df_plot3['team'] == team]
        fig.add_trace(go.Scatter(
            x=df_team['time_minutes'],
            y=df_team['velocity'],
            mode='lines',
            name=team,
            line=dict(color=colors[team], width=2)
            ))

    # Líneas verticales y anotaciones de goles
    for _, row in goals.iterrows():
        fig.add_shape(type="line",
                      x0=row["time_minutes"], x1=row["time_minutes"],
                      y0=0, y1=20,
                      line=dict(color="gray", width=1, dash="dash"))
        fig.add_annotation(x=row["time_minutes"],
                           y=20*0.95,
                           text=row["resultado"],
                           showarrow=False,
                           xanchor='right',
                           yanchor='top',
                           textangle=-90,
                           font=dict(color="black"))

    # Líneas horizontales de medias
    fig.add_shape(type="line",
                  x0=0, x1=df_plot3["time_minutes"].max()+2,
                  y0=sums_home["velocity"].mean(),
                  y1=sums_home["velocity"].mean(),
                  line=dict(color="red", width=1, dash="dash"),
                  name="Media Home")

    fig.add_shape(type="line",
                  x0=0, x1=df_plot3["time_minutes"].max()+2,
                  y0=sums_away["velocity"].mean(),
                  y1=sums_away["velocity"].mean(),
                  line=dict(color="blue", width=1, dash="dash"),
                  name="Media Away")

    # Layout
    fig.update_layout(
        xaxis_title="Tiempo (minutos)",
        yaxis_title="Ritmo de juego (m/s)",
        xaxis=dict(range=[0, df_plot3["time_minutes"].max()+2]),
        yaxis=dict(range=[0, 20]),
        legend=dict(title="Equipo", x=0.01, y=0.99, xanchor='left', yanchor='top'),
        width=1000,
        height=500
        )
    st.plotly_chart(fig,use_container_width=True)
    
    ########
    st.markdown("### Longitud de las jugadas en número de pases")
    total_long = (
        df_pass.groupby("possession_id")
        .agg({
            "time_minutes": "last",
            "team_id":"first",
            "possession_id": "count"   
        })
        .rename(columns={"possession_id": "num_passes"})
        .reset_index()
    )

    total_long_home=total_long[total_long["team_id"]==int(home_id)]
    total_long_home["num_passes"]=total_long_home["num_passes"].rolling(10).mean()
    total_long_away=total_long[total_long["team_id"]==int(away_id)]
    total_long_away["num_passes"]=total_long_away["num_passes"].rolling(10).mean()
    df_plot4 = (
        pd.concat([
            total_long_home.assign(team=home_team),
            total_long_away.assign(team=away_team)
        ])
    )
    
    fig=go.Figure()
    for team in df_plot4["team"].unique():
        df_team=(df_plot4[df_plot4["team"]==team].sort_values("time_minutes").copy())
        df_team['num_passes'] = df_team['num_passes'].interpolate().ffill().bfill()

        fig.add_trace(go.Scatter(
            x=df_team['time_minutes'],
            y=df_team['num_passes'],
            mode='lines',
            name=team,
            line=dict(color=colors[team], width=2),
            connectgaps=True
            ))
    for _, row in goals.iterrows():
        fig.add_shape(
            type="line",
            x0=row["time_minutes"], x1=row["time_minutes"],
            y0=0, y1=20,
            line=dict(color="gray", width=1, dash="dash")
            )
        fig.add_annotation(
            x=row["time_minutes"],
            y=20 * 0.95,
            text=row["resultado"],
            showarrow=False,
            xanchor='right',
            yanchor='top',
            textangle=-90,
            font=dict(color="black")
            )

    # === Líneas horizontales de medias ===
    fig.add_shape(
        type="line",
        x0=0, x1=df_plot4["time_minutes"].max() + 2,
        y0=total_long_home["num_passes"].mean(),
        y1=total_long_home["num_passes"].mean(),
        line=dict(color="red", width=1, dash="dash")
        )
    fig.add_shape(
        type="line",
        x0=0, x1=df_plot4["time_minutes"].max() + 2,
        y0=total_long_away["num_passes"].mean(),
        y1=total_long_away["num_passes"].mean(),
        line=dict(color="blue", width=1, dash="dash")
        )

    # === Layout ===
    fig.update_layout(
        xaxis_title="Tiempo (minutos)",
        yaxis_title="Longitud de la secuencia (pases)",
        xaxis=dict(range=[0, df_plot4["time_minutes"].max() + 2]),
        yaxis=dict(range=[0, 20]),
        legend=dict(title="Equipo", x=0.01, y=0.99, xanchor='left', yanchor='top'),
        width=1000,
        height=500,
        plot_bgcolor='white'
        )

    # Líneas de cuadrícula suaves
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='lightgray')

    # Mostrar en Streamlit
    st.plotly_chart(fig, use_container_width=True)

    #########

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
    st.markdown("### Evolución de los goles esperados durante el partido")
    st.markdown(
    f"<span style='color:red'>{home_goals} - {home_team}  (xG={total_xg_home:.2f})</span> - <span style='color:blue'>{away_goals} - {away_team}  (xG={total_xg_away:.2f})</span>",
    unsafe_allow_html=True
)
    df_plot4 = (
        pd.concat([
            shot_events_home.assign(team=home_team),
            shot_events_away.assign(team=away_team)
        ])
    )
    df_plot4 = df_plot4.sort_values(['team','time_minutes'])
    fig = go.Figure()

    # === Líneas por equipo (tipo "steps-pre") ===
    for team in df_plot4["team"].unique():
        df_team = (
            df_plot4[df_plot4["team"] == team]
            .sort_values("time_minutes")
            .reset_index(drop=True)
            )

        fig.add_trace(go.Scatter(
            x=df_team["time_minutes"],
            y=df_team["cumulative"],
            mode="lines",
            name=team,
            line=dict(color=colors[team], width=2, shape="hv"),  # 'hv' → estilo "steps-pre"
            ))
        
        # === Puntos (scatter) ===
        fig.add_trace(go.Scatter(
            x=df_team["time_minutes"],
            y=df_team["cumulative"],
            mode="markers",
            marker=dict(color=colors[team], size=6, line=dict(color="black", width=1)),
            name=f"{team} puntos",
            showlegend=False
            ))

    # === Líneas verticales y anotaciones de goles ===
    for _, row in goals.iterrows():
        fig.add_shape(
            type="line",
            x0=row["time_minutes"], x1=row["time_minutes"],
            y0=0, y1=df_plot4["cumulative"].max(),
            line=dict(color="gray", width=1, dash="dash")
            )
        fig.add_annotation(
            x=row["time_minutes"],
            y=df_plot4["cumulative"].max() * 0.95,
            text=row["resultado"],
            showarrow=False,
            xanchor='right',
            yanchor='top',
            textangle=-90,
            font=dict(color="black")
            )

    # === Layout general ===
    fig.update_layout(
       xaxis_title="Tiempo (minutos)",
       yaxis_title="Evolución de xG",
       xaxis=dict(range=[0, df_plot4["time_minutes"].max() + 2]),
       yaxis=dict(range=[0, df_plot4["cumulative"].max() * 1.1]),
       legend=dict(
           title="Equipo",
           x=0.01, y=0.99,
           xanchor='left',
           yanchor='top'
           ),
       width=1000,
       height=500,
       plot_bgcolor='white'
       )

    # === Líneas de cuadrícula suaves ===
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='lightgray')

    # # === Leyenda personalizada con xG y resultado ===
    # fig.update_layout(
    #     legend_title_text="",
    #     legend=dict(
    #         itemsizing="constant",
    #         font=dict(size=10),
    #         ),
    #     annotations=[
    #         # Left (home team)
    #         dict(
    #             text=f"<b>{home_goals} - {home_team}</b> (xG={total_xg_home:.2f})",
    #             xref="paper", yref="paper",
    #             x=0.25, y=1.12, showarrow=False,
    #             font=dict(color="red", size=13),
    #             xanchor="center",
    #             yanchor="bottom",
    #             ),
    #         # Right (away team)
    #         dict(
    #             text=f"<b>{away_goals} - {away_team}</b> (xG={total_xg_away:.2f})",
    #             xref="paper", yref="paper",
    #             x=0.75, y=1.12, showarrow=False,
    #             font=dict(color="blue", size=13),
    #             xanchor="center",
    #             yanchor="bottom",
    #             )   
    #         ]
    #     )

    
    # Mostrar en Streamlit
    st.plotly_chart(fig, use_container_width=True)
    
    ##########
    events=parse_f70_events(filepath_f70)
    shot_events = events[events['type_id'].isin(['13', '14', '15', '16'])]
    shot_events["type_id"]=shot_events["type_id"].astype(int)
    shot_events["321"]=shot_events["321"].astype(float)
    ####
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

        # Goal coordinates
        goal_y = 0
        goal_height = 40
        goal_left = 44.2
        goal_right = 55.8

        # Draw goal posts
        ax.plot([goal_left, goal_left], [goal_y, goal_y + goal_height], color='black', linewidth=2)
        ax.plot([goal_right, goal_right], [goal_y, goal_y + goal_height], color='black', linewidth=2)
        ax.plot([goal_left, goal_right], [goal_y + goal_height, goal_y + goal_height], color='black', linewidth=2)

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

