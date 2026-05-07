#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 24 12:55:39 2025

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

import os
import math
from reportlab.platypus import Paragraph, Image, SimpleDocTemplate, Spacer, Frame
from reportlab.platypus import PageTemplate, BaseDocTemplate, PageBreak, FrameBreak
from reportlab.platypus import Flowable
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT  
from reportlab.platypus import KeepInFrame
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Preformatted
# Si queremos tablas...
from reportlab.platypus import Table, TableStyle
# Importamos clase de hoja de estilo de ejemplos
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import KeepTogether

# Se importa el tamaño de la hoja.
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

# Y los colores.
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.lib.units import cm
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
from PizzaWyscout2RFEF import pizzaplot_player
from Pizzaplot_Opta import pizzaplot_player_opta
from IntentoArrays import extract_arrays_wyscout, extract_arrays_physical
import time
from PIL import Image as PILImage
import io
from TryGraficas2D import graficas_2D
from reportlab.platypus import KeepInFrame
#from Notas_tacticas import notas_tacticas
from IntentoArrays_Opta import extract_arrays_wyscout,notas_tacticas
#from .Notas_Skillcorner import notas_fisicas
from PizzaPhysical import pizzaplot_phys
from colorsys import rgb_to_hls
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus import NextPageTemplate
from Arrays_ChatOpta import extract_arrays_wyscout2
from ChatTextReport import create_chat_log, chat
import time
import os
import shutil
import argparse

import warnings
import pandas as pd
import os
import tempfile
from pathlib import Path
from reportlab.graphics.shapes import Line
import re

# Ignorar PerformanceWarning de pandas
warnings.simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 
current_l="La Liga"
current_season="2024/25"
def clean_text_for_paragraph(text):
    # Keep only allowed tags <b>, <i>, <br/>
    # Replace all other angle brackets to avoid breaking Paragraph
    text = re.sub(r"</?(?!b|i|br/)[^>]*>", "", text)

    # Fix broken <b> tags like 0.65&lt;/b
    text = text.replace("&lt;/b", "</b>").replace("&lt;/i", "</i>")

    # Balance <b> and <i> tags
    for tag in ["b", "i"]:
        open_tag_count = text.count(f"<{tag}>")
        close_tag_count = text.count(f"</{tag}>")
        if open_tag_count > close_tag_count:
            text += f"</{tag}>" * (open_tag_count - close_tag_count)
        elif close_tag_count > open_tag_count:
            text = re.sub(f"</{tag}>", "", close_tag_count - open_tag_count)

    # Replace stray & with &amp; (but keep &lt; and &gt; safe)
    text = text.replace("&", "&amp;").replace("&amp;lt;", "&lt;").replace("&amp;gt;", "&gt;")

    return text


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

