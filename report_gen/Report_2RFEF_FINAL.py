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
from IntentoArrays import extract_arrays_wyscout, extract_arrays_physical
import time
from PIL import Image as PILImage
import io
from Graficas_2D import graficas_2D
from reportlab.platypus import KeepInFrame
from Notas_tacticas import notas_tacticas
#from .Notas_Skillcorner import notas_fisicas
from PizzaPhysical import pizzaplot_phys
from colorsys import rgb_to_hls
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus import NextPageTemplate
from ArraysChat import extract_arrays_wyscout2
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

# Ignorar PerformanceWarning de pandas
warnings.simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 
current_l="La Liga"
current_season="2024/25"
def create_report(player_id_analizing,wyscout_file,parameters_file,position_number,min_minutes,color_selection="#FFFFFF",summary=0,current_league=current_l,season="2024/25"):
    
    
    print("BASE DIR:",BASE_DIR)
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
    
    company_name="Departamento de Sports Analytics"
    fichero_glossary="Glossary.xlsx"
    if not os.path.exists(wyscout_file):
        print(f"El fichero {wyscout_file} no existe.")
        return None
    if not os.path.exists(parameters_file):
        print(f"El fichero {parameters_file} no existe.")
        return None
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
    positions=["portero","defensa","defmid","ofmid","lateral","delantero","extremo"]
    glossary={}
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
    
    check=pd.read_excel(wyscout_file)
    if player_id_analizing>len(check):
        print("Player not valid")
        return None
    check["player_id"] = check.index + 2
    
    if player_id_analizing not in check["player_id"].values:
        print("No se encuentra el jugador")
        return None
    
    check=check[check["Minutos jugados"]>=min_minutes].copy()
    if player_id_analizing not in check["player_id"].values:
        print(f"El jugador ha jugado menos de {min_minutes} minutos.")
        return None
    
    min_of1, max_of1, player_of1, param_of1,df_all_stats,percentiles_of1,_ = extract_arrays_wyscout(
        wyscout_file,parameters_file,
        player_id_analizing,
        "param_of1", min_minutes
    )
    min_of2, max_of2, player_of2, param_of2, _ ,percentiles_of2,_= extract_arrays_wyscout(
        wyscout_file,parameters_file,
        player_id_analizing,
        "param_of2",min_minutes
    )
    min_def, max_def, player_def, param_def, _,percentiles_def,_ = extract_arrays_wyscout(
        wyscout_file,parameters_file,
        player_id_analizing,
        "param_def",min_minutes
    )
    
    positions_name_dict={"portero":"Portero","defensa":"Defensa","lateral":"Lateral",
                         "defmid":"Centrocampista defensivo","ofmid":"Centrocampista ofensivo",
                         "extremo":"Extremo","delantero":"Delantero"}

    positions_name_dict1={"portero":"Portero","defensa":"Defensa","lateral":"Lateral",
                         "defmid":"Centrocampista <br /> defensivo","ofmid":"Centrocampista <br /> ofensivo",
                         "extremo":"Extremo","delantero":"Delantero"}
    df_general_stats=df_all_stats[["Jugador","Equipo","Equipo durante el período seleccionado","Edad","Valor de mercado","Vencimiento contrato","Partidos jugados","Minutos jugados","player_id",'general_position', 'general_position2',"general_position3"]].copy()
    general_stats_player=df_general_stats[df_general_stats["player_id"]==player_id_analizing].iloc[0]
    stats_player=df_all_stats[df_all_stats["player_id"]==player_id_analizing].iloc[0]
    player_name=general_stats_player["Jugador"]
    print(player_name)
    player_team=general_stats_player["Equipo durante el período seleccionado"]
    player_team_loan=general_stats_player["Equipo durante el período seleccionado"]
    player_age=general_stats_player["Edad"]
    player_value=general_stats_player["Valor de mercado"]
    if player_value==0:
        player_value="-- "
    player_contract=general_stats_player["Vencimiento contrato"]
    if not player_contract or player_contract in ["", "NaN", None]:
        player_contract = "Fecha Desconocida"
    player_games=general_stats_player["Partidos jugados"]
    player_minutes=general_stats_player["Minutos jugados"]
    player_position_original=general_stats_player["general_position"]
    player_position1=positions_name_dict[general_stats_player["general_position"]]
    player_param=stats_player["general_position"]
    
    #print("linea 226")
    position_key = general_stats_player["general_position2"]

    if position_key and position_key != "None":
        player_position2 = positions_name_dict[position_key]
    else:
        player_position2 = "No second position"
        
    position_key2=general_stats_player["general_position3"]
    if position_key2 and position_key2 != "None":
        player_position3 = positions_name_dict[position_key2]
    else:
        player_position3 = "No third position"
    
    if position_number==1:
        PLAYER_POSITION=player_position1
        print(PLAYER_POSITION)
        #print(f"PLAYER POSITION: {PLAYER_POSITION}")
        player_position_text=positions_name_dict1[general_stats_player["general_position"]]
    elif position_number==2 and player_position2!="No second position":
        PLAYER_POSITION=player_position2
        print(PLAYER_POSITION)
        player_position_text=positions_name_dict1[general_stats_player["general_position2"]]
    elif position_number==3 and player_position3!="No third position":
        PLAYER_POSITION=player_position3
        print(PLAYER_POSITION)
        player_position_text=positions_name_dict1[general_stats_player["general_position3"]]
    else:
        print("No es valida la posición insertada")
        return None
        
    #print("linea 257")
    player_goals=stats_player["Goles"]
    player_assists=stats_player["Asistencias"]
    player_nationality=stats_player["Pasaporte"]
    player_weight=stats_player["Peso"]
    player_height=stats_player["Altura"]
    player_foot=stats_player["Pie"]
    player_allpositions=stats_player["Posición específica"]
    player_birth_country=stats_player["País de nacimiento"]
    
    # team_id=186
    # _next_path=f"{team_id}/logo/l_t{team_id}.png"
    # complete_teampath=filepath_carpeta+"/"+_next_path
    # player_id2=223255
    # nextpath=f"/{team_id}/formation/f_t{team_id}_p{player_id2}.png"
    # player_path=filepath_carpeta+nextpath
    #player path lo dejo asi generic por ahora

    #print("linea 275")
    if player_minutes>min_minutes:
        fig1,output_path1,fig2,output_path2,fig3,output_path3=pizzaplot_player(wyscout_file,parameters_file,player_id_analizing,min_minutes,position_number,color_selection_og,league=current_league,season=season)
        #print(output_path2)
    else:
        print(f"El jugador ha jugado menos de {min_minutes} minutos, selecciona otro jugador o baja el número de minutos necesarios.")
        return None

    of_score,of_letter,def_score,def_letter,full_score,full_letter,number_of_players_position,Rank_of,Rank_def,Rank_full=notas_tacticas(PLAYER_POSITION,wyscout_file,parameters_file,player_id_analizing,min_minutes)
    # print(of_score)
    # print(def_score)
    phys_score,phys_letter=None,None
    output_phys=None
    of_score=round(of_score,2)
    def_score=round(def_score,2)

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
    PLAYER_NAME = player_name
    PLAYER_TEAM = player_team
    
    PLAYER_AGE = player_age
    PLAYER_VALUE = player_value
    PLAYER_CONTRACT = player_contract
    paths_graficas_2D=graficas_2D(wyscout_file,player_id_analizing,PLAYER_POSITION,min_minutes,color_selection_og)

    ##################################

    
    #Funcion de crear las barras

    def create_bar_chart(value,percentiles, max_value=100, min_value=0, width=200, height=10, corner_radius=5,text="Variable"):
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
        
        original_value=value
        # Create a drawing
        drawing = Drawing(width + 50, height + 10)

        # Ensure the value is within bounds
        max_value=100
        min_value=0
        value = max(min_value, min(value, max_value))

        # Calculate the effective range
        range_value = max_value - min_value
        if percentiles < 20:
            color = "#D2222D"  # Dark red (worst)
        elif 20 <= percentiles < 40:
            color = "#D44C56"  # Muted red
        elif 40 <= percentiles < 60:
            color = "#FFBF00"  # Yellow
        elif 60 <= percentiles < 80:
            color = "#45B05B"  # Lighter green
        elif percentiles >= 80:
            color = "#007000"  # Dark green (best)
        else:
            color = "#FFDFBA"  # Very light peach
            
            
        fill_color = HexColor(color)
        # Background bar (empty state) with rounded corners (gray)
        drawing.add(Rect(0, 0, width, height, fillColor=HexColor("#333333"), rx=corner_radius, ry=corner_radius, strokeWidth=0))

        # Calculate filled width based on min and max values
        
        #filled_width = ((value - min_value) / range_value) * width
        filled_width=(percentiles/100)*width
        #percent_filled = (value - min_value) / (max_value - min_value) * 100
        


        # Filled bar (current value) with rounded corners and chosen color
        drawing.add(Rect(0, 0, filled_width, height, fillColor=fill_color, rx=corner_radius, ry=corner_radius, strokeWidth=0))

        # Add text for the value with chosen color and Helvetica font
        drawing.add(String(width - 200, height + 4, f"{text}: {original_value:.2f}", fillColor=HexColor(letter_colors), fontSize=10, fontName="Helvetica"))

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
    output_filename=f"{BASE_DIR}/report_gen/ReportsGenerados/Report_{PLAYER_TEAM}_{player_name}.pdf"
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
    #front_page_story.append(NextPageTemplate('front'))
    # Título Principal
    front_page_story.append(Spacer(0,20))
    front_page_story.append(Paragraph("Análisis Individual", title_style))
    # Nombre del Jugador
    front_page_story.append(Spacer(0,2))
    front_page_story.append(Paragraph(PLAYER_NAME, subtitle_style))
    front_page_story.append(Paragraph(f"{PLAYER_TEAM} - {PLAYER_POSITION}", subtitle_style))  # subtitulo con equipo y posicion
    front_page_story.append(Spacer(0,2))
    data_text = f"Edad: {PLAYER_AGE} | Valor: {PLAYER_VALUE} € | Contrato hasta: {PLAYER_CONTRACT}"
    front_page_story.append(Paragraph(data_text, data_style))
    front_page_story.append(Spacer(0,20))

    # Foto del Jugador
    photo = Image(PLAYER_PHOTO, width=123.5, height=140)
    photo.hAlign = 'CENTER'
    front_page_story.append(photo)
    front_page_story.append(Spacer(1, 0.2 * inch))

    # Datos Adicionales  
    data_text = f"Edad: {PLAYER_AGE} | Valor: {PLAYER_VALUE} € | Contrato hasta: {PLAYER_CONTRACT}"
    front_page_story.append(Paragraph(data_text, data_style))
    front_page_story.append(Spacer(0,1))
    data=[[Image(img_path_1,width=30,height=30),Image(img_path_2,width=30,height=30),Image(img_path_3,width=30,height=30)],
          [f'{player_games}',f'{player_goals}',f'{player_assists}']]
    # Create the table object
    table = Table(data)
    table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), HexColor(letter_colors)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),         # Center alignment
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),        # Vertical alignment
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 24),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
    table.hAling="CENTER"

    front_page_story.append(Spacer(0,1))
    front_page_story.append(table)
    ####
    front_page_story.append(Spacer(0,25))
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
        ["Posiciones", "Edad", "Valor de mercado", "Partidos jugados","Minutos jugados"],
        [player_allpositions, f"{player_age} años", f"{player_value} €", player_games,player_minutes]
        ]

    data2 = [
        ["Peso", "Altura","Pie dominante", "Pasaporte","País de nacimiento"],
        [f"{player_weight} kg", f"{player_height} cm",player_foot, player_nationality,player_birth_country]
        ]

    # Crear tablas
    table1 = Table(data1, colWidths=[100, 60, 130, 100])
    table2 = Table(data2, colWidths=[60, 60, 130, 130])

    # Opcional: aplicar estilos a las tablas
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

    # Añadir tablas al contenido
    front_page_story.append(table1)
    front_page_story.append(Spacer(0, 10))
    front_page_story.append(table2)
    front_page_story.append(Spacer(0, 10))

    #Estilo de la cabecera
    cabecera=estiloHoja["Heading1"]
    cabecera.alignment=TA_CENTER
    cabecera.textColor=colors.HexColor(letter_colors)
    
    d31=full_letter
    d32=of_letter
    d33=def_letter
    
  

    d34="No Disponible"
        
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
        
    if d34=="A":
        full_colord34="#007000"
    elif d34=="B":
        full_colord34="#45B05B" #verde mas clarito
    elif d34=="C":
        full_colord34="#FFBF00"
    else:
        full_colord34="#D2222D"

    estilo_notes = ParagraphStyle(
        'BodyText',
        parent=estiloHoja['BodyText'],
        textColor=HexColor("#808080"),  # White text for visibility on dark background
        fontSize=20,
        fontName="Helvetica-Bold",
        alignment=1
    )
    Paragraph_d1=Paragraph(f'<font color="{full_colord31}">{d31} </font>',estilo_notes)
    Paragraph_d2=Paragraph(f'<font color="{full_colord32}">{d32} </font>',estilo_notes)
    Paragraph_d3=Paragraph(f'<font color="{full_colord33}">{d33} </font>',estilo_notes)
    Paragraph_d4=Paragraph(f'<font color="{full_colord34}">{d34} </font>',estilo_notes)
    
    
    d41=Rank_full
    d42= Rank_of
    d43=Rank_def
    
    d44="No Disponible"
        
    front_page_story.append(Spacer(0,6))
    parrafo3=Paragraph(f"Valoraciones",sub_heading)
    front_page_story.append(Spacer(0,3))
    front_page_story.append(parrafo3)
    data_t3=[
        ["Valoración táctica global","Valoración ofensiva","Valoración defensiva"],
        [Paragraph_d1,Paragraph_d2,Paragraph_d3],
        [f"{d41}/{number_of_players_position}",f"{d42}/{number_of_players_position}",f"{d43}/{number_of_players_position}"]
        ]
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Light grey background for the header row
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),       # Black text color for header row
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),    # Bold font for header row
        ('FONTNAME', (0, 1), (-1, 2), 'Helvetica-Bold'),         # Normal Helvetica for second row (maybe first data row)
        ('FONTSIZE', (0, 0), (-1, 0), 9),                  # Font size 9 for all cells
        ('FONTSIZE', (0, 1), (-1, 2), 18), 
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),              # Center alignment for all cells
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),             # Padding at the bottom of each cell
    # No GRID or BOX styles — table will not have visible borders or lines
    ])
    table3 = Table(data_t3, colWidths=[120, 120, 120, 120])
    table3.setStyle(style)
    front_page_story.append(table3)
    
    # # Fecha de Generación
    
    date_style = ParagraphStyle('Date', parent=estiloHoja['Normal'], alignment=1, fontSize=10,textColor=HexColor(letter_colors))
    front_page_story.append(Spacer(1,50))
    front_page_story.append(Paragraph(f"Informe generado el {time.strftime('%d/%m/%Y')} | {current_league}, temporada {season}", date_style))
    

    #AHORA PARA LA SEGUNDA PAGINA, LA DE INFO

    #Ahora defino los frames
    frame_front_page = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='front_page_frame')
    # frame1=Frame(doc.leftMargin,doc.bottomMargin,(doc.width/2)-cm,doc.height,id="col1")
    # frame2=Frame(doc.leftMargin+(doc.width/2)+cm,doc.bottomMargin,(doc.width/2) - cm,doc.height,id="col2")
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
        #doc.height+doc.topMargin,  # Full height of the page
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
    data_glossary=glossary[player_position_original]

    # main_story15.append(glossary_table)
    glossary_text="<br/>".join(data_glossary)
    glossary_paragraph = Paragraph(glossary_text, glossary_style)

    wrapped_paragraph = KeepInFrame(500, 800, content=[glossary_paragraph], mode='shrink')  # or mode='truncate'/'overflow'
    main_story15.append(wrapped_paragraph)
    #main_story15.append(Paragraph(glossary_text,glossary_style))
    
 
    #PIZZAPLOT
    

    main_story2=[]
    #main_story2.append(NextPageTemplate('main'))
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
    
    aclaracion2="* Entre paréntesis se indican, para todas las métricas, los valores promedio para esta posición en la liga."
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
        player_value=player_of1.iloc[i]
        text=player_of1.index[i]
        percentile=percentiles_of1[i]
        bar=create_bar_chart(player_value,percentile,max_value,min_value,width=200, height=10, corner_radius=5,text=text)
        bars.append(bar)
    bars2=[]

    for i in range(len(min_of2)):
        min_value=min_of2.iloc[i]
        max_value=max_of2.iloc[i]
        player_value=player_of2.iloc[i]
        text=player_of2.index[i]
        percentile=percentiles_of2[i]
        bar=create_bar_chart(player_value,percentile,max_value,min_value,width=200, height=10, corner_radius=5,text=text)
        bars2.append(bar)
            
    main_story3=[]
    main_story3.append(Spacer(0,20))
    cadena6=f"Estadísticas Ofensivas"
    parrafo9=Paragraph(cadena6,title_style)
    cadena66=f"{player_name}"
    parrafo99=Paragraph(cadena66,cabecera)
    main_story3.append(parrafo9)
    main_story3.append(parrafo99)
    main_story3.append(Spacer(0,5))
    grouped_bars = [bars[i:i+2] for i in range(0, len(bars), 2)]
    for row_index, bar_pair in enumerate(grouped_bars):
        # Create table with 2 columns for this row
        table_data = [bar_pair]  # Use the pair directly as a row
        
        # Create table with invisible borders
        t = Table(table_data, colWidths=[250, 250])  # Adjust column widths as needed
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP')              # Align content at the top
        ]))
        main_story3.append(t)
        main_story3.append(Spacer(0, 15))  # Add vertical space between rows
    grouped_bars2 = [bars2[i:i+2] for i in range(0, len(bars2), 2)]
    for row_index, bar_pair2 in enumerate(grouped_bars2):
        # Create table with 2 columns for this row
        table_data2 = [bar_pair2]  # Use the pair directly as a row
        
        # Create table with invisible borders
        t2 = Table(table_data2, colWidths=[250, 250])  # Adjust column widths as needed
        t2.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP')              # Align content at the top
        ]))
        main_story3.append(t2)
        main_story3.append(Spacer(0, 15))  # Add vertical space between rows
    
    score_style = ParagraphStyle(
        'Title',
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=36,
        alignment=1,
        spaceAfter=12,
        textColor=HexColor(letter_colors)  
    )
    if of_letter=="A":
        of_color="#007000"
    elif of_letter=="B":
        of_color="#45B05B" #verde mas clarito
    elif of_letter=="C":
        of_color="#FFBF00"
    else:
        of_color="#D2222D"
        
    if def_letter=="A":
        def_color="#007000"
    elif def_letter=="B":
        def_color="#45B05B" #verde mas clarito
    elif def_letter=="C":
        def_color="#FFBF00"
    else:
        def_color="#D2222D"
    
    if full_letter=="A":
        full_color="#007000"
    elif full_letter=="B":
        full_color="#45B05B" #verde mas clarito
    elif full_letter=="C":
        full_color="#FFBF00"
    else:
        full_color="#D2222D"
    main_story3.append(Spacer(0,10))
    Paragraph_of=f"Valoración ofensiva ({PLAYER_POSITION}):"
    main_story3.append(Paragraph(Paragraph_of,title_style))
    #Paragraph_score_of=f'<font color="{of_color}">{of_letter} </font>'
    letters=["A","B","C","D"]
    formatted=''
    for letter in letters:
        if letter==of_letter:
            formatted+= f'<font color="{of_color}" size="48"> <b>{letter}</b></font>&nbsp  '
        else:
            formatted+=f"{letter} &nbsp "
    Paragraph_score_of =formatted   
    main_story3.append(Spacer(0,5))
    main_story3.append(Paragraph(Paragraph_score_of,score_style))
    main_story3.append(Spacer(0,20))
    texto_aclaración="* Valoración en función de las variables ponderadas según la posición del jugador"
    main_story3.append(Paragraph(texto_aclaración,aclaracion_style2))
    
    
    main_story4=[]
    main_story4.append(Spacer(0,20))
    cadena7=f"Estadísticas Defensivas"
    parrafo10=Paragraph(cadena7,title_style)
    cadena77=f"{player_name}"
    parrafo100=Paragraph(cadena77,cabecera)
    main_story4.append(parrafo10)
    main_story4.append(parrafo100)
    main_story4.append(Spacer(0,5))
    
    bars3=[]

    for i in range(len(min_def)):
        min_value=min_def.iloc[i]
        max_value=max_def.iloc[i]
        player_value=player_def.iloc[i]
        text=player_def.index[i]
        percentile=percentiles_def[i]
        bar=create_bar_chart(player_value,percentile,max_value,min_value,width=200, height=10, corner_radius=5,text=text)
        bars3.append(bar)
        
    grouped_bars3 = [bars3[i:i+2] for i in range(0, len(bars3), 2)]
    for row_index, bar_pair3 in enumerate(grouped_bars3):
        # Create table with 2 columns for this row
        table_data3 = [bar_pair3]  # Use the pair directly as a row
        
        # Create table with invisible borders
        t3 = Table(table_data3, colWidths=[250, 250])  # Adjust column widths as needed
        t3.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP')              # Align content at the top
        ]))
        main_story4.append(t3)
        main_story4.append(Spacer(0, 15))  # Add vertical space between rows
    main_story4.append(Spacer(0,10))
    Paragraph_def=f"Valoración defensiva ({PLAYER_POSITION}):"
    main_story4.append(Paragraph(Paragraph_def,title_style))
    main_story4.append(Spacer(0,5))
    Paragraph_score_def=f'<font color="{def_color}">{def_letter} </font>'
    letters=["A","B","C","D"]
    formatted2=''
    for letter in letters:
        if letter==def_letter:
            formatted2+= f'<font color="{def_color}" size="48"><b>{letter}</b></font>&nbsp  '
        else:
            formatted2+=f"{letter} &nbsp "
    Paragraph_score_def =formatted2 
    main_story4.append(Paragraph(Paragraph_score_def,score_style))
    main_story4.append(Spacer(0,15))
    linea_image_path="Logos/linea_break.jpg"
    Linea = Image(linea_image_path,width=500, height=10)
    Linea.hAlign = "CENTER"
    main_story4.append(Linea)
    Paragraph_full=f"Valoración táctica global ({PLAYER_POSITION}):"
    main_story4.append(Paragraph(Paragraph_full,title_style))
    main_story4.append(Spacer(0,5))
    Paragraph_score_full=f'<font color="{full_color}">{full_letter} </font>'
    letters=["A","B","C","D"]
    formatted3=''
    for letter in letters:
        if letter==full_letter:
            formatted3+= f'<font color="{full_color}" size="48"><b>{letter}</b></font>&nbsp  '
        else:
            formatted3+=f"{letter} &nbsp "
    Paragraph_score_full =formatted3 
    main_story4.append(Paragraph(Paragraph_score_full,score_style))
    main_story4.append(Spacer(0,20))
    main_story4.append(Paragraph(texto_aclaración,aclaracion_style2))
    
    # Add page template with the two-column layout
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
    context=f"You are going to contribute to a player report about a player in {current_league} league in Spain. Be thorough and impartial, providing clear observations and evidence to support your analysis. Highlight key performance indicators and suggest potential for development. If the value is smaller than the average it means he is worse. If the value is better than the average it means he is better. If you know his place of birth, add it."
    create_chat_log(context)
    player_arrayof1,average_arrayof1,player_name,player_pos,params_arrayof1=extract_arrays_wyscout2(wyscout_file,parameters_file,player_id_analizing,"param_of1",min_minutes)
    player_arrayof2,average_arrayof2,player_name,player_pos,params_arrayof2=extract_arrays_wyscout2(wyscout_file,parameters_file,player_id_analizing,"param_of2",min_minutes)
    player_arrayof = pd.concat([player_arrayof1, player_arrayof2])
    
    #print(type(params_arrayof1))
    average_arrayof = pd.concat([average_arrayof1, average_arrayof2])
    #params_arrayof = pd.concat([params_arrayof1, params_arrayof2])
    
    #average_arrayof=average_arrayof1+average_arrayof2
    params_arrayof=params_arrayof1+params_arrayof2
    
    dict_english={"delantero":"forward","ofmid":"ofensive midfielder","extremo":"winger","defmid":"defensive midfielder","lateral":"fullback","defensa":"center back","portero":"goalkeeper"}
    
    chat_comment = f"Write a paragraph highlighting the ofensive strengths and weaknesses of the player {player_name} in the position {dict_english[player_pos]}. The parameters we are evaluating are; {params_arrayof}. The player's values are: {player_arrayof}. The average values are: {average_arrayof}"
    chat(chat_comment, context, action="translate", language="Spanish",chat_log=None)
    
    with open("response.txt","r",encoding="utf-8") as file:
        text_ofensive=file.read()
    paragraphs=text_ofensive.split("\n\n")
    
    
    #we keep all paragraphs expect first
    of_text = "<br/><br/>".join(paragraphs[2:]) if len(paragraphs) > 1 else ""
    #print(of_text)
    parrafo_oftxt=Paragraph(of_text,glossary_style2)
    main_story23.append(Paragraph("Resumen Ofensivo",title_style))
    main_story23.append(parrafo_oftxt)
    with open("response.txt", "w", encoding="utf-8") as file:
        file.write("")
    
    
    player_arraydef,average_arraydef,player_name,player_pos,params_arraydef=extract_arrays_wyscout2(wyscout_file,parameters_file,player_id_analizing,"param_def",min_minutes)
    
    chat_comment = f"Write a paragraph highlighting the defensive strengths and weaknesses of the player {player_name} in the position {dict_english[player_pos]}. The parameters we are evaluating are; {params_arraydef}. The player's values are: {player_arraydef}. The average values are: {average_arraydef}"
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
        

    #print("linea 1204")
   
    
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
            # #### INDICE
            # index_story=[]
            # styles = getSampleStyleSheet()
            # toc = TableOfContents()
            # toc.levelStyles = [
            #     ParagraphStyle(fontName='Helvetica', fontSize=14, name='TOCHeading1', leftIndent=20, firstLineIndent=-20, spaceBefore=5, leading=16),
            #     ]
            # index_story.append(Paragraph('Índice', styles['Heading1']))
            # index_story.append(toc)
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
            # #### INDICE
            # index_story=[]
            # styles = getSampleStyleSheet()
            # toc = TableOfContents()
            # toc.levelStyles = [
            #     ParagraphStyle(fontName='Helvetica', fontSize=14, name='TOCHeading1', leftIndent=20, firstLineIndent=-20, spaceBefore=5, leading=16),
            #     ]
            # index_story.append(Paragraph('Índice', styles['Heading1']))
            # index_story.append(toc)
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
        
    #print("peta el build?")
    doc.build(
        full_Story
    )
    # destination_folder="/Users/julieta/Dropbox/Informes_copy"
    # shutil.copy(output_filename, destination_folder)
    images_to_delete = [output_path1, output_path2, output_path3] + paths_graficas_2D
    
    for image_file in images_to_delete:
        try:
            os.remove(image_file)
        except Exception as e:
            print(f"Error deleting {image_file}: {e}")
            
    print("PDF generated successfully!")
    
#create_report(101,"LigaF_wyscout_2025.xlsx","parameters.xlsx",1,100,color_selection="#FFFFFF",summary=0,current_league="Liga F",season="2025/26")


if __name__ == "__main__":
    #print("ENTRAMOS BIEN")
    parser = argparse.ArgumentParser()
    parser.add_argument("--player_id_analizing", type=int, required=True)
    parser.add_argument("--wyscout_file", type=str, required=True)
    parser.add_argument("--parameters_file", type=str, required=True)
    parser.add_argument("--position_number", type=int, default=1)
    parser.add_argument("--min_minutes", type=int, default=500)
    parser.add_argument("--color_selection", type=str, default="#FFFFFF")
    parser.add_argument("--summary", type=int, default=0)
    parser.add_argument("--current_league", type=str, default="Liga F")
    parser.add_argument("--season", type=str, default="2024/25")

    args = parser.parse_args()
    create_report(
        player_id_analizing=args.player_id_analizing,
        wyscout_file=args.wyscout_file,
        parameters_file=args.parameters_file,
        position_number=args.position_number,
        min_minutes=args.min_minutes,
        color_selection=args.color_selection,
        summary=args.summary,
        current_league=args.current_league,
        season=args.season
    )