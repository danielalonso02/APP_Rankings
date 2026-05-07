#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 15 11:32:15 2025

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
#from IntentoArrays import extract_arrays_wyscout



import re

# df_all_players=pd.read_excel("/Users/julieta/Desktop/LigaF_opta_2024.xlsx")

# player_id=246558
# player_id_analizing=246558

# player_position=df_all_players[df_all_players["player_id"]==player_id]["position"].iloc[0]
# df_player=df_all_players[df_all_players["player_id"]==player_id]

# df_position=df_all_players[df_all_players["position"]==player_position].copy()

def calculate_pizza_values(df_position,position,formulas_filepath):
    #formulas=pd.read_excel("/Users/julieta/Desktop/formulas.xlsx",sheet_name=player_position)
    formulas=pd.read_excel(formulas_filepath,sheet_name=position)
    
    def is_convertible_to_numeric(series):
        # Try converting, return True if any non-NaN result (means convertible)
        return not pd.to_numeric(series, errors='coerce').isna().all()

    for col in df_position.columns:
        if is_convertible_to_numeric(df_position[col]):
            # Convert to numeric safely
            df_position[col] = pd.to_numeric(df_position[col], errors='coerce')
            # Fill NaNs with median
            df_position[col] = df_position[col].fillna(df_position[col].median())
        else:
            # Keep non-numeric columns as is
            pass
        
    for _, row in formulas.iterrows():
        formula = row['formula']
        variable = row['variable_get']

        # Find all columns used in the formula (assuming they are written without df[])
        cols_in_formula = re.findall(r"'(.*?)'", formula)  # look for 'Duels won', 'Duels', etc.

        # Convert those columns to numeric safely
        for col in cols_in_formula:
            df_position[col] = pd.to_numeric(df_position[col], errors='coerce')
            df_position[col] = df_position[col].fillna(df_position[col].median())

            # Replace column name in formula with df["col"]
            formula = formula.replace(f"'{col}'", f'df_position["{col}"]')

        # Evaluate the formula
        try:
            df_position[variable] = eval(formula)
            #print(f"Successfully calculated {variable}")
        except Exception as e:
            print(f"Error calculating {variable}: {e}")
            print("Formula:", formula)
            print("Column types:", df_position[cols_in_formula].dtypes)
            
    return df_position
            
# df_position=calculate_pizza_values(df_position,"Defender","/Users/julieta/Desktop/formulas.xlsx")

# min_minutes=500




def extract_arrays_wyscout(df_position,parameters_file,player_id_analizing,param_entry,min_minutes):
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
    #print(df_stats_position.columns.tolist())
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
        player_array=stats_player[param_ofensive1]
        params_array=param_ofensive1
        percentiles_player=df_stats_percentile[param_ofensive1].values.flatten().tolist()
        param_en=param_of1_id
        
    elif param_entry=="param_of2":
        min_array=df_stats[param_ofensive2].min(axis=0)
        max_array=df_stats[param_ofensive2].max(axis=0)
        player_array=stats_player[param_ofensive2]
        params_array=param_ofensive2
        percentiles_player=df_stats_percentile[param_ofensive2].values.flatten().tolist()
        param_en=param_of2_id
    elif param_entry=="param_def":
        min_array=df_stats[param_defensive].min(axis=0)
        max_array=df_stats[param_defensive].max(axis=0)
        player_array=stats_player[param_defensive]
        params_array=param_defensive
        percentiles_player=df_stats_percentile[param_defensive].values.flatten().tolist()
        param_en=param_def_id
    else:
        min_array=None
        max_array=None
        player_array=None
        params_array=None
        percentiles_player=None
        param_en=None
        
    return min_array,max_array,player_array,params_array, df_stats,percentiles_player,param_en