def create_report(player_id1,player_id2,opta_filepath,parameters_file,min_minutes,color_selection="#FFFFFF",summary=0,current_league=current_l,season="2024/25"):
    class MyDocTemplate(BaseDocTemplate):
        def __init__(self, filename, **kwargs):
            super().__init__(filename, **kwargs)

            # Define frame
            frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id='normal')

            # Página normal con fondo
            main_template = PageTemplate(id='main', frames=frame, onPage=add_background)

            # Si quieres una portada distinta, define otra
            front_template = PageTemplate(id='front', frames=frame, onPage=create_front_page)

            # Agrega las plantillas que vas a usar
            self.addPageTemplates([front_template, main_template])

            # Table of contents
            self.toc = TableOfContents()
            self.toc.levelStyles = [
                ParagraphStyle(fontName='Helvetica', fontSize=14, name='TOCHeading1', leftIndent=20, firstLineIndent=-20, spaceBefore=5, leading=16),
                ]

        def afterFlowable(self, flowable):
            if hasattr(flowable, 'outlineLevel'):
                self.notify('TOCEntry', (flowable.outlineLevel, flowable.getPlainText(), self.page))
    
    if not os.path.exists(opta_filepath):
        print(f"El fichero {opta_filepath} no existe.")
        return None
    df_all_players=pd.read_excel(opta_filepath)

    color_selection_og=color_selection
    color_selection=color_selection.lstrip("#")
    r,g,b=int(color_selection[0:2],16),int(color_selection[2:4],16),int(color_selection[4:6],16)
    h,l,s=rgb_to_hls(r/255.0,g/255.0,b/255.0)
    if l>0.5:
        letter_colors="#000000"
        
    else:
        letter_colors="#FFFFFF"
    img_path_1="Logos/icons8-soccer-64.png"
    img_path_2="Logos/icons8-goal-64.png"
    img_path_3="Logos/icons8-kick-off-64.png"

    player_path="Logos/player_Generic.jpeg"
    if not os.path.exists(img_path_1):
        print(f"El fichero {img_path_1} no existe.")
        return None

    if not os.path.exists(img_path_2):
        print(f"El fichero {img_path_2} no existe.")
        return None

    if not os.path.exists(img_path_3):
        print(f"El fichero {img_path_3} no existe.")
        return None

    # if not os.path.exists(filepath_carpeta):
    #     print(f"La carpeta {filepath_carpeta} no existe.")
    #     return None
    positions=["Goalkeeper","Defender","Midfielder","Forward"]
    glossary={}
    company_name="Departamento de Sports Analytics"
    fichero_glossary="Glossary.xlsx"
    for position in positions:
        try:
            df_glossary = pd.read_excel(fichero_glossary, sheet_name=position)
            glossary[position] = []
            for entry in df_glossary["Glossary"].dropna().astype(str):
                if ":" in entry:
                    key, value = entry.split(":", 1)
                    formatted_entry = f"<b>{key.strip()}</b>: {value.strip()}"
                else:
                    formatted_entry = entry  # Leave it as is if no colon
                glossary[position].append(formatted_entry)
        except ValueError:
            print(f"Hoja '{position}' no encontrada en el archivo.")
        except Exception as e:
            print(f"Error al leer la hoja '{position}': {e}")
    
    
    if (player_id1 not in df_all_players["player_id"].values) or (player_id2 not in df_all_players["player_id"].values):
        print("No se encuentra al jugador")
        return None

    
    df_all_players=df_all_players[df_all_players["Time Played"]>min_minutes].copy()
    if player_id1 not in df_all_players["player_id"].values:
        print(f"El jugador 1 ha jugado menos de {min_minutes} minutos.")
        return None
    if player_id2 not in df_all_players["player_id"].values:
        print(f"El jugador 2 ha jugado menos de {min_minutes} minutos.")
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
    df_position=df_all_players[df_all_players["position"]==player_position].copy()
    #CHANGE FORMULAS FOR CORRECT PATH
    df_position=calculate_pizza_values(df_position,player_position,"formulas.xlsx")
    #print("MIN MINUTES:",min_minutes)
    
    ########
    min_of1, max_of1, player_of11,player_of12, param_of1,df_all_stats,percentiles_of11,percentiles_of12,_ = extract_arrays_wyscout(
        df_position,parameters_file,
        player_id1,player_id2,
        "param_of1", min_minutes
    )
    min_of2, max_of2, player_of21,player_of22, param_of2, _ ,percentiles_of21,percentiles_of22,_= extract_arrays_wyscout(
        df_position,parameters_file,
        player_id1,player_id2,
        "param_of2",min_minutes
    )
    min_def, max_def, player_def1,player_def2, param_def, _,percentiles_def1,percentiles_def2,_ = extract_arrays_wyscout(
        df_position,parameters_file,
        player_id1,player_id2,
        "param_def",min_minutes
    )
    ########
    
    # min_of1, max_of1, player_of1, param_of1,df_all_stats,percentiles_of1,_ = extract_arrays_wyscout(df_position,parameters_file,player_id_analizing,"param_of1",min_minutes)

    # min_of2, max_of2, player_of2, param_of2, _ ,percentiles_of2,_= extract_arrays_wyscout(df_position,parameters_file,player_id_analizing,"param_of2",min_minutes)
    # min_def, max_def, player_def, param_def, _,percentiles_def,_ = extract_arrays_wyscout(df_position,parameters_file,player_id_analizing,"param_def",min_minutes)
    
    
    positions_name_dict={"Goalkeeper":"Portero","Defender":"Defensa","Midfielder":"Centrocampista",
                         "Forward":"Delantero"}

    positions_name_dict1={"Goalkeeper":"Portero","Defender":"Defensa","Midfielder":"Centrocampista",
                         "Forward":"Delantero"}
    df_general_stats=df_all_stats[["player_name","team_name","age","Appearances","Time Played","weight","height","player_id","position"]].copy()
    general_stats_player1=df_general_stats[df_general_stats["player_id"]==player_id1].iloc[0]
    stats_player1=df_all_stats[df_all_stats["player_id"]==df_position].iloc[0]
    player_name1=general_stats_player1["player_name"]
    
    
    print(player_name1)
    #print("GENERAL STATS PLAYER:",general_stats_player)
    player_team1=general_stats_player1["team_name"]

    player_age1=general_stats_player1["age"]


    player_games1=general_stats_player1["Appearances"]
    player_minutes1=general_stats_player1["Time Played"]
    player_position_original1=general_stats_player1["position"]
    player_position11=positions_name_dict[general_stats_player1["position"]]
    player_param1=stats_player1["position"]

    player_position_text=positions_name_dict1[player_position]
        
    #print("linea 257")
    player_goals1=stats_player1["Goals"]
    if np.isnan(player_goals1):
        player_goals1=0
    player_assists1=stats_player1["Goal Assists"]
    if np.isnan(player_assists1):
        player_assists1=0
    player_nationality1=stats_player1["first_nationality"]
    player_weight1=stats_player1["weight"]
    player_height1=stats_player1["height"]
    player_foot1=stats_player1["prefered_foot"]
    player_allpositions1=stats_player1["position"]
    player_birth_country1=stats_player1["first_nationality"]
    
    
    general_stats_player2=df_general_stats[df_general_stats["player_id"]==player_id1].iloc[0]
    stats_player2=df_all_stats[df_all_stats["player_id"]==df_position].iloc[0]
    player_name2=general_stats_player2["player_name"]
    
    
    print(player_name2)
    #print("GENERAL STATS PLAYER:",general_stats_player)
    player_team2=general_stats_player2["team_name"]

    player_age2=general_stats_player2["age"]


    player_games2=general_stats_player2["Appearances"]
    player_minutes2=general_stats_player2["Time Played"]
    player_position_original2=general_stats_player2["position"]
    player_position12=positions_name_dict[general_stats_player2["position"]]
    player_param2=stats_player2["position"]

    player_position_text=positions_name_dict1[player_position]
        
    #print("linea 257")
    player_goals2=stats_player2["Goals"]
    if np.isnan(player_goals2):
        player_goals2=0
    player_assists2=stats_player2["Goal Assists"]
    if np.isnan(player_assists2):
        player_assists2=0
    player_nationality2=stats_player2["first_nationality"]
    player_weight2=stats_player2["weight"]
    player_height2=stats_player2["height"]
    player_foot2=stats_player2["prefered_foot"]
    player_allpositions2=stats_player2["position"]
    player_birth_country2=stats_player2["first_nationality"]
    
    # team_id=186
    # _next_path=f"{team_id}/logo/l_t{team_id}.png"
    # complete_teampath=filepath_carpeta+"/"+_next_path
    # player_id2=223255
    # nextpath=f"/{team_id}/formation/f_t{team_id}_p{player_id2}.png"
    # player_path=filepath_carpeta+nextpath
    #player path lo dejo asi generic por ahora
    PLAYER_POSITION=player_position

    #print("linea 275")
    if player_minutes1>min_minutes:
        fig1,output_path1,fig2,output_path2,fig3,output_path3=pizzaplot_player_opta(df_position,player_id1,player_id2,player_position,parameters_file,min_minutes,color=color_selection_og,league=current_league,season=season)

        #print(output_path2)
    else:
        print(f"El jugador ha jugado menos de {min_minutes} minutos, selecciona otro jugador o baja el número de minutos necesarios.")
        return None

    of_score1,of_letter1,def_score1,def_letter1,full_score1,full_letter1,number_of_players_position,Rank_of1,Rank_def1,Rank_full1=notas_tacticas(PLAYER_POSITION,df_position,parameters_file,player_id1,min_minutes)
    
    of_score2,of_letter2,def_score2,def_letter2,full_score2,full_letter2,number_of_players_position,Rank_of2,Rank_def2,Rank_full2=notas_tacticas(PLAYER_POSITION,df_position,parameters_file,player_id2,min_minutes)# print(of_score)
    # print(def_score)
    phys_score,phys_letter=None,None
    output_phys=None
    of_score1=round(of_score1,2)
    def_score1=round(def_score1,2)
    
    of_score2=round(of_score2,2)
    def_score2=round(def_score2,2)

    PIZZAPLOT_OF1=output_path1
    PIZZAPLOT_OF2=output_path2
    PIZZAPLOT_DEF=output_path3
    PIZZAPLOT_PHYS=output_phys
    

    #######################
    #Imagenes

   # TEAM_LOGO = complete_teampath
    PLAYER_LOGO=player_path

    #mas cositas
    PLAYER_PHOTO = player_path
    PLAYER_NAME1 = player_name1
    PLAYER_TEAM1 = player_team1
    
    PLAYER_AGE1 = player_age1

    paths_graficas_2D=graficas_2D(opta_filepath,player_id1,player_id2,min_minutes,color="#FFFFFF")

    ##################################

    
    #Funcion de crear las barras

    def create_bar_chart(value1,value2,percentiles1,percentiles2, max_value=100, min_value=0, width=150, height=10, corner_radius=5,text="Variable"):
        """
        Creates a horizontal bar chart with rounded corners and a value indicator.

        Args:
            value (float): The current value to display (e.g., 56.30).
            max_value (float): The maximum value (default is 100).
            min_value (float): The minimum value (default is 0).
            width (int): The width of the bar chart.
            height (int): The height of the bar chart.
            corner_radius (int): The radius for rounding the corners.
            percentiles: for choosing the color of the bars

        Returns:
            Drawing: A ReportLab Drawing object containing the bar chart.
        """
        
        # Convert color to HexColor object
        # Create a drawing
        drawing = Drawing(width + 50, height + 10)

        # Ensure the value is within bounds
        max_value=100
        min_value=0
        value=min(value1,value2)
        value = max(min_value, min(value, max_value))

        # Calculate the effective range
        range_value = max_value - min_value
        if percentiles1 < 20:
            color1 = "#D2222D"  # Dark red (worst)
        elif 20 <= percentiles1 < 40:
            color1 = "#D44C56"  # Muted red
        elif 40 <= percentiles1 < 60:
            color1 = "#FFBF00"  # Yellow
        elif 60 <= percentiles1 < 80:
            color1 = "#45B05B"  # Lighter green
        elif percentiles1 >= 80:
            color1 = "#007000"  # Dark green (best)
        else:
            color1 = "#FFDFBA"  # Very light peach
            
            
        fill_color1 = HexColor(color1)
        # Background bar (empty state) with rounded corners (gray)
        drawing.add(Rect(0, 0, width, height, fillColor=HexColor("#333333"), rx=corner_radius, ry=corner_radius, strokeWidth=0))

        # Calculate filled width based on min and max values

        filled_width1=(percentiles1/100)*width
        
        
        if percentiles2 < 20:
            color2 = "#D2222D"  # Dark red (worst)
        elif 20 <= percentiles2 < 40:
            color2 = "#D44C56"  # Muted red
        elif 40 <= percentiles2 < 60:
            color2 = "#FFBF00"  # Yellow
        elif 60 <= percentiles2 < 80:
            color2 = "#45B05B"  # Lighter green
        elif percentiles2 >= 80:
            color2 = "#007000"  # Dark green (best)
        else:
            color2 = "#FFDFBA"  # Very light peach
            
            
        fill_color2 = HexColor(color2)
        
        # Calculate filled width based on min and max values

        filled_width2=(percentiles2/100)*width
        
        ##Ahora hay que dibujar las barras
        spacing=3
        y1=height+spacing
        
        filled_width1 = (percentiles1 / 100) * width
        

        drawing.add(Rect(0, y1, width, height, fillColor=HexColor("#333333"), rx=corner_radius, ry=corner_radius, strokeWidth=0))
        drawing.add(Rect(0, y1, filled_width1, height, fillColor=color1, rx=corner_radius, ry=corner_radius, strokeWidth=0))

        drawing.add(
            String(
            0,                     # X position near left edge
            y1 + height + 4,       # Y position slightly above the top bar
            f"{text}:",             # Just the label
            fillColor=letter_colors,
            fontSize=10
            )
        )

        # Value BESIDE the top bar (like before)
        drawing.add(
            String(
            width + 5,             # X position right of the bar
            y1,                     # Aligned vertically with the bar
            f"{value1:.1f}",
            fillColor=letter_colors,
            fontSize=10
            )
        )
        # --- Second bar ---
        y2 = 0
        filled_width2 = (percentiles2 / 100) * width
        

        drawing.add(Rect(0, y2, width, height, fillColor=HexColor("#333333"), rx=corner_radius, ry=corner_radius, strokeWidth=0))
        drawing.add(Rect(0, y2, filled_width2, height, fillColor=color2, rx=corner_radius, ry=corner_radius, strokeWidth=0))
        #drawing.add(String(width-200, y2+height + 2, f"      {value2:.1f}", fillColor=letter_colors, fontSize=10))
        drawing.add(String(width+5, y2, f"{value2:.1f}", fillColor=letter_colors, fontSize=10))
        avg_percentile = 50
        avg_x = (avg_percentile / 100) * width
        line = Line(avg_x, y2, avg_x, y1 + height)
        line.strokeColor = HexColor(letter_colors)  # Choose color (white, gray, etc.)
        line.strokeWidth = 1
        line.strokeDashArray = [2, 2]

        return drawing
    #print("linea 382")
    class ImageFlowable(Flowable):
        def __init__(self, image_path, width, height, x=0, y=0):
            Flowable.__init__(self)
            self.image = Image(image_path, width=width, height=height)
            self.x = x  # Posición X
            self.y = y  # Posición Y
            self.image_width = width  # Guardamos el ancho
            self.image_height = height  # Guardamos la altura

        def draw(self):
            # Coloca la imagen en las coordenadas deseadas
            self.image.drawOn(self.canv, self.x, self.y)

        def wrap(self, availWidth, availHeight):
            # Retorna el tamaño de la imagen que especificamos
            return self.image_width, self.image_height

        def drawOn(self, canv, x, y, _sW=0):
            self.canv = canv
            self.x = x
            self.y = y
            self.image.drawOn(self.canv, self.x, self.y)
    
    """
    Ahora me pongo a hacer la parte del reportlab
    """
    #Aqui lo que hago es inicializar el documento y poner los estilos de las letras
    # out_dir = Path(tempfile.gettempdir()) / "ReportsGenerados"
    # out_dir.mkdir(parents=True, exist_ok=True)
    # output_filename = out_dir / f"Report_{PLAYER_TEAM}_{player_name}.pdf"
    print("pre output-name:",BASE_DIR)
    output_filename=f"{BASE_DIR}/report_gen_opta/ReportsGenerados/Report_{player_name1}_{player_name2}.pdf"
    print(output_filename)
    doc=BaseDocTemplate(output_filename,pagesize=A4,bottomMargin=0)
    #BaseDocTemplate(output_filename,pagesize=A4,bottomMargin=0)
    
    estiloHoja=getSampleStyleSheet()
    normal_style=estiloHoja["Normal"]

    # Estilos Personalizados
    title_style = ParagraphStyle(
        'Title',
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=36,
        alignment=1,
        spaceAfter=12,
        textColor=HexColor(letter_colors)  
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        fontName='Helvetica',
        fontSize=16,
        leading=20,
        alignment=1,
        spaceAfter=6,
        textColor=HexColor(letter_colors)  # Gris
    )

    data_style = ParagraphStyle(
        'Data',
        fontName='Helvetica',
        fontSize=12,
        leading=14,
        alignment=1,
        textColor=HexColor(letter_colors)  # Gris oscuro
    )
    glossary_style = ParagraphStyle(
        'Data',
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        alignment=0,
        textColor=HexColor(letter_colors)  # Gris oscuro
    )
    #ESTO ES TODO PARA LA PORTADA
    # Función para el Fondo de la Portada
    def add_background(canvas, doc):
        #print("Adding background to page", doc.page)
        canvas.saveState()
        canvas.setFillColor(HexColor(color_selection_og))  # grey-blue background
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)  # Full-page rectangle
        # Logo paths (update with your actual paths)
        logo_left_path = "Logos/URJC_Logo.png"
        logo_right_path = "Logos/Redes_Logo.png"

        # Logo size (adjust as needed)
        logo_width = 0.89 * inch
        logo_width2 = 0.75 * inch
        logo_height = 0.89 * inch

        # Draw left logo (top-left corner)
        canvas.drawImage(
            logo_left_path,
            x=0.2 * inch,
            y=A4[1] - logo_height - 0.2 * inch,
            width=logo_width,
            height=logo_height,
            mask='auto'
        )

        # Draw right logo (top-right corner)
        canvas.drawImage(
            logo_right_path,
            x=A4[0] - logo_width - 0.2 * inch,
            y=A4[1] - logo_height - 0.2 * inch,
            width=logo_width,
           height=logo_height,
           mask='auto'
        )
        page_num = canvas.getPageNumber()
        text = f"Página {page_num}"
        canvas.setFont("Helvetica", 9)
        canvas.setFillColorRGB(0, 0, 0)  # Black text
        canvas.drawRightString(A4[0] - 0.2 * inch, 0.2 * inch, text)
        
        text2=f"{company_name}"
        canvas.setFont("Helvetica", 9)
        canvas.setFillColorRGB(0, 0, 0)  # Black text
        canvas.drawRightString(2.2* inch, 0.2 * inch, text2)
        canvas.restoreState()
        

    # Creación de la Portada
    def create_front_page(canvas, doc):
        add_background(canvas, doc)
        canvas.saveState()
        # Líneas decorativas
        canvas.setStrokeColor(HexColor(letter_colors))
        canvas.setLineWidth(1)
        page_num = canvas.getPageNumber()
        # text = f"Page {page_num}"
        # canvas.setFont("Helvetica", 9)
        # canvas.setFillColorRGB(0, 0, 0)  # Black text
        # canvas.drawRightString(A4[0] - 0.5 * inch, 0.5 * inch, text)
        canvas.restoreState()
    

    # Elementos de la Portada
    front_page_story = []
    # Título Principal
    front_page_story.append(Spacer(0,15))
    front_page_story.append(Paragraph("Análisis Comparativo", title_style))
    # Nombre del Jugador
    front_page_story.append(Spacer(0,2))
    front_page_story.append(Paragraph(f"{PLAYER_NAME1} - {player_name2}", title_style))
    front_page_story.append(Spacer(0,20))
    #####
    names1=f"{PLAYER_NAME1} | {PLAYER_TEAM1}"
    names2=f"{player_name2} | {player_team2}"
    
    photo1 = Image(PLAYER_PHOTO, width=61.75, height=70)
    photo2 = Image(PLAYER_PHOTO, width=61.75, height=70)

    # Las fotitos de las stats
    imgs_row_1 = [Image(img_path_1, width=30, height=30),
                  Image(img_path_2, width=30, height=30),
                  Image(img_path_3, width=30, height=30)]

    imgs_row_2 = [Image(img_path_1, width=30, height=30),
                  Image(img_path_2, width=30, height=30),
                  Image(img_path_3, width=30, height=30)]

    # Todas las rows
    row1=[names1,'', '', '', names2, '', '']
    row2 = [photo1, '', '', '', photo2, '', '']  # player photos
    row3 = imgs_row_1 + [''] + imgs_row_2       # stat icons
    row4 = [f'{int(player_games1)}', f'{int(player_goals1)}', f'{int(player_assists1)}', '',
            f'{int(player_games2)}', f'{int(player_goals2)}', f'{int(player_assists2)}']  # stats
    
    
    # Build table
    merged_data = [row1, row2, row3,row4]
    col_widths = [60, 60, 60, 70, 60, 60, 60]  # 20px width for the separator

    table = Table(merged_data, colWidths=col_widths)

    # Styling
    table.setStyle(TableStyle([
    # Span player photos
        
        ('SPAN', (0, 0), (2, 0)),  # photo1 spans cols 0–2
        ('SPAN', (4, 0), (6, 0)),  # photo2 spans cols 4–6
         
        ('SPAN', (0, 1), (2, 1)),  # photo1 spans cols 0–2
        ('SPAN', (4, 1), (6, 1)),  # photo2 spans cols 4–6

        # Alignments
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

    # Font and color for stats
        ("FONTNAME", (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 3), (-1, 3), 16),
        ('TEXTCOLOR', (0, 3), (-1, 3), HexColor(letter_colors)),

    # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ]))

    # Add to story
    front_page_story.append(table)
    front_page_story.append(Spacer(1, 0.2 * inch))
    
    
    front_page_story.append(Spacer(0,15))
    sub_heading=estiloHoja["Heading2"]
    sub_heading.alignment=TA_CENTER
    sub_heading.textColor=colors.HexColor(letter_colors)
    parrafo2=Paragraph(f"Ficha del jugador",sub_heading)
    front_page_story.append(parrafo2)
    front_page_story.append(Spacer(0,3))
    estilo_frames1 = ParagraphStyle(
        'BodyText',
        parent=estiloHoja['BodyText'],
        textColor=HexColor("#808080"),  # White text for visibility on dark background
        fontSize=12,
        fontName="Helvetica-Bold",
        alignment=1
    )
    estilo_frames2 = ParagraphStyle(
        'BodyText',
        parent=estiloHoja['BodyText'],
        textColor=HexColor(letter_colors),  # White text for visibility on dark background
        fontSize=12,
        fontName="Helvetica",
        alignment=1
    )
    
    # Datos de la tabla (2 filas por bloque)
    data1 = [
        ["Jugador","Posición", "Edad", "Partidos jugados","Minutos jugados"],
        [player_name1,player_position, f"{int(player_age1)} años", player_games1,player_minutes1],
        [player_name2,player_position, f"{int(player_age2)} años", player_games2,player_minutes2]
        ]

    data2 = [
        ["Jugador","Peso", "Altura","Pie dominante", "Pasaporte","País de nacimiento"],
        [player_name1,f"{int(player_weight1)} kg", f"{int(player_height1)} cm",player_foot1, player_nationality1,player_birth_country1],
        [player_name2,f"{int(player_weight2)} kg", f"{int(player_height2)} cm",player_foot2, player_nationality2,player_birth_country2]
        ]

    # Crear tablas
    table1 = Table(data1, colWidths=[100,80, 50, 100, 100])
    table2 = Table(data2, colWidths=[100,40, 40, 130, 130])

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    # Nada de GRID ni BOX para que no se vean líneas
    ])

    table1.setStyle(style)
    table2.setStyle(style)
    front_page_story.append(table1)
    front_page_story.append(Spacer(0, 10))
    front_page_story.append(table2)
    front_page_story.append(Spacer(0, 10))
    #Estilo de la cabecera
    cabecera=estiloHoja["Heading1"]
    cabecera.alignment=TA_CENTER
    cabecera.textColor=colors.HexColor(letter_colors)
    
    d31=full_letter1
    d32=of_letter1
    d33=def_letter1

    if d31=="A":
        full_colord31="#007000"
    elif d31=="B":
        full_colord31="#45B05B" #verde mas clarito
    elif d31=="C":
        full_colord31="#FFBF00"
    else:
        full_colord31="#D2222D"
    
    if d32=="A":
        full_colord32="#007000"
    elif d32=="B":
        full_colord32="#45B05B" #verde mas clarito
    elif d32=="C":
        full_colord32="#FFBF00"
    else:
        full_colord32="#D2222D"
        
    if d33=="A":
        full_colord33="#007000"
    elif d33=="B":
        full_colord33="#45B05B" #verde mas clarito
    elif d33=="C":
        full_colord33="#FFBF00"
    else:
        full_colord33="#D2222D"

    estilo_notes = ParagraphStyle(
        'BodyText',
        parent=estiloHoja['BodyText'],
        textColor=HexColor("#808080"),  
        fontSize=20,
        fontName="Helvetica-Bold",
        alignment=1
    )
    Paragraph_d1=Paragraph(f'<font color="{full_colord31}">{d31} </font>',estilo_notes)
    Paragraph_d2=Paragraph(f'<font color="{full_colord32}">{d32} </font>',estilo_notes)
    Paragraph_d3=Paragraph(f'<font color="{full_colord33}">{d33} </font>',estilo_notes)
    
    
    d41=Rank_full1
    d42= Rank_of1
    d43=Rank_def1
    
    d312=full_letter2
    d322=of_letter2
    d332=def_letter2

    if d312=="A":
        full_colord312="#007000"
    elif d312=="B":
        full_colord312="#45B05B" #verde mas clarito
    elif d312=="C":
        full_colord312="#FFBF00"
    else:
        full_colord312="#D2222D"
    
    if d322=="A":
        full_colord322="#007000"
    elif d322=="B":
        full_colord322="#45B05B" #verde mas clarito
    elif d322=="C":
        full_colord322="#FFBF00"
    else:
        full_colord322="#D2222D"
        
    if d332=="A":
        full_colord332="#007000"
    elif d332=="B":
        full_colord332="#45B05B" #verde mas clarito
    elif d332=="C":
        full_colord332="#FFBF00"
    else:
        full_colord332="#D2222D"

    estilo_notes = ParagraphStyle(
        'BodyText',
        parent=estiloHoja['BodyText'],
        textColor=HexColor("#808080"),  # White text for visibility on dark background
        fontSize=20,
        fontName="Helvetica-Bold",
        alignment=1
    )
    Paragraph_d12=Paragraph(f'<font color="{full_colord312}">{d312} </font>',estilo_notes)
    Paragraph_d22=Paragraph(f'<font color="{full_colord322}">{d322} </font>',estilo_notes)
    Paragraph_d32=Paragraph(f'<font color="{full_colord332}">{d332} </font>',estilo_notes)
    
    
    d412=Rank_full2
    
    d422= Rank_of2
    d432=Rank_def2

    parrafo3=Paragraph(f"Valoraciones",sub_heading)
    front_page_story.append(Spacer(0,3))
    front_page_story.append(parrafo3)
    data_t3=[
        ["Jugador","Valoración táctica global","Valoración ofensiva","Valoración defensiva"],
        [player_name1,Paragraph_d1,Paragraph_d2,Paragraph_d3],
        [" ",f"{d41}/{number_of_players_position}",f"{d42}/{number_of_players_position}",f"{d43}/{number_of_players_position}"],
        [player_name2,Paragraph_d12,Paragraph_d22,Paragraph_d32],
        [" ",f"{d412}/{number_of_players_position}",f"{d422}/{number_of_players_position}",f"{d432}/{number_of_players_position}"]
        ]
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Light grey background for the header row
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),       # Black text color for header row
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),    # Bold font for header row
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),         # Normal Helvetica for second row (maybe first data row)
        ('FONTSIZE', (0, 0), (-1, 0), 9),                  # Font size 9 for all cells
        ('FONTSIZE', (0, 1), (-1, -1), 14), 
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),              # Center alignment for all cells
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),             # Padding at the bottom of each cell
    # NO VISIBLE BORDERS
    ])
    table3 = Table(data_t3, colWidths=[100,120, 120, 120, 120])
    table3.setStyle(style)
    front_page_story.append(table3)
    
    ### Fecha de Generación
    
    date_style = ParagraphStyle('Date', parent=estiloHoja['Normal'], alignment=1, fontSize=10,textColor=HexColor(letter_colors))
    front_page_story.append(Spacer(1,35))
    front_page_story.append(Paragraph(f"Informe generado el {time.strftime('%d/%m/%Y')}", date_style))
    
    #Ahora defino los frames
    frame_front_page = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='front_page_frame')

    logo_buffer=0*inch
    frame_main = Frame(
        0,  # Start from left margin
        0,  # Start from the bottom
        doc.width,  # Full width of the page
        doc.height,  # Full height of the page
        id="main_frame"
    )
    #page 2 of report
    frame_main2 = Frame(
        0,  # Start from left margin
        0,  # Start from the bottom
        doc.width,  # Full width of the page
        doc.height,
        id="main_frame2"
    )
    
    
   
    #templates for frontpage and main page
    template_front_page = PageTemplate(id='front_page', frames=[frame_front_page], onPage=create_front_page)
    template_main = PageTemplate(id='main', frames=[frame_main],onPage=add_background)
    template_main2=PageTemplate(id="main_2",frames=[frame_main2],onPage=add_background)
    template_main3=PageTemplate(id="main_3",frames=[frame_main2],onPage=add_background)
    #aqui ya seguimos con main page

    main_story=[]
    main_story.append(Spacer(0,20))

    ####
    #IMAGEN FOTO JUGADOR
    image_path = os.path.realpath(PLAYER_PHOTO)
    
    #### Pagina Glossary wyscout
    main_story15=[]
    glossary_title="Variables de análisis táctico"
    main_story15.append(Paragraph(glossary_title,title_style))
    main_story15.append(Spacer(0,1))
    data_glossary=glossary[player_position_original1]

    # main_story15.append(glossary_table)
    glossary_text="<br/>".join(data_glossary)
    glossary_paragraph = Paragraph(glossary_text, glossary_style)

    wrapped_paragraph = KeepInFrame(500, 800, content=[glossary_paragraph], mode='shrink')  # or mode='truncate'/'overflow'
    main_story15.append(wrapped_paragraph)
    #main_story15.append(Paragraph(glossary_text,glossary_style))
    
 
    #PIZZAPLOT
    

    main_story2=[]

    heading2=Paragraph('Estadísticas Ofensivas 1',title_style)
    heading2.outlineLevel=0
    main_story2.append(heading2)
    
    pizza_offensive_1=Image(PIZZAPLOT_OF1,width=525,height=600)
    pizza_offensive_1.hAlign="CENTER"
    main_story2.append(pizza_offensive_1)
    
    aclaracion_style = ParagraphStyle(
        'Data',
        fontName='Helvetica',
        fontSize=20,
        leading=16,
        alignment=2,
        textColor=HexColor(letter_colors)  # Gris oscuro
    )
    aclaracion_style2 = ParagraphStyle(
        'Data',
        fontName='Helvetica',
        fontSize=10,
        leading=16,
        alignment=0,
        textColor=HexColor(letter_colors)  # Gris oscuro
    )
    
    aclaracion2=f"* Entre paréntesis se indican, para todas las métricas, los valores promedio para esta posición en la liga. El primer valor corresponde a {player_name1} y el segundo a {player_name2}. "
    main_story2.append(Spacer(0,5))
    main_story2.append(Paragraph(aclaracion2,aclaracion_style2))
    

    main_story6=[]
    
    if PIZZAPLOT_OF2 is not None:
        main_story6.append(Paragraph('Estadísticas Ofensivas 2',title_style))
        pizza_offensive_2=Image(PIZZAPLOT_OF2,width=525,height=600)
        pizza_offensive_2.hAlign="CENTER"
        main_story6.append(pizza_offensive_2)
        main_story6.append(Spacer(0,5))
        main_story6.append(Paragraph(aclaracion2,aclaracion_style2))
    else:
        
        Paragraph_not= "PIZZAPLOT_OF2 does not exist."
        main_story6.append(Paragraph(Paragraph_not, title_style))
    

    main_story5=[]
    
    heading5=Paragraph('Estadísticas Defensivas',title_style)
    heading5.outlineLevel=0
    main_story5.append(heading5)
    pizza_defensive = Image(PIZZAPLOT_DEF,width=525, height=600)
    pizza_defensive.hAlign = 'CENTER'
    main_story5.append(pizza_defensive)
    main_story5.append(Spacer(0,5))
    main_story5.append(Paragraph(aclaracion2,aclaracion_style2))
    
    
    #pagina 3 con percentiles
    bars=[]
   
    for i in range(len(min_of1)):
        min_value=min_of1.iloc[i]
        max_value=max_of1.iloc[i]
        player_value1=player_of11.iloc[i]
        player_value2=player_of12.iloc[i]
        text=player_of11.index[i]
        percentile1=percentiles_of11[i]
        percentile2=percentiles_of12[i]

        bar=create_bar_chart(player_value1,player_value2,percentile1,percentile2,max_value,min_value,width=200, height=10, corner_radius=5,text=text)
        bars.append(bar)
    bars2=[]

    for i in range(len(min_of2)):
        min_value=min_of2.iloc[i]
        max_value=max_of2.iloc[i]
        player_value1=player_of21.iloc[i]
        player_value2=player_of22.iloc[i]
        text=player_of21.index[i]
        percentile1=percentiles_of21[i]
        percentile2=percentiles_of22[i]
        
        bar=create_bar_chart(player_value1,player_value2,percentile1,percentile2,max_value,min_value,width=200, height=10, corner_radius=5,text=text)
        bars2.append(bar)
            
    main_story3=[]
    main_story3.append(Spacer(0,1))
    cadena6=f"Estadísticas Ofensivas"
    parrafo9=Paragraph(cadena6,title_style)
    cadena66=f"{player_name1} - {player_name2}"
    parrafo99=Paragraph(cadena66,cabecera)
    main_story3.append(parrafo9)
    main_story3.append(parrafo99)
    main_story3.append(Spacer(0,20))
    grouped_bars = [bars[i:i+2] for i in range(0, len(bars), 2)]
    for row_index, bar_pair in enumerate(grouped_bars):
        # 2 columns para cada row
        table_data = [bar_pair]  # Use the pair directly as a row
        
        #bordes invisibles
        t = Table(table_data, colWidths=[290, 290], rowHeights=[25])  
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP')             
        ]))
        main_story3.append(t)
        main_story3.append(Spacer(0, 20))  # Add vertical space between rows
    grouped_bars2 = [bars2[i:i+2] for i in range(0, len(bars2), 2)]
    for row_index, bar_pair2 in enumerate(grouped_bars2):
        table_data2 = [bar_pair2]  # Use the pair directly as a row

        t2 = Table(table_data2, colWidths=[290, 290],rowHeights=[25])  
        t2.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP')              
        ]))
        main_story3.append(t2)
        main_story3.append(Spacer(0, 20)) 
    styles = getSampleStyleSheet()
    score_style = ParagraphStyle(
        'score',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=52,
        alignment=1,
        spaceAfter=12,
        textColor=HexColor(letter_colors),
        textDecoration="none",  
        underline=False,
    )
    if of_letter1=="A":
        of_color1="#007000"
    elif of_letter1=="B":
        of_color1="#45B05B" #verde mas clarito
    elif of_letter1=="C":
        of_color1="#FFBF00"
    else:
        of_color1="#D2222D"
        
    if def_letter1=="A":
        def_color1="#007000"
    elif def_letter1=="B":
        def_color1="#45B05B" #verde mas clarito
    elif def_letter1=="C":
        def_color1="#FFBF00"
    else:
        def_color1="#D2222D"
    
    if full_letter1=="A":
        full_color1="#007000"
    elif full_letter1=="B":
        full_color1="#45B05B" #verde mas clarito
    elif full_letter1=="C":
        full_color1="#FFBF00"
    else:
        full_color1="#D2222D"
        
    if of_letter2=="A":
        of_color2="#007000"
    elif of_letter2=="B":
        of_color2="#45B05B" #verde mas clarito 
    elif of_letter2=="C":
        of_color2="#FFBF00"
    else:
        of_color2="#D2222D"
    
    if def_letter2=="A":
        def_color2="#007000"
    elif def_letter2=="B":
        def_color2="#45B05B" #verde mas clarito
    elif def_letter2=="C":
        def_color2="#FFBF00"
    else:
        def_color2="#D2222D"

    if full_letter2=="A":
        full_color2="#007000"
    elif full_letter2=="B":
        full_color2="#45B05B" #verde mas clarito
    elif full_letter2=="C":
        full_color2="#FFBF00"
    else:
        full_color2="#D2222D"
    main_story3.append(Spacer(0,5))
    
    title_style_smaller = ParagraphStyle(
        'Title',
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=36,
        alignment=1,
        spaceAfter=12,
        textColor=HexColor(letter_colors)  
    )
    
    Paragraph_of=f"Valoración ofensiva ({PLAYER_POSITION}):"
    main_story3.append(Paragraph(Paragraph_of,title_style_smaller))
    letters=["A","B","C","D"]
    formatted=''
    for letter in letters:
        if letter==of_letter1:
            formatted+= f'<font color="{of_color1}" size="48"><b>{letter}</b></font>&nbsp;'
        else:
            formatted+=f"{letter} &nbsp "
    Paragraph_score_of1 =formatted 
    
    letters=["A","B","C","D"]
    formatted12=''
    for letter in letters:
        if letter == of_letter2:
            formatted12 += f'<font color="{of_color2}" size="48"><b>{letter}</b></font>&nbsp;'
        else:
            formatted12 += f"{letter}&nbsp;"
    
    
    formatted_paragraph1 = Paragraph(formatted, score_style)
    formatted_paragraph2 = Paragraph(formatted12, score_style)

    data_val_of = [
        [Paragraph(player_name1,title_style_smaller), Paragraph(player_name2,title_style_smaller)],
        [formatted_paragraph1, formatted_paragraph2]
        ]
    table_val_of = Table(data_val_of, colWidths=[200, 200])

    # Table style: no visible lines
    table_val_of.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0, colors.white),  # invisible grid
        ('BOX', (0,0), (-1,-1), 0, colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5)
        ]))

    #Paragraph_of_score=f"{formatted} &nbsp | &nbsp {formatted12}"
    main_story3.append(Spacer(0,1))
    main_story3.append(table_val_of)
    main_story3.append(Spacer(0,10))
    texto_aclaración="* Valoración en función de las variables ponderadas según la posición del jugador"
    main_story3.append(Paragraph(texto_aclaración,aclaracion_style2))
    
    
    main_story4=[]
    main_story4.append(Spacer(0,20))
    cadena7=f"Estadísticas Defensivas"
    parrafo10=Paragraph(cadena7,title_style)
    cadena77=f"{player_name1} - {player_name2}"
    parrafo100=Paragraph(cadena77,cabecera)
    main_story4.append(parrafo10)
    main_story4.append(parrafo100)
    main_story4.append(Spacer(0,35))
    
    bars3=[]

    for i in range(len(min_def)):
        min_value=min_def.iloc[i]
        max_value=max_def.iloc[i]
        player_value1=player_def1.iloc[i]
        player_value2=player_def2.iloc[i]
        text=player_def1.index[i]
        percentile1=percentiles_def1[i]
        percentile2=percentiles_def2[i]
        
        
        bar=create_bar_chart(player_value1,player_value2,percentile1,percentile2,max_value,min_value,width=200, height=10, corner_radius=5,text=text)
        bars3.append(bar)
        
    grouped_bars3 = [bars3[i:i+2] for i in range(0, len(bars3), 2)]
    for row_index, bar_pair3 in enumerate(grouped_bars3):

        table_data3 = [bar_pair3]  # Use the pair directly as a row

        t3 = Table(table_data3, colWidths=[297, 297],rowHeights=[25])  
        t3.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP')        
        ]))
        main_story4.append(t3)
        main_story4.append(Spacer(0, 25))  # Add vertical space between rows
    main_story4.append(Spacer(0,10))
    Paragraph_def=f"Valoración defensiva ({PLAYER_POSITION}):"
    main_story4.append(Paragraph(Paragraph_def,title_style_smaller))
    main_story4.append(Spacer(0,2))
    Paragraph_score_def=f'<font color="{def_color1}">{def_letter1} </font>'
    letters=["A","B","C","D"]
    formatted2=''
    for letter in letters:
        if letter==def_letter1:
            formatted2+= f'<font color="{def_color1}" size="48"><b>{letter}</b></font>&nbsp  '
        else:
            formatted2+=f"{letter} &nbsp "
    formatted22=''
    for letter in letters:
        if letter==def_letter2:
            formatted22+= f'<font color="{def_color2}" size="48"> <b>{letter}</b></font>&nbsp  '
        else:
            formatted22+=f"{letter} &nbsp "
            
    formatted_paragraph2 = Paragraph(formatted2, score_style)
    formatted_paragraph22 = Paragraph(formatted22, score_style)

    data_val_def = [
        [Paragraph(player_name1,title_style_smaller), Paragraph(player_name2,title_style_smaller)],
        [formatted_paragraph2, formatted_paragraph22]
        ]
    table_val_def = Table(data_val_def, colWidths=[200, 200])

    # Table style: no visible lines
    table_val_def.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0, colors.white),  # invisible grid
        ('BOX', (0,0), (-1,-1), 0, colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5)
        ]))
    
    #Paragraph_def_score=f"{formatted2} &nbsp | &nbsp {formatted22}"
    main_story4.append(table_val_def)
    main_story4.append(Spacer(0,15))
    linea_image_path="Logos/linea_break.jpg"
    Linea = Image(linea_image_path,width=500, height=10)
    Linea.hAlign = "CENTER"
    main_story4.append(Linea)
    main_story4.append(Spacer(0,1))
    Paragraph_full=f"Valoración táctica global ({PLAYER_POSITION}):"
    main_story4.append(Paragraph(Paragraph_full,title_style_smaller))
    main_story4.append(Spacer(0,2))
    Paragraph_score_full=f'<font color="{full_color1}">{full_letter1} </font>'
    letters=["A","B","C","D"]
    formatted3=''
    for letter in letters:
        if letter==full_letter1:
            formatted3+= f'<font color="{full_color1}" size="48"><b>{letter}</b></font>&nbsp  '
        else:
            formatted3+=f"{letter} &nbsp "
    formatted32=''
    for letter in letters:
        if letter==full_letter2:
            formatted32+= f'<font color="{full_color2}" size="48"> <b>{letter}</b></font>&nbsp  '
        else:
            formatted32+=f"{letter} &nbsp "
    Paragraph_score_full=f"{formatted3} &nbsp | &nbsp {formatted32}"
    
    formatted_paragraph3 = Paragraph(formatted3, score_style)
    formatted_paragraph32 = Paragraph(formatted32, score_style)

    data_val_full = [
        [Paragraph(player_name1,title_style_smaller), Paragraph(player_name2,title_style_smaller)],
        [formatted_paragraph3, formatted_paragraph32]
        ]
    table_val_full = Table(data_val_full, colWidths=[200, 200])

    # Table style: no visible lines
    table_val_full.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0, colors.white),  # invisible grid
        ('BOX', (0,0), (-1,-1), 0, colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5)
        ]))
    main_story4.append(table_val_full)
    main_story4.append(Spacer(0,20))
    main_story4.append(Paragraph(texto_aclaración,aclaracion_style2))

    doc.addPageTemplates([template_front_page, template_main])
    
    main_story17=[]
    title_style_small=ParagraphStyle(
        'Title',
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=36,
        alignment=1,
        spaceAfter=12,
        textColor=HexColor(letter_colors)  
    )

    title_17="Métricas Ofensivas"
    main_story17.append(Paragraph(title_17,title_style))
    main_story17.append(Paragraph("Goles y goles esperados (xG)",title_style_small))
    Grafica2D1 = Image(paths_graficas_2D[0],width=600, height=600)
    Grafica2D1.hAlign = "CENTER"
    main_story17.append(Grafica2D1)
    main_story17.append(PageBreak())
    main_story17.append(Paragraph("Asistencias y asistencias esperadas (xA)",title_style_small))
    Grafica2D2 = Image(paths_graficas_2D[1],width=600, height=600)
    Grafica2D2.hAlign = "CENTER"
    main_story17.append(Grafica2D2)
    
    main_story18=[]
    main_story18.append(Paragraph("Jugadas Clave",title_style_small))
    Grafica2D3 = Image(paths_graficas_2D[2],width=600, height=600)
    Grafica2D3.hAlign = "CENTER"
    main_story18.append(Grafica2D3)
    main_story18.append(PageBreak())
    
    main_story18.append(Paragraph("Pases último tercio",title_style_small))
    Grafica2D4 = Image(paths_graficas_2D[3],width=600, height=600)
    Grafica2D4.hAlign = "CENTER"
    main_story18.append(Grafica2D4)
    
    main_story18.append(PageBreak())
    main_story18.append(Paragraph("Duelos atacantes",title_style_small))
    Grafica2D5 = Image(paths_graficas_2D[4],width=600, height=600)
    Grafica2D5.hAlign = "CENTER"
    main_story18.append(Grafica2D5)
    
    main_story19=[]
    main_story19.append(Paragraph("Pases cortos y medios",title_style_small))
    Grafica2D6 = Image(paths_graficas_2D[5],width=600, height=600)
    Grafica2D6.hAlign = "CENTER"
    main_story19.append(Grafica2D6)
    main_story19.append(PageBreak())
    main_story19.append(Paragraph("Pases largos",title_style_small))
    Grafica2D7 = Image(paths_graficas_2D[6],width=600, height=600)
    Grafica2D7.hAlign = "CENTER"
    main_story19.append(Grafica2D7)
    
    main_story20=[]
    main_story20.append(Paragraph("Pases progresivos",title_style_small))
    Grafica2D8 = Image(paths_graficas_2D[7],width=600, height=600)
    Grafica2D8.hAlign = "CENTER"
    main_story20.append(Grafica2D8)
    main_story20.append(PageBreak())
    
    main_story20.append(Paragraph("Regates",title_style_small))
    Grafica2D9 = Image(paths_graficas_2D[8],width=600, height=600)
    Grafica2D9.hAlign = "CENTER"
    main_story20.append(Grafica2D9)
    
    main_story21=[]
    
    title_21="Métricas Defensivas"
    main_story21.append(Paragraph(title_21,title_style))
    main_story21.append(Paragraph("Duelos defensivos",title_style_small))
    Grafica2D10 = Image(paths_graficas_2D[9],width=600, height=600)
    Grafica2D10.hAlign = "CENTER"
    main_story21.append(Grafica2D10)
    main_story21.append(PageBreak())
    main_story21.append(Paragraph("Interceptaciones vs posesión conquistada",title_style_small))
    Grafica2D11 = Image(paths_graficas_2D[10],width=600, height=600)
    Grafica2D11.hAlign = "CENTER"
    main_story21.append(Grafica2D11)
    
    main_story22=[]
    title_22="Posiciones Específicas"
    main_story22.append(Paragraph(title_22,title_style))
    texto = """GK: portero.
    LB: lateral izquierdo.
    RB: lateral derecho.
    DMF: mediocentro defensivo.
    OF: mediocentro ofensivo.
    AMF: mediapunta.
    LCB: defensa central izquierdo.
    RCB: defensa central derecho.
    CB: defensa central.
    LWF: extremo izquierdo.
    RWF: extremo derecho.
    LW: carrillero izquierdo.
    RW: carrillero derecho.
    LAMF: media punta izquierdo.
    RAMF: media punta derecho.
    LCMF: interior (mediapunta izquierdo).
    RCMF: interior (mediapunta derecho).
    CF: delantero centro."""
    
    partes=texto.split("\n")
    contenido_format=""
    for linea in partes:
        if ":" in linea:
            clave, valor=linea.split(":",1)
            contenido_format+=f"<b>{clave.strip()}:</b>{valor.strip()}<br/>"
            
            
    glossary_style2 = ParagraphStyle(
        'Data',
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        alignment=0,
        textColor=HexColor(letter_colors)  # Gris oscuro
    )
    main_story22.append(Spacer(0,5))
    parrafo11=Paragraph(contenido_format,glossary_style2)

    main_story22.append(parrafo11)
    
   
    
    # aqui voy a empezar a añadir lo de chat gpt- que sea ofensivo y defensivo y que sean dos hojas distintas?
    #por ahora 1 hojita
    main_story23=[]
    context=f"You are going to contribute to a two players comparison report about two players in {current_league} league in Spain. Be thorough and impartial, providing clear observations and evidence to support your analysis. Compare the key performance indicators of {player_name1} and {player_name2}. Choose the best overall player. If the value is smaller than the average it means she is worse. If the value is better than the average it means she is better."
    create_chat_log(context)
    player_arrayof11,average_arrayof1,player_name,player_pos,params_arrayof1=extract_arrays_wyscout2(wyscout_file,parameters_file,player_id1,"param_of1",min_minutes)
    player_arrayof21,average_arrayof2,player_name,player_pos,params_arrayof2=extract_arrays_wyscout2(wyscout_file,parameters_file,player_id1,"param_of2",min_minutes)
    
    player_arrayof12,average_arrayof1,player_name,player_pos,params_arrayof1=extract_arrays_wyscout2(wyscout_file,parameters_file,player_id2,"param_of1",min_minutes)
    player_arrayof22,average_arrayof2,player_name,player_pos,params_arrayof2=extract_arrays_wyscout2(wyscout_file,parameters_file,player_id2,"param_of2",min_minutes)
    
    player_arrayof1 = pd.concat([player_arrayof11, player_arrayof21])
    player_arrayof2 = pd.concat([player_arrayof12, player_arrayof22])

    average_arrayof = pd.concat([average_arrayof1, average_arrayof2])

    params_arrayof=params_arrayof1+params_arrayof2
    
    dict_english={"delantero":"forward","ofmid":"ofensive midfielder","extremo":"winger","defmid":"defensive midfielder","lateral":"fullback","defensa":"center back","portero":"goalkeeper"}
    
    chat_comment = f"Write a paragraph comparing the offensive strengths and weaknesses of Player A and Player B, both playing as {dict_english[player_pos]}. The parameters being evaluated are: {params_arrayof}.The values for each player are: {player_name1} {player_arrayof1}, {player_name1}: {player_arrayof2}. The average values for the position are: {average_arrayof}.Highlight where each player excels or underperforms compared to each other and to the average, and suggest areas where they could improve. Choose the best player."
    chat(chat_comment, context, action="translate", language="Spanish",chat_log=None)
    
    with open("response.txt","r",encoding="utf-8") as file:
        text_ofensive=file.read()
    paragraphs=text_ofensive.split("\n\n")
    

    of_text = "<br/><br/>".join(paragraphs[2:]) if len(paragraphs) > 1 else ""

    parrafo_oftxt=Paragraph(of_text,glossary_style2)
    main_story23.append(Paragraph("Resumen Ofensivo",title_style))
    main_story23.append(parrafo_oftxt)
    with open("response.txt", "w", encoding="utf-8") as file:
        file.write("")
    
    
    player_arraydef1,average_arraydef,player_name1,player_pos,params_arraydef=extract_arrays_wyscout2(df_position,parameters_file,player_id1,"param_def",min_minutes)
    player_arraydef2,average_arraydef,player_name2,player_pos,params_arraydef=extract_arrays_wyscout2(df_position,parameters_file,player_id2,"param_def",min_minutes)
    
    chat_comment = f"Write a paragraph comparing the defensive strengths and weaknesses of Player A and Player B, both playing as {dict_english[player_pos]}. The parameters being evaluated are: {params_arrayof}.The values for each player are: {player_arraydef1} {player_arraydef2}, {player_name1}: {player_arraydef2}. The average values for the position are: {average_arraydef}.Highlight where each player excels or underperforms compared to each other and to the average, and suggest areas where they could improve. Choose the best player."
    chat(chat_comment, context, action="translate", language="Spanish",chat_log=None)
    
    with open("response.txt","r",encoding="utf-8") as file:
        text_defensive=file.read()
    paragraphs=text_defensive.split("\n\n")
    #we keep all paragraphs expect first
    def_text = "<br/><br/>".join(paragraphs[2:]) if len(paragraphs) > 1 else ""
    parrafo_deftxt=Paragraph(def_text,glossary_style2)
    main_story23.append(PageBreak())
    main_story23.append(Paragraph("Resumen Defensivo",title_style))
    main_story23.append(parrafo_deftxt)
    
    with open("response.txt", "w", encoding="utf-8") as file:
        file.write("")
        
    
    if PLAYER_POSITION=="Defensa" or PLAYER_POSITION=="Lateral" or PLAYER_POSITION=="Portero":
        #### INDICE
        index_story=[]
            
        index_style = ParagraphStyle(
            'TOC',
            fontName='Helvetica',
            fontSize=14,
            leading=36,
            alignment=0,
            spaceAfter=12,
            textColor=HexColor(letter_colors)
        )
            
        entries = [("1. Estadísticas Ofensivas", "3"),
            ("2. Estadísticas Defensivas", "4"),
            ("3. Anexos", "5")]

        def fill_dots(title, total_width=98):
            width=total_width-len(title)-1
            return title + " " 

        index_story = []
        index_story.append(Paragraph("Índice", title_style))
        index_story.append(Spacer(1, 20))
            
        table_data = []
        for title, page in entries:
                
            table_data.append([fill_dots(title, 96), page])

        table = Table(table_data, colWidths=[150*mm, 20*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))

            
        index_story.append(table)

        full_Story = ( 
            front_page_story + [PageBreak()] +
            index_story + [PageBreak()] +
            main_story2 + [PageBreak()] +
            main_story3 + [PageBreak()] +
            main_story5 + [PageBreak()] +
            main_story4 + [PageBreak()] +
            main_story23 + [PageBreak()] +
            main_story17 + [PageBreak()] +
            main_story18 + [PageBreak()] +
            main_story19 + [PageBreak()] +
            main_story20 + [PageBreak()] +
            main_story21 + [PageBreak()] +
            main_story15 + [PageBreak()] +
            main_story22
            )
            
    else:
            #### INDICE
        index_story=[]
            
        index_style = ParagraphStyle(
            'TOC',
            fontName='Helvetica',
            fontSize=14,
            leading=36,
            alignment=0,
            spaceAfter=12,
            textColor=HexColor(letter_colors)
        )
            
        entries = [("1. Estadísticas Ofensivas", "3"),
            ("2. Estadísticas Defensivas", "5"),
            ("3. Anexos", "6")]

        def fill_dots(title, total_width=98):
            width=total_width-len(title)-1
            return title + " " 

        index_story = []
        index_story.append(Paragraph("Índice", title_style))
        index_story.append(Spacer(1, 20))
            
        table_data = []
        for title, page in entries:
                
            table_data.append([fill_dots(title, 96), page])

        table = Table(table_data, colWidths=[150*mm, 20*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))

            
        index_story.append(table)

        full_Story = ( 
            front_page_story + [PageBreak()] +
            index_story + [PageBreak()] +
            main_story2 + [PageBreak()] +
            main_story6 + [PageBreak()] +
            main_story3 + [PageBreak()] +
            main_story5 + [PageBreak()] +
            main_story4 + [PageBreak()] +
            main_story23 + [PageBreak()] +
            main_story17 + [PageBreak()] +
            main_story18 + [PageBreak()] +
            main_story19 + [PageBreak()] +
            main_story20 + [PageBreak()] +
            main_story21 + [PageBreak()] +
            main_story15 + [PageBreak()] +
            main_story22 
            )
    if summary==1:
        if PLAYER_POSITION=="Defensa" or PLAYER_POSITION=="Lateral" or PLAYER_POSITION=="Portero":
            full_Story = ( 
                front_page_story + [PageBreak()] +
                index_story + [PageBreak()] +
                main_story2 + [PageBreak()] +
                main_story6 + [PageBreak()] +
                main_story3 + [PageBreak()] +
                main_story5 + [PageBreak()] +
                main_story4 + [PageBreak()] +
                main_story23 + [PageBreak()] +
                main_story15 + [PageBreak()] +
                main_story22 
                )
        else:
            full_Story = ( 
                front_page_story + [PageBreak()] +
                index_story + [PageBreak()] +
                main_story2 + [PageBreak()] +
                main_story6 + [PageBreak()] +
                main_story3 + [PageBreak()] +
                main_story5 + [PageBreak()] +
                main_story4 + [PageBreak()] +
                main_story23 + [PageBreak()] +
                main_story15 + [PageBreak()] +
                main_story22 
                )
        

    doc.build(
        full_Story
    )
    #############

    # destination_folder="/Users/julieta/Dropbox/Informes_copy"
    # shutil.copy(output_filename, destination_folder)
    images_to_delete = [output_path1, output_path2, output_path3] + paths_graficas_2D
    
    for image_file in images_to_delete:
        try:
            os.remove(image_file)
        except Exception as e:
            print(f"Error deleting {image_file}: {e}")
            
    print("PDF generated successfully!")
