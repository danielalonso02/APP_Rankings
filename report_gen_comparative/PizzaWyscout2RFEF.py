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
from itertools import product

def pizzaplot_player(filepath_excel,file_parameters,player_id1,player_id2,min_minutos,position_number,color="#34495E",league="2º RFEF",season="2024/25"):
    """
    

    Parameters
    ----------
    filepath_excel : (str) la ruta del archivo excel de la categoria que estemos analizando, con TODOS los jugadores
    
    file_parameters: (str) la ruta del archivo excel que tiene los parámetros para cada posición
    
    player_id_analizing : (int) el id del jugador que queremos analizar, ES EL NUMERO DE LA FILA DEL EXCEL
    
    min_minutos:(int) minimo de minutos que deben haber jugado los jugadores para ser considerados
    
    position_number:(int) 1,2 o 3 la posición del jugador que quieres sacar,
                    (1: principal, 2: secundaria, 3: terciaria)
    
    Returns
    -------
    tuple
        Tupla con cuatro elementos:
        - fig : matplotlib.figure.Figure
            Figura del primer gráfico generado.
        - output_path : str
            Ruta donde se guardó el primer gráfico (formato PNG).
        - fig3 : matplotlib.figure.Figure
            Figura del segundo gráfico generado (comparación).
        - output_path2 : str
            Ruta donde se guardó el segundo gráfico (formato PNG).

    """
    
    try:
        df_stats = pd.read_excel(filepath_excel)
        
    except FileNotFoundError:
        print(f"Error: El archivo '{filepath_excel}' no existe.")
        return None,None,None,None, None, None
    #pongo el player_id para cada jugado, los identificaremos con esto
    for i,row in df_stats.iterrows():
        df_stats.loc[i,"player_id"]=i+2
    #filtramos por minutos jugados la base de datos
    df_stats=df_stats[df_stats["Minutos jugados"]>=min_minutos]
    
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
    else:
        letter_color="#F2F2F2"
        fig1 = plt.figure(facecolor=color)
        fig2 = plt.figure(facecolor=color)
        fig3 = plt.figure(facecolor=color)
    #lo primero es comprobar si esta el jugador
    if player_id1 not in df_stats["player_id"].values:
        raise PlayerNotFoundError(f"El jugador elegido, {player_id1}, no está en la base de datos o ha jugado menos de {min_minutos}.")
        return None, None, None, None, None, None  
    
    if player_id2 not in df_stats["player_id"].values:
        raise PlayerNotFoundError(f"El jugador elegido, {player_id2}, no está en la base de datos o ha jugado menos de {min_minutos}.")
        return None, None, None, None, None, None  
    df_stats.fillna(df_stats.mean(numeric_only=True),inplace=True)
    
    positions_dict={"GK":"portero","LB":"lateral","RB":"lateral","DMF":"defmid","OF":"ofmid",
                    "AMF":"ofmid","LCB":"defensa","RCB":"defensa","LWF":"extremo","RWF":"extremo",
                    "LAMF":"ofmid","RAMF":"ofmid","LCMF":"ofmid","RCMF":"ofmid","CF":"delantero",
                    "CB":"defensa","RW":"extremo","LDMF":"defmid","LW":"extremo","RDMF":"defmid",
                    }
    positions=["portero","defensa","defmid","ofmid","lateral","delantero","extremo"]
    

    parameters = {}
    for position in positions:
        try:
            
            df_position = pd.read_excel(file_parameters, sheet_name=position)
            
            
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
    
    #con esta funcion se mapean las posiciones especificas a las generales
    def map_positions(positions_str):
        positions = positions_str.split(", ")  
        general_positions = [positions_dict.get(pos, pos) for pos in positions]  
        unique_positions = set(general_positions)  
        return ", ".join(unique_positions)  # Unir las posiciones únicas

    df_stats["general_position"] = df_stats["Posición específica"].apply(map_positions)

    df_stats[['general_position', 'general_position2',"general_position3"]] = df_stats['general_position'].str.split(", ", n=2, expand=True)

    general_stats=df_stats[["Jugador","Equipo","Equipo durante el período seleccionado","Edad","Valor de mercado","Vencimiento contrato","Partidos jugados","Minutos jugados","player_id",'general_position', 'general_position2',"general_position3"]].copy()
    
    #Una vez tenemos las posiciones genericas de todos los jugadores, hay que dividir por cada posicion
    
    portero=df_stats[(df_stats["general_position"]=="portero") | (df_stats["general_position2"]=="portero") | (df_stats["general_position3"]=="portero")].copy()
    defensa=df_stats[(df_stats["general_position"]=="defensa") | (df_stats["general_position2"]=="defensa") | (df_stats["general_position3"]=="defensa")].copy()
    defmid=df_stats[(df_stats["general_position"]=="defmid") | (df_stats["general_position2"]=="defmid") | (df_stats["general_position3"]=="defmid")].copy()
    ofmid=df_stats[(df_stats["general_position"]=="ofmid") | (df_stats["general_position2"]=="ofmid") | (df_stats["general_position3"]=="ofmid")].copy()
    delantero=df_stats[(df_stats["general_position"]=="delantero") | (df_stats["general_position2"]=="delantero") | (df_stats["general_position3"]=="delantero")].copy()
    extremo=df_stats[(df_stats["general_position"]=="extremo") | (df_stats["general_position2"]=="extremo") | (df_stats["general_position3"]=="extremo")].copy()
    lateral=df_stats[(df_stats["general_position"]=="lateral") | (df_stats["general_position2"]=="lateral") | (df_stats["general_position3"]=="lateral")].copy()
    #filtramos con esos parametros:
    general_stats=["Jugador","Equipo","Equipo durante el período seleccionado","Edad",
        "Valor de mercado","Vencimiento contrato","Partidos jugados","Minutos jugados","player_id"]

    positions=["portero","defensa","defmid","ofmid","lateral","delantero","extremo"]

    columns_goal = pd.Series(general_stats + parameters["portero"]["defensive"] + parameters["portero"]["ofensive"]).unique().tolist()
    portero =portero[columns_goal].copy()

    columns_defense = pd.Series(general_stats + parameters["defensa"]["defensive"] + parameters["defensa"]["ofensive"]).unique().tolist()
    defensa = defensa[columns_defense].copy()


    columns_defmid = pd.Series(general_stats + parameters["defmid"]["defensive"] + parameters["defmid"]["ofensive"]).unique().tolist()
    defmid = defmid[columns_defmid].copy()


    columns_ofmid = pd.Series(general_stats + parameters["ofmid"]["defensive"] + parameters["ofmid"]["ofensive"]).unique().tolist()
    ofmid = ofmid[columns_ofmid].copy()


    columns_striker = pd.Series(general_stats + parameters["delantero"]["defensive"] + parameters["delantero"]["ofensive"]).unique().tolist()
    delantero = delantero[columns_striker].copy()


    columns_wing = pd.Series(general_stats + parameters["extremo"]["defensive"] + parameters["extremo"]["ofensive"]).unique().tolist()
    extremo = extremo[columns_wing].copy()


    columns_lateral = pd.Series(general_stats + parameters["lateral"]["defensive"] + parameters["lateral"]["ofensive"]).unique().tolist()
    lateral = lateral[columns_lateral].copy()
    
    #Antes de sacar los percentiles saco las MEDIAS de los valores reales
    columns_goal2= pd.Series(parameters["portero"]["ofensive"] + parameters["portero"]["defensive"]).unique().tolist()
    portero_values_average=portero[columns_goal2].mean()
    columns_defense2 = pd.Series( parameters["defensa"]["ofensive"] + parameters["defensa"]["defensive"] ).unique().tolist()
    defensa_values_average= defensa[columns_defense2].mean()
    columns_defmid2 = pd.Series(parameters["defmid"]["ofensive"] + parameters["defmid"]["defensive"]).unique().tolist()
    defmid_values_average=defmid[columns_defmid2].mean()
    columns_ofmid2 = pd.Series(parameters["ofmid"]["ofensive"] + parameters["ofmid"]["defensive"]).unique().tolist()
    ofmid_values_average=ofmid[columns_ofmid2].mean()
    columns_striker2 = pd.Series(parameters["delantero"]["ofensive"] + parameters["delantero"]["defensive"]).unique().tolist()
    delantero_values_average=delantero[columns_striker2].mean()
    columns_wing2 = pd.Series(parameters["extremo"]["ofensive"] + parameters["extremo"]["defensive"]).unique().tolist()
    extremo_values_average=extremo[columns_wing2].mean()
    lateral_columns2=pd.Series(parameters["lateral"]["ofensive"] + parameters["lateral"]["defensive"]).unique().tolist()
    lateral_values_average=lateral[lateral_columns2].mean()
    #y lo meto todo en un diccionario
    average_values_={"portero":portero_values_average,"defensa":defensa_values_average,"lateral":lateral_values_average,
                    "ofmid":ofmid_values_average,"defmid":defmid_values_average,
                    "delantero":delantero_values_average,"extremo":extremo_values_average}
    
    
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

    portero = calculate_and_assign_percentiles(portero, parameters["portero"]["defensive"], parameters["portero"]["ofensive"])
    defensa = calculate_and_assign_percentiles(defensa, parameters["defensa"]["defensive"], parameters["defensa"]["ofensive"])
    defmid = calculate_and_assign_percentiles(defmid,parameters["defmid"]["defensive"], parameters["defmid"]["ofensive"])
    ofmid = calculate_and_assign_percentiles(ofmid, parameters["ofmid"]["defensive"], parameters["ofmid"]["ofensive"])
    delantero = calculate_and_assign_percentiles(delantero, parameters["delantero"]["defensive"], parameters["delantero"]["ofensive"])
    extremo = calculate_and_assign_percentiles(extremo, parameters["extremo"]["defensive"], parameters["extremo"]["ofensive"])
    lateral = calculate_and_assign_percentiles(lateral, parameters["lateral"]["defensive"], parameters["lateral"]["ofensive"])


    #ahora habría que sacar las medias
    columns_goal2= pd.Series(parameters["portero"]["ofensive"] + parameters["portero"]["defensive"]).unique().tolist()
    portero_average=portero[columns_goal2].mean().astype(int)
    columns_defense2 = pd.Series( parameters["defensa"]["ofensive"] + parameters["defensa"]["defensive"] ).unique().tolist()
    defensa_average= defensa[columns_defense2].mean().astype(int)
    columns_defmid2 = pd.Series(parameters["defmid"]["ofensive"] + parameters["defmid"]["defensive"]).unique().tolist()
    defmid_average=defmid[columns_defmid2].mean().astype(int)
    columns_ofmid2 = pd.Series(parameters["ofmid"]["ofensive"] + parameters["ofmid"]["defensive"]).unique().tolist()
    ofmid_average=ofmid[columns_ofmid2].mean().astype(int)
    columns_striker2 = pd.Series(parameters["delantero"]["ofensive"] + parameters["delantero"]["defensive"]).unique().tolist()
    delantero_average=delantero[columns_striker2].mean().astype(int)
    columns_wing2 = pd.Series(parameters["extremo"]["ofensive"] + parameters["extremo"]["defensive"]).unique().tolist()
    extremo_average=extremo[columns_wing2].mean().astype(int)
    lateral_columns2=pd.Series(parameters["lateral"]["ofensive"] + parameters["lateral"]["defensive"]).unique().tolist()
    lateral_average=lateral[lateral_columns2].mean().astype(int)
    
    
    #####################################################################################


    values_dict = {
        "portero": [parameters["portero"]["ofensive"], parameters["portero"]["ofensive es"], parameters["portero"]["defensive"], parameters["portero"]["defensive es"], portero, portero_average],
        "defensa": [parameters["defensa"]["ofensive"], parameters["defensa"]["ofensive es"], parameters["defensa"]["defensive"], parameters["defensa"]["defensive es"], defensa, defensa_average],
        "lateral": [parameters["lateral"]["ofensive"], parameters["lateral"]["ofensive es"], parameters["lateral"]["defensive"], parameters["lateral"]["defensive es"], lateral, lateral_average],
        "defmid": [parameters["defmid"]["ofensive"], parameters["defmid"]["ofensive es"], parameters["defmid"]["defensive"], parameters["defmid"]["defensive es"], defmid, defmid_average],
        "ofmid": [parameters["ofmid"]["ofensive"], parameters["ofmid"]["ofensive es"], parameters["ofmid"]["defensive"], parameters["ofmid"]["defensive es"], ofmid, ofmid_average],
        "delantero": [parameters["delantero"]["ofensive"], parameters["delantero"]["ofensive es"], parameters["delantero"]["defensive"], parameters["delantero"]["defensive es"], delantero, delantero_average],
        "extremo": [parameters["extremo"]["ofensive"], parameters["extremo"]["ofensive es"], parameters["extremo"]["defensive"], parameters["extremo"]["defensive es"], extremo, extremo_average]
        }
    

    #TODO para player_1
    player_stats_values1=df_stats[df_stats["player_id"]==player_id1]
    player_name1=player_stats_values1["Jugador"].iloc[0]

    if pd.notna(player_stats_values1["general_position"].iloc[0]):
        player_position11 = player_stats_values1["general_position"].iloc[0]
        
        

    if pd.notna(player_stats_values1["general_position2"].iloc[0]):
        player_position21 = player_stats_values1["general_position2"].iloc[0]
    else:
        player_position21="None"
        
    if pd.notna(player_stats_values1["general_position3"].iloc[0]):
        player_position31= player_stats_values1["general_position3"].iloc[0]
    else:
        player_position31="None"
        
        
    player_stats_values2=df_stats[df_stats["player_id"]==player_id2]
    player_name2=player_stats_values2["Jugador"].iloc[0]

    if pd.notna(player_stats_values2["general_position"].iloc[0]):
        player_position12 = player_stats_values2["general_position"].iloc[0]
        
        

    if pd.notna(player_stats_values2["general_position2"].iloc[0]):
        player_position22 = player_stats_values2["general_position2"].iloc[0]
    else:
        player_position22="None"
        
    if pd.notna(player_stats_values2["general_position3"].iloc[0]):
        player_position32= player_stats_values2["general_position3"].iloc[0]
    else:
        player_position32="None"
    
    #print(f"POSITION P1: {player_position11}")
    #print(f"POSITION P2: {player_position12}")
    positions1=[player_position11,player_position21,player_position31]
    positions2=[player_position12,player_position22,player_position32]
    common=set(positions1) & set(positions2)
    seen = set()
    common_ordered_unique = [pos for pos in positions1 if pos in positions2 and not (pos in seen or seen.add(pos))]
   
    if common_ordered_unique:
        #print(f"todo bien: {common_ordered_unique}")
        if position_number==1:
            position_players=common_ordered_unique[0]
        elif position_number==2:
            if len(common_ordered_unique)>1:
                position_players=common_ordered_unique[1]
        elif position_number==3:
            if len(common_ordered_unique)>2:
                position_players=common_ordered_unique[2]
            else:
                print("No tienen segunda posicion conjunta")
                return None, None, None, None, None, None
        elif position_number==3:
            if len(common_ordered_unique)>2:
                position_players=common_ordered_unique[2]
            else:
                print("No tienen tercera posicion conjunta")
                return None, None, None, None, None, None
        else:
            print("Número de posicion no válido")
            return None, None, None, None, None, None
    else:
        print("No tienen posiciones iguales")
        return None, None, None, None, None, None
    
    param_ofensive, param_of_label, param_defensive, param_def_label, full_values, average_values = values_dict[position_players]
    player_stats1 = full_values[full_values["player_id"] == player_id1]
    player_stats2 = full_values[full_values["player_id"] == player_id2]
    
    # Obtener of_number desde parameters
    of_number = parameters[position_players]["of_number"]
        
        
    # Inicializamos las listas para los parámetros ofensivos
    param_ofensive1 = []
    param_ofensive1_labels=[]
    param_ofensive2 = []
    param_ofensive2_labels=[]
        
    # Dividir los parámetros ofensivos según el valor de of_number
    for i, param in enumerate(param_ofensive):
        if of_number[i] == 1:
            param_ofensive1.append(param)
            
        elif of_number[i] == 2:
            param_ofensive2.append(param)
    for i, param in enumerate(param_of_label):
        if of_number[i] == 1:
            param_ofensive1_labels.append(param)
            
        elif of_number[i] == 2:
            param_ofensive2_labels.append(param)
            
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
            
    position=position_players
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
    average_values_list1=average_values_[position_players]
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
    
    #jugador 2
    
    average_values_of12=[round(value,2) for value in average_values_list1[param_ofensive1].tolist()]
    average_values_of22=[round(value,2) for value in average_values_list1[param_ofensive2].tolist()]
    
    
    
    #DEFENSIVE
    #Valores REALES 
    average_values_def=[round(value,2) for value in average_values_list1[param_defensive].tolist()]
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
        
        #diccionario para que queden bien los nombres:
    positions_name_dict={"portero":"porteros","defensa":"defensas","lateral":"laterales",
                         "defmid":"centrocampistas defensivos","ofmid":"centrocampistas ofensivos",
                         "extremo":"extremos","delantero":"delanteros"}

    
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
        f"{param}: {value1} | {value2}, ({values})"
        for param, value1,value2, values in zip(param_ofensive1, player_stats_of11,player_stats_of12, average_values_of11)
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
    output_path1=f"pizzaplot_ofensivo_1_{player_name1}_{player_name2}_{position}.png"
    fig1.savefig(output_path1,dpi=500)
    plt.close(fig1)
    
    #fig1.savefig(output_path1, dpi=300, bbox_inches='tight')
    #plt.show()

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
            f"{param}: {value1} | {value2}, ({values})"
            for param, value1,value2, values in zip(param_ofensive2, player_stats_of21,player_stats_of22, average_values_of21)
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
        output_path2=f"pizzaplot_ofensivo_2_{player_name1}_{player_name2}_{position}.png"
        fig2.savefig(output_path2, dpi=500)
        plt.close(fig2)
        #plt.show()
    else:
        output_path2=None
        fig2=None


    ##### ---- y el defensivo -----
    fig3 = plt.figure(figsize=(14, 16), facecolor=color)
    ax3 = fig3.add_subplot(111, projection="polar", facecolor=color)
    fig3.subplots_adjust(top=0.85, bottom=0.15)
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
        f"{param}: {value1} | {value2}, ({values})"
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
    
    


    output_path3 = f"pizzaplot_defensivo_{player_name1}_{player_name2}_{position}.png"
    fig3.savefig(output_path3, dpi=500)
    plt.close(fig3)
    #plt.show()
    return fig1, output_path1,fig2, output_path2, fig3,output_path3
            
#fig,output,fig3,output2,fig4,out4=pizzaplot_player("/Users/julieta/Desktop/WYSCOUT/datoswyscout/espana_1_2025_2025_03_03.xlsx","/Users/julieta/Desktop/Intento_Report_Comparativo/parameters.xlsx",39,42,600,1,"#F3FAFF")            
#fig,output,fig3,output2,fig3,out5=pizzaplot_player("/Users/julieta/Desktop/WYSCOUT/datoswyscout/espana_3_2025_2025_26_03.xlsx","/Users/julieta/Desktop/parameters.xlsx",522,500,1)
