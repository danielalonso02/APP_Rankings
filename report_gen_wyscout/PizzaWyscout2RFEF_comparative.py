# -*- coding: utf-8 -*-
"""
Created on Fri Apr 10 12:28:48 2026

@author: danie
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


def pizzaplot_player(wyscout_file1, wyscout_file2=None, parameters_file=None, player_id1=None, player_id2=None, min_minutes=500, position_number=1, color_selection_og="#34495E", league="LIGA F", season="2025/26"):
    """
    Genera pizza plots comparativos entre dos jugadoras.
    Soporta jugadoras de ligas distintas (wyscout_file1 != wyscout_file2).
    Los percentiles se calculan contra la liga propia de cada jugadora.
    """
    if wyscout_file2 is None:
        wyscout_file2 = wyscout_file1

    try:
        df_stats1 = pd.read_excel(wyscout_file1)
    except FileNotFoundError:
        print(f"Error: El archivo '{wyscout_file1}' no existe.")
        return None, None, None, None, None, None

    try:
        df_stats2 = pd.read_excel(wyscout_file2)
    except FileNotFoundError:
        print(f"Error: El archivo '{wyscout_file2}' no existe.")
        return None, None, None, None, None, None

    df_stats1["player_id"] = df_stats1.index + 2
    df_stats2["player_id"] = df_stats2.index + 2

    df_stats1 = df_stats1[df_stats1["Minutos jugados"] >= min_minutes]
    df_stats2 = df_stats2[df_stats2["Minutos jugados"] >= min_minutes]

    same_league = (wyscout_file1 == wyscout_file2)
    if same_league:
        df_stats = df_stats1.copy()
        player_id2_internal = player_id2
    else:
        offset = int(df_stats1["player_id"].max()) + 100
        df_stats2_offset = df_stats2.copy()
        df_stats2_offset["player_id"] = df_stats2_offset["player_id"] + offset
        player_id2_internal = player_id2 + offset
        df_stats = pd.concat([df_stats1, df_stats2_offset], ignore_index=True)

    if df_stats.empty:
        print(f"No hay jugadores con más de {min_minutes} minutos jugados.")
        return None, None, None, None, None, None
    class PlayerNotFoundError(Exception):
        pass
   
    color_selection=color_selection_og.lstrip("#")
    r,g,b=int(color_selection[0:2],16),int(color_selection[2:4],16),int(color_selection[4:6],16)
    h,l,s=rgb_to_hls(r/255.0,g/255.0,b/255.0)
    if l>0.5:
        letter_color="#000000"
        fig1 = plt.figure(facecolor=color_selection_og)
        fig2 = plt.figure(facecolor=color_selection_og)
        fig3 = plt.figure(facecolor=color_selection_og)
    else:
        letter_color="#F2F2F2"
        fig1 = plt.figure(facecolor=color_selection_og)
        fig2 = plt.figure(facecolor=color_selection_og)
        fig3 = plt.figure(facecolor=color_selection_og)
    #lo primero es comprobar si esta el jugador
    if player_id1 not in df_stats["player_id"].values:
        raise PlayerNotFoundError(f"El jugador elegido, {player_id1}, no está en la base de datos o ha jugado menos de {min_minutes}.")
        return None, None, None, None, None, None
    
    if player_id2_internal not in df_stats["player_id"].values:
        raise PlayerNotFoundError(f"El jugador elegido, {player_id2}, no está en la base de datos o ha jugado menos de {min_minutes}.")
        return None, None, None, None, None, None  
    
    df_stats.fillna(df_stats.mean(numeric_only=True),inplace=True)
    
    positions_dict={"GK":"portera","LB":"lateral","RB":"lateral","DMF":"defmid","OF":"ofmid",
                    "AMF":"ofmid","LCB":"defensa","RCB":"defensa","LWF":"extremo","RWF":"extremo",
                    "LAMF":"ofmid","RAMF":"ofmid","LCMF":"ofmid","RCMF":"ofmid","CF":"delantera",
                    "CB":"defensa","RW":"extremo","LDMF":"defmid","LW":"extremo","RDMF":"defmid",
                    }
    positions=["portera","defensa","defmid","ofmid","lateral","delantera","extremo"]
    

    parameters = {}
    for position in positions:
        try:
            
            df_position = pd.read_excel(parameters_file, sheet_name=position)
            
            
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
    
    def map_positions(positions_str):
        positions = str(positions_str).split(", ")
        general_positions = [positions_dict.get(pos, pos) for pos in positions]
        seen = []
        for p in general_positions:
            if p not in seen:
                seen.append(p)
        return ", ".join(seen)

    df_stats["general_position"] = df_stats["Posición específica"].apply(map_positions)

    df_stats[['general_position', 'general_position2',"general_position3"]] = df_stats['general_position'].str.split(", ", n=2, expand=True)
    if "Valor de mercado (Transfermarkt)" in df_stats.columns:
        market_value_col = "Valor de mercado (Transfermarkt)"
    elif "Valor de mercado" in df_stats.columns:
        market_value_col = "Valor de mercado"
    else:
        market_value_col = None

    contract_col = "Vencimiento contrato" if "Vencimiento contrato" in df_stats.columns else None

    base_cols = ["Jugador", "Equipo", "Equipo durante el período seleccionado", "Edad"]
    if market_value_col:
        base_cols.append(market_value_col)
    if contract_col:
        base_cols.append(contract_col)
    base_cols += ["Partidos jugados", "Minutos jugados", "player_id", "general_position", "general_position2", "general_position3"]

    # Añadir columnas ausentes a df_stats ANTES de hacer slices por posición
    if not market_value_col:
        df_stats["Valor de mercado"] = None
        market_value_col = "Valor de mercado"
    if not contract_col:
        df_stats["Vencimiento contrato"] = None
        contract_col = "Vencimiento contrato"

    general_stats = df_stats[base_cols].copy()
    
    #Una vez tenemos las posiciones genericas de todos los jugadores, hay que dividir por cada posicion
    
    portera=df_stats[(df_stats["general_position"]=="portera") | (df_stats["general_position2"]=="portera") | (df_stats["general_position3"]=="portera")].copy()
    defensa=df_stats[(df_stats["general_position"]=="defensa") | (df_stats["general_position2"]=="defensa") | (df_stats["general_position3"]=="defensa")].copy()
    defmid=df_stats[(df_stats["general_position"]=="defmid") | (df_stats["general_position2"]=="defmid") | (df_stats["general_position3"]=="defmid")].copy()
    ofmid=df_stats[(df_stats["general_position"]=="ofmid") | (df_stats["general_position2"]=="ofmid") | (df_stats["general_position3"]=="ofmid")].copy()
    delantera=df_stats[(df_stats["general_position"]=="delantera") | (df_stats["general_position2"]=="delantera") | (df_stats["general_position3"]=="delantera")].copy()
    extremo=df_stats[(df_stats["general_position"]=="extremo") | (df_stats["general_position2"]=="extremo") | (df_stats["general_position3"]=="extremo")].copy()
    lateral=df_stats[(df_stats["general_position"]=="lateral") | (df_stats["general_position2"]=="lateral") | (df_stats["general_position3"]=="lateral")].copy()
    #filtramos con esos parametros:
    general_stats=["Jugador","Equipo","Equipo durante el período seleccionado","Edad",
        market_value_col,"Vencimiento contrato","Partidos jugados","Minutos jugados","player_id"]

    positions=["portera","defensa","defmid","ofmid","lateral","delantera","extremo"]

    columns_goal = pd.Series(general_stats + parameters["portera"]["defensive"] + parameters["portera"]["ofensive"]).unique().tolist()
    portera =portera[columns_goal].copy()

    columns_defense = pd.Series(general_stats + parameters["defensa"]["defensive"] + parameters["defensa"]["ofensive"]).unique().tolist()
    defensa = defensa[columns_defense].copy()


    columns_defmid = pd.Series(general_stats + parameters["defmid"]["defensive"] + parameters["defmid"]["ofensive"]).unique().tolist()
    defmid = defmid[columns_defmid].copy()


    columns_ofmid = pd.Series(general_stats + parameters["ofmid"]["defensive"] + parameters["ofmid"]["ofensive"]).unique().tolist()
    ofmid = ofmid[columns_ofmid].copy()


    columns_striker = pd.Series(general_stats + parameters["delantera"]["defensive"] + parameters["delantera"]["ofensive"]).unique().tolist()
    delantera = delantera[columns_striker].copy()


    columns_wing = pd.Series(general_stats + parameters["extremo"]["defensive"] + parameters["extremo"]["ofensive"]).unique().tolist()
    extremo = extremo[columns_wing].copy()


    columns_lateral = pd.Series(general_stats + parameters["lateral"]["defensive"] + parameters["lateral"]["ofensive"]).unique().tolist()
    lateral = lateral[columns_lateral].copy()
    
    #Antes de sacar los percentiles saco las MEDIAS de los valores reales
    columns_goal2= pd.Series(parameters["portera"]["ofensive"] + parameters["portera"]["defensive"]).unique().tolist()
    portera_values_average=portera[columns_goal2].mean()
    columns_defense2 = pd.Series( parameters["defensa"]["ofensive"] + parameters["defensa"]["defensive"] ).unique().tolist()
    defensa_values_average= defensa[columns_defense2].mean()
    columns_defmid2 = pd.Series(parameters["defmid"]["ofensive"] + parameters["defmid"]["defensive"]).unique().tolist()
    defmid_values_average=defmid[columns_defmid2].mean()
    columns_ofmid2 = pd.Series(parameters["ofmid"]["ofensive"] + parameters["ofmid"]["defensive"]).unique().tolist()
    ofmid_values_average=ofmid[columns_ofmid2].mean()
    columns_striker2 = pd.Series(parameters["delantera"]["ofensive"] + parameters["delantera"]["defensive"]).unique().tolist()
    delantera_values_average=delantera[columns_striker2].mean()
    columns_wing2 = pd.Series(parameters["extremo"]["ofensive"] + parameters["extremo"]["defensive"]).unique().tolist()
    extremo_values_average=extremo[columns_wing2].mean()
    lateral_columns2=pd.Series(parameters["lateral"]["ofensive"] + parameters["lateral"]["defensive"]).unique().tolist()
    lateral_values_average=lateral[lateral_columns2].mean()
    #y lo meto todo en un diccionario
    average_values_={"portera":portera_values_average,"defensa":defensa_values_average,"lateral":lateral_values_average,
                    "ofmid":ofmid_values_average,"defmid":defmid_values_average,
                    "delantera":delantera_values_average,"extremo":extremo_values_average}
    
    
    #AQUI CALCULO LOS PERCENTILES
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

    portera = calculate_and_assign_percentiles(portera, parameters["portera"]["defensive"], parameters["portera"]["ofensive"])
    defensa = calculate_and_assign_percentiles(defensa, parameters["defensa"]["defensive"], parameters["defensa"]["ofensive"])
    defmid = calculate_and_assign_percentiles(defmid,parameters["defmid"]["defensive"], parameters["defmid"]["ofensive"])
    ofmid = calculate_and_assign_percentiles(ofmid, parameters["ofmid"]["defensive"], parameters["ofmid"]["ofensive"])
    delantera = calculate_and_assign_percentiles(delantera, parameters["delantera"]["defensive"], parameters["delantera"]["ofensive"])
    extremo = calculate_and_assign_percentiles(extremo, parameters["extremo"]["defensive"], parameters["extremo"]["ofensive"])
    lateral = calculate_and_assign_percentiles(lateral, parameters["lateral"]["defensive"], parameters["lateral"]["ofensive"])


    #ahora habría que sacar las medias
    columns_goal2= pd.Series(parameters["portera"]["ofensive"] + parameters["portera"]["defensive"]).unique().tolist()
    portera_average=portera[columns_goal2].mean().astype(int)
    columns_defense2 = pd.Series( parameters["defensa"]["ofensive"] + parameters["defensa"]["defensive"] ).unique().tolist()
    defensa_average= defensa[columns_defense2].mean().astype(int)
    columns_defmid2 = pd.Series(parameters["defmid"]["ofensive"] + parameters["defmid"]["defensive"]).unique().tolist()
    defmid_average=defmid[columns_defmid2].mean().astype(int)
    columns_ofmid2 = pd.Series(parameters["ofmid"]["ofensive"] + parameters["ofmid"]["defensive"]).unique().tolist()
    ofmid_average=ofmid[columns_ofmid2].mean().astype(int)
    columns_striker2 = pd.Series(parameters["delantera"]["ofensive"] + parameters["delantera"]["defensive"]).unique().tolist()
    delantera_average=delantera[columns_striker2].mean().astype(int)
    columns_wing2 = pd.Series(parameters["extremo"]["ofensive"] + parameters["extremo"]["defensive"]).unique().tolist()
    extremo_average=extremo[columns_wing2].mean().astype(int)
    lateral_columns2=pd.Series(parameters["lateral"]["ofensive"] + parameters["lateral"]["defensive"]).unique().tolist()
    lateral_average=lateral[lateral_columns2].mean().astype(int)
    
    
    #####################################################################################


    values_dict = {
        "portera": [parameters["portera"]["ofensive"], parameters["portera"]["ofensive es"], parameters["portera"]["defensive"], parameters["portera"]["defensive es"], portera, portera_average],
        "defensa": [parameters["defensa"]["ofensive"], parameters["defensa"]["ofensive es"], parameters["defensa"]["defensive"], parameters["defensa"]["defensive es"], defensa, defensa_average],
        "lateral": [parameters["lateral"]["ofensive"], parameters["lateral"]["ofensive es"], parameters["lateral"]["defensive"], parameters["lateral"]["defensive es"], lateral, lateral_average],
        "defmid": [parameters["defmid"]["ofensive"], parameters["defmid"]["ofensive es"], parameters["defmid"]["defensive"], parameters["defmid"]["defensive es"], defmid, defmid_average],
        "ofmid": [parameters["ofmid"]["ofensive"], parameters["ofmid"]["ofensive es"], parameters["ofmid"]["defensive"], parameters["ofmid"]["defensive es"], ofmid, ofmid_average],
        "delantera": [parameters["delantera"]["ofensive"], parameters["delantera"]["ofensive es"], parameters["delantera"]["defensive"], parameters["delantera"]["defensive es"], delantera, delantera_average],
        "extremo": [parameters["extremo"]["ofensive"], parameters["extremo"]["ofensive es"], parameters["extremo"]["defensive"], parameters["extremo"]["defensive es"], extremo, extremo_average]
        }
    
    # --- BLOQUE DE VALIDACIÓN Y EXTRACCIÓN COMPARATIVA ---
    
    # 1. Obtener las filas de datos de ambos jugadores para comparar posiciones
    try:
        p1_row = df_stats[df_stats["player_id"] == player_id1].iloc[0]
        p2_row = df_stats[df_stats["player_id"] == player_id2_internal].iloc[0]
        
        player_name1 = p1_row["Jugador"]
        player_name2 = p2_row["Jugador"]
        
        # Obtenemos sus listas de posiciones (pueden tener varias separadas por coma)
        pos1_list = [p.strip() for p in p1_row["general_position"].split(",")]
        pos2_list = [p.strip() for p in p2_row["general_position"].split(",")]
    except IndexError:
        print("Error: No se encontró a uno de los jugadores.")
        return None, None, None, None, None, None

    # 2. Comprobar si comparten AL MENOS una posición
    posicion_comun = None
    for p in pos1_list:
        if p in pos2_list and p in values_dict:
            posicion_comun = p
            break # Nos quedamos con la primera coincidencia
    
    if not posicion_comun:
        print(f"\n[ERROR] COMPARATIVA IMPOSIBLE")
        print(f"{player_name1} juega de: {pos1_list}")
        print(f"{player_name2} juega de: {pos2_list}")
        print("No comparten ninguna posición general para comparar percentiles.\n")
        return None, None, None, None, None, None

    print(f"Validado: Comparando a ambos como '{posicion_comun}'")

    # 3. Extraer los datos de la posición común del diccionario values_dict
    # Estructura: [param_of, param_of_es, param_def, param_def_es, df_pos, avg_perc]
    current_config = values_dict[posicion_comun]
    
    p_ofensive    = current_config[0]
    p_ofensive_es = current_config[1]
    p_defensive   = current_config[2]
    p_defensive_es = current_config[3]
    df_posicion   = current_config[4]
    
    # 4. Extraer los percentiles de cada jugadora (del DF que ya está calculado)
    # Filtramos en df_posicion para asegurar que sus percentiles son relativos a esa posición
    stats_p1 = df_posicion[df_posicion["player_id"] == player_id1].iloc[0]
    stats_p2 = df_posicion[df_posicion["player_id"] == player_id2_internal].iloc[0]

    # 5. Separar parámetros Ofensivos 1 y 2 usando el of_number que guardamos antes
    # (Lo sacamos del diccionario 'parameters' original que creaste al principio)
    of_numbers = parameters[posicion_comun]["of_number"]
    
    param_of1, param_of1_es = [], []
    param_of2, param_of2_es = [], []
    
    for i in range(len(p_ofensive)):
        if of_numbers[i] == 1:
            param_of1.append(p_ofensive[i])
            param_of1_es.append(p_ofensive_es[i])
        else:
            param_of2.append(p_ofensive[i])
            param_of2_es.append(p_ofensive_es[i])
    


    # 1. Ya tenemos la 'posicion_comun' y 'stats_p1', 'stats_p2' del paso anterior.
    # Ahora extraemos la configuración de esa posición:
    param_ofensive, param_of_label, param_defensive, param_def_label, full_values, average_values = values_dict[posicion_comun]
    
    # 2. Obtener of_number desde la configuración original
    of_number = parameters[posicion_comun]["of_number"]
    
    # 3. Inicializamos las listas de parámetros y etiquetas (son las mismas para ambas)
    param_ofensive1, param_ofensive1_labels = [], []
    param_ofensive2, param_ofensive2_labels = [], []
    
    # Dividir los parámetros ofensivos según el valor de of_number
    for i, param in enumerate(param_ofensive):
        if of_number[i] == 1:
            param_ofensive1.append(param)
            param_ofensive1_labels.append(param_of_label[i])
        elif of_number[i] == 2:
            param_ofensive2.append(param)
            param_ofensive2_labels.append(param_of_label[i])

    # Limpiar etiquetas (saltos de línea)
    param_ofensive1_labels = [label.replace("\\n", "\n") for label in param_ofensive1_labels if pd.notna(label)]
    param_ofensive2_labels = [label.replace("\\n", "\n") for label in param_ofensive2_labels if pd.notna(label)]
    param_def_label = [label.replace("\\n", "\n") for label in param_def_label if pd.notna(label)]

    # 4. EXTRAER LOS VALORES PARA AMBAS JUGADORAS
    # --- Ofensivo 1 ---
    values_of1_p1 = stats_p1[param_ofensive1].values.flatten().tolist()
    values_of1_p2 = stats_p2[param_ofensive1].values.flatten().tolist()
    
    # --- Ofensivo 2 ---
    values_of2_p1 = stats_p1[param_ofensive2].values.flatten().tolist()
    values_of2_p2 = stats_p2[param_ofensive2].values.flatten().tolist()
    
    # --- Defensivo ---
    values_def_p1 = stats_p1[param_defensive].values.flatten().tolist()
    values_def_p2 = stats_p2[param_defensive].values.flatten().tolist()

    # Guardamos la posición para el título
    position = posicion_comun
    
    
# --- PREPARACIÓN DE VALORES REALES Y MEDIAS PARA LEYENDAS ---
    # Extraemos los promedios de la liga para la posición común
    avg_vals_list = average_values_[posicion_comun]
    
    # Medias de la liga
    avg_of1 = [round(v, 2) for v in avg_vals_list[param_ofensive1].tolist()]
    avg_of2 = [round(v, 2) for v in avg_vals_list[param_ofensive2].tolist()]
    avg_def = [round(v, 2) for v in avg_vals_list[param_defensive].tolist()]
    
    # Valores reales de la Jugadora 1
    real_of1_p1 = [round(v, 2) for v in p1_row[param_ofensive1].tolist()]
    real_of2_p1 = [round(v, 2) for v in p1_row[param_ofensive2].tolist()]
    real_def_p1 = [round(v, 2) for v in p1_row[param_defensive].tolist()]
    
    # Valores reales de la Jugadora 2
    real_of1_p2 = [round(v, 2) for v in p2_row[param_ofensive1].tolist()]
    real_of2_p2 = [round(v, 2) for v in p2_row[param_ofensive2].tolist()]
    real_def_p2 = [round(v, 2) for v in p2_row[param_defensive].tolist()]

    # Configuración de colores para la comparativa
    color_j1 = "#1A78CF"  # Azul (Jugadora 1) 
    color_j2 = "#E74C3C"  # Rojo (Jugadora 2)
    positions_name_dict = {"portera":"porteras","defensa":"defensas","lateral":"laterales",
                           "defmid":"centrocampistas defensivos","ofmid":"centrocampistas ofensivos",
                           "extremo":"extremos","delantera":"delanteras"}

    # --- FIGURA 1: OFENSIVO 1 ---
    fig1 = plt.figure(figsize=(14, 16), facecolor=color_selection_og)
    ax1 = fig1.add_subplot(111, projection="polar", facecolor="#7CBAF3")
    fig1.subplots_adjust(top=0.85, bottom=0.28)

    baker_of1 = PyPizza(params=param_ofensive1_labels, background_color="#7CBAF3", 
                        straight_line_color="#222222", last_circle_color="#222222", other_circle_ls="-.")

    baker_of1.make_pizza(
        values=values_of1_p1, 
        compare_values=values_of1_p2, 
        ax=ax1,
        kwargs_slices=dict(facecolor=color_j1, edgecolor="#000000", zorder=1, linewidth=1),
        # En lugar de kwargs_compare_slices, usamos el manejo nativo de compare_values
        # Si quieres transparencia en el segundo, se suele controlar globalmente o por zorder
        kwargs_params=dict(color=letter_color, fontsize=22, va="center"),
        kwargs_values=dict(color="#000000", fontsize=16, bbox=dict(edgecolor="#000000", facecolor=color_j1, boxstyle="round,pad=0.2")),
        kwargs_compare_values=dict(color="#000000", fontsize=16, bbox=dict(edgecolor="#000000", facecolor=color_j2, boxstyle="round,pad=0.2"))
    )
    
    # --- AJUSTE DE ETIQUETAS PARA EVITAR SUPERPOSICIÓN ---
    # Obtenemos todos los textos que son valores numéricos
    value_texts = [t for t in ax1.texts if "%" in t.get_text() or t.get_text().replace('.','',1).isdigit()]
    
    # PyPizza dibuja primero los valores de P1 y luego los de P2
    half = len(value_texts) // 2
    p1_texts = value_texts[:half]
    p2_texts = value_texts[half:]
    
    for t1, t2 in zip(p1_texts, p2_texts):
        # Obtenemos la posición actual (en coordenadas polares: theta, radio)
        theta, r = t2.get_position()
        
        # Aplicamos un pequeño desplazamiento angular (theta) 
        # 0.1 o 0.15 radianes suele ser suficiente para moverlo a un lado
        # Si quieres que se mueva a la izquierda, sumamos o restamos según el sentido
        t2.set_position((theta - 0.12, r)) 
        
        # Opcional: Ajustar el alineamiento para que se vea más ordenado
        t2.set_ha('right') # Alineado a la derecha del nuevo punto
        t1.set_ha('left')  # El original alineado a la izquierda
    
    for i, slice_obj in enumerate(ax1.patches):
        if i >= len(values_of1_p1): # Estos son los sectores del segundo jugador
            slice_obj.set_facecolor(color_j2)
            slice_obj.set_alpha(0.5)

    fig_text(0.5, 0.99, f"Percentiles de <{player_name1}> y <{player_name2}> en {league} (Ofensivo II)", size=30, fig=fig1, 
             highlight_textprops=[{"color": color_j1}, {"color": color_j2}], ha="center", color=letter_color)
    
    
    # Leyenda Ofensivo 1: Nombre | Dato J1 (Media) vs Dato J2
    legend_labels1 = [f"{p}: {v1} | {v2}, ({a})" for p, v1, v2, a in zip(param_ofensive1, real_of1_p1, real_of1_p2, avg_of1)]
        
    handles_metrics1 = [
        Line2D([0], [0], marker='o',markeredgecolor=letter_color,
               markerfacecolor="#E74C3C", color='w', markersize=14, label=label) 
        for label in legend_labels1
    ]
        
    lg1 = fig1.legend(
        handles=handles_metrics1, 
        loc='lower center', 
        fontsize=16, 
        ncol=2,
        mode=None,        # Para que no intente expandir
        frameon=False, 
        bbox_to_anchor=(0.5, 0.02),
        columnspacing=2,    # Aumenta este valor si las columnas se siguen pisando
        handletextpad=0.5, # Espacio entre el "marcador" y el texto
        alignment='left'
    )
    for t in lg1.get_texts(): t.set_color(letter_color)

    output_path1 = f"comp_of1_{player_name1}_{player_name2}.png"
    fig1.savefig(output_path1, dpi=150)

    # --- FIGURA 2: OFENSIVO 2 ---
    if len(values_of2_p1) > 0:
        fig2 = plt.figure(figsize=(14, 16), facecolor=color_selection_og)
        ax2 = fig2.add_subplot(111, projection="polar", facecolor="#7CBAF3")
        fig2.subplots_adjust(top=0.85, bottom=0.22)
        
        baker_of2 = PyPizza(params=param_ofensive2_labels, background_color="#7CBAF3",
                            straight_line_color="#222222", last_circle_color="#222222", other_circle_ls="-.")
        
        baker_of2.make_pizza(
            values=values_of2_p1, 
            compare_values=values_of2_p2, 
            ax=ax2,
            kwargs_slices=dict(facecolor=color_j1, edgecolor="#000000", zorder=1, linewidth=1),
            kwargs_params=dict(color=letter_color, fontsize=22, va="center"),
            kwargs_values=dict(color="#000000", fontsize=16, bbox=dict(edgecolor="#000000", facecolor=color_j1, boxstyle="round,pad=0.2")),
            kwargs_compare_values=dict(color="#000000", fontsize=16, bbox=dict(edgecolor="#000000", facecolor=color_j2, boxstyle="round,pad=0.2"))
        )
        
        # --- AJUSTE DE ETIQUETAS PARA EVITAR SUPERPOSICIÓN ---
        # Obtenemos todos los textos que son valores numéricos
        value_texts = [t for t in ax2.texts if "%" in t.get_text() or t.get_text().replace('.','',1).isdigit()]
        
        # PyPizza dibuja primero los valores de P1 y luego los de P2
        half = len(value_texts) // 2
        p1_texts = value_texts[:half]
        p2_texts = value_texts[half:]
        
        for t1, t2 in zip(p1_texts, p2_texts):
            # Obtenemos la posición actual (en coordenadas polares: theta, radio)
            theta, r = t2.get_position()
            
            # Aplicamos un pequeño desplazamiento angular (theta) 
            # 0.1 o 0.15 radianes suele ser suficiente para moverlo a un lado
            # Si quieres que se mueva a la izquierda, sumamos o restamos según el sentido
            t2.set_position((theta - 0.12, r)) 
            
            # Opcional: Ajustar el alineamiento para que se vea más ordenado
            t2.set_ha('right') # Alineado a la derecha del nuevo punto
            t1.set_ha('left')  # El original alineado a la izquierda
        
        for i, slice_obj in enumerate(ax2.patches):
            if i >= len(values_of2_p2): # Estos son los sectores del segundo jugador
                slice_obj.set_facecolor(color_j2)
                slice_obj.set_alpha(0.5)
        
        fig_text(0.5, 0.99, f"Percentiles de <{player_name1}> y <{player_name2}> en {league} (Ofensivo II)", size=30, fig=fig2, 
                 highlight_textprops=[{"color": color_j1}, {"color": color_j2}], ha="center", color=letter_color)
        
        # Leyenda Ofensivo 2: Nombre | Dato J1 (Media) vs Dato J2
        legend_labels2 = [f"{p}: {v1} | {v2}, ({a})" for p, v1, v2, a in zip(param_ofensive2, real_of2_p1, real_of2_p2, avg_of2)]
            
        handles_metrics2 = [
            Line2D([0], [0], marker='o',markeredgecolor=letter_color,
                   markerfacecolor="#E74C3C", color='w',markersize=14, label=label) 
            for label in legend_labels2
        ]
            
        lg2 = fig2.legend(
            handles=handles_metrics2, 
            loc='lower center', 
            fontsize=16, 
            ncol=2,
            mode=None,        # Para que no intente expandir
            frameon=False, 
            bbox_to_anchor=(0.5, 0.02),
            columnspacing=2,    # Aumenta este valor si las columnas se siguen pisando
            handletextpad=0.5, # Espacio entre el "marcador" y el texto
            alignment='left'
        )
        for t in lg2.get_texts(): t.set_color(letter_color)
        
        output_path2 = f"comp_of2_{player_name1}_{player_name2}.png"
        fig2.savefig(output_path2, dpi=150)
    else:
        fig2, output_path2 = None, None

    # --- FIGURA 3: DEFENSIVO ---
    fig3 = plt.figure(figsize=(14, 16), facecolor=color_selection_og)
    ax3 = fig3.add_subplot(111, projection="polar", facecolor="#7CBAF3")
    fig3.subplots_adjust(top=0.85, bottom=0.22)
    baker_def = PyPizza(params=param_def_label, background_color="#7CBAF3")
    baker_def.make_pizza(
        values=values_def_p1, 
        compare_values=values_def_p2, 
        ax=ax3,
        kwargs_slices=dict(facecolor=color_j1, edgecolor="#000000", zorder=1, linewidth=1),
        kwargs_params=dict(color=letter_color, fontsize=22, va="center"),
        kwargs_values=dict(color="#000000", fontsize=16, bbox=dict(edgecolor="#000000", facecolor=color_j1, boxstyle="round,pad=0.2")),
        kwargs_compare_values=dict(color="#000000", fontsize=16, bbox=dict(edgecolor="#000000", facecolor=color_j2, boxstyle="round,pad=0.2"))
    )
    
    # --- AJUSTE DE ETIQUETAS PARA EVITAR SUPERPOSICIÓN ---
    #   Obtenemos todos los textos que son valores numéricos
    value_texts = [t for t in ax3.texts if "%" in t.get_text() or t.get_text().replace('.','',1).isdigit()]
    
    # PyPizza dibuja primero los valores de P1 y luego los de P2
    half = len(value_texts) // 2
    p1_texts = value_texts[:half]
    p2_texts = value_texts[half:]
    
    for t1, t2 in zip(p1_texts, p2_texts):
        # Obtenemos la posición actual (en coordenadas polares: theta, radio)
        theta, r = t2.get_position()
        
        # Aplicamos un pequeño desplazamiento angular (theta) 
        # 0.1 o 0.15 radianes suele ser suficiente para moverlo a un lado
        # Si quieres que se mueva a la izquierda, sumamos o restamos según el sentido
        t2.set_position((theta - 0.12, r)) 
        
        # Opcional: Ajustar el alineamiento para que se vea más ordenado
        t2.set_ha('right') # Alineado a la derecha del nuevo punto
        t1.set_ha('left')  # El original alineado a la izquierda
        
    for i, slice_obj in enumerate(ax3.patches):
        if i >= len(values_def_p2): # Estos son los sectores del segundo jugador
            slice_obj.set_facecolor(color_j2)
            slice_obj.set_alpha(0.5)

    
    fig_text(0.5, 0.99, f"Percentiles de <{player_name1}> y <{player_name2}> en {league} (Defensivo)", size=30, fig=fig3, 
             highlight_textprops=[{"color": color_j1}, {"color": color_j2}], ha="center", color=letter_color)
    
    legend_labels3 = [f"{p}: {v1} | {v2}, ({a})" for p, v1, v2, a in zip(param_def_label, real_def_p1, real_def_p2, avg_def)]
        
    handles_metrics3 = [
        Line2D([0], [0], marker='o',markeredgecolor=letter_color,
               markerfacecolor="#E74C3C", color='w',markersize=14, label=label) 
        for label in legend_labels3
    ]
        
    lg3 = fig3.legend(
        handles=handles_metrics3, 
        loc='lower center', 
        fontsize=16, 
        ncol=2,
        mode=None,        # Para que no intente expandir
        frameon=False, 
        bbox_to_anchor=(0.5, 0.02),
        columnspacing=2,    # Aumenta este valor si las columnas se siguen pisando
        handletextpad=0.5, # Espacio entre el "marcador" y el texto
        alignment='left'
    )
    for t in lg3.get_texts(): t.set_color(letter_color)
    
    output_path3 = f"comp_def_{player_name1}_{player_name2}.png"
    fig3.savefig(output_path3, dpi=150)

    plt.close('all')
    return fig1, output_path1, fig2, output_path2, fig3, output_path3
            
#fig,output,fig3,output2,fig4,out4=pizzaplot_player("/Users/julieta/Desktop/WYSCOUT/datoswyscout/espana_1_2025_2025_03_03.xlsx","/Users/julieta/Desktop/parameters.xlsx",80,600,1,"#F3FAFF")            
#fig,output,fig3,output2,fig3,out5=pizzaplot_player("/Users/julieta/Desktop/WYSCOUT/datoswyscout/espana_3_2025_2025_26_03.xlsx","/Users/julieta/Desktop/parameters.xlsx",522,500,1)
