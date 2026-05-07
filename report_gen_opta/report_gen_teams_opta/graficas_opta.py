#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 20 12:29:44 2025

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
from sklearn.preprocessing import MinMaxScaler
import mplsoccer
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from pathlib import Path

pd.options.mode.chained_assignment = None  # Oculta SettingWithCopyWarning



events=parse_f70_events("/Users/julieta/Desktop/APP_Generic_Femeni/data_femeni/raw/f70/f70-903-2024-2482790-expectedgoals.xml")



team_summary=get_xG_xGA_allteams("/Users/julieta/Desktop/APP_Generic_Femeni/data_femeni/raw/f72")



    

shots_df=get_shots_shotsA_allteams("/Users/julieta/Desktop/APP_Generic_Femeni/data_femeni/raw/f30")

combined_df=pd.merge(team_summary,shots_df,on="team",how="left")

combined_df["xG_shot"]=combined_df["expected_goals"]/combined_df["Shots"]
combined_df["xG_shot_A"]=combined_df["expected_goals_conceded"]/combined_df["Shots Conceded"]




##########3
equipos_df, league=parse_teams_from_f30("/Users/julieta/Desktop/APP_Generic_Femeni/data_femeni/raw/f30", 903)

equipos_df["% de duelos aereos ganados"]=(equipos_df["Aerial Duels won"]/equipos_df["Aerial Duels"])*100

combined_df=pd.merge(equipos_df,combined_df,left_on="team_name",right_on="team",how="left")

combined_df["% de acierto de pases"]=(combined_df["Total Successful Passes ( Excl Crosses & Corners ) "]/combined_df["Total Passes"])*100

combined_df["Centros totales"]=combined_df["Successful Crosses open play"]+combined_df["Unsuccessful Crosses open play"]

#########


######## PILLAR PPDA 




matches_df=pd.read_excel("/Users/julieta/Desktop/APP_Generic_Femeni/data_femeni/matches_relations.xlsx")


team_analizing="Barcelona Femenino"

df_all_matches=get_all_matches(team_analizing,matches_df)


#df_barca=get_PPDA(team_analizing,df_all_matches,2024)


team_names = ['Atlético de Madrid Femenino', 'Barcelona Femenino',
              'Deportivo de La Coruña Femenino', 'Eibar Femenino',
              'Espanyol Femenino', 'Granada Femenino', 'Levante Femenino',
              'Real Madrid Femenino', 'Sevilla Femenino', 'UD Tenerife Femenino',
              'Valencia Femenino','Madrid CF Femenino',"Real Betis Féminas","Levante Badalona Femenino",
              "Athletic Club Femenino","Real Sociedad Femenino"]



df_all_summaries=get_all_PPDA("/Users/julieta/Desktop/APP_Generic_Femeni/data_femeni/raw/f73","/Users/julieta/Desktop/APP_Generic_Femeni/data_femeni/matches_relations.xlsx",team_names,2024)    

######## xG-xGA ranking
xG_for=combined_df[["team_name","xg_difference","expected_goals","expected_goals_conceded"]]
xG_for=xG_for.sort_values(by="xg_difference",ascending=False)

fig1, ax = plt.subplots(figsize=(14, 10))
plt.bar(xG_for["team_name"],xG_for["xg_difference"],color="blue",edgecolor="black")
plt.ylim(min(0,min(xG_for["xg_difference"])-0.05),max(xG_for["xg_difference"])+0.05)
plt.ylabel("xG-xGa",fontsize=16,fontweight='bold')
plt.xticks(rotation=45, ha='right',fontweight='bold',fontsize=18)
ax.axhline(0, color='black', linewidth=1.3)
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
output_path1="xG_xGa_allteams.png"
fig1.savefig(output_path1, dpi=300, bbox_inches='tight')
plt.close(fig1)

##### xG vs xGA
fig2,ax=plt.subplots(figsize=(16,8))
sns.scatterplot(data=xG_for,x="expected_goals_conceded",y="expected_goals",s=300,facecolors="none",edgecolor="black",ax=ax)
for i, row in xG_for.iterrows():
    plt.text(row['expected_goals_conceded'], row['expected_goals'], row['team_name'], fontsize=12, alpha=0.8,zorder=2)
