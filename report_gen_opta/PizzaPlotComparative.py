#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 18 11:10:18 2025

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
from colorsys import rgb_to_hls
import os
import argparse
import re
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

BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 

formulas_filepath_st=f"{BASE_DIR}/report_gen_opta/formulas.xslx"
def calculate_pizza_values(df_position,position,formulas_filepath=formulas_filepath_st):
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

def pizzaplot_player_opta(opta_filepath,player_id1,player_id2,file_parameters,min_minutos,color="#FFFFFF",league="2º RFEF",season="2024/25"):
    
    
    if not os.path.exists(opta_filepath):
        print(f"El fichero {opta_filepath} no existe.")
        return None
    df_all_players=pd.read_excel(opta_filepath)
    
    if (player_id1 not in df_all_players["player_id"].values) or (player_id2 not in df_all_players["player_id"].values):
        print("No se encuentra al jugador")
        return None

    
    df_all_players=df_all_players[df_all_players["Time Played"]>min_minutos].copy()
    if player_id1 not in df_all_players["player_id"].values:
        print(f"El jugador 1 ha jugado menos de {min_minutos} minutos.")
        return None
    if player_id2 not in df_all_players["player_id"].values:
        print(f"El jugador 2 ha jugado menos de {min_minutos} minutos.")
        return None
    df_player1=df_all_players[df_all_players["player_id"]==player_id1]
    df_player2=df_all_players[df_all_players["player_id"]==player_id2]
    
    player_position1=df_player1["position"].iloc[0]
    player_position2=df_player2["position"].iloc[0]
    if player_position1!=player_position2:
        print(f"No tienen la misma posición, {player_position1}, {player_position2}")
        return None
    else:
        player_position=player_position1

    
    df_all_players=df_all_players[df_all_players["Time Played"]>min_minutos].copy()

    df_position=df_all_players[df_all_players["position"]==player_position].copy()
    
    #CHANGE FORMULAS FOR CORRECT PATH
    df_position=calculate_pizza_values(df_position,player_position,"formulas.xlsx")
    color_selection=color.lstrip("#")
    r,g,b=int(color_selection[0:2],16),int(color_selection[2:4],16),int(color_selection[4:6],16)
    h,l,s=rgb_to_hls(r/255.0,g/255.0,b/255.0)
    if l>0.5:
        letter_color="#000000"
        fig1 = plt.figure(facecolor=color)
        fig2 = plt.figure(facecolor=color)
        fig3 = plt.figure(facecolor=color)
    else:
        letter_color="#F2F2F2"
        fig1 = plt.figure(facecolor=color)
        fig2 = plt.figure(facecolor=color)
        fig3 = plt.figure(facecolor=color)
        
    player_stats_values1=df_position[df_position["player_id"]==player_id1]
    player_stats_values2=df_position[df_position["player_id"]==player_id2]

    if df_position.empty:
        print(f"No hay jugadores con más de {min_minutos} minutos jugados.")
        
    class PlayerNotFoundError(Exception):
        pass

    color_selection=color.lstrip("#")
    r,g,b=int(color_selection[0:2],16),int(color_selection[2:4],16),int(color_selection[4:6],16)
    h,l,s=rgb_to_hls(r/255.0,g/255.0,b/255.0)
    if l>0.5:
        letter_color="#000000"
        fig1 = plt.figure(facecolor=color)
        fig2 = plt.figure(facecolor=color)
        fig3 = plt.figure(facecolor=color)
    else:
        letter_color="#F2F2F2"
        fig1 = plt.figure(facecolor=color)
        fig2 = plt.figure(facecolor=color)
        fig3 = plt.figure(facecolor=color)
    #lo primero es comprobar si esta el jugador
    if (player_id1 not in df_position["player_id"].values) or (player_id2 not in df_position["player_id"].values):
        print("Not in the database")
        #raise PlayerNotFoundError(f"El jugador elegido, {player_id_analizing}, no está en la base de datos o ha jugado menos de {min_minutos}.")
        #return None, None, None, None, None, None  
    df_position.fillna(df_position.mean(numeric_only=True),inplace=True)
    df_stats=df_position.copy()
    positions=["Goalkeeper","Defender","Midfielder","Forward"]
    parameters = {}
    for position in positions:
        try:
            
            df_position = pd.read_excel(f"{BASE_DIR}/report_gen/parameters.xlsx", sheet_name=position)
            
            
            # Crear un diccionario con las claves 'ofensivo' y 'defensivo' y los valores correspondientes
            parameters[position] = {
                "ofensive": df_position['ofensivo'].dropna().tolist(),  # Convertir la columna 'ofensivo' en lista
                "ofensive es":df_position['ofensivo es'].dropna().tolist(),
                "defensive": df_position['defensivo'].dropna().tolist(),  # Convertir la columna 'defensivo' en lista
                "defensive es":df_position['defensivo es'].dropna().tolist(),
                "of_number":df_position["PizzaPlot_of"].dropna().tolist()
            }
        except ValueError:
            print(f"Hoja '{position}' no encontrada en el archivo.")
        except Exception as e:
            print(f"Error al leer la hoja '{position}': {e}")

    general_stats=df_stats[["player_name","team_name","age","Appearances","Time Played","weight","height","player_id","position"]].copy()

    #Una vez tenemos las posiciones genericas de todos los jugadores, hay que dividir por cada posicion

    portero=df_stats[(df_stats["position"]=="Goalkeeper")].copy()
    defensa=df_stats[(df_stats["position"]=="Defender")].copy()
    midfielder=df_stats[(df_stats["position"]=="Midfielder")].copy()
    delantero=df_stats[(df_stats["position"]=="Forward")].copy()
        #filtramos con esos parametros:
    general_stats=["player_name","team_name","age","Appearances","Time Played","weight","height","player_id","position"]

    position_map = {
        "Goalkeeper": portero,
        "Defender": defensa,
        "Midfielder": midfielder,
        "Forward": delantero
        }

    # Select the relevant dataframe based on the player's position
    df = position_map[player_position]

    # Get the list of stats for that position
    columns = pd.Series(general_stats 
        + parameters[player_position]["defensive"] 
         + parameters[player_position]["ofensive"]
         ).unique().tolist()

    columns = [col for col in columns if col in df.columns]
    df = df[columns].copy()

    # Get the stats used for averaging
    columns_avg = pd.Series(
        parameters[player_position]["ofensive"] 
       + parameters[player_position]["defensive"]
       ).unique().tolist()

    # Compute the averages
    columns_avg_existing = [col for col in columns_avg if col in df.columns]

    # Compute the average safely
    values_average = df[columns_avg_existing].mean()
    values_average_num=values_average

    # Store in a dictionary (only for the player's position)
    average_values_ = {player_position: values_average}


    def calculate_and_assign_percentiles(df, *column_lists):

        columns = pd.Series(sum(column_lists, [])).unique().tolist()
        
        # Calcular los percentiles para las columnas 
        for col in columns:
            if col in df.columns:
                values = df[col].values
                percentiles = [percentileofscore(values, x, kind='rank') for x in values]
                df[col] = pd.Series(percentiles).round().astype(int).values
        
        return df

    df = position_map[player_position]

    df = calculate_and_assign_percentiles(
        df,
        parameters[player_position]["defensive"],
        parameters[player_position]["ofensive"]
        )

    # Compute the averages
    columns_avg = pd.Series(
        parameters[player_position]["ofensive"] 
        + parameters[player_position]["defensive"]
        ).unique().tolist()

    #average de los percentiles
    values_average = df[columns_avg].mean().astype(int)

    # Store in a dictionary (only for the player's position)

    average_values_ = {player_position: values_average}

    param_ofensive = parameters[player_position]["ofensive"]
    param_of_label = parameters[player_position]["ofensive es"]
    param_defensive = parameters[player_position]["defensive"]
    param_def_label = parameters[player_position]["defensive es"]

    # Get the dataframe and averages for that position
    df_2 = position_map[player_position]
    #average de los percentiles
    average_values = df_2[columns_avg].mean().astype(int)  # from your earlier computation

    # Calculate pizza values (you already had this function)
    #df_position = calculate_pizza_values(df, player_position, "/Users/julieta/Desktop/formulas.xlsx")

    # Get the player-specific row
    player_stats1 = df[df["player_id"] == player_id1]
    player_stats2 = df[df["player_id"] == player_id2]

    # Get the offensive grouping info
    of_number = parameters[player_position]["of_number"]

    # Initialize lists
    param_ofensive1, param_ofensive2 = [], []
    param_ofensive1_labels, param_ofensive2_labels = [], []

    # Split parameters into groups based on of_number
    for i, param in enumerate(param_ofensive):
        if of_number[i] == 1:
            param_ofensive1.append(param)
        elif of_number[i] == 2:
            param_ofensive2.append(param)

    for i, label in enumerate(param_of_label):
        if of_number[i] == 1:
            param_ofensive1_labels.append(label)
        elif of_number[i] == 2:
            param_ofensive2_labels.append(label)

    param_ofensive1_labels = [label.replace("\\n", "\n") for label in param_ofensive1_labels if pd.notna(label)]
    param_ofensive2_labels = [label.replace("\\n", "\n") for label in param_ofensive2_labels if pd.notna(label)]
    param_def_label = [label.replace("\\n", "\n") for label in param_def_label if pd.notna(label)]
    # Obtener las estadísticas de los jugadores para las listas separadas

    value_stats_ofensive11 = player_stats1[param_ofensive1].values.flatten().tolist()
    value_stats_ofensive21 = player_stats1[param_ofensive2].values.flatten().tolist()
    value_stats_defensive1 = player_stats1[param_defensive].values.flatten().tolist()

    value_stats_ofensive12 = player_stats2[param_ofensive1].values.flatten().tolist()
    value_stats_ofensive22 = player_stats2[param_ofensive2].values.flatten().tolist()
    value_stats_defensive2 = player_stats2[param_defensive].values.flatten().tolist()
        
    position=player_position
    # #####
    #OFENSIVE
    #estos 3 son de valores absolutos, NO PERCENTILES OFENSIVE
    #player_stats_of es VALORES REALES de cada parámetro
    #jugador 1
    player_stats_of11=player_stats_values1[param_ofensive1].values.flatten().tolist()
    player_stats_of21=player_stats_values1[param_ofensive2].values.flatten().tolist()
    #jugador 2
    player_stats_of12=player_stats_values2[param_ofensive1].values.flatten().tolist()
    player_stats_of22=player_stats_values2[param_ofensive2].values.flatten().tolist()


    #Average de TODOS los parametros en VALORES REALES
    average_values_list1=average_values_[player_position]
    #print(f"AVERAGE_VALUES_LIST1: {average_values_list1}")


    #esto son percentiles
    #jugador 1
    values_list_of11=[round(value,2) for value in value_stats_ofensive11]
    values_list_of21=[round(value,2) for value in value_stats_ofensive21]
    average_ofensive1=average_values[param_ofensive1]
    average_ofensive2=average_values[param_ofensive2]
    average_ofensive_list1 = [round(value, 2) for value in average_ofensive1.tolist()]
    average_ofensive_list2 = [round(value, 2) for value in average_ofensive2.tolist()]

    #jugador 2
    values_list_of12=[round(value,2) for value in value_stats_ofensive12]
    values_list_of22=[round(value,2) for value in value_stats_ofensive22]

    #Esto son VALORES REALES
    #jugador 1

    average_values_of11=[round(value,2) for value in average_values_list1[param_ofensive1].tolist()]
    average_values_of21=[round(value,2) for value in average_values_list1[param_ofensive2].tolist()]
    values_list_of1 = [round(value, 2) for value in value_stats_ofensive11]
    values_list_of2 = [round(value, 2) for value in value_stats_ofensive21]
    params_offset_of1 = [True] * len(param_ofensive1)
    params_offset_of2 = [True] * len(param_ofensive2)
    
    
    average_values_of1=[round(value,2) for value in values_average_num[param_ofensive1].tolist()]
    average_values_of2=[round(value,2) for value in values_average_num[param_ofensive2].tolist()]
    average_values_def=[round(value,2) for value in values_average_num[param_defensive].tolist()]
    #jugador 2

    average_values_of12=[round(value,2) for value in average_values_list1[param_ofensive1].tolist()]
    average_values_of22=[round(value,2) for value in average_values_list1[param_ofensive2].tolist()]



    #DEFENSIVE
    #Valores REALES 
    #average_values_def=[round(value,2) for value in average_values_list1[param_defensive].tolist()]
    #jugador 1
    player_stats_def1=player_stats_values1[param_defensive].values.flatten().tolist()
    #jugador 2
    player_stats_def2=player_stats_values2[param_defensive].values.flatten().tolist()
    #estos 3 son de valores absolutos, NO PERCENTILES

    #Percentiles
    #jugador 1
    values_list_def1=[round(value,2) for value in value_stats_defensive1]
    #jugador 2 
    values_list_def2=[round(value,2) for value in value_stats_defensive2]
    average_defensive=average_values[param_defensive]
    average_defensive_list = [round(value, 2) for value in average_defensive.tolist()]
    params_offset_def = [True] * len(param_defensive)

    player_name1=player_stats1["player_name"].iloc[0]
    player_name2=player_stats2["player_name"].iloc[0]

    positions_name_dict={"Goalkeeper":"porteros","Defender":"defensas",
                          "Midfielder":"centrocampistas","Forward":"delanteros"}
     # font_normal = FontManager('https://raw.githubusercontent.com/googlefonts/roboto/main/'
     #                           'src/hinted/Roboto-Regular.ttf')
     # font_italic = FontManager('https://raw.githubusercontent.com/googlefonts/roboto/main/'
     #                           'src/hinted/Roboto-Italic.ttf')
     # font_bold = FontManager('https://raw.githubusercontent.com/google/fonts/main/apache/robotoslab/'
     #                         'RobotoSlab[wght].ttf')
     
    fig1 = plt.figure(figsize=(14, 16), facecolor=color)
    
    ax1 = fig1.add_subplot(111, projection="polar", facecolor=color)
    fig1.subplots_adjust(top=0.85, bottom=0.20)
    

    baker_of = PyPizza(
        params=param_ofensive1_labels,
        background_color=color,
        straight_line_color="#222222",
        straight_line_lw=2,
        last_circle_lw=1,
        last_circle_color="#222222",
        other_circle_ls="-.",
        other_circle_lw=1
        )

    baker_of.make_pizza(
        values_list_of11,
        compare_values=values_list_of12,
        ax=ax1,
        color_blank_space="same",
        param_location=112,
        blank_alpha=0.4,
        kwargs_slices=dict(facecolor="#1A78CF", edgecolor="#000000", zorder=1, linewidth=1,alpha=0.4),
        kwargs_compare=dict(facecolor="#FF8C18", edgecolor="#222222",zorder=2, linewidth=2),
        kwargs_params=dict(color=letter_color, fontsize=24, zorder=5, va="center"),
        kwargs_values=dict(color="#000000", fontsize=18,
            bbox=dict(edgecolor="#000000", facecolor="#1A78CF", boxstyle="round,pad=0.2", lw=1)
        ),
        kwargs_compare_values=dict(color="#000000", fontsize=12,
            bbox=dict(edgecolor="#000000", facecolor="#FF8C18", boxstyle="round,pad=0.2", lw=1)
        ),
    )
    params_offset_of1 = [True]*len(param_ofensive1_labels)
    baker_of.adjust_texts(params_offset_of1, offset=-0.15, adj_comp_values=True)

    #NARANJA-> FF8C18  // AZUL -> 1A78CF
    theta1 = np.linspace(0, 2 * np.pi, len(param_ofensive1), endpoint=False)
    radius1 = [value for value in values_list_of1]

    for i, value in enumerate(values_list_of11):
        ax1.text(
            theta1[i], radius1[i], f"{value}%",
            color='black', ha='center', va='center', fontsize=18,
            bbox=dict(edgecolor="000000", facecolor="#7CBAF3", boxstyle="round,pad=0.5", lw=1)
        )
    compare_radius = [value for value in values_list_of12]
    theta = np.linspace(0, 2 * np.pi, len(values_list_of12), endpoint=False)
    theta1_adjusted = [ angle - 0.17 if offset else angle for angle, offset in zip(theta, params_offset_of1) ]
    for i, percentage in enumerate(compare_radius):
        # Offset for compare values: use a slightly smaller or larger radius to avoid label overlap
        # For example, offset inward by 0.15 units (or a fraction)
        
        r = compare_radius[i] #+ offset
        ax1.text(
            theta1_adjusted[i], r, f"{percentage}%",
            color='black', ha='center', va='center', fontsize=18,
            bbox=dict(edgecolor="#000000", facecolor="#FF8C18", boxstyle="round,pad=0.5", lw=1)
            )
    #baker_of.adjust_texts(params_offset_of1, offset=-0.15, adj_comp_values=True)


    legend_labels_of1 = [
        f"{param}: {value1:.2f} | {value2:.2f}, ({values:.2f})"
        for param, value1,value2, values in zip(param_ofensive1, player_stats_of11,player_stats_of12, average_values_of1)
    ]
    handles_of = [
        Line2D([0], [0], marker='o', markeredgecolor=letter_color, color='w',
               markerfacecolor="#E74C3C", markersize=14, label=label)
        for label in legend_labels_of1
        ]
    legend1 = fig1.legend(handles=handles_of, loc='lower center', fontsize=18, ncol=2,
                      frameon=False, bbox_to_anchor=(0.5, 0.0))
    for label in legend1.get_texts():
        label.set_color(letter_color)

    fig_text(0.5, 0.99, f"Percentil de <{player_name1}> vs <{player_name2}> en {league}",
             size=30, fig=fig1, highlight_textprops=[{"color": '#1A78CF'},{"color":"#FF8C18"}],
             ha="center", color=letter_color)

    fig1.text(0.5, 0.94,
              f"{league}, promedio de {positions_name_dict[position]} | Temporada {season}",
              size=28, ha="center", color=letter_color)
    output_path1 = os.path.join(BASE_DIR, f"pizzaplot_ofensivo_1_{player_name1}_{player_name2}_{position}.png")
    fig1.savefig(output_path1, dpi=500)
    plt.close(fig1)
    
    # ----- PIZZA PLOT OFENSIVO 2 -----
    
    if len(values_list_of2)!=0:
        fig2 = plt.figure(figsize=(14, 16), facecolor=color)
        ax2 = fig2.add_subplot(111, projection="polar", facecolor=color)
        
        
        fig2.subplots_adjust(top=0.85, bottom=0.20)

        # ----- PIZZA PLOT OFENSIVO 2-----
        baker_of2 = PyPizza(
            params=param_ofensive2_labels,
            background_color=color,
            straight_line_color="#222222",
            straight_line_lw=2,
            last_circle_lw=1,
            last_circle_color="#222222",
            other_circle_ls="-.",
            other_circle_lw=1
            )
        baker_of2.make_pizza(
            values_list_of21,
            compare_values=values_list_of22,
            ax=ax2,
            color_blank_space="same",
            param_location=112,
            blank_alpha=0.4,
            kwargs_slices=dict(facecolor="#1A78CF", edgecolor="#000000", zorder=1, linewidth=2,alpha=0.4),
            kwargs_compare=dict(facecolor="#FF8C18", edgecolor="#222222",zorder=2, linewidth=2),
            kwargs_params=dict(color=letter_color, fontsize=24, zorder=5, va="center"),
            kwargs_values=dict(color="#000000", fontsize=18, 
                               bbox=dict(edgecolor="#000000", facecolor="#1A78CF", boxstyle="round,pad=0.2", lw=1)
                               ),
            kwargs_compare_values=dict(color="#000000", fontsize=12, 
                               bbox=dict(edgecolor="#000000", facecolor="#FF8C18", boxstyle="round,pad=0.2", lw=1)
                               )
            )
        params_offset_of2 = [True]*len(param_ofensive2_labels)
        baker_of2.adjust_texts(params_offset_of2, offset=-0.15, adj_comp_values=True)
        theta2 = np.linspace(0, 2 * np.pi, len(param_ofensive2), endpoint=False)
        radius2 = [value for value in values_list_of21]

        for i, value in enumerate(values_list_of21):
            ax2.text(
                theta2[i], radius2[i], f"{value}%",
                color='black', ha='center', va='center', fontsize=18,
                bbox=dict(edgecolor="000000", facecolor="#7CBAF3", boxstyle="round,pad=0.5", lw=1)
                )
        compare_radius = [value for value in values_list_of22]
        theta = np.linspace(0, 2 * np.pi, len(values_list_of22), endpoint=False)
        theta1_adjusted = [ angle - 0.17 if offset else angle for angle, offset in zip(theta, params_offset_of2) ]
        for i, percentage in enumerate(compare_radius):
            # Offset for compare values: use a slightly smaller or larger radius to avoid label overlap
            # For example, offset inward by 0.15 units (or a fraction)
            
            r = compare_radius[i] #+ offset
            ax2.text(
                theta1_adjusted[i], r, f"{percentage}%",
                color='black', ha='center', va='center', fontsize=18,
                bbox=dict(edgecolor="#000000", facecolor="#FF8C18", boxstyle="round,pad=0.5", lw=1)
                )
        # baker_of2.adjust_texts(params_offset_of2, offset=-0.20, adj_comp_values=True)

    

        legend_labels_of2 = [
            f"{param}: {value1:.2f} | {value2:.2f}, ({values:.2f})"
            for param, value1,value2, values in zip(param_ofensive2, player_stats_of21,player_stats_of22, average_values_of2)
            ]
        handles_of2 = [
            Line2D([0], [0], marker='o', markeredgecolor=letter_color, color='w',
                   markerfacecolor="#E74C3C", markersize=14, label=label)
            for label in legend_labels_of2
            ]
        legend2 = fig2.legend(handles=handles_of2, loc='lower center', fontsize=18, ncol=2,
                          frameon=False, bbox_to_anchor=(0.5, 0.0))
        for label in legend2.get_texts():
            label.set_color(letter_color)

        fig_text(0.5, 0.99, f"Percentil de <{player_name1}> vs <{player_name2}> en {league}",
                 size=30, fig=fig2, highlight_textprops=[{"color": '#1A78CF'},{"color":"#FF8C18"}],
                 ha="center", color=letter_color)

        fig2.text(0.5, 0.94,
                  f"{league}, {positions_name_dict[position]} | Temporada {season}",
                  size=28, ha="center", color=letter_color)
        output_path2 = os.path.join(BASE_DIR, f"pizzaplot_ofensivo_2_{player_name1}_{player_name2}_{position}.png")
        fig2.savefig(output_path2, dpi=500)
        plt.close(fig2)
        #plt.show()
    else:
        output_path2=None
        fig2=None


    ##### ---- y el defensivo -----
    fig3 = plt.figure(figsize=(14, 16), facecolor=color)
    ax3 = fig3.add_subplot(111, projection="polar", facecolor=color)
    fig3.subplots_adjust(top=0.85, bottom=0.25)
    baker_def = PyPizza(
        params=param_def_label,
        background_color=color,
        straight_line_color="#222222",
        straight_line_lw=2,
        last_circle_lw=1,
        last_circle_color="#222222",
        other_circle_ls="-.",
        other_circle_lw=1
    )

    baker_def.make_pizza(
        values_list_def1,
        compare_values=values_list_def2,
        ax=ax3,
        color_blank_space="same",
        blank_alpha=0.4,
        param_location=110,
        kwargs_slices=dict(facecolor="#1A78CF", edgecolor="#000000", zorder=1, linewidth=2,alpha=0.4),
        kwargs_compare=dict(facecolor="#FF8C18", edgecolor="#222222",zorder=2, linewidth=2),
        kwargs_params=dict(color=letter_color, fontsize=24, va="center"),
        kwargs_values=dict(
            color="#000000", fontsize=18,
            bbox=dict(edgecolor="#000000", facecolor="#1A78CF", boxstyle="round,pad=0.2", lw=1)
        ),
        kwargs_compare_values=dict(
            color="#000000", fontsize=12,
            bbox=dict(edgecolor="#000000", facecolor="#FF8C18", boxstyle="round,pad=0.2", lw=1)
        )
    )
    params_offset_def = [True]*len(values_list_def1)
    baker_def.adjust_texts(params_offset_def, offset=-0.15, adj_comp_values=True)

    # Etiquetas sobre los valores defensivos
    num_params = len(param_defensive)
    theta = np.linspace(0, 2 * np.pi, num_params, endpoint=False)
    radius = [value for value in values_list_def1]


    ###
    ####
    for i, param in enumerate(values_list_def1):
        percentage = radius[i]
        ax3.text(
            theta[i], radius[i], f"{percentage}%",
            color='black', ha='center', va='center', fontsize=18,
            bbox=dict(edgecolor="000000", facecolor="#7CBAF3", boxstyle="round,pad=0.5", lw=1)
        )
        
    compare_radius = [value for value in values_list_def2]
    theta = np.linspace(0, 2 * np.pi, len(param_defensive), endpoint=False)
    theta1_adjusted = [ angle - 0.17 if offset else angle for angle, offset in zip(theta, params_offset_def) ]
    for i, percentage in enumerate(compare_radius):
        # Offset for compare values: use a slightly smaller or larger radius to avoid label overlap
        # For example, offset inward by 0.15 units (or a fraction)
        #offset = -0.15  # Try positive or negative to tune appearance, or match 'adjust_texts' offset
        r = compare_radius[i] #+ offset
        ax3.text(
            theta1_adjusted[i], r, f"{percentage}%",
            color='black', ha='center', va='center', fontsize=18,
            bbox=dict(edgecolor="#000000", facecolor="#FF8C18", boxstyle="round,pad=0.5", lw=1)
            )
        
    
   # baker_def.adjust_texts(params_offset_def, offset=-0.230, adj_comp_values=True)
    
    # Leyenda para defensivo
    legend_labels_def = [
        f"{param}: {value1:.2f} | {value2:.2f}, ({values:.2f})"
        for param, value1,value2, values in zip(param_defensive, player_stats_def1,player_stats_def2, average_values_def)
    ]
    handles_def = [
        Line2D([0], [0], marker='o', markeredgecolor=letter_color, color='w', markerfacecolor="#E74C3C", markersize=14, label=label)
        for label in legend_labels_def
    ]
    legend_def = fig3.legend(handles=handles_def, loc='lower center', fontsize=18, ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0))
    for label in legend_def.get_texts():
        label.set_color(letter_color)
    # Texto global defensivo

    fig_text(
        0.515, 0.99, f"Percentil de <{player_name1}> vs <{player_name2}> en {league}",
        size=30, fig=fig3,
        highlight_textprops=[{"color": '#1A78CF'},{"color":"#FF8C18"}],
        ha="center", color=letter_color
    )
    fig_text(
        0.515, 0.96, f"{league}, {positions_name_dict[position]} | Temporada {season}",
        size=28, fig=fig3,
        ha="center", color=letter_color
    )
    
    


    output_path3 = os.path.join(BASE_DIR, f"pizzaplot_defensivo_{player_name1}_{player_name2}_{position}.png")
    fig3.savefig(output_path3, dpi=500)
    plt.close(fig3)
    
    json_path = os.path.join(BASE_DIR, "image_paths_comparative.json")

    # Your image paths
    result = {"images": [output_path1, output_path2, output_path3]}
    print("RESULTS:",result)
    # print("OUT1:",output_path1)
    # print("OUT2:",output_path2)
    # print("OUT3:",output_path3)
    # Write to file safely
    with open(json_path, "w") as f:
        json.dump(result, f)
        f.flush()
        os.fsync(f.fileno())  # ensures the data is physically written
    
    print("✅ Imagenes generadas")
    
