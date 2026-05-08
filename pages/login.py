#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 21 10:11:15 2025

@author: julieta
"""
import streamlit as st
from utils import login
from utils.styles import inject_login_css

st.set_page_config(
    page_title="Login | Liga F Analytics",
    page_icon=":material/sports_and_outdoors:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "usuario" in st.session_state:
    st.switch_page("app.py")

inject_login_css()



col1, col2,col3,col5 = st.columns([2, 1.5,1.5, 2])
with col2:
    st.image("assets/Logos/Redes_Logo.png")
with col3:
    st.image("assets/Logos/URJC_Logo.png")
    
    #st.text("¡Bienvenido!")

col1, col2, col3 = st.columns([2, 1.5, 2])
with col2:
   users_dict = st.secrets["login"]["users"]
   roles_dict = st.secrets["login"]["roles"]
   with st.form('frmLogin'):
        parUsuario = st.text_input('Usuario')
        parPassword = st.text_input('Password', type='password')
        btnLogin = st.form_submit_button('Ingresar', type='primary')
        if btnLogin:
            if parUsuario in users_dict and parPassword == users_dict[parUsuario]:
                st.session_state['usuario'] = parUsuario
                
                # 2. GUARDAMOS EL ROL (Si no existe, por defecto le damos 'admin')
                st.session_state['rol'] = roles_dict.get(parUsuario, "admin")
                
                st.query_params.update({'user': parUsuario})  # persistencia en URL
                st.success("¡Login exitoso!")
                st.switch_page("app.py")
            else:
                st.error("Usuario o clave inválidos", icon=":material/gpp_maybe:")