min_val = min(xG_for["expected_goals_conceded"].min(), xG_for["expected_goals"].min())
max_val = max(xG_for["expected_goals_conceded"].max(), xG_for["expected_goals"].max())
ax.plot([min_val, max_val], [min_val, max_val], ls='--', c='gray', label="1:1 line")
plt.xlim(min(xG_for["expected_goals_conceded"])-0.1,max(xG_for["expected_goals_conceded"]+0.1))
plt.ylim(min(xG_for["expected_goals"])-0.1,max(xG_for["expected_goals"]+0.1))
plt.xlabel("Goles esperados en contra (xGa)",fontsize=14,fontweight="bold")
plt.ylabel("Goles esperados (xG)",fontsize=14,fontweight="bold")
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.5)
output_path2="Scatter_xG_xGa_teams.png"
fig2.savefig(output_path2,dpi=300,bbox_inches="tight")
plt.close(fig2)

########### scatter plot tiros (xG por tiro)

Goles_por_tiro=combined_df[["team_name","expected_goals_sum","expected_goals_conceded_sum"
                            ,"Shots","Shots Conceded"]]

Goles_por_tiro["xGa_por_tiro"]=Goles_por_tiro["expected_goals_conceded_sum"]/Goles_por_tiro["Shots Conceded"]
Goles_por_tiro["xG_por_tiro"]=Goles_por_tiro["expected_goals_sum"]/Goles_por_tiro["Shots"]

fig3,ax=plt.subplots(figsize=(16,8))
sns.scatterplot(data=Goles_por_tiro,x="xGa_por_tiro",y="xG_por_tiro",s=200,facecolors="none",edgecolor="black",ax=ax)
for i, row in Goles_por_tiro.iterrows():
    plt.text(row['xGa_por_tiro'], row['xG_por_tiro'], row['team_name'], fontsize=10, alpha=0.8,zorder=2)
min_val = min(Goles_por_tiro["xGa_por_tiro"].min(), Goles_por_tiro["xG_por_tiro"].min())
max_val = max(Goles_por_tiro["xGa_por_tiro"].max(), Goles_por_tiro["xG_por_tiro"].max())
ax.plot([min_val, max_val], [min_val, max_val], ls='--', c='gray', label="1:1 line")
plt.xlim(min(Goles_por_tiro["xGa_por_tiro"])-0.005,max(Goles_por_tiro["xGa_por_tiro"])+0.005)
plt.ylim(min(Goles_por_tiro["xG_por_tiro"])-0.005,max(Goles_por_tiro["xG_por_tiro"])+0.005)
plt.xlabel("Goles esperados por tiro rival",fontsize=14,fontweight="bold")
plt.ylabel("Goles esperados por tiro",fontsize=14,fontweight="bold")
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.5)
output_path3="Scatter_xG_xGa_por_tiros_teams.png"
fig3.savefig(output_path3,dpi=300,bbox_inches="tight")
plt.close(fig3)

########## METRICAS DEFENSIVAS ####################

#### faltaría fig4 que es recuperaciones 1º tercio vs 3º tercio (sería con parse f24 de TODOS los partidos)
#### llevaría un rato computacionalmente supongo

Duelos_aereos=combined_df[["team_name","Aerial Duels","% de duelos aereos ganados","Games Played"]]
Duelos_aereos["Aerial Duels"]=Duelos_aereos["Aerial Duels"]/Duelos_aereos["Games Played"]

fig6,ax=plt.subplots(figsize=(16,8))
sns.scatterplot(data=Duelos_aereos,x="Aerial Duels",y="% de duelos aereos ganados",s=200,facecolors="none",edgecolor="black",ax=ax)
for i, row in Duelos_aereos.iterrows():
    plt.text(row['Aerial Duels'], row['% de duelos aereos ganados'], row['team_name'], fontsize=10, alpha=0.8,zorder=2)
