import streamlit as st
from utils import login
from utils import util
import subprocess
import os
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import sys
import json
import glob
from pathlib import Path
from utils.constants import init_report_session_state
from utils.styles import inject_report_css, page_header, page_footer, loader_display, log_viewer
import pandas as pd


st.set_page_config(
    page_title="Informe Individual | Liga F Analytics",
    page_icon=":material/sports_and_outdoors:",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_report_css()
login.generarLogin()

if "usuario" not in st.session_state:
    st.stop()

page_header("Informe Individual", "Generación de informes de rendimiento de jugadoras")

init_report_session_state()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ruta_script = os.path.join(BASE_DIR, "report_gen_wyscout", "Report_LIGAF_FINAL.py")
directorio_logs = os.path.join(BASE_DIR, "logs")
ruta_parameters = os.path.join(BASE_DIR, "report_gen_wyscout", "parameters.xlsx")
ruta_excel2 = os.path.join(BASE_DIR)
directorio_base = os.path.dirname(ruta_script)
parameters_route_xlsx = os.path.join(BASE_DIR, "report_gen_wyscout", "parameters.xlsx")
folder_path_delete = os.path.join(BASE_DIR, "report_gen_wyscout", "image_individual")
RUTA_FAVORITOS = os.path.join(BASE_DIR, "config_pesos_favoritos.json")
RUTA_FAVORITOS_FIS = os.path.join(BASE_DIR, "config_pesos_fisicos.json")

os.makedirs(directorio_logs, exist_ok=True)

# ── Uploader de datos de jugadoras ──
if "df_dashboard" not in st.session_state:
    st.session_state["df_dashboard"] = None
    st.session_state["df_dashboard_nombre"] = None
    st.session_state["df_dashboard_bytes"] = None  # guardamos bytes para pasarlos al script

# ── Estado del logo personalizado ──
if "logo_file_path" not in st.session_state:
    st.session_state["logo_file_path"] = None

if st.session_state["df_dashboard"] is not None:
    col_info, col_cambiar = st.columns([3, 1])
    with col_info:
        st.success(
            f"✅ Datos cargados: **{st.session_state['df_dashboard_nombre']}** "
            f"({len(st.session_state['df_dashboard']):,} jugadoras · {len(st.session_state['df_dashboard'].columns)} columnas)"
        )
    with col_cambiar:
        if st.button("🔄 Cambiar archivo", use_container_width=True, key="cambiar_dashboard"):
            st.session_state["df_dashboard"] = None
            st.session_state["df_dashboard_nombre"] = None
            st.session_state["df_dashboard_bytes"] = None
            st.rerun()
    df_jugadoras = st.session_state["df_dashboard"]
    ruta_archivo_temp = st.session_state.get("df_dashboard_ruta_temp", None)
else:
    st.info("ℹ️ Sube el archivo Excel con los datos de jugadoras para comenzar.")
    uploaded_dash = st.file_uploader(
        "📂 Archivo de datos de jugadoras (.xlsx)",
        type=["xlsx"],
        key="uploader_dashboard"
    )
    if uploaded_dash is not None:
        try:
            import io as _io_dash, tempfile as _tmp_dash
            file_bytes = uploaded_dash.read()
            df_tmp = pd.read_excel(_io_dash.BytesIO(file_bytes))
            # Guardar el archivo en un temporal para pasarlo al script externo
            tmp_file = _tmp_dash.NamedTemporaryFile(suffix=".xlsx", delete=False)
            tmp_file.write(file_bytes)
            tmp_file.close()
            st.session_state["df_dashboard"] = df_tmp
            st.session_state["df_dashboard_nombre"] = uploaded_dash.name
            st.session_state["df_dashboard_bytes"] = file_bytes
            st.session_state["df_dashboard_ruta_temp"] = tmp_file.name
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error al leer el archivo: {e}")
    st.stop()

# Ruta del archivo temporal (para pasar al script externo de generación)
ruta_archivo_temp = st.session_state.get("df_dashboard_ruta_temp", ruta_excel2)

#@st.fragment
def filtros_fragment():

    # Ajustes básicos
    st.markdown(":material/settings: Ajustes básicos")
    
    col1, col2, col3 = st.columns([2, 1.5, 1])

    with col1:
        player = None
        player_id = None
        if df_jugadoras is not None:
            lista_jugadores = util.obtener_lista_jugadores(df_jugadoras, "Jugadores")
            player = st.selectbox("Jugadora:", lista_jugadores, placeholder="Escribe el nombre del jugador...")
            player_id = util.obtener_id_jugador_df(df_jugadoras, player_name=player)
    with col2:
        min_minutes = st.text_input("Mínimo de Minutos:", value=500, placeholder="Mínimo minutos", key="min_minutes")
    with col3:
        summary = util.select_summary()

    # ── Logo personalizado ──
    st.markdown(":material/image: Logo del informe")
    col_logo, col_logo_preview = st.columns([3, 1])
    with col_logo:
        uploaded_logo = st.file_uploader(
            "📷 OPCIONAL — Subir logo personalizado — PNG o JPG",
            type=["png", "jpg", "jpeg"],
            key="uploader_logo"
        )
        if uploaded_logo is not None:
            import tempfile as _tmp_logo
            ext = uploaded_logo.name.rsplit(".", 1)[-1]
            tmp_logo = _tmp_logo.NamedTemporaryFile(suffix=f".{ext}", delete=False)
            tmp_logo.write(uploaded_logo.read())
            tmp_logo.close()
            st.session_state["logo_file_path"] = tmp_logo.name
        elif st.session_state.get("logo_file_path"):
            st.caption(f"✅ Logo cargado: `{os.path.basename(st.session_state['logo_file_path'])}`")
        
    with col_logo_preview:
        if uploaded_logo is not None:
            st.image(uploaded_logo, width=80, caption="Vista previa")
        elif st.session_state.get("logo_file_path") and os.path.exists(st.session_state["logo_file_path"]):
            st.image(st.session_state["logo_file_path"], width=80, caption="Logo actual")

    # ── Selector de configuración de pesos ──
    st.markdown(":material/tune: Configuración de pesos")
    pesos_favorito_sel = None
    if os.path.exists(RUTA_FAVORITOS):
        with open(RUTA_FAVORITOS, "r", encoding="utf-8") as _f:
            import json as _json
            _favs = _json.load(_f)
        if _favs:
            _opciones = ["Sin favorito (pesos por defecto)"] + list(_favs.keys())
            _sel = st.selectbox("Configuración de pesos guardada:", _opciones, key="pesos_sel")
            if _sel != "Sin favorito (pesos por defecto)":
                pesos_favorito_sel = _sel
        else:
            st.caption("No hay configuraciones guardadas en Rankings.")
    else:
        st.caption("No se ha encontrado ningún archivo de configuraciones de pesos.")

    # ── Selector de configuración de pesos físicos ──
    pesos_fisicos_sel = None
    if os.path.exists(RUTA_FAVORITOS_FIS):
        with open(RUTA_FAVORITOS_FIS, "r", encoding="utf-8") as _f2:
            _favs_fis = _json.load(_f2)
        if _favs_fis:
            _opciones_fis = ["Sin favorito (pesos por defecto)"] + list(_favs_fis.keys())
            _sel_fis = st.selectbox("Configuración de pesos físicos guardada:", _opciones_fis, key="pesos_fisicos_sel")
            if _sel_fis != "Sin favorito (pesos por defecto)":
                pesos_fisicos_sel = _sel_fis
        else:
            st.caption("No hay configuraciones físicas guardadas en Rankings Físicos.")
    else:
        st.caption("No se ha encontrado ningún archivo de configuraciones de pesos físicos.")

    result = {
        "ruta_script": ruta_script,
        "player_id": player_id,
        "min_minutes": min_minutes,
        "summary": summary,
        "pesos_favorito_sel": pesos_favorito_sel,
        "pesos_fisicos_sel": pesos_fisicos_sel,
        "wyscout_file_temp": ruta_archivo_temp,
        "logo_file_path": st.session_state.get("logo_file_path"),
    }

    # ── FIX: guardar siempre los filtros actuales en session_state ──
    st.session_state.filtros_guardados = result

    return result


filtros = filtros_fragment()

st.dataframe(df_jugadoras)


# Botones
col1, col2, col3 = st.columns([1.33, 1.33, 1.33])
with col2:
    ejecutar = st.button("Generar Report", type="secondary", width='stretch', disabled=st.session_state.proceso is not None)
st.divider()

if ejecutar:
    # ── FIX: usar los filtros guardados en session_state, no los de la
    # variable local `filtros`, que puede haber sido recalculada durante
    # el rerun del botón con valores distintos a los que el usuario veía.
    filtros_ejecucion = st.session_state.get("filtros_guardados", filtros)

    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_log = os.path.join(directorio_logs, f"report_log_{ts}.txt")

        ruta_script_abs = Path(str(filtros_ejecucion["ruta_script"])).resolve()
        base_cwd        = Path(str(directorio_base)).resolve()
        params_xlsx     = Path(str(parameters_route_xlsx)).resolve()

        assert ruta_script_abs.is_file(), f"Script not found: {ruta_script_abs}"
        assert base_cwd.exists(),         f"CWD not found: {base_cwd}"

        # Abrimos el log en modo line-buffered para ver el output en tiempo real
        with open(ruta_log, "w", buffering=1) as log_file:
            cmd = [
                sys.executable, "-u", str(ruta_script_abs),
                "--player_id",      str(filtros_ejecucion["player_id"]),
                "--wyscout_file",   str(filtros_ejecucion["wyscout_file_temp"]),
                "--parameters_file", str(params_xlsx),
                "--position_number", "1",
                "--min_minutes",    str(filtros_ejecucion["min_minutes"]),
                "--color_selection", filtros_ejecucion.get("color_selection", "#FFFFFF"),
                "--summary",        str(filtros_ejecucion.get("summary", 0)),
            ]
            # Añadir logo personalizado si se ha subido
            _logo_path = filtros_ejecucion.get("logo_file_path")
            if _logo_path and os.path.exists(_logo_path):
                cmd += ["--logo_file", _logo_path]

            # Añadir pesos tácticos si hay favorito seleccionado
            import json as _json, tempfile as _tempfile
            _pesos_sel = filtros_ejecucion.get("pesos_favorito_sel")
            if _pesos_sel:
                if os.path.exists(RUTA_FAVORITOS):
                    with open(RUTA_FAVORITOS, "r", encoding="utf-8") as _f:
                        _all_favs = _json.load(_f)
                    if _pesos_sel in _all_favs:
                        _tmp = _tempfile.NamedTemporaryFile(
                            mode="w", suffix=".json", delete=False, encoding="utf-8"
                        )
                        _json.dump(_all_favs[_pesos_sel], _tmp, ensure_ascii=False)
                        _tmp.close()
                        cmd += ["--pesos_file", _tmp.name]
            # Añadir pesos físicos si hay favorito físico seleccionado
            _pesos_fis_sel = filtros_ejecucion.get("pesos_fisicos_sel")
            if _pesos_fis_sel:
                if os.path.exists(RUTA_FAVORITOS_FIS):
                    with open(RUTA_FAVORITOS_FIS, "r", encoding="utf-8") as _f2:
                        _all_favs_fis = _json.load(_f2)
                    if _pesos_fis_sel in _all_favs_fis:
                        _tmp_fis = _tempfile.NamedTemporaryFile(
                            mode="w", suffix=".json", delete=False, encoding="utf-8"
                        )
                        _json.dump(_all_favs_fis[_pesos_fis_sel], _tmp_fis, ensure_ascii=False)
                        _tmp_fis.close()
                        cmd += ["--pesos_file_fisico", _tmp_fis.name]

            proc = subprocess.Popen(
                cmd,
                cwd=str(base_cwd),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                env=dict(os.environ, PYTHONUNBUFFERED="1"),
            )

        # Guarda el estado (un solo Popen)
        st.session_state.proceso           = proc
        st.session_state.log_path          = ruta_log
        st.session_state.pid               = proc.pid
        st.session_state.inicio_ejecucion  = time.time()

        # Si el proceso muere al instante, avisa
        time.sleep(1)
        ret = proc.poll()
        if ret is not None:
            st.error(f"El generador terminó inmediatamente (código {ret}). Revisa el log: {ruta_log}")
        else:
            st.success("🚀 El informe se está generando.")

    except Exception as e:
        st.error(f"Error al iniciar generador: {e}")


# ── BOTÓN PARA DESCARGARSE PDF ──

def get_latest_pdf(folder_path):
    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
    if not pdf_files:
        return None
    latest_pdf = max(pdf_files, key=os.path.getmtime)
    return latest_pdf

folder = "report_gen/ReportsGenerados"
latest_pdf_path = get_latest_pdf(folder)

if latest_pdf_path:
    with open(latest_pdf_path, "rb") as f:
        pdf_data = f.read()

    st.download_button(
        label="📄 Descargar el último PDF",
        data=pdf_data,
        file_name=os.path.basename(latest_pdf_path),
        mime="application/pdf",
        on_click="ignore"
    )
else:
    st.write("No se ha encontrado ningún PDF.")


# Mostrar tiempo de ejecución si corresponde
if st.session_state.proceso is not None and st.session_state.inicio_ejecucion:
    tiempo_transcurrido = int(time.time() - st.session_state.inicio_ejecucion)
    horas, rem = divmod(tiempo_transcurrido, 3600)
    minutos, segundos = divmod(rem, 60)
    loader_display(horas, minutos, segundos)


# Auto-refresh solo si el proceso está en ejecución
if st.session_state.proceso is not None:
    st_autorefresh(interval=5000, key="auto_refresh")

# Mostrar contenido del log
if "log_path" in st.session_state and os.path.exists(st.session_state.log_path):
    with open(st.session_state.log_path, "r") as file:
        contenido_log = file.read()

    segundos_desde_actualizacion = int(time.time() - st.session_state.last_log_update)
    st.session_state.last_log_update = time.time()
    log_viewer(contenido_log, segundos_desde_actualizacion)

# Proceso finalizado por su cuenta
if st.session_state.proceso is not None and st.session_state.proceso.poll() is not None:
    with open(st.session_state.log_path, "a") as log_file:
        log_file.write("\n Proceso finalizado.")
    st.session_state.proceso = None
    st.rerun()

st.write("""
**Esta página te permite generar un informe individual de la jugadora que selecciones.**  
Durante el proceso, podrás seguir el progreso en el recuadro de **"log"**.  
La generación del informe puede tardar entre **2 y 3 minutos**, así que te pedimos un poco de paciencia.  
Una vez finalizado, podrás **descargar el informe** fácilmente utilizando el botón de descarga.  

🔹 *Consejo:* evita **actualizar o cerrar la página** mientras se genera el informe para no interrumpir el proceso.  

ℹ️ *Nota:* si la jugadora ha disputado **menos minutos** de los establecidos en el campo **"Mínimo de minutos"**, **no se generará el informe**. En ese caso, aparecerá una notificación indicándolo.
""")
page_footer("Plataforma de Análisis Liga F", "Fuente de datos: Hudl Wyscout")