#create_report(250568,"/Users/julieta/Desktop/APP_Generic_Femeni/report_gen/LigaF_opta_2024.xlsx","/Users/julieta/Desktop/APP_Generic_Femeni/report_gen/parameters.xlsx",500,color_selection="#FFFFFF",summary=0,current_league="Liga F",season="2024/25")

if __name__ == "__main__":
    #print("ENTRAMOS BIEN")
    parser = argparse.ArgumentParser()
    parser.add_argument("--player_id_analizing", type=int, required=True)
    parser.add_argument("--opta_filepath", type=str, required=True)
    parser.add_argument("--parameters_file", type=str, required=True)
    parser.add_argument("--min_minutes", type=int, default=500)
    parser.add_argument("--color_selection", type=str, default="#FFFFFF")
    parser.add_argument("--summary", type=int, default=0)
    parser.add_argument("--current_league", type=str, default="Liga F")
    parser.add_argument("--season", type=str, default="2024/25")

    args = parser.parse_args()
    create_report(
        player_id_analizing=args.player_id_analizing,
        opta_filepath=args.opta_filepath,
        parameters_file=args.parameters_file,
        min_minutes=args.min_minutes,
        color_selection=args.color_selection,
        summary=args.summary,
        current_league=args.current_league,
        season=args.season
    )