plt.axhline(Duelos_aereos['% de duelos aereos ganados'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
mean_duelos_ganados = Duelos_aereos['% de duelos aereos ganados'].mean()
plt.xlim(min(Duelos_aereos["Aerial Duels"])-1,max(Duelos_aereos["Aerial Duels"]+1))
plt.ylim(min(Duelos_aereos["% de duelos aereos ganados"])-1,max(Duelos_aereos["% de duelos aereos ganados"]+1))
plt.text(
    Duelos_aereos['Aerial Duels'].max()+1,  # x-coordinate (left of plot)
    mean_duelos_ganados + 0.2,             # y-coordinate slightly above the line
    f"{mean_duelos_ganados:.2f} %",   # formatted text
    color='red',
    fontsize=10,
    fontweight='bold'
)
plt.xlabel("Duelos aéreos",fontsize=14,fontweight="bold")
plt.ylabel("% Duelos aéreos ganados",fontsize=14,fontweight="bold")
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.5)
output_path6="Scatter_duelos_aereos_teams.png"
fig6.savefig(output_path6,dpi=300,bbox_inches="tight")
plt.close(fig6)


############ Despejes vs Interceptaciones
Despejes=combined_df[["team_name","Games Played","Interceptions","Total Clearances"]]
Despejes["interceptaciones"]=Despejes["Interceptions"]/Despejes["Games Played"]
Despejes["despejes"]=Despejes["Total Clearances"]/Despejes["Games Played"]

fig7,ax=plt.subplots(figsize=(16,8))
sns.scatterplot(data=Despejes,x="interceptaciones",y="despejes",s=200,facecolors="none",edgecolor="black",ax=ax)
for i, row in Despejes.iterrows():
    plt.text(row['interceptaciones'], row['despejes'], row['team_name'], fontsize=10, alpha=0.8,zorder=2)
plt.xlim(min(Despejes["interceptaciones"])-1,max(Despejes["interceptaciones"]+1))
plt.ylim(min(Despejes["despejes"])-1,max(Despejes["despejes"]+1))
plt.xlabel("Interceptaciones",fontsize=14,fontweight="bold")
plt.ylabel("Despejes",fontsize=14,fontweight="bold")
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.5)
output_path7="Scatter_despejes_teams.png"
fig7.savefig(output_path7,dpi=300,bbox_inches="tight")
plt.close(fig7)

############ PPDA bar graph


PPDA=df_all_summaries[["team_name","PPDA"]]
PPDA=PPDA.sort_values(by="PPDA",ascending=False)

fig8, ax = plt.subplots(figsize=(14, 10))
plt.bar(PPDA["team_name"],PPDA["PPDA"],color="blue",edgecolor="black")
plt.ylabel("PPDA",fontsize=16,fontweight='bold')
plt.xticks(rotation=45, ha='right',fontweight='bold',fontsize=18)
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
output_path8="PPDA_allteams.png"
fig8.savefig(output_path8, dpi=300, bbox_inches='tight')
plt.close(fig8)

############## PPDA scatter
PPDA_full=df_all_summaries[["team_name","PPDA","PPDA del Rival"]]

fig9,ax=plt.subplots(figsize=(16,8))
sns.scatterplot(data=PPDA_full,x="PPDA del Rival",y="PPDA",s=200,facecolors="none",edgecolor="black",ax=ax)
for i, row in PPDA_full.iterrows():
    plt.text(row['PPDA del Rival'], row['PPDA'], row['team_name'], fontsize=10, alpha=0.8,zorder=2)
min_val = min(PPDA_full["PPDA del Rival"].min(), PPDA_full["PPDA"].min())
max_val = max(PPDA_full["PPDA del Rival"].max(), PPDA_full["PPDA"].max())
ax.plot([0, max_val], [0, max_val], ls='--', c='gray', label="1:1 line")
plt.xlim(min(PPDA_full["PPDA del Rival"])-0.5,max(PPDA_full["PPDA del Rival"]+0.5))
plt.ylim(min(PPDA_full["PPDA"])-0.5,max(PPDA_full["PPDA"]+0.5))
plt.xlabel("PPDA del rival",fontsize=14,fontweight="bold")
plt.ylabel("PPDA",fontsize=14,fontweight="bold")
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.5)
output_path9="Scatter_PPDA_teams.png"
fig9.savefig(output_path9,dpi=300,bbox_inches="tight")
plt.close(fig9)

############# tarjetas amarillas y rojas
tarjetas=combined_df[["team_name","Games Played","Yellow Cards","Total Red Cards"]]

tarjetas["Amarillas"]=(tarjetas["Yellow Cards"]).fillna(0)
tarjetas["Rojas"]=(tarjetas["Total Red Cards"]).fillna(0)

