#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  1 11:43:32 2025

@author: julieta
"""

import pandas as pd
import os
import numpy as np
import json
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
def parse_f27(filepath_f27):
    
    if not os.path.exists(filepath_f27):
        print(f"Error: El archivo '{filepath_f27}' no existe.")
        return None, None

    tree = ET.parse(filepath_f27)
    root = tree.getroot()
    
    # Crear una lista para almacenar los datos

    # Obtener el atributo "team_name" del nodo <SoccerFeed>
    team_analizing = root.get("team_name")
    home_team = root.get("home_team_name")
    away_team = root.get("away_team_name")
    season = root.get("season_name")

    # print("Team Name:", team_name)
    pases_data = []

    for player in root.findall("Player"):
        passer_name = player.get("player_name")
        passer_position = player.get("position")  # Obtener la posición del jugador
        passer_x = float(player.get("x"))  # Obtener la coordenada X
        passer_y = float(player.get("y"))  # Obtener la coordenada Y
        sub_on = player.get("sub_on")  # Minuto en el que ingresó como suplente
        sub_on = int(eval(sub_on)) if sub_on is not None else None  # Convertir a entero si existe

        # Iterar sobre los jugadores a los que se les hacen los pases
        for pass_receiver in player.findall("Player"):
            receiver_name = pass_receiver.get("player_name")
            passes = int(pass_receiver.text)

            # Añadir los datos a la lista
            pases_data.append({
                "player": passer_name,
                "position": passer_position,
                "x": passer_x,
                "y": passer_y,
                "receiver": receiver_name,
                "pases": passes,
                "sub": sub_on is not None,  # True si salió como suplente
                "entry_minute": sub_on  # Minuto en el que entró, None si no es suplente
            })

    # Crear el DataFrame
    df_pases = pd.DataFrame(pases_data)
    
    return df_pases, team_analizing,home_team,away_team, season

def parse_f40(filepath_f40,team_analizing):
    
    if not os.path.exists(filepath_f40):
        print(f"Error: El archivo '{filepath_f40}' no existe.")
        return None , None

    tree = ET.parse(filepath_f40)
    root = tree.getroot()
    equipos = {team.get("uID"): team.find("Name").text for team in root.findall(".//Team")}
    jugadores_data = []

    for team in root.findall(".//Team"):
        team_name = team.find("Name").text  # Obtener el nombre del equipo

        # Iterar sobre los jugadores de cada equipo
        for player in team.findall(".//Player"):
            player_name = player.find("Name").text  # Obtener el nombre del jugador
            position = player.find("Position").text  # Obtener la posición del jugador
            jersey_stat = player.find('.//Stat[@Type="jersey_num"]')
            jersey_number = jersey_stat.text if jersey_stat is not None else None  # Manejar si no existe

            # Añadir los datos a la lista, incluyendo el equipo
            jugadores_data.append({
                "player": player_name,
                "position": position,
                "team": team_name,
                "jersey_num": jersey_number
            })

    # Crear un DataFrame con los datos extraídos
    df_jugadores = pd.DataFrame(jugadores_data)

    df_jugadores = df_jugadores[df_jugadores["team"] == team_analizing]
    # antes de juntar los dos dataframes voy a quitar todas las tildes prq a veces no coinciden
    replace_dict = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")
    df_jugadores["player"] = df_jugadores["player"].str.translate(replace_dict)
    
    return df_jugadores, equipos 

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


def Heatmap_one_team(team_analizing, file_path_40, file_path_24):
    
    URL = 'https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Regular.ttf'
    URL2 = 'https://raw.githubusercontent.com/google/fonts/main/apache/robotoslab/RobotoSlab[wght].ttf'
    robotto_regular = FontManager(URL)
    robboto_bold = FontManager(URL2)
    _, equipos=parse_f40(file_path_40,team_analizing)
    df_events,team_names=parse_f24(file_path_24)
    
    df_equipos = pd.DataFrame(list(equipos.items()), columns=["team_id", "team_name"])
    df_equipos["team_id"] = df_equipos["team_id"].str.extract('(\\d+)').astype(int)
    df_equipos.set_index("team_id", inplace=True)
    
    tree = ET.parse(file_path_40)
    root = tree.getroot()
    equipos = {team.get("uID"): team.find("Name").text for team in root.findall(".//Team")}
    
    data = []
    for team in root.findall(".//Team"):
        for player in team.findall("Player"):
            stats = {stat.get("Type"): stat.text for stat in player.findall("Stat")}
            row = {
                "team_id": team.get("uID"),
                "team_name": equipos.get(team.get("uID"), f"Equipo {team.get('uID')}"),
                "player_id": player.get("uID"),
                "player_name": player.find("Name").text if player.find("Name") is not None else None,
                **stats,
            }
            data.append(row)
    
    df = pd.DataFrame(data)
    
    player_relations = df[["player_name", "player_id", "team_id", "team_name"]].copy()
    player_relations["player_id"] = player_relations["player_id"].str.extract('(\\d+)').astype(int)
    player_relations["team_id"] = player_relations["team_id"].str.extract('(\\d+)').astype(int)
    player_relations = player_relations.drop_duplicates(subset=["player_id", "team_id"]).set_index(["player_id", "team_id"])
    player_relations = player_relations.reset_index().merge(df_equipos, on="team_id", how="left")
    player_relations["team_name"] = player_relations["team_name_y"].fillna(player_relations["team_name_x"])
    player_relations.drop(columns=["team_name_x", "team_name_y"], inplace=True)
    player_relations.set_index(["player_id", "team_id"], inplace=True)

    home_team, away_team = team_names.iloc[0][["home_team_name", "away_team_name"]]
    
    #home_id ,away_id=team_names.iloc[0][["home_team_id", "away_team_id"]]
    df_events["team_id"] = df_events["team_id"].astype(int)
    home_id, away_id = team_names.iloc[0][["home_team_id", "away_team_id"]].astype(int)
    if team_analizing=="home":
        team_id=home_id
        team_analizing=home_team
    elif team_analizing=="away":
        team_id=away_id
        team_analizing=away_team
        
    
   
    df_events_ = df_events[df_events["team_id"]==team_id][["x", "y"]]
    print(df_events_.columns)
    if team_analizing==away_team:
       
        df_events_["x"]=100-df_events_["x"]
        df_events_["y"]=100-df_events_["y"]

    flamingo_cmap = LinearSegmentedColormap.from_list("Flamingo - 100 colors", ['#e3aca7', '#c03a1d'], N=100)
    pitch = Pitch(pitch_type='opta', line_color='#000009', line_zorder=2)
    fig, axs = pitch.grid(figheight=10, title_height=0.08, endnote_space=0, title_space=0, axis=False, grid_height=0.82, endnote_height=0.03)
    
    pitch.kdeplot(df_events_.x, df_events_.y, ax=axs['pitch'], fill=True, levels=100, thresh=0, cut=4, cmap="cividis")
    if team_analizing==home_team:
        arrow = FancyArrowPatch(
            (0.4, 0.015),    
            (0.6, 0.015),   
            transform=axs['pitch'].transAxes,   
            arrowstyle='simple', 
            color='black',
            mutation_scale=30,  
            linewidth=2
            )
        axs['pitch'].add_patch(arrow)
    elif team_analizing==away_team:

        arrow = FancyArrowPatch(
            (0.6, 0.015),    
            (0.4, 0.015),   
            transform=axs['pitch'].transAxes,   
            arrowstyle='simple', 
            color='black',
            mutation_scale=30,  
            linewidth=2
            )
        axs['pitch'].add_patch(arrow)
   
    #axs['title'].text(0.5, 0.7, f"{team_analizing}'s Actions", color='#000009', va='center', ha='center', fontproperties=robotto_regular.prop, fontsize=30)
    #axs['title'].text(0.5, 0.25, f"{home_team} vs {away_team}", color='#000009', va='center', ha='center', fontproperties=robotto_regular.prop, fontsize=20)
    output_path = f"heatmap_{team_analizing}.png"
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.show()
    plt.close(fig)
    return output_path
#Heatmap_one_team("away", "/Users/julieta/Desktop/data_madridcff/f40/f40-squad-102.xml", "/Users/julieta/Desktop/data_madridcff/f24/f24-903-2025-2572345-eventdetails.xml")

def passnetwork_oneteam(filepath_f27, filepath_f40,MIN_PASS):
    """
    

    Parameters
    ----------
    filepath_f27 : Ruta del archivo f27 que contiene la matriz de pases de un unico equipo para un partido
                    en cada archivo f27 solo viene un equipo, si se quieren los 2 equipos hay que hacerlo por separado
                    
                    forma: pass_matrix_{competition_id}_{season_id}_g{game_id}_t{team_id}.xml

    filepath_f40 : Ruta del archivo f24 que contiene datos de todos los jugadores

    Returns
    --------
    tuple (matplotlib.figure.Figure, str)  
    Figura generada y ruta donde se guarda la imagen.  

    """

    df_pases, team_analizing,home_team,away_team,season=parse_f27(filepath_f27)
    
    pitch = Pitch(
       pitch_type="opta", pitch_color="white", line_color="black", linewidth=1,
       )
    #print(df_pases["x"])
    
    df_jugadores, equipos =parse_f40(filepath_f40,team_analizing)

    replace_dict = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")

    df_pases["player"] = df_pases["player"].str.translate(replace_dict)
    df_pases["receiver"] = df_pases["receiver"].str.translate(replace_dict)
    
    df_pases = pd.merge(df_pases, df_jugadores, left_on="player", right_on="player", how="left")
    df_pases = pd.merge(df_pases, df_jugadores, left_on="receiver", right_on="player", how="left")

    df_pases = df_pases.drop(["position_y", "position", "team_y", "player_y"], axis=1)

    df_pases = df_pases.rename(columns={"position_x": "position", "player_x": "player", "team_x": "team", "jersey_num_x": "jersey_player", "jersey_num_y": "jersey_receiver"})
    mask = df_pases["team"] == (away_team)
    df_pases.loc[mask, "x"] = 100 - df_pases.loc[mask, "x"]
    df_pases.loc[mask, "y"] = 100 - df_pases.loc[mask, "y"]
    
    subs = df_pases[df_pases["sub"] == True]
    subs_jerseynum = subs["jersey_player"].drop_duplicates()
    df_pases = df_pases[~df_pases["jersey_player"].isin(subs_jerseynum) & ~df_pases["jersey_receiver"].isin(subs_jerseynum)]
    
    #hasta aqui tengo un df que es 'player', 'position', 'x', 'y', 'receiver', 'pases', 'sub','entry_minute', 'team', 'jersey_player', 'jersey_receiver']
    #con solo los titulares

    pass_cols = ['jersey_player', 'jersey_receiver']
    #passes formation es basicamente todos los pases que se dan entre titulares
    passes_formation = df_pases.loc[(df_pases.team == team_analizing) &
                                      df_pases.jersey_receiver.notnull(), pass_cols].copy()
    #passes subs es pases dirigidos A subs, que luego se eliminan
    passes_subs = subs.loc[(subs.team == team_analizing) &
                                      subs.jersey_receiver.notnull(), pass_cols].copy()

    location_cols = ["jersey_player", "x", "y"]

    #location formation es donde esta cada jugador, x,y del campo
    location_formation = df_pases.loc[(df_pases.team == team_analizing), location_cols].copy()
    #average locs and count es el average de las location Y cuenta el número de pases hechos por cada jugador
    average_locs_and_count = (location_formation.groupby('jersey_player')
                              .agg({'x': ['mean'], 'y': ['mean', 'count']}))
    
    
    average_locs_and_count.columns = ['x', 'y', 'count']

    location_formation = location_formation.drop_duplicates()
    #location formation de donde esta cada jugador en el campo
    location_formation["jersey_player"] = location_formation["jersey_player"].astype(int)
    passes_formation['pos_max'] = (passes_formation[['jersey_player',
                                                    'jersey_receiver']]
                                   .max(axis='columns'))
    passes_formation['pos_min'] = (passes_formation[['jersey_player',
                                                    'jersey_receiver']]
                                   .min(axis='columns'))
    passes_formation["pos_min"]=passes_formation["pos_min"].astype(int)
    passes_formation["pos_max"]=passes_formation["pos_max"].astype(int)
    #passes_formation.to_excel("passes_formation.xlsx",index=False)
    passes_between = passes_formation.groupby(['pos_min',"pos_max"]).size().reset_index(name='pass_count')

    # add on the location of each player so we have the start and end positions of the lines
    passes_between = passes_between.merge(location_formation, left_on='pos_min', right_on="jersey_player")
    passes_between = passes_between.merge(location_formation, left_on='pos_max', right_on="jersey_player",
                                          suffixes=['', '_end'])
    
    player_location_df = (
        df_pases[["player", "x", "y", "pases"]]
        .groupby("player")
        .agg({
            "x": "mean",
            "y": "mean",
            "pases": "sum"
            })
        .reset_index()
        )
    
    
    players_passes_df=df_pases[["player","receiver","pases"]]
    
    players_passes_df = players_passes_df.merge(player_location_df[['player', 'x', 'y']], 
                                        left_on='player', right_on='player').\
                                            rename(columns={'x': 'passer_x', 
                                                            'y': 'passer_y'}
                                                   )

    players_passes_df = players_passes_df.merge(player_location_df[['player', 'x', 'y']], 
                                            left_on='receiver', right_on='player').\
                                                rename(columns={'x': 'recipient_x', 
                                                                'y': 'recipient_y', 
                                                                'player_x': 'player'}
                                                    ) 
    players_passes_df.drop("player_y",axis=1,inplace=True)
    player_location_df=player_location_df.rename(columns={"pases":"total"})
    players_passes_df=players_passes_df.rename(columns={"pases":"passes","receiver":"pass_recipient"})
    player_names=df_pases[["player","jersey_player"]].drop_duplicates().copy()
    player_names_dict = dict(zip(player_names["player"], player_names["player"]))

    players = pd.unique(players_passes_df[['player', 'pass_recipient']].values.ravel())


    players_loc=player_location_df[["player","x","y"]]
    players_passes_df=players_passes_df[players_passes_df["passes"]>MIN_PASS]
    
    #aqui creo el grafo
    g = ig.Graph(directed=True)
    
    #y aqui añado vertices, los nodos, cada jugador
    g.add_vertices(list(players))

    #aqui los links entre jugadores
    #defino
    edges=list(zip(players_passes_df["player"],players_passes_df["pass_recipient"]))
    
    #añado
    g.add_edges(edges)
    
    #aqui añado los pesos
    g.es["weight"]=players_passes_df["passes"].tolist()
    
    #añado las coordenadas de cada jugador
    coords={}
    for _,row in players_loc.iterrows():
        player=row["player"]
        coords.setdefault(player,[]).append((row["x"],row["y"]))
       
    layout=[coords[player] for player in players]
    
    layout = [coords[player][0] for player in g.vs['name']]

    
    node_fill = "#2F6DB3"
    node_edge = "#2F6DB3"

    edge_color = "#C4B5FD99"
    
    g.vs["color"] = node_fill
    g.vs["frame_color"] = node_edge
    g.vs["frame_width"] = 1.0
    g.es["color"] = edge_color
    
    g.vs["label_dist"]=0.5
    g.vs['label_angle'] = -math.pi/2  
    g.vs['label_size'] = 6    # bigger font size
    g.vs['label_color'] = 'black'
    g.es["arrow_size"]  = 1.4   # 0.8–1.4 usually looks good
    g.es["arrow_width"] = 1.0  
    #fig, ax = plt.subplots()
    
    #asignamos labels a cada vertice, con la label siendo el nombre
    g.vs['label'] = g.vs['name']
    g.es['weight'] = players_passes_df['passes'].tolist()
    max_edge_weight = max(g.es["weight"])
    weights = np.array(g.es['weight'])
    
    #normalizo prq sino no se nota tanto
    min_width, max_width = 1, 7
    scaled_widths = min_width + (weights - weights.min()) / (weights.max() - weights.min()) * (max_width - min_width)
    #controls width of lines
    g.es['width'] = scaled_widths.tolist()
    
    total_passes = players_passes_df.groupby('player')['passes'].sum()
    norm = mcolors.Normalize(vmin=min(total_passes), vmax=max(total_passes))
    cmap = cm.get_cmap('YlOrRd')  # or 'coolwarm', 'plasma', etc.
    

    # Map each player to a color
    #vertex_colors = [mcolors.to_hex(cmap(norm(total_passes.get(player, 0))))
    #                 for player in g.vs['name']]
    
    # Create a list of sizes matching the order of g.vs['name']
    sizes = [total_passes.get(player, 1) for player in g.vs['name']]  # default size 1 if missing

    # Optionally, scale sizes so they look good on plot, e.g.:
    min_size, max_size = 20, 80
    max_node_size=max(sizes)
    min_passes, max_passes = min(sizes), max(sizes)
    scaled_sizes = [
        min_size + (s - min_passes) / (max_passes - min_passes) * (max_size - min_size)
        if max_passes != min_passes else min_size
        for s in sizes
        ]

    g.vs["size"] = scaled_sizes
    radius_pts = (np.array(g.vs["size"]) / 2.0) + 1.2
    
    edge_pairs = np.array(g.get_edgelist(), dtype=int)  
    sources = edge_pairs[:, 0]
    targets = edge_pairs[:, 1]

    edge_curvature = 0.18
    sign = np.where(sources < targets, 1.0, -1.0)        # split A→B vs B→A
    curv = (edge_curvature * sign).tolist()
    ## lo ploteamos 
    
    fig,ax=pitch.draw()
    
    fig.patch.set_facecolor('white')
    pitch.draw(ax=ax) 
    edge_rgba = mcolors.to_rgba("#C4B5FD", 0.6)
    ig.plot(g, layout=layout, target=ax)
    
    norm_teamname=team_analizing.replace(" ","_")


    import matplotlib.patches as mpatches
    color="#2F6DB3"
    circle = mpatches.Ellipse((5, -10), width=4, height=6 * ax.get_data_ratio(), 
                          color=color, clip_on=False)
    ax.add_patch(circle)
    circle = mpatches.Ellipse((11, -10), width=5.5, height=8 * ax.get_data_ratio(), 
                          color=color, clip_on=False)
    ax.add_patch(circle)
    
    circle = mpatches.Ellipse((19, -10), width=7.5, height=11 * ax.get_data_ratio(), 
                          color=color, clip_on=False)
    ax.add_patch(circle)
    
    arrow = FancyArrowPatch(posA=(2,-18), posB=(25, -18), 
                        arrowstyle='->', color='black', 
                        mutation_scale=15, lw=2,clip_on=False)
    ax.add_patch(arrow)
    ax.text(11,-20,f"{MIN_PASS} passes        {max_node_size} passes",fontsize=8,va="top",ha="center",color="black")
    line_col="#C4B5FD99"
    ax.plot([40, 45], [-10, -6], color=line_col, linewidth=1, clip_on=False)
    ax.plot([45, 50], [-10, -6], color=line_col, linewidth=2, clip_on=False)
    ax.plot([50, 55], [-10, -6], color=line_col, linewidth=4, clip_on=False)
    
    arrow = FancyArrowPatch(posA=(40,-18), posB=(60, -18), 
                        arrowstyle='->', color='black', 
                        mutation_scale=15, lw=2,clip_on=False)
    ax.add_patch(arrow)
    ax.text(50,-20,f"{MIN_PASS} passes           {max_edge_weight} passes",fontsize=8,va="top",ha="center",color="black")
    
    
    ax.text(100, 
            -5, 
            f"Minimum Passes: {MIN_PASS}",
            fontsize=10, 
            va='top',
            ha='right',
            color="white"
            )
    output_path=f"{norm_teamname}_passmap.png"
    plt.savefig(f"{norm_teamname}_passmap.png",dpi=300, bbox_inches='tight')


    return fig, output_path    



passnetwork_oneteam("/Users/julieta/Desktop/data_madridcff/f27/pass_matrix_903_2025_g2572345_t13320.xml", "/Users/julieta/Desktop/data_madridcff/f40/f40-squad-102.xml",1)

