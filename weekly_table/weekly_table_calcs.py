#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 19 13:11:31 2025

@author: julieta
"""

import pandas as pd
import os
matches_relations=pd.read_excel("/Users/julieta/Desktop/APP_Generic_Femeni_2/datos_opta/matches_relations_2025.xlsx")

team_ids_list=[12034,13319,15762,9121,16881,13323,13320,
               14503,11212,13326,8650,13324,23225,18644,16928, 18643]

team_names_list=['Athletic Club Femenino','Levante Femenino','Deportivo de La Coruña Femenino',
 'Barcelona Femenino','Eibar Femenino','Espanyol Femenino','Madrid CF Femenino',
 'DUX Logroño Femenino','Atlético de Madrid Femenino','Sevilla Femenino','Granada Femenino',
 'Real Sociedad Femenino','Tenerife Femenino','Alhama Femenino','Real Madrid Femenino','Badalona Women']

team_try="Barcelona Femenino"

team_matches=matches_relations[(matches_relations["team1_name"]==team_try) | (matches_relations["team2_name"]==team_try)]

team_matches = team_matches.dropna(subset=['team1_score',"team2_score"])


# for i,row in team_matches.iterrows():
#     if row["team1_name"]==team_try:
#         if row["team1_score"]>row["team2_score"]:
#             team_scores.append(3)
#         elif row["team1_score"]<row["team2_score"]:
#             team_scores.append(0)
#         elif row["team1_score"]==row["team2_score"]:
#             team_scores.append(1)
#     elif row["team2_name"]==team_try:
#         if row["team1_score"]>row["team2_score"]:
#             team_scores.append(0)
#         elif row["team1_score"]<row["team2_score"]:
#             team_scores.append(3)
#         elif row["team1_score"]==row["team2_score"]:
#             team_scores.append(1)
#     jornada=jornada+1
            
# team_score=sum(team_scores)
#####
team_results=[]
team_difs=[]
for team_name in team_names_list:
    
    team_matches=matches_relations[(matches_relations["team1_name"]==team_name) | (matches_relations["team2_name"]==team_name)]

    team_matches = team_matches.dropna(subset=['team1_score',"team2_score"])

    team_scores=[]
    team_diffs=0
    jornada=0
    team_score = 0
    for _, row in team_matches.iterrows():
        if row["team1_name"] == team_name:
            if row["team1_score"] > row["team2_score"]:
               team_score += 3
            elif row["team1_score"] < row["team2_score"]:
               team_score += 0
            else:
               team_score += 1
            team_diffs+=(row["team1_score"]-row["team2_score"])
        elif row["team2_name"] == team_name:
            if row["team1_score"] > row["team2_score"]:
               team_score += 0
            elif row["team1_score"] < row["team2_score"]:
               team_score += 3
            else:
               team_score += 1
            team_diffs+=(row["team2_score"]-row["team1_score"])
        

    team_results.append({"team_name": team_name, "team_score": team_score,"goal_diff":team_diffs})
df_team_scores = pd.DataFrame(team_results)
df_team_scores = df_team_scores.sort_values(by=["team_score", "goal_diff"], ascending=[False, False])

BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 
BASE_DIR="/Users/julieta/Desktop/APP_Generic_Femeni_2"

team_dict = {name: f"{BASE_DIR}/assets/logos_table/{name}.png" for name in df_team_scores["team_name"]}
df_team_scores["logos_path"]=df_team_scores["team_name"].map(team_dict)

df_team_scores.to_excel("weekly_table.xlsx",index=False)