#tarjetas["Amarillas"]=(tarjetas["Yellow Cards"]/tarjetas["Games Played"]).fillna(0)
#tarjetas["Rojas"]=(tarjetas["Total Red Cards"]/tarjetas["Games Played"]).fillna(0)


tarjetas["Totales"]=tarjetas["Amarillas"]+tarjetas["Rojas"]
tarjetas = tarjetas.sort_values("Totales", ascending=False)
fig10,ax=plt.subplots(figsize=(14,10))
plt.bar(tarjetas["team_name"],tarjetas["Rojas"],color="#C70000",edgecolor="black")
plt.bar(tarjetas["team_name"],tarjetas["Amarillas"],bottom=tarjetas["Rojas"],color="#FFE000",edgecolor="black")
plt.ylabel("Promedio de tarjetas",fontsize=16,fontweight='bold')
plt.xticks(rotation=45, ha='right',fontweight='bold',fontsize=18)
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
output_path10="Tarjetas_allteams.png"
fig10.savefig(output_path10, dpi=300, bbox_inches='tight')
plt.close(fig10)


################# METRICAS DE ATAQUE ####################

# fig 11, contraataque vs ataque posicional no puedo hacerlo

################ Pases totales vs % de acierto
Pases=combined_df[["team_name","Total Passes","Passing Accuracy","Games Played"]]
Pases["pases"]=Pases["Total Passes"]/Pases["Games Played"]

fig12,ax=plt.subplots(figsize=(16,8))
sns.scatterplot(data=Pases,x="pases",y="Passing Accuracy",s=200,facecolors="none",edgecolor="black",ax=ax)
for i, row in Pases.iterrows():
    plt.text(row['pases'], row['Passing Accuracy'], row['team_name'], fontsize=10, alpha=0.8,zorder=2)
