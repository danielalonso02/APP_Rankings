#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 21 10:53:30 2025

@author: julieta
"""

# futbot_api.py (microservicio con FastAPI)
from fastapi import FastAPI, Request
from pydantic import BaseModel
import subprocess
import os
import sys
from report_gen.Report_2RFEF_FINAL import create_report
import json

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 
RUTA_SCRIPT_PIZZA = os.path.join(BASE_DIR,"report_gen/PizzaWyscout.py")
DIRECTORIO_BASE = os.path.dirname(RUTA_SCRIPT_PIZZA)

class ReportRequest(BaseModel):
    player_id: int 
    wyscout_file: str
    parameters_file: str 
    position_number: int = 1
    min_minutes: int =500
    color_selection: str = "#FFFFFF"
    summary: int = 0
    current_league: str = "2º RFEF"
    season: str = "2024/25"



@app.post("/start")
async def generate_report(req: ReportRequest):
    try:
        args = [
            sys.executable, RUTA_SCRIPT_PIZZA,
            "--player_id_analizing", int(req.player_id),
            "--wyscout_file", req.wyscout_file,
            "--parameters_file", req.parameters_file,
            "--position_number", int(req.position_number),
            "--min_minutes", int(req.min_minutes),
            "--color_selection", req.color_selection,
            "--current_league", str(req.current_league),
            "--season", str(req.season)
        ]

        pizza_process = subprocess.Popen(
            args,
            cwd=DIRECTORIO_BASE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return {"status": "Report started", "pid": pizza_process.pid}
    except Exception as e:
        return {"error": str(e)}
    
