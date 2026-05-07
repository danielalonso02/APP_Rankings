#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  8 11:35:51 2025

@author: julieta
"""

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
import difflib
import unicodedata
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 

from pathlib import Path

reportgen_path = Path(__file__).resolve().parent
folder_skillcorner = reportgen_path / "SKILLCORNER"

formulas_filepath_st=f"{BASE_DIR}/report_gen_opta/formulas.xlsx"
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

def pizzaplot_phys(PLAYER_NAME, PLAYER_POSITION, folder_path, color="#FFFFFF"):
    
    # 1. Carga de datos con encoding robusto
    try:
        df_phys = pd.read_csv(f"{folder_path}/SkillCorner-2026-03-30.csv", delimiter=";", encoding="utf-8-sig")
    except:
        try:
            df_phys = pd.read_csv(f"{folder_path}/SkillCorner-2026-03-30.csv", delimiter=";", encoding="latin1")
        except FileNotFoundError:
            print("Error: El archivo no existe.")
            return None, None, None, None, None

    col_name = "Player" if "Player" in df_phys.columns else "Jugador"

    # 2. Función de limpieza extrema (Maneja los caracteres rotos de tus capturas)
    def clean_extreme(text):
        if pd.isna(text): return ""
        text = str(text)
        replacements = {
            'Ã¸': 'O', 'Ã¤': 'A', 'Ã­': 'I', 'Ã©': 'E', 'Ã¡': 'A', 
            'Ã³': 'O', 'Ãº': 'U', 'Ã±': 'N', 'Ã': 'A', 'Â': '', 
            'A¤': 'A', 'A©': 'E', 'A­': 'I', 'A±': 'N', 'Ã¼': 'U'
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        text = text.upper()
        text = re.sub(r'[^A-Z\s]', ' ', text)
        return " ".join(text.split())

    # 3. BUSCADOR INTELIGENTE DE JUGADORA
    target_clean = clean_extreme(PLAYER_NAME)
    nombres_csv = df_phys[col_name].unique()
    match_final = None

    # Prioridad 1: Contención (Caza a Angela Sosa en Angela Sosa Martin)
    for n_csv in nombres_csv:
        n_csv_clean = clean_extreme(n_csv)
        if target_clean in n_csv_clean or n_csv_clean in target_clean:
            match_final = n_csv
            break
    
    # Prioridad 2: Similitud (Fuzzy) si la contención falla
    if not match_final:
        # Creamos una lista de nombres limpios para comparar
        clean_list = [clean_extreme(n) for n in nombres_csv]
        close_matches = difflib.get_close_matches(target_clean, clean_list, n=1, cutoff=0.7)
        if close_matches:
            idx = clean_list.index(close_matches[0])
            match_final = nombres_csv[idx]

    if match_final:
        PLAYER_NAME = match_final # Sincronizamos con el nombre exacto del CSV
    else:
        print(f"ERROR: No se encontró a {PLAYER_NAME} en datos físicos.")
        return None, None, None, None, None

    # 4. Filtrado por posición para percentiles justos
    dictionary_positions = {
        "Delantera": "Center Forward", "Defensa": "Central Defender",
        "Centrocampista ofensivo": "Midfield", "Centrocampista defensivo": "Midfield",
        "Lateral": "Full Back", "Extremo": "Wide Attacker"
    }
    pos_to_filter = dictionary_positions.get(PLAYER_POSITION, PLAYER_POSITION)
    
    if "Position Group" in df_phys.columns:
        df_phys = df_phys[df_phys["Position Group"] == pos_to_filter]
    elif "Position" in df_phys.columns:
        df_phys = df_phys[df_phys["Position"] == pos_to_filter]

    # --- El resto del proceso de percentiles y gráfico sigue igual ---
    columns_pizza = ["PSV-99", "Running Distance P90", "HSR Distance P90",
                     "Sprint Distance P90", "HI Count P90", "Medium Acceleration Count P90",
                     "High Acceleration Count P90", "Medium Deceleration Count P90",
                     "High Deceleration Count P90", "Explosive Acceleration to Sprint Count P90"]

    def calculate_and_assign_percentiles(df, cols):
        df_res = df.copy()
        for col in cols:
            if col in df_res.columns:
                values = df_res[col].values
                df_res[col] = [int(percentileofscore(values, x, kind='rank')) for x in values]
        return df_res

    # Datos reales (Raw)
    player_raw_data = df_phys[df_phys[col_name] == PLAYER_NAME][columns_pizza].values.flatten().tolist()
    player_raw_data = [int(val) for val in player_raw_data]
    
    # Percentiles
    phys_position = calculate_and_assign_percentiles(df_phys, columns_pizza)
    player_df = phys_position[phys_position[col_name] == PLAYER_NAME]
    player_params = player_df[columns_pizza].values.flatten().tolist()
    
    # Medias de la posición
    phys_average = df_phys[columns_pizza].mean().fillna(0).astype(int).tolist()

    # --- Configuración Visual del Gráfico ---
    # (Mantengo tu lógica de colores y PyPizza...)
    color_selection = color.lstrip("#")
    r, g, b = int(color_selection[0:2], 16), int(color_selection[2:4], 16), int(color_selection[4:6], 16)
    h, l, s = rgb_to_hls(r/255.0, g/255.0, b/255.0)
    letter_color = "#000000" if l > 0.5 else "#F2F2F2"

    parameters_show = ["PSV-99", "Distancia corriendo /90", "Distancia corriendo \n a alta intensidad /90",
                       "Distancia a Sprint /90", "Número de actividades \n a alta intensidad /90",
                       "Número de aceleraciones \n medias /90", "Número de \n aceleraciones altas /90",
                       "Número de decelaraciones \n medias /90", "Número de \n decelaraciones altas /90",
                       "Número de aceleraciones \n explosivas a Sprint /90"]

    params_down = [p.replace("\n", "") for p in parameters_show]
    
    fig1 = plt.figure(figsize=(16, 20), facecolor=color)
    ax1 = fig1.add_subplot(111, projection="polar", facecolor=color)

    baker_of = PyPizza(
        params=parameters_show,
        background_color=color,
        straight_line_color="#222222",
        straight_line_lw=1,
        last_circle_lw=1,
        last_circle_color="#222222",
        other_circle_ls="-.",
        other_circle_lw=1
    )

    baker_of.make_pizza(
        player_params,
        ax=ax1,
        color_blank_space="same",
        param_location=112,
        blank_alpha=0.4,
        kwargs_slices=dict(facecolor="#1A78CF", edgecolor="#000000", zorder=1, linewidth=1),
        kwargs_params=dict(color=letter_color, fontsize=24, zorder=5, va="center"),
        kwargs_values=dict(color="#000000", fontsize=18,
                           bbox=dict(edgecolor="#000000", facecolor="#1A78CF", boxstyle="round,pad=0.2", lw=1))
    )

    # Añadir los porcentajes sobre los sectores
    theta1 = np.linspace(0, 2 * np.pi, len(columns_pizza), endpoint=False)
    for i, value in enumerate(player_params):
        ax1.text(theta1[i], value, f"{value}%", color='black', ha='center', va='center', fontsize=18,
                 bbox=dict(edgecolor="000000", facecolor="#7CBAF3", boxstyle="round,pad=0.5", lw=1))

    # Ajustes finales y Leyenda
    legend_labels = [f"{p}: {v} ({a})" for p, v, a in zip(params_down, player_raw_data, phys_average)]
    handles = [Line2D([0], [0], marker='o', color='w', markerfacecolor="#E74C3C", markersize=14, label=l) for l in legend_labels]
    
    legend1 = fig1.legend(handles=handles, loc='lower center', fontsize=18, ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0))
    for text in legend1.get_texts(): text.set_color(letter_color)

    fig_text(0.5, 0.95, f"<Percentil de {PLAYER_NAME} en Liga F> ", size=28, fig=fig1, 
             highlight_textprops=[{"color": '#1A78CF'}], ha="center", color=letter_color)

    output_path1 = f"pizzaplot_fisico_{PLAYER_NAME}_{PLAYER_POSITION}.png"
    fig1.savefig(output_path1, dpi=300, bbox_inches='tight')
    
    return fig1, output_path1

def pizzaplot_player_opta(opta_filepath,player_id_analizing,file_parameters,min_minutos,color="#FFFFFF",league="2º RFEF",season="2024/25"):
    
    
    if not os.path.exists(opta_filepath):
        print(f"El fichero {opta_filepath} no existe.")
        return None
    df_all_players=pd.read_excel(opta_filepath)
    
    if player_id_analizing not in df_all_players["player_id"].values:
        print("No se encuentra al jugador")
        return None

    
    df_all_players=df_all_players[df_all_players["Time Played"]>min_minutos].copy()
    if player_id_analizing not in df_all_players["player_id"].values:
        print(f"El jugador ha jugado menos de {min_minutos} minutos.")
        return None
    df_player=df_all_players[df_all_players["player_id"]==player_id_analizing]
    player_position=df_player["position"].iloc[0]

    df_position=df_all_players[df_all_players["position"]==player_position].copy()
    #CHANGE FORMULAS FOR CORRECT PATH
    df_position=calculate_pizza_values(df_position, player_position, f"{BASE_DIR}/report_gen_opta/formulas.xlsx")
    
    df_stats=df_position
    
    df_stats=df_stats[df_stats["Time Played"]>min_minutos].copy()
    
    if df_stats.empty:
        print(f"No hay jugadores con más de {min_minutos} minutos jugados.")
        return None,None,None,None, None, None
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
        fig4 = plt.figure(facecolor=color)
    else:
        letter_color="#F2F2F2"
        fig1 = plt.figure(facecolor=color)
        fig2 = plt.figure(facecolor=color)
        fig3 = plt.figure(facecolor=color)
        fig4 = plt.figure(facecolor=color)
    #lo primero es comprobar si esta el jugador
    if player_id_analizing not in df_stats["player_id"].values:
        raise PlayerNotFoundError(f"El jugador elegido, {player_id_analizing}, no está en la base de datos o ha jugado menos de {min_minutos}.")
        return None, None, None, None, None, None  
    df_stats.fillna(df_stats.mean(numeric_only=True),inplace=True)
    
    df_stats=df_position

    
    player_stats_values=df_stats[df_stats["player_id"]==player_id_analizing]

    if df_stats.empty:
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
        fig4 = plt.figure(facecolor=color)
    else:
        letter_color="#F2F2F2"
        fig1 = plt.figure(facecolor=color)
        fig2 = plt.figure(facecolor=color)
        fig3 = plt.figure(facecolor=color)
        fig4 = plt.figure(facecolor=color)
    #lo primero es comprobar si esta el jugador
    if player_id_analizing not in df_stats["player_id"].values:
        print("NO")
        #raise PlayerNotFoundError(f"El jugador elegido, {player_id_analizing}, no está en la base de datos o ha jugado menos de {min_minutos}.")
        #return None, None, None, None, None, None  
    df_stats.fillna(df_stats.mean(numeric_only=True),inplace=True)
    positions=["Goalkeeper","Defender","Midfielder","Forward"]
    parameters = {}
    for position in positions:
        try:
            
            df_position = pd.read_excel(f"{BASE_DIR}/report_gen_opta/parameters.xlsx", sheet_name=position)
            
            
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
            if col in df.columns:   # check existence
                
                values = df[col].values
            percentiles = [
                percentileofscore(values, x, kind='rank') 
                for x in values
            ]
            
            
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
    player_stats = df[df["player_id"] == player_id_analizing]

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

    # Clean up labels
    param_ofensive1_labels = [label.replace("\\n", "\n") for label in param_ofensive1_labels if pd.notna(label)]
    param_ofensive2_labels = [label.replace("\\n", "\n") for label in param_ofensive2_labels if pd.notna(label)]
    param_def_label = [label.replace("\\n", "\n") for label in param_def_label if pd.notna(label)]

    # Extract the player’s stat values for each group
    value_stats_ofensive1 = player_stats[param_ofensive1].values.flatten().tolist()
    value_stats_ofensive2 = player_stats[param_ofensive2].values.flatten().tolist()
    value_stats_defensive = player_stats[param_defensive].values.flatten().tolist()

    position=player_position
        # #####
        #OFENSIVE
        #estos 3 son de valores absolutos, NO PERCENTILES OFENSIVE
        #player_stats_of es VALORES REALES de cada parámetro
    player_stats_of1=player_stats_values[param_ofensive1].values.flatten().tolist()
    player_stats_of2=player_stats_values[param_ofensive2].values.flatten().tolist()
        #Average de TODOS los parametros en VALORES REALES
    average_values_list=average_values_[player_position]

    #esto son percentiles
    values_list_of1=[round(value,2) for value in value_stats_ofensive1]
    values_list_of2=[round(value,2) for value in value_stats_ofensive2]
    average_ofensive1=average_values[param_ofensive1]
    average_ofensive2=average_values[param_ofensive2]
    average_ofensive_list1 = [round(value, 2) for value in average_ofensive1.tolist()]
    average_ofensive_list2 = [round(value, 2) for value in average_ofensive2.tolist()]
        #Esto son VALORES REALES
    average_values_of1=[round(value,2) for value in values_average_num[param_ofensive1].tolist()]
    average_values_of2=[round(value,2) for value in values_average_num[param_ofensive2].tolist()]
    values_list_of1 = [round(value, 2) for value in value_stats_ofensive1]
    values_list_of2 = [round(value, 2) for value in value_stats_ofensive2]
    params_offset_of1 = [True] * len(param_ofensive1)
    params_offset_of2 = [True] * len(param_ofensive2)

        #DEFENSIVE
        #Valores REALES 
    average_values_def=[round(value,2) for value in values_average_num[param_defensive].tolist()]
    player_stats_def=player_stats_values[param_defensive].values.flatten().tolist()
        #estos 3 son de valores absolutos, NO PERCENTILES
        #Percentiles
    values_list_def=[round(value,2) for value in value_stats_defensive]
    average_defensive=average_values[param_defensive]
    average_defensive_list = [round(value, 2) for value in average_defensive.tolist()]
    params_offset_def = [True] * len(param_defensive)

    league="Liga F"
    season="2024/25"
    player_name=player_stats["player_name"].iloc[0]

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
         straight_line_lw=1,
         last_circle_lw=1,
         last_circle_color="#222222",
         other_circle_ls="-.",
         other_circle_lw=1
         )

    baker_of.make_pizza(
         values_list_of1,
         ax=ax1,
         color_blank_space="same",
         param_location=112,
         blank_alpha=0.4,
         kwargs_slices=dict(facecolor="#1A78CF", edgecolor="#000000", zorder=1, linewidth=1),
         kwargs_params=dict(color=letter_color, fontsize=24, zorder=5, va="center"),
         kwargs_values=dict(color="#000000", fontsize=18,
             bbox=dict(edgecolor="#000000", facecolor="#1A78CF", boxstyle="round,pad=0.2", lw=1)
         )
     )

    theta1 = np.linspace(0, 2 * np.pi, len(param_ofensive1), endpoint=False)
    radius1 = [value for value in values_list_of1]

    for i, value in enumerate(values_list_of1):
         ax1.text(
             theta1[i], radius1[i], f"{value}%",
             color='black', ha='center', va='center', fontsize=18,
             bbox=dict(edgecolor="000000", facecolor="#7CBAF3", boxstyle="round,pad=0.5", lw=1)
         )

    baker_of.adjust_texts(params_offset_of1, offset=-0.30, adj_comp_values=True)


    legend_labels_of1 = [
         f"{param}: {value:.2f}, ({values:.2f})"
         for param, value, values in zip(param_ofensive1, player_stats_of1, average_values_of1)
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

    fig_text(0.5, 0.99, f"<Percentil de {player_name} en {league}> ",
              size=30, fig=fig1, highlight_textprops=[{"color": '#1A78CF'}],
              ha="center", color=letter_color)

    fig1.text(0.5, 0.94,
               f"{league}, promedio de {positions_name_dict[position]} | Temporada {season}",
               size=28, ha="center", color=letter_color)
    pizzaplots_dir = os.path.join(BASE_DIR, "report_gen_opta", "pizzaplots")
    os.makedirs(pizzaplots_dir, exist_ok=True)
    output_path1 = os.path.join(pizzaplots_dir, f"pizzaplot_ofensivo_1_{player_id_analizing}_{player_position}.png")
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
            straight_line_lw=1,
            last_circle_lw=1,
            last_circle_color="#222222",
            other_circle_ls="-.",
            other_circle_lw=1
            )
        baker_of2.make_pizza(
            values_list_of2,
            ax=ax2,
            color_blank_space="same",
            param_location=112,
            blank_alpha=0.4,
            kwargs_slices=dict(facecolor="#1A78CF", edgecolor="#000000", zorder=1, linewidth=1),
            kwargs_params=dict(color=letter_color, fontsize=24, zorder=5, va="center"),
            kwargs_values=dict(color="#000000", fontsize=18, 
                               bbox=dict(edgecolor="#000000", facecolor="#1A78CF", boxstyle="round,pad=0.2", lw=1)
                               )
            )

        theta2 = np.linspace(0, 2 * np.pi, len(param_ofensive2), endpoint=False)
        radius2 = [value for value in values_list_of2]

        for i, value in enumerate(values_list_of2):
            ax2.text(
                theta2[i], radius2[i], f"{value}%",
                color='black', ha='center', va='center', fontsize=18,
                bbox=dict(edgecolor="000000", facecolor="#7CBAF3", boxstyle="round,pad=0.5", lw=1)
                )

        # baker_of2.adjust_texts(params_offset_of2, offset=-0.20, adj_comp_values=True)

    

        legend_labels_of2 = [
            f"{param}: {value:.2f}, ({values:.2f})"
            for param, value, values in zip(param_ofensive2, player_stats_of2, average_values_of2)
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

        fig_text(0.5, 0.99, f"<Percentil de {player_name} en {league}> ",
                 size=30, fig=fig2, highlight_textprops=[{"color": '#1A78CF'}],
                 ha="center", color=letter_color)

        fig2.text(0.5, 0.94,
                  f"{league}, {positions_name_dict[position]} | Temporada {season}",
                  size=28, ha="center", color=letter_color)
        output_path2 = os.path.join(pizzaplots_dir, f"pizzaplot_ofensivo_2_{player_id_analizing}_{player_position}.png")
        fig2.savefig(output_path2, dpi=500)
        plt.close(fig2)
    else:
        output_path2 = None
        fig2 = None


    ##### ---- y el defensivo -----
    fig3 = plt.figure(figsize=(14, 16), facecolor=color)
    ax3 = fig3.add_subplot(111, projection="polar", facecolor=color)
    fig3.subplots_adjust(top=0.85, bottom=0.25)
    baker_def = PyPizza(
        params=param_def_label,
        background_color=color,
        straight_line_color="#222222",
        straight_line_lw=1,
        last_circle_lw=1,
        last_circle_color="#222222",
        other_circle_ls="-.",
        other_circle_lw=1
    )

    baker_def.make_pizza(
        values_list_def,
        ax=ax3,
        color_blank_space="same",
        blank_alpha=0.4,
        param_location=110,
        kwargs_slices=dict(facecolor="#1A78CF", edgecolor="#000000", zorder=1, linewidth=1),
        kwargs_params=dict(color=letter_color, fontsize=24, va="center"),
        kwargs_values=dict(
            color="#000000", fontsize=18,
            bbox=dict(edgecolor="#000000", facecolor="#1A78CF", boxstyle="round,pad=0.2", lw=1)
        )
    )

    # Etiquetas sobre los valores defensivos
    num_params = len(param_defensive)
    theta = np.linspace(0, 2 * np.pi, num_params, endpoint=False)
    radius = [value for value in values_list_def]

    for i, param in enumerate(values_list_def):
        percentage = radius[i]
        ax3.text(
            theta[i], radius[i], f"{percentage}%",
            color='black', ha='center', va='center', fontsize=18,
            bbox=dict(edgecolor="000000", facecolor="#7CBAF3", boxstyle="round,pad=0.5", lw=1)
        )
   # baker_def.adjust_texts(params_offset_def, offset=-0.230, adj_comp_values=True)
    
    # Leyenda para defensivo
    legend_labels_def = [
        f"{param}: {value:.2f}, ({values:.2f})"
        for param, value, values in zip(param_defensive, player_stats_def, average_values_def)
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
        0.515, 0.99, f"<Percentil de {player_name} en {league}> ",
        size=30, fig=fig3,
        highlight_textprops=[{"color": '#1A78CF'}],
        ha="center", color=letter_color
    )
    fig_text(
        0.515, 0.96, f"{league}, {positions_name_dict[position]} | Temporada {season}",
        size=28, fig=fig3,
        ha="center", color=letter_color
    )
    
    


    output_path3 = os.path.join(pizzaplots_dir, f"pizzaplot_defensivo_{player_id_analizing}_{player_position}.png")
    fig3.savefig(output_path3, dpi=500)
    plt.close(fig3)
    
    fig4,output_path4=pizzaplot_phys(player_name, position, folder_skillcorner, color="#FFFFFF")

    json_path = os.path.join(BASE_DIR, "image_paths.json")

    # Store paths relative to report_gen_opta/ so individual_player.py can join them correctly
    report_gen_opta_dir = os.path.join(BASE_DIR, "report_gen_opta")
    result = {"images": [
        os.path.relpath(output_path1, report_gen_opta_dir),
        os.path.relpath(output_path2, report_gen_opta_dir) if output_path2 else None,
        os.path.relpath(output_path3, report_gen_opta_dir),
        os.path.relpath(output_path4, report_gen_opta_dir),
        
    ]}
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
    
#pizzaplot_player_opta("/Users/julieta/Desktop/APP_Generic_Femeni/report_gen/LigaF_opta_2024.xlsx",176173,"/Users/julieta/Desktop/APP_Generic_Femeni/report_gen/parameters.xlsx",500,color="#FFFFFF",league="Liga F",season="2024/25")
#pizzaplot_player_opta(opta_filepath,player_id_analizing,file_parameters,min_minutos,color="#FFFFFF",league="2º RFEF",season="2024/25")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--opta_filepath", type=str, required=True)
    parser.add_argument("--player_id_analizing", type=int, required=True)
    parser.add_argument("--parameters_file", type=str, required=True)
    parser.add_argument("--min_minutes", type=int, default=500)
    parser.add_argument("--color_selection", type=str, default="#FFFFFF")
    parser.add_argument("--current_league", type=str, default="Liga F")
    parser.add_argument("--season", type=str, default="2024/25")

    args = parser.parse_args()
    print(args)

    pizzaplot_player_opta(
        opta_filepath=args.opta_filepath,
        player_id_analizing=args.player_id_analizing,
        file_parameters=args.parameters_file,
        min_minutos=args.min_minutes,
        color=args.color_selection,
        league=args.current_league,
        season=args.season
    ) 