plt.xlim(min(Pases["pases"])-1.5,max(Pases["pases"]+1.5))
plt.ylim(min(Pases["Passing Accuracy"])-1.5,max(Pases["Passing Accuracy"]+1.5))
plt.xlabel("Pases totales",fontsize=14,fontweight="bold")
plt.ylabel("% de acierto en el pase",fontsize=14,fontweight="bold")
plt.axhline(Pases['Passing Accuracy'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
mean_duelos_ganados =Pases['Passing Accuracy'].mean()

plt.text(
    Pases['pases'].max(),  # x-coordinate (left of plot)
    mean_duelos_ganados + 0.5,             # y-coordinate slightly above the line
    f"{mean_duelos_ganados:.2f} %",   # formatted text
    color='red',
    fontsize=10,
    fontweight='bold'
)
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.5)
output_path12="Scatter_pases_teams.png"
fig12.savefig(output_path12,dpi=300,bbox_inches="tight")
plt.close(fig12)


####### pases último tercio vs pases en profundidad por ahora no lo tengo

############# Centros totales vs centros preciosos
Centros=combined_df[["Centros totales","Crossing Accuracy","team_name","Games Played"]]
Centros["centros"]=Centros["Centros totales"]/Centros["Games Played"]


fig14,ax=plt.subplots(figsize=(16,8))
sns.scatterplot(data=Centros,x="centros",y="Crossing Accuracy",s=200,facecolors="none",edgecolor="black",ax=ax)
for i, row in Centros.iterrows():
    plt.text(row['centros'], row['Crossing Accuracy'], row['team_name'], fontsize=10, alpha=0.8,zorder=2)
plt.xlim(min(Centros["centros"])-1,max(Centros["centros"]+1))
plt.ylim(min(Centros["Crossing Accuracy"])-1,max(Centros["Crossing Accuracy"]+1))
plt.xlabel("Centros totales",fontsize=14,fontweight="bold")
plt.ylabel("% de acierto en los centros",fontsize=14,fontweight="bold")
plt.axhline(Centros['Crossing Accuracy'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
mean_centros_ganados =Centros['Crossing Accuracy'].mean()

plt.text(
    Centros['centros'].max(),  # x-coordinate (left of plot)
    mean_centros_ganados + 0.2,             # y-coordinate slightly above the line
    f"{mean_centros_ganados:.2f} %",   # formatted text
    color='red',
    fontsize=10,
    fontweight='bold'
)
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.5)
output_path14="Scatter_centros_teams.png"
fig14.savefig(output_path14,dpi=300,bbox_inches="tight")
plt.close(fig14)


#################### ACCIONES A BALON PARADO ####################

#   NO SEGURA SI ESTA BIEN
ABP=combined_df[["team_name","Games Played","Attempts from Set Pieces",
                 'Corners Taken (incl short corners)', "Penalties Taken",
                 "Goal Kicks",'Throw Ins to Own Player','Throw Ins to Opposition Player']]
ABP["total_set_pieces"]=(
    combined_df['Corners Taken (incl short corners)'] 
)

ABP["abp"]=ABP["total_set_pieces"]/ABP["Games Played"]
ABP["abp_precision"]=(ABP["Attempts from Set Pieces"]/ABP["total_set_pieces"])*100

fig15,ax=plt.subplots(figsize=(16,8))
sns.scatterplot(data=ABP,x="abp",y="abp_precision",s=200,facecolors="none",edgecolor="black",ax=ax)
for i, row in ABP.iterrows():
    plt.text(row['abp'], row['abp_precision'], row['team_name'], fontsize=10, alpha=0.8,zorder=2)
plt.xlim(min(ABP["abp"])-0.5,max(ABP["abp"]+0.5))
plt.ylim(min(ABP["abp_precision"])-0.5,max(ABP["abp_precision"]+0.5))
plt.xlabel("Acciones a balón parado totales",fontsize=14,fontweight="bold")
plt.ylabel("% de acciones a balón parado con remate",fontsize=14,fontweight="bold")
plt.axhline(ABP['abp_precision'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
mean_abp_ganados =ABP['abp_precision'].mean()

plt.text(
    ABP['abp'].max(),  # x-coordinate (left of plot)
    mean_abp_ganados + 0.2,             # y-coordinate slightly above the line
    f"{mean_abp_ganados:.2f} %",   # formatted text
    color='red',
    fontsize=10,
    fontweight='bold'
)
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.5)
output_path15="Scatter_abp_teams.png"
fig15.savefig(output_path15,dpi=300,bbox_inches="tight")
plt.close(fig15)


 ############# corners totales vs rematados
Corners=combined_df[["team_name","Games Played","Corners Taken (incl short corners)","Successful Corners into Box"]]
Corners["corners"]=Corners["Corners Taken (incl short corners)"]/Corners["Games Played"]
Corners["corners_precision"]=(Corners["Successful Corners into Box"]/Corners["Corners Taken (incl short corners)"])*100

fig16,ax=plt.subplots(figsize=(16,8))
sns.scatterplot(data=Corners,x="corners",y="corners_precision",s=200,facecolors="none",edgecolor="black",ax=ax)
for i, row in Corners.iterrows():
    plt.text(row['corners'], row['corners_precision'], row['team_name'], fontsize=10, alpha=0.8,zorder=2)
plt.xlim(min(Corners["corners"])-0.2,max(Corners["corners"]+0.2))
plt.ylim(min(Corners["corners_precision"])-0.3,max(Corners["corners_precision"]+0.3))
plt.xlabel("Córneres totales",fontsize=14,fontweight="bold")
plt.ylabel("% de córneres rematados",fontsize=14,fontweight="bold")
plt.axhline(Corners['corners_precision'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
mean_corners_ganados =Corners['corners_precision'].mean()

plt.text(
    Corners['corners'].max(),  # x-coordinate (left of plot)
    mean_corners_ganados + 0.2,             # y-coordinate slightly above the line
    f"{mean_corners_ganados:.2f} %",   # formatted text
    color='red',
    fontsize=10,
    fontweight='bold'
)
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.5)
output_path16="Scatter_corners_teams.png"
fig16.savefig(output_path16,dpi=300,bbox_inches="tight")
plt.close(fig16)

############### penaltis vs % de penaltis marcados

Penaltis=combined_df[["team_name","Games Played","Penalties Taken","Penalty Goals"]]
Penaltis["penaltis"]=Penaltis["Penalties Taken"]
Penaltis["penaltis_aciertos"]=(Penaltis["Penalty Goals"]/Penaltis["Penalties Taken"])*100

fig18,ax=plt.subplots(figsize=(16,8))
sns.scatterplot(data=Penaltis,x="penaltis",y="penaltis_aciertos",s=200,facecolors="none",edgecolor="black",ax=ax)
for i, row in Penaltis.iterrows():
    plt.text(row['penaltis'], row['penaltis_aciertos'], row['team_name'], fontsize=10, alpha=0.8,zorder=2)
plt.xlim(min(Penaltis["penaltis"])-0.1,max(Penaltis["penaltis"]+0.1))
plt.ylim(min(Penaltis["penaltis_aciertos"])-0.7,max(Penaltis["penaltis_aciertos"]+0.7))
plt.xlabel("Penaltis totales",fontsize=14,fontweight="bold")
plt.ylabel("% de penaltis marcados",fontsize=14,fontweight="bold")
plt.axhline(Penaltis['penaltis_aciertos'].mean(), color='red', linestyle='--', linewidth=2,zorder=1)
mean_penaltis_ganados =Penaltis['penaltis_aciertos'].mean()

plt.text(
    Penaltis['penaltis'].max(),  # x-coordinate (left of plot)
    mean_penaltis_ganados+0.4,             # y-coordinate slightly above the line
    f"{mean_penaltis_ganados:.2f} %",   # formatted text
    color='red',
    fontsize=10,
    fontweight='bold'
)
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.5)
output_path18="Scatter_penaltis_teams.png"
fig18.savefig(output_path18,dpi=300,bbox_inches="tight")
plt.close(fig18)

######### ahora habría que hacer lo individual del equipo

#es la lista de matches del barca

matches_team=matches_df[matches_df["matchcode"].isin(df_all_matches)]
def match_result(row):
    if row['team1_name'] == team_analizing:
        if row['team1_score'] > row['team2_score']:
            return "Win"
        elif row['team1_score'] < row['team2_score']:
            return "Lose"
        else:
            return "Draw"
    elif row['team2_name'] == team_analizing:
        if row['team2_score'] > row['team1_score']:
            return "Win"
        elif row['team2_score'] < row['team1_score']:
            return "Lose"
        else:
            return "Draw"
    else:
        return None 
matches_team["result"]=matches_team.apply(match_result,axis=1)
def match_home_away(row):
    if row["team1_name"]==team_analizing:
        return "Home"
    elif row["team2_name"]==team_analizing:
        return "Away"
    else:
        return None
matches_team["place"]=matches_team.apply(match_home_away,axis=1)

year=2024
all_matches_data = [] 
for match_id in df_all_matches:
    events_match=parse_f70_xg(f"/Users/julieta/Desktop/APP_Generic_Femeni/data_femeni/raw/f70/f70-903-{year}-{match_id}-expectedgoals.xml")
    all_matches_data.append(events_match)
df_all_matches_summary = pd.concat(all_matches_data, ignore_index=True)

matches_team=pd.merge(matches_team,df_all_matches_summary,left_on="matchcode",right_on="GameID",how="left")


results_palette={
    "Win":"green",
    "Draw":"blue",
    "Lose":"red"
    }
place_palette={
    "Home":"D",
    "Away":"o"
    }

Orense_xG=matches_team[["expected_goals","vs.","expected_goals_conceded","result","place"]]

fig19,ax=plt.subplots(figsize=(12,6))
sns.scatterplot(data=Orense_xG,x="expected_goals_conceded",y="expected_goals",s=200,hue="result",style="place",
                edgecolor="black",palette=results_palette,markers=place_palette,ax=ax)
for i, row in Orense_xG.iterrows():
    opponent=row["vs."]
    plt.text(row["expected_goals_conceded"],row["expected_goals"],f"vs {opponent}")
max_val = max(Orense_xG["expected_goals_conceded"].max(), Orense_xG["expected_goals"].max())
ax.plot([0, max_val], [0, max_val], ls='--', c='gray', label="1:1 line")
plt.xlim(min(Orense_xG["expected_goals_conceded"])-0.2,max(Orense_xG["expected_goals_conceded"]+0.2))
plt.ylim(min(Orense_xG["expected_goals"])-0.2,max(Orense_xG["expected_goals"]+0.2))
plt.xlabel("Goles esperados en contra (xGa)",fontsize=14,fontweight="bold")
plt.ylabel("Goles esperados (xG)",fontsize=14,fontweight="bold")
ax.legend_.remove()
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.5)
output_path19=f"Scatter_xG_{team_analizing}.png"
fig19.savefig(output_path19,dpi=300,bbox_inches="tight")
plt.close(fig19)


################ PPDA vs PPDA del rival

############## Recuperaciones en el 1 tercio vs ultimo tercio
all_events=[]
for match_id in df_all_matches:
    df_events,team_names=parse_f24(f"/Users/julieta/Desktop/APP_Generic_Femeni/data_femeni/raw/f24/f24-903-{year}-{match_id}-eventdetails.xml")
    all_events.append(df_events)
all_events_df = pd.concat(all_events, ignore_index=True)
all_events_df["type_id"]=all_events_df["type_id"].astype(int)
recoveries=all_events_df[(all_events_df["type_id"]==49) & (all_events_df["team_name"]==team_analizing)]


# Filter recoveries
recoveries = all_events_df[all_events_df["type_id"] == 49]

# Group by match and apply the function
recoveries_by_match = recoveries.groupby("game_id").apply(count_zones).reset_index()

matches_team=pd.merge(matches_team,recoveries_by_match,left_on="matchcode",right_on="game_id",how="left")

Orense_rec=matches_team[["vs.","ultimo_tercio","primer_tercio","result","place"]]
fig21,ax=plt.subplots(figsize=(16,8))
sns.scatterplot(data=Orense_rec,x="primer_tercio",y="ultimo_tercio",s=200,hue="result",style="place",
                edgecolor="black",palette=results_palette,markers=place_palette,ax=ax)
for i, row in Orense_rec.iterrows():
    opponent=row["vs."]
    plt.text(row["primer_tercio"],row["ultimo_tercio"],f"vs {opponent}")
plt.xlim(min(Orense_rec["primer_tercio"])-0.5,max(Orense_rec["primer_tercio"]+0.5))
plt.ylim(min(Orense_rec["ultimo_tercio"])-0.5,max(Orense_rec["ultimo_tercio"]+0.5))
plt.xlabel("Balones recuperados en el primer tercio",fontsize=14,fontweight="bold")
plt.ylabel("Balones recuperados en el último tercio",fontsize=14,fontweight="bold")
ax.legend_.remove()
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.5)
output_path21=f"Scatter_recuperados_{team_analizing}.png"
fig21.savefig(output_path21,dpi=300,bbox_inches="tight")
plt.close(fig21)

duelos_team=all_events_df[(all_events_df["type_id"].isin([3,4,7,44,45,54,69])) & (all_events_df["team_name"]==team_analizing) & (all_events_df["first_qualifier_id"].isin([285,286]))]


duels_by_match = duelos_team.groupby("game_id").apply(of_def_duels).reset_index()
matches_team=pd.merge(matches_team,duels_by_match,left_on="matchcode",right_on="game_id",how="left")

Orense_duelos=matches_team[["duelos_ofensivos","duelos_defensivos","vs.","result","place"]]
fig22,ax=plt.subplots(figsize=(16,8))
sns.scatterplot(data=Orense_duelos,x="duelos_defensivos",y="duelos_ofensivos",s=200,hue="result",style="place",
                edgecolor="black",palette=results_palette,markers=place_palette,ax=ax)
for i, row in Orense_duelos.iterrows():
    opponent=row["vs."]
    plt.text(row["duelos_defensivos"],row["duelos_ofensivos"],f"vs {opponent}")
max_val = max(Orense_duelos["duelos_defensivos"].max(), Orense_duelos["duelos_ofensivos"].max())
ax.plot([45, max_val], [40, max_val], ls='--', c='gray', label="1:1 line")
plt.xlim(min(Orense_duelos["duelos_defensivos"])-1,max(Orense_duelos["duelos_defensivos"]+1))
plt.ylim(min(Orense_duelos["duelos_ofensivos"])-1.5,max(Orense_duelos["duelos_ofensivos"]+1.5))
plt.xlabel("Duelos defensivos",fontsize=14,fontweight="bold")
plt.ylabel("Duelos ofensivos",fontsize=14,fontweight="bold")
ax.legend_.remove()
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, linestyle='--', alpha=0.5)
output_path22=f"Scatter_duelos_{team_analizing}.png"
fig22.savefig(output_path22,dpi=300,bbox_inches="tight")
plt.close(fig22)
