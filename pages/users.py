import streamlit as st
from utils import login
from utils.styles import inject_global_css, page_header

st.set_page_config(
    page_title="Usuarios | Liga F Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_global_css()
login.generarLogin()

if "usuario" not in st.session_state:
    st.stop()

page_header("Gestión de Usuarios", "Administración de cuentas de la plataforma")
