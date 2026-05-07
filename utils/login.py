import streamlit as st
import pandas as pd

# Validación simple de usuario y clave con un archivo csv
def validarUsuario(usuario, clave):
    dfusuarios = pd.read_csv('usuarios.csv')
    return any((dfusuarios['usuario'] == usuario) & (dfusuarios['clave'] == clave))

def generarMenu(usuario):
    # 1. Recuperar el rol directamente de secrets para que sea persistente al recargar
    # Buscamos en el diccionario 'roles' de tu secrets.toml
    rol = st.secrets["login"]["roles"].get(usuario, "scout") 
    st.session_state['rol'] = rol
    
    with st.sidebar:
        # dfusuarios = pd.read_csv('usuarios.csv')
        # dfUsuario = dfusuarios[(dfusuarios['usuario'] == usuario)]
        nombre = st.secrets["login"]["names"].get(usuario, usuario)
        st.write(f"Hola **:blue-background[{nombre}]** ")
        
        st.page_link("app.py", label="Inicio", icon=":material/home:")
        # st.subheader("Clasificación")
        # st.page_link("pages/table_page.py", label="Clasificación Liga F", icon=":material/trending_up:")
        
        st.subheader("Rankings :material/star:")
        st.page_link("pages/rankings.py", label="Rankings de jugadoras", icon=":material/star:")
        
        st.subheader("Informes :material/contacts:")
        st.page_link("pages/dashboard.py", label="Generador de informes individuales", icon=":material/contacts:")
        st.page_link("pages/dashboard_comparative.py", label="Generador de informes comparativos", icon=":material/contacts:")
        

        if st.button("Salir", type="tertiary", icon=":material/logout:"):
            cerrarSesion()

# 🔹 Función para cerrar sesión y limpiar query_params
def cerrarSesion():
    if 'usuario' in st.session_state:
        del st.session_state['usuario']
    
    st.query_params.clear()  # 🔹 Limpia la URL
    st.session_state.clear()
    st.switch_page("pages/login.py")
    st.rerun()

def generarLogin():
    # 🔄 Restaurar sesión desde la URL si existe
    usuario_actual = st.query_params.get("user")

    if usuario_actual and "usuario" not in st.session_state:
        st.session_state['usuario'] = usuario_actual
        
    if 'usuario' in st.session_state:
        st.query_params.update({"user": st.session_state["usuario"]})
        generarMenu(st.session_state['usuario'])
    else:
        st.switch_page("pages/login.py")
        