##############
PLAYER_POSITION="Midfielder"
parameters_file="/Users/julieta/Desktop/APP_Generic_Femeni/report_gen/parameters.xlsx"
#
def notas_tacticas(PLAYER_POSITION,df_position,parameters_file,player_id_analizing,min_minutos):
    
    percentages_file="datoswyscout/wyscout_positions_porcentajes.xlsx"
    dict_excels={"Goalkeeper":"goalkeeper","Defender":"defender","Midfielder":"midfielder",
                 "Forward":"forward"}

    position_excel=dict_excels[PLAYER_POSITION]

    excel_path=f"datoswyscout/variables_wyscout_{position_excel}.xlsx"

    df_ponderations=pd.read_excel(excel_path)

    df_ponderations = df_ponderations.rename(columns={0: "ofensive", "0.1": "defensive"})

    df_ponderations = df_ponderations[~((df_ponderations["ofensive"] == 0) & (df_ponderations["defensive"] == 0))]

    _, _, _, _,df_all_stats,_,_ = extract_arrays_wyscout(df_position,parameters_file,player_id_analizing,"param_of1",min_minutos)

    stats_player=df_all_stats[df_all_stats["player_id"]==player_id_analizing].iloc[0]
    player_position=stats_player["position"]
    df_stats_position=df_all_stats[(df_all_stats["position"]==player_position)].copy()

    numeric_cols_pos = [col for col in df_stats_position.select_dtypes(include=['number']).columns if col != "player_id"]
    # Apply Min-Max scaling to each numeric column
    df_stats_position[numeric_cols_pos] = (df_stats_position[numeric_cols_pos] - df_stats_position[numeric_cols_pos].min()) / (df_stats_position[numeric_cols_pos].max() - df_stats_position[numeric_cols_pos].min())
    #df_stats_position.to_excel("dfstatsposition.xlsx")
    number_of_players_position=len(df_stats_position)

    of_list = df_ponderations.loc[df_ponderations['ofensive'] != 0, 'team_id'].tolist()

    of_stats=df_all_stats[of_list]

    ponderaciones_OF=df_stats_position

    def_list=df_ponderations.loc[df_ponderations['defensive'] != 0, 'team_id'].tolist()


    def_stats=df_all_stats[def_list]

    of_ponderations=df_ponderations.set_index("team_id")["ofensive"].to_dict()


    cols_of=[col for col in df_stats_position.columns if col in of_ponderations]

    of_weights=pd.Series({col: of_ponderations[col] for col in cols_of})

    of_weights=of_weights/of_weights.sum()
    #print(of_weights)
    df_stats_position[cols_of] = df_stats_position[cols_of].fillna(0)
    df_stats_position["OF_score"]=df_stats_position[cols_of].dot(of_weights)
    min_score=df_stats_position["OF_score"].min()
    max_score=df_stats_position["OF_score"].max()

    if max_score == min_score:
        
        df_stats_position["OF_score"] = 0  # or 100, or any constant
    else:
        df_stats_position["OF_score"] = 100 * (df_stats_position["OF_score"] - min_score) / (max_score - min_score)
    #df_stats_position["OF_score"]=100*(df_stats_position["OF_score"]-min_score)/(max_score - min_score)

    #DEFENSIVE
    def_ponderations=df_ponderations.set_index("team_id")["defensive"].to_dict()

    cols_def=[col for col in df_stats_position.columns if col in def_ponderations]

    def_weights=pd.Series({col: def_ponderations[col] for col in cols_def})

    def_weights=def_weights/def_weights.sum()

    df_stats_position["DEF_score"]=df_stats_position[cols_def].dot(def_weights)

    min_score=df_stats_position["DEF_score"].min()
    max_score=df_stats_position["DEF_score"].max()

    if max_score == min_score:
        df_stats_position["DEF_score"] = 0  # or 100, or any constant
    else:
        df_stats_position["DEF_score"] = 100 * (df_stats_position["DEF_score"] - min_score) / (max_score - min_score)
    #df_stats_position["DEF_score"]=100*(df_stats_position["DEF_score"]-min_score)/(max_score - min_score)

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
    #print(player_of_score)

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
    #df_stats_position.to_excel("RANKS_POSITION.xlsx",index=False)

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
    return player_of_score,player_of_letter,player_def_score,player_def_letter,player_full_score,player_full_letter,number_of_players_position,Rank_of,Rank_def,Rank_full


#player_of_score,player_of_letter,player_def_score,player_def_letter,player_full_score,player_full_letter,number_of_players_position,Rank_of,Rank_def,Rank_full=notas_tacticas("Defender",df_position,parameters_file,246558,500)