#pizzaplot_player_opta("/Users/julieta/Desktop/APP_Generic_Femeni/report_gen/LigaF_opta_2024.xlsx",176173,165355,"/Users/julieta/Desktop/APP_Generic_Femeni/report_gen/parameters.xlsx",500,color="#FFFFFF",league="Liga F",season="2024/25")
#pizzaplot_player_opta(opta_filepath,player_id_analizing,file_parameters,min_minutos,color="#FFFFFF",league="2º RFEF",season="2024/25")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--opta_filepath", type=str, required=True)
    parser.add_argument("--player_id1", type=int, required=True)
    parser.add_argument("--player_id2", type=int, required=True)
    parser.add_argument("--parameters_file", type=str, required=True)
    parser.add_argument("--min_minutes", type=int, default=500)
    parser.add_argument("--color_selection", type=str, default="#FFFFFF")
    parser.add_argument("--current_league", type=str, default="Liga F")
    parser.add_argument("--season", type=str, default="2024/25")

    args = parser.parse_args()
    print(args)

    pizzaplot_player_opta(
        opta_filepath=args.opta_filepath,
        player_id1=args.player_id1,
        player_id2=args.player_id2,
        file_parameters=args.parameters_file,
        min_minutos=args.min_minutes,
        color=args.color_selection,
        league=args.current_league,
        season=args.season
    ) 
