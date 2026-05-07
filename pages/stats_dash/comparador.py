#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  8 10:41:56 2025

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
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import unicodedata

def show_page():

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
    
    def filtros_fragment():
        
        col1,col2,col3=st.columns([1,1,1])
    
        with col1:
            championship_excel = util.select_competicion()
            league=util.from_excel_to_str(championship_excel)
        with col2:
            year = util.select_season()
            season=util.convert_season(year)
        with col3:
            team_name=util.select_team()
            
        return {
            "ruta_script": ruta_script,
            "championship_excel": championship_excel,
            "Equipo":team_name,
            "year":year}
    filtros=filtros_fragment()
    
    df=pd.read_excel(f"{ruta_excel2}/{filtros['championship_excel']}_wyscout_{filtros['year']}.xlsx")
    if "Todos" not in filtros["Equipo"]:
        df = df[df["Equipo"].isin(filtros["Equipo"])]
    #st.dataframe(df)
   
    numeric_cols = df.select_dtypes(include='number').columns
    
    
    numeric_cols_list = df.select_dtypes(include='number').columns.tolist()
    to_remove=["Valor de mercado","Edad"]
    numeric_cols_list = [x for x in numeric_cols_list if x not in to_remove]
    #st.write(numeric_cols_list)
    numeric_cols_list.sort()
    
    select_variable=st.multiselect(label="Elija 2 o 3 métricas a visualizar",options=numeric_cols_list,default=["Goles","Asistencias"])
    
    col1,col2=st.columns([1,1])
    with col1:
        lower_better = st.checkbox("Menor valor es mejor",help="Marque esta opción si un valor menor implica mejor rendimiento.")
    
    st.markdown("### Número de jugadores a mostrar para el análisis multivariable")
    values = st.slider("", 0,50, 10)
    
    if len(select_variable) >= 2:
        df_display = df.copy()

        
        for col in select_variable:
            if lower_better:
                
                df_display[col + "_norm"] = 1 - (df_display[col] - df_display[col].min()) / (df_display[col].max() - df_display[col].min())
            else:
             
                df_display[col + "_norm"] = (df_display[col] - df_display[col].min()) / (df_display[col].max() - df_display[col].min())

        df_display["score"] = df_display[[col + "_norm" for col in select_variable]].mean(axis=1)

        

        df_display = df_display.sort_values(by="score", ascending=False).head(values)
      
        if len(select_variable) == 2:

            
            fig = px.scatter(
                df_display,
                x=select_variable[0],
                y=select_variable[1],
                color="score",
                hover_name="Jugador",
                color_continuous_scale='Viridis',
                text="Jugador"
                )
            fig.update_traces(marker=dict(size=16),textposition="top center")

        elif len(select_variable) == 3:
            fig = px.scatter_3d(
                df_display,
                x=select_variable[0],
                y=select_variable[1],
                z=select_variable[2],
                color="score",
                hover_name="Jugador",
                color_continuous_scale='Viridis',
                text="Jugador"
                )

        else:
            fig = None

        if fig:
            st.plotly_chart(fig, width='stretch')

    else:
        st.info("Por favor, seleccione 2 o 3 métricas para visualizar.")
    
    
    df_display=df_display.head(values)
    #st.dataframe(df_display)
    #fig = px.bar(df_display, x='Jugador', y=select_variable,color=select_variable,color_continuous_scale="Viridis")
    #st.plotly_chart(fig,width='stretch')
    
    
    
    
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

    last_update=last_modified(f"{BASE_DIR}/report_gen")

    st.write(f"Última actualización: {last_update} | Fuente de datos: Hudl Wyscout")