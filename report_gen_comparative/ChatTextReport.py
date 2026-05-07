#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 23 16:35:28 2025

@author: julieta
"""

from ArraysChat import extract_arrays_wyscout2
#param entry sería param_of1, param_of2 y param_def

import subprocess
import importlib
import ensurepip
import logging

def truncate(text, max_length):
    return text if len(text) <= max_length else text[:max_length - 3] + "..."


def install_dependency(package):
    try:
        importlib.import_module(package)
    except ImportError:
        subprocess.check_call(['pip', 'install', package])

def install_pip():
    try:
        importlib.import_module('pip')
    except ImportError:
        print("pip not found. Installing pip...")
        ensurepip.bootstrap()
        subprocess.check_call(['pip', 'install', '--upgrade', 'pip'])

# List of required packages
dependencies = [ 'dotenv', 'pandas']

# Install pip if not present
#install_pip()

# Install dependencies
for dependency in dependencies:
    install_dependency(dependency)

print("Dependencies installed successfully.")

import openai
import os
from dotenv import load_dotenv
import json
import pandas as pd

max_length = 2000

# Load environment variables from a .env file
load_dotenv()
API_KEY = os.environ.get('OPENAI_KEY')


# Raise an error if API_KEY is not set in the environment variables
if API_KEY is None:
    raise ValueError("API_KEY is not set. Set it in the environment variables.")

# Set the OpenAI API key
openai.api_key = API_KEY

# Define constants
MODEL_NAME = 'gpt-4o-mini'  # OpenAI model to use
#gpt-4o-mini
#o1-preview
RESPONSE_FILE = "response.txt"  # File to log responses
CHAT_LOG_FILE = 'chat_log.json'  # File to store chat history
EXCEL_FILE = 'chat_errors.xlsx'  # File to store chat errors

# Function to load existing error data from an Excel file
def load_existing_data():
    if os.path.isfile(EXCEL_FILE):
        # If the Excel file exists, load the data
        return pd.read_excel(EXCEL_FILE)
    else:
        # If the file doesn't exist, return an empty DataFrame
        return pd.DataFrame(columns=['question','log_error'])

# Function to write a DataFrame to an Excel file
def write_to_excel(dataframe):
    dataframe.to_excel(EXCEL_FILE, index=False, header=True)

# Function to append content to a text file
def write_to_file(file_path, content):
    with open(file_path, "a", encoding='utf-8', errors='replace') as text_file:
        text_file.write(content + '\n')

# Function to write data to a JSON file
def write_to_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8', errors='replace') as file:
        json.dump(data, file)

# Function to log errors into an Excel file
def log_error(exception, question):
    print(f"Error: {exception}")
    # Create a DataFrame with the error and question
    new_data = pd.DataFrame({'question': [question], 'log_error': [exception]})
    dataframe = load_existing_data()  # Load existing data
    dataframe = pd.concat([dataframe, new_data], ignore_index=True)  # Append new error
    if not dataframe.empty:
        write_to_excel(dataframe)  # Save the updated data to Excel
    return f"{question}"

# Function to generate a response using OpenAI API
def generate_api_response(messages, question):
    try:
        # Generate response using the OpenAI model
        response = openai.ChatCompletion.create(model=MODEL_NAME, n=1, messages=messages)
        return response.choices[0]['message']['content']
    except Exception as e:
        # If an error occurs, log it
        return log_error(e, question)

# Function to create a system message for the chatbot
def create_system_message(content):
    #return {"role": "system", "content": content}
    return {"role": "user", "content": content}

# Function to create a user message for the chatbot
def create_user_message(action, question):
    return {"role": "user", "content": f"{action}: {question}"}

# Function to manage the chat log and prepare it for a new interaction
def handle_chat_log(chat_log, context, action, question, response_file):
    if chat_log is not None and len(chat_log) >= 10:
        # If there is a long chat log, summarize it
        with open(response_file, "r", encoding='utf-8', errors='replace') as text_file:
            long_string = ', '.join(text_file.readlines())
        chat_log = [
            create_system_message("Now, your task is to summarize this text and extract the main information from it."),
            create_user_message('Summarize the following text in a paragraph. Make sure to extract the main events and all the information:',f' {long_string}')
        ]

    elif chat_log is None and action != 'reply':
        # If chat log is empty, start with a new context
        chat_log = [create_system_message(context)]
        write_to_file(response_file, context + '\n')

    elif chat_log is None and action == 'reply':
        # If chat log is empty and action is 'reply', load the chat log from the file
        with open(CHAT_LOG_FILE, 'r', encoding='utf-8', errors='replace') as file:
            chat_log = json.load(file)

    return chat_log


# Main chat function to interact with the chatbot
def chat(question, context, action, language=None, chat_log=None):
    #
    chat_log = handle_chat_log(chat_log, context, action, question, RESPONSE_FILE)
    
    # Define action-specific messages
    if action == 'rewrite':
        action_message =f'Rewrite the following sentence. Do not use more than {os.getenv("MAX_WORDS")} words. Do not use "". Convert yards to meters if yards are present in the message. Do not add hyperlinks if there are none. Preserve any hyperlinks as they are.'
    elif action == 'player ofensive':
        action_message=f"Write a brief commentary on the player, highlighting their main ofensive strengths and weaknesses. You will receive one dataframe with the player’s statistics and another with the average statistics for their position. Do not use more than 200 words."
    elif action == 'player defensive':
        action_message=f"Write a brief commentary on the player, highlighting their main defensive strengths and weaknesses. You will receive one dataframe with the player’s statistics and another with the average statistics for their position. Do not use more than 200 words."
    elif action == 'translate': 
        #action_message = f'Rewrite and Translate this football-context message to {language} in a coherent and detailed way. Do not use "". Use football technical language. Imagine you are a football scout agent. Create a DAFO. Do not use more than 200 words.'
        #action_message=f"Rewrite and translate this football-context message into {language}, using coherent, detailed, and professional football technical language and include the values provided. Act as an experienced football scout agent. Provide ONLY a DAFO (SWOT) analysis of the player/team/idea described. Do not include any additional commentary or quotes. Limit the response to 200 words. For bold letter weight use <b> and </b> instead of ** **."
        action_message = (
            f"Limit the response to 200 words. Rewrite and translate this football-context message into {language}, using coherent, detailed, and professional football technical language, incorporating the values provided. "
            f"Act as an experienced football scout agent. Provide ONLY a comparative analysis between the two players described, highlighting key differences and similarities in their strengths, weaknesses, opportunities, and threats. "
            f"Also write a small paragraph comparing both highlighting their differences and similarities."
            f"Do not include any additional commentary or quotes. Limit the response to 200 words. For bold letter weight use <b> and </b> instead of ** **."
            )
    # Create user message and append it to chat log
    user_message = create_user_message(action_message, question)
    if isinstance(chat_log, str):
        chat_log = [chat_log]  # Convertir a lista si es un string
    
    chat_log.append(user_message)
    #print("##########")
    #print(f"ChatGPT 172: chat_log = {chat_log}")
    #print("-----------")
    # Generate response from the assistant
    assistant_reply = generate_api_response(chat_log,question)
    #print(f"ChatGPT 177: assistant_reply = {assistant_reply}")
    #print("##########")

    print("chatGPT 181: generate_api_response:")

    if assistant_reply:
        if len(assistant_reply) > max_length:
            print("chatGPT 185: Texto en el embed truncado debido a límite de caracteres.")
            logging.warning("chatGPT 186: Texto en el embed truncado debido a límite de caracteres.")

            if assistant_reply is not None:
                assistant_reply = truncate(assistant_reply, max_length)
                print(f"chatGPT 194: truncate: {assistant_reply}")
    else:
        print("Error: assistant_reply no tiene un valor asignado")

    # Log assistant's response
    assistant_message = {"role": "assistant", "content": assistant_reply}
    chat_log.append(assistant_message)
    
    # Save the response and chat log
    write_to_file(RESPONSE_FILE, assistant_reply)
    write_to_json(CHAT_LOG_FILE, chat_log)

    return assistant_reply, chat_log


def create_chat_log(context):
    chat_log = [{"role": "system", "content": context}]
    with open('chat_log.json', 'w', encoding='utf-8', errors='replace') as file:
        json.dump(chat_log, file)
    
# context="You are going to contribute to a player report about a player in 2º RFEF league in Spain. Be thorough and impartial, providing clear observations and evidence to support your analysis. Highlight key performance indicators and suggest potential for development. If the value is smaller than the average it means he is worse. If the value is better than the average it means he is better. If you know his place of birth, add it."
# create_chat_log(context)

# player_array,average_array,player_name,player_pos,params_array=extract_arrays_wyscout("/Users/julieta/Desktop/2RFEF_wyscout.xlsx","/Users/julieta/Desktop/parameters.xlsx",4,"param_of1",500)
# positions=["portero","defensa","defmid","","lateral","",""]
# dict_english={"delantero":"forward","ofmid":"ofensive midfielder","extremo":"winger","defmid":"defensive midfielder","lateral":"fullback","defensa":"center back","portero":"goalkeeper"}
# create_chat_log(context)
# chat_comment = f"Write a paragraph highlighting the strengths and weaknesses of the player {player_name} in the position {dict_english[player_pos]}. The parameters we are evaluating are; {params_array}. The player's values are: {player_array}. The average values are: {average_array}"
# chat(chat_comment, context, action="translate", language="Spanish",chat_log=None)

# with open("response.txt","r",encoding="utf-8") as file:
#     text_ofensive=file.read()
# paragraphs=text_ofensive.split("\n\n")
# #we keep all paragraphs expect first
# of_text = "\n\n".join(paragraphs[1:]) if len(paragraphs) > 1 else ""

# with open("response.txt", "w", encoding="utf-8") as file:
#     file.write("")