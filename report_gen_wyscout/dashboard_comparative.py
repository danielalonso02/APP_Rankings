import streamlit as st
from utils import login
from utils import util
import subprocess
import os
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import sys
import glob
from pathlib import Path
from utils.constants import init_report_session_state
from utils.styles import inject_report_css, page_header, page_footer, loader_display, log_viewer


st.set_page_config(
    page_title="Informe Comparativo | Liga F Analytics",
    page_icon=":material/compare_arrows:",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_report_css()
login.generarLogin()

if "usuario" not in st.session_state:
    st.stop()

page_header("Informe Comparativo", "Comparación de rendimiento entre dos jugadoras")

init_report_session_state()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ruta_script = os.path.join(BASE_DIR, "report_gen_comparative", "Report_LIGAF_Comparative.py")
directorio_logs = os.path.join(BASE_DIR, "logs")
ruta_excel2 = os.path.join(BASE_DIR)
directorio_base = os.path.dirname(ruta_script)
parameters_route_xlsx = os.path.join(BASE_DIR, "report_gen_comparative", "parameters.xlsx")

os.makedirs(directorio_logs, exist_ok=True)


def filtros_fragment():

    # --- Ajustes comunes ---
    st.markdown(":material/settings: Ajustes básicos")
    col_min, col_sum = st.columns([1, 1])
    with col_min:
        min_minutes = st.text_input("Mínimo de Minutos:", value=500, placeholder="Mínimo minutos", key="min_minutes")
    with col_sum:
        summary = util.select_summary()

    st.divider()

    # --- Selección independiente por jugadora ---
    st.markdown(":material/person: Selección de jugadoras")
    col4, col5 = st.columns(2)

    # --- JUGADORA 1 ---
    with col4:
        st.markdown("**Jugadora 1**")
        championship_excel1 = util.select_competicion(key="competicion_1")
        league1 = util.from_excel_to_str(championship_excel1)
        year1 = util.select_season(key="temporada_1")
        season1 = util.convert_season(year1)

        df2_p1 = util.leer_excel_jugadores2(ruta_excel2, championship_excel1, year1)
        lista_jugadoras1 = util.obtener_lista_jugadores(df2_p1, "Jugadores") if df2_p1 is not None else []

        player1 = st.selectbox(
            "Jugadora 1:",
            lista_jugadoras1,
            placeholder="Escribe el nombre...",
            key="player1",
            label_visibility="collapsed"
        )
        wyscout_file1 = f"{championship_excel1}_wyscout_{year1}.xlsx"
        player_id1 = util.obtener_id_jugador(
            f"{ruta_excel2}/{wyscout_file1}",
            player_name=player1
        ) if player1 else None

    # --- JUGADORA 2 ---
    with col5:
        st.markdown("**Jugadora 2**")
        championship_excel2 = util.select_competicion(key="competicion_2")
        league2 = util.from_excel_to_str(championship_excel2)
        year2 = util.select_season(key="temporada_2")
        season2 = util.convert_season(year2)

        df2_p2 = util.leer_excel_jugadores2(ruta_excel2, championship_excel2, year2)
        lista_jugadoras2 = util.obtener_lista_jugadores(df2_p2, "Jugadores") if df2_p2 is not None else []

        player2 = st.selectbox(
            "Jugadora 2:",
            lista_jugadoras2,
            placeholder="Escribe el nombre...",
            key="player2",
            label_visibility="collapsed"
        )
        wyscout_file2 = f"{championship_excel2}_wyscout_{year2}.xlsx"
        player_id2 = util.obtener_id_jugador(
            f"{ruta_excel2}/{wyscout_file2}",
            player_name=player2
        ) if player2 else None

    # Aviso si misma jugadora y mismo archivo
    same_player = (
        player1 == player2
        and wyscout_file1 == wyscout_file2
        and player1 is not None
        and player2 is not None
    )
    if same_player:
        st.warning("⚠️ Has seleccionado la misma jugadora dos veces. Por favor, elige jugadoras distintas.")

    # Liga y temporada combinadas para el título del informe
    if league1 == league2 and season1 == season2:
        league_display = league1
        season_display = season1
    else:
        league_display = f"{league1} / {league2}"
        season_display = f"{season1} / {season2}"

    return {
        "ruta_script": ruta_script,
        "wyscout_file1": wyscout_file1,
        "wyscout_file2": wyscout_file2,
        "championship_excel1": championship_excel1,
        "championship_excel2": championship_excel2,
        "year1": year1,
        "year2": year2,
        "player_id1": player_id1,
        "player_id2": player_id2,
        "player1": player1,
        "player2": player2,
        "min_minutes": min_minutes,
        "summary": summary,
        "season1": season1,
        "season2": season2,
        "league1": league1,
        "league2": league2,
        "league_display": league_display,
        "season_display": season_display,
        "same_player": same_player,
    }


filtros = filtros_fragment()

# Mostrar tabla de la jugadora 1 y jugadora 2 side by side
col_t1, col_t2 = st.columns(2)
with col_t1:
    st.caption(f"Datos: {filtros['championship_excel1']} {filtros['year1']}")
    df_show1 = util.filter_df_show(f"{ruta_excel2}/{filtros['wyscout_file1']}")
    st.dataframe(df_show1, use_container_width=True)
with col_t2:
    st.caption(f"Datos: {filtros['championship_excel2']} {filtros['year2']}")
    df_show2 = util.filter_df_show(f"{ruta_excel2}/{filtros['wyscout_file2']}")
    st.dataframe(df_show2, use_container_width=True)

# Botón generar
col1, col2, col3 = st.columns([1.33, 1.33, 1.33])
with col2:
    ejecutar = st.button(
        "Generar Report Comparativo",
        type="secondary",
        width="stretch",
        disabled=(
            st.session_state.proceso is not None
            or filtros["same_player"]
            or not filtros["player_id1"]
            or not filtros["player_id2"]
        )
    )
st.divider()

if ejecutar:
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_log = os.path.join(directorio_logs, f"report_comparative_log_{ts}.txt")

        ruta_script_path = Path(str(filtros["ruta_script"])).resolve()
        base_cwd = Path(str(directorio_base)).resolve()
        params_xlsx = Path(str(parameters_route_xlsx)).resolve()

        assert ruta_script_path.is_file(), f"Script not found: {ruta_script_path}"
        assert base_cwd.exists(), f"CWD not found: {base_cwd}"

        with open(ruta_log, "w", buffering=1) as log_file:
            cmd = [
                sys.executable, "-u", str(ruta_script_path),
                "--player_id1",    str(filtros["player_id1"]),
                "--player_id2",    str(filtros["player_id2"]),
                "--wyscout_file1", filtros["wyscout_file1"],
                "--wyscout_file2", filtros["wyscout_file2"],
                "--parameters_file", str(params_xlsx),
                "--position_number", "1",
                "--min_minutes",   str(filtros["min_minutes"]),
                "--color_selection", filtros.get("color_selection", "#FFFFFF"),
                "--summary",       str(filtros.get("summary", 0)),
                "--league1",       str(filtros["league1"]),
                "--league2",       str(filtros["league2"]),
                "--season1",       str(filtros["season1"]),
                "--season2",       str(filtros["season2"]),
            ]

            proc = subprocess.Popen(
                cmd,
                cwd=str(base_cwd),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                env=dict(os.environ, PYTHONUNBUFFERED="1"),
            )

        st.session_state.proceso = proc
        st.session_state.log_path = ruta_log
        st.session_state.pid = proc.pid
        st.session_state.inicio_ejecucion = time.time()

        time.sleep(1)
        ret = proc.poll()
        if ret is not None:
            st.error(f"El generador terminó inmediatamente (código {ret}). Revisa el log: {ruta_log}")
        else:
            st.success(f"🚀 Generando informe comparativo: {filtros['player1']} vs {filtros['player2']}")

    except Exception as e:
        st.error(f"Error al iniciar generador: {e}")


# Descarga del último PDF
def get_latest_pdf(folder_path):
    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
    if not pdf_files:
        return None
    return max(pdf_files, key=os.path.getmtime)


folder = "report_gen/ReportsGenerados"
latest_pdf_path = get_latest_pdf(folder)

if latest_pdf_path:
    with open(latest_pdf_path, "rb") as f:
        pdf_data = f.read()
    st.download_button(
        label="📄 Descargar el último PDF comparativo",
        data=pdf_data,
        file_name=os.path.basename(latest_pdf_path),
        mime="application/pdf",
        on_click="ignore"
    )
else:
    st.write("No se ha encontrado ningún PDF.")

# Tiempo de ejecución
if st.session_state.proceso is not None and st.session_state.inicio_ejecucion:
    tiempo_transcurrido = int(time.time() - st.session_state.inicio_ejecucion)
    horas, rem = divmod(tiempo_transcurrido, 3600)
    minutos, segundos = divmod(rem, 60)
    loader_display(horas, minutos, segundos)

# Auto-refresh
if st.session_state.proceso is not None:
    st_autorefresh(interval=5000, key="auto_refresh_comparative")

# Log viewer
if "log_path" in st.session_state and os.path.exists(st.session_state.log_path):
    with open(st.session_state.log_path, "r") as file:
        contenido_log = file.read()
    segundos_desde_actualizacion = int(time.time() - st.session_state.last_log_update)
    st.session_state.last_log_update = time.time()
    log_viewer(contenido_log, segundos_desde_actualizacion)

# Proceso finalizado
if st.session_state.proceso is not None and st.session_state.proceso.poll() is not None:
    with open(st.session_state.log_path, "a") as log_file:
        log_file.write("\n Proceso finalizado.")
    st.session_state.proceso = None
    st.rerun()

st.write("""
**Esta página te permite generar un informe comparativo entre dos jugadoras de cualquier liga o temporada.**  
Cada jugadora puede pertenecer a una competición y temporada distintas.  
Durante el proceso, podrás seguir el progreso en el recuadro de **"log"**.  
La generación del informe puede tardar entre **2 y 3 minutos**.  
Una vez finalizado, podrás **descargar el informe** fácilmente utilizando el botón de descarga.  

🔹 *Consejo:* evita **actualizar o cerrar la página** mientras se genera el informe para no interrumpir el proceso.  

ℹ️ *Nota:* si alguna de las jugadoras ha disputado **menos minutos** de los establecidos, **no se generará el informe**.
""")

page_footer("Plataforma de Análisis Liga F", "Fuente de datos: Hudl Wyscout")
