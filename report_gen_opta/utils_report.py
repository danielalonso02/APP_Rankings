#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 16 10:50:56 2025

@author: julieta
"""
import pandas as pd
import os 
import xml.etree.ElementTree as ET
#folder_path="/Users/julieta/Desktop/APP_Generic_Femeni/data_femeni/raw/f70"






def parse_allf70(folder_path):
    
    def parse_player(player, team_side, team_ref):
        data = {
            "PlayerRef": player.attrib.get("PlayerRef"),
            "ShirtNumber": int(player.attrib.get("ShirtNumber")),
            "Position": player.attrib.get("Position"),
            "Status": player.attrib.get("Status"),
            "TeamSide": team_side,
            "TeamRef": team_ref
        }
        for stat in player.findall("Stat"):
            try:
                data[stat.attrib["Type"]] = float(stat.text)
            except:
                data[stat.attrib["Type"]] = stat.text
        return data

    all_players = []

    for filename in os.listdir(folder_path):
        if not filename.endswith('.xml'):
            continue
        fullname = os.path.join(folder_path, filename)
        
        tree = ET.parse(fullname)
        root = tree.getroot()
       
        for team in root.findall(".//TeamData"):
            team_side = team.attrib.get("Side")
            team_ref = team.attrib.get("TeamRef")
            for player in team.findall(".//MatchPlayer"):
                all_players.append(parse_player(player, team_side, team_ref))


    df_players = pd.DataFrame(all_players)
    non_numeric_cols = [c for c in df_players.select_dtypes(exclude='number').columns if c != 'PlayerRef']

    # Group numeric columns and sum
    numeric_cols = df_players.select_dtypes(include='number').columns
    df_grouped = df_players.groupby('PlayerRef')[numeric_cols].sum().reset_index()

    # Group non-numeric columns and take the first value
    df_non_numeric = df_players.groupby('PlayerRef')[non_numeric_cols].first().reset_index()

    # Merge numeric and non-numeric
    df_players_summary = pd.merge(df_grouped, df_non_numeric, on='PlayerRef')
    
    df_players_summary["PlayerRef"] = df_players_summary["PlayerRef"].str.lstrip('p')
    df_players_summary["PlayerRef"] = df_players_summary["PlayerRef"].astype(int)

    
    return df_players_summary

#df_players_summary=parse_allf70(folder_path)
