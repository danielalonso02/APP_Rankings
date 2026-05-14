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
import pandas as pd


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
ruta_script = os.path.join(BASE_DIR, "report_gen_wyscout", "Report_LIGAF_Comparative.py")
directorio_logs = os.path.join(BASE_DIR, "logs")
ruta_excel2 = os.path.join(BASE_DIR)
directorio_base = os.path.dirname(ruta_script)
parameters_route_xlsx = os.path.join(BASE_DIR, "report_gen_wyscout", "parameters.xlsx")
RUTA_FAVORITOS = os.path.join(BASE_DIR, "config_pesos_favoritos.json")
RUTA_FAVORITOS_FIS = os.path.join(BASE_DIR, "config_pesos_fisicos.json")

os.makedirs(directorio_logs, exist_ok=True)

# ── Uploader: puede subir 1 o 2 archivos (si ambas jugadoras están en el mismo Excel, basta uno) ──
if "df_comp1" not in st.session_state:
    st.session_state["df_comp1"] = None
    st.session_state["df_comp1_nombre"] = None
    st.session_state["df_comp1_ruta_temp"] = None
if "df_comp2" not in st.session_state:
    st.session_state["df_comp2"] = None
    st.session_state["df_comp2_nombre"] = None
    st.session_state["df_comp2_ruta_temp"] = None

st.markdown(":material/upload_file: **Archivos de datos**")
st.caption("Si ambas jugadoras están en el mismo archivo, sube el mismo Excel en los dos campos. "
           "Si son de temporadas o competiciones distintas, sube un archivo diferente para cada una.")

up_col1, up_col2 = st.columns(2)

def _save_temp(file_bytes):
    import tempfile as _t
    f = _t.NamedTemporaryFile(suffix=".xlsx", delete=False)
    f.write(file_bytes)
    f.close()
    return f.name

with up_col1:
    st.markdown("**Jugadora 1 — archivo de datos**")
    if st.session_state["df_comp1"] is not None:
        st.success(f"✅ {st.session_state['df_comp1_nombre']} ({len(st.session_state['df_comp1']):,} filas)")
        if st.button("🔄 Cambiar", key="cambiar_comp1", use_container_width=True):
            st.session_state["df_comp1"] = None
            st.session_state["df_comp1_nombre"] = None
            st.session_state["df_comp1_ruta_temp"] = None
            st.rerun()
    else:
        up1 = st.file_uploader("Archivo jugadora 1 (.xlsx)", type=["xlsx"], key="uploader_comp1", label_visibility="collapsed")
        if up1:
            import io as _io_c
            b = up1.read()
            st.session_state["df_comp1"] = pd.read_excel(_io_c.BytesIO(b))
            st.session_state["df_comp1_nombre"] = up1.name
            st.session_state["df_comp1_ruta_temp"] = _save_temp(b)
            st.rerun()

with up_col2:
    st.markdown("**Jugadora 2 — archivo de datos**")
    if st.session_state["df_comp2"] is not None:
        st.success(f"✅ {st.session_state['df_comp2_nombre']} ({len(st.session_state['df_comp2']):,} filas)")
        if st.button("🔄 Cambiar", key="cambiar_comp2", use_container_width=True):
            st.session_state["df_comp2"] = None
            st.session_state["df_comp2_nombre"] = None
            st.session_state["df_comp2_ruta_temp"] = None
            st.rerun()
    else:
        up2 = st.file_uploader("Archivo jugadora 2 (.xlsx)", type=["xlsx"], key="uploader_comp2", label_visibility="collapsed")
        if up2:
            import io as _io_c2
            b2 = up2.read()
            st.session_state["df_comp2"] = pd.read_excel(_io_c2.BytesIO(b2))
            st.session_state["df_comp2_nombre"] = up2.name
            st.session_state["df_comp2_ruta_temp"] = _save_temp(b2)
            st.rerun()

if st.session_state["df_comp1"] is None or st.session_state["df_comp2"] is None:
    st.info("ℹ️ Sube los archivos de datos para continuar.")
    st.stop()

df_jugadoras1 = st.session_state["df_comp1"]
df_jugadoras2 = st.session_state["df_comp2"]


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
        lista_jugadoras1 = util.obtener_lista_jugadores(df_jugadoras1, "Jugadores") if df_jugadoras1 is not None else []
        player1 = st.selectbox(
            "Jugadora 1:",
            lista_jugadoras1,
            placeholder="Escribe el nombre...",
            key="player1",
            label_visibility="collapsed"
        )
        player_id1 = util.obtener_id_jugador_df(df_jugadoras1, player_name=player1) if player1 else None

    # --- JUGADORA 2 ---
    with col5:
        st.markdown("**Jugadora 2**")
        lista_jugadoras2 = util.obtener_lista_jugadores(df_jugadoras2, "Jugadores") if df_jugadoras2 is not None else []
        player2 = st.selectbox(
            "Jugadora 2:",
            lista_jugadoras2,
            placeholder="Escribe el nombre...",
            key="player2",
            label_visibility="collapsed"
        )
        player_id2 = util.obtener_id_jugador_df(df_jugadoras2, player_name=player2) if player2 else None

    # Aviso si misma jugadora y mismo archivo
    same_player = (
        player1 == player2
        and st.session_state["df_comp1_nombre"] == st.session_state["df_comp2_nombre"]
        and player1 is not None
        and player2 is not None
    )
    if same_player:
        st.warning("⚠️ Has seleccionado la misma jugadora dos veces. Por favor, elige jugadoras distintas.")

    # ── Selectores de configuración de pesos ──
    import json as _json
    st.markdown(":material/tune: Configuración de pesos")
    pesos_favorito_sel = None
    if os.path.exists(RUTA_FAVORITOS):
        with open(RUTA_FAVORITOS, "r", encoding="utf-8") as _f:
            _favs = _json.load(_f)
        if _favs:
            _opciones = ["Sin favorito (pesos por defecto)"] + list(_favs.keys())
            _sel = st.selectbox("Configuración de pesos tácticos:", _opciones, key="pesos_sel_comp")
            if _sel != "Sin favorito (pesos por defecto)":
                pesos_favorito_sel = _sel
        else:
            st.caption("No hay configuraciones tácticas guardadas en Rankings.")
    else:
        st.caption("No se ha encontrado archivo de configuraciones de pesos tácticos.")

    pesos_fisicos_sel = None
    if os.path.exists(RUTA_FAVORITOS_FIS):
        with open(RUTA_FAVORITOS_FIS, "r", encoding="utf-8") as _f2:
            _favs_fis = _json.load(_f2)
        if _favs_fis:
            _opciones_fis = ["Sin favorito (pesos por defecto)"] + list(_favs_fis.keys())
            _sel_fis = st.selectbox("Configuración de pesos físicos:", _opciones_fis, key="pesos_fisicos_sel_comp")
            if _sel_fis != "Sin favorito (pesos por defecto)":
                pesos_fisicos_sel = _sel_fis
        else:
            st.caption("No hay configuraciones físicas guardadas en Rankings Físicos.")
    else:
        st.caption("No se ha encontrado archivo de configuraciones de pesos físicos.")

    return {
        "ruta_script": ruta_script,
        "pesos_favorito_sel": pesos_favorito_sel,
        "pesos_fisicos_sel": pesos_fisicos_sel,
        "wyscout_file1_temp": st.session_state["df_comp1_ruta_temp"],
        "wyscout_file2_temp": st.session_state["df_comp2_ruta_temp"],
        "player_id1": player_id1,
        "player_id2": player_id2,
        "player1": player1,
        "player2": player2,
        "min_minutes": min_minutes,
        "summary": summary,
        "same_player": same_player,
    }


filtros = filtros_fragment()

# Mostrar tabla de jugadora 1 y jugadora 2 side by side
col_t1, col_t2 = st.columns(2)
with col_t1:
    st.caption(f"Datos: {st.session_state['df_comp1_nombre']}")
    if filtros["player1"] and "Jugador" in df_jugadoras1.columns:
        df_show1 = df_jugadoras1[df_jugadoras1["Jugador"] == filtros["player1"]]
    else:
        df_show1 = df_jugadoras1
    st.dataframe(df_show1, use_container_width=True)
with col_t2:
    st.caption(f"Datos: {st.session_state['df_comp2_nombre']}")
    if filtros["player2"] and "Jugador" in df_jugadoras2.columns:
        df_show2 = df_jugadoras2[df_jugadoras2["Jugador"] == filtros["player2"]]
    else:
        df_show2 = df_jugadoras2
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
                "--wyscout_file1", str(filtros["wyscout_file1_temp"]),
                "--wyscout_file2", str(filtros["wyscout_file2_temp"]),
                "--parameters_file", str(params_xlsx),
                "--position_number", "1",
                "--min_minutes",   str(filtros["min_minutes"]),
                "--color_selection", filtros.get("color_selection", "#FFFFFF"),
                "--summary",       str(filtros.get("summary", 0)),
            ]
            # Añadir pesos tácticos si hay favorito seleccionado
            import json as _json, tempfile as _tempfile
            _pesos_sel = filtros.get("pesos_favorito_sel")
            if _pesos_sel and os.path.exists(RUTA_FAVORITOS):
                with open(RUTA_FAVORITOS, "r", encoding="utf-8") as _f:
                    _all_favs = _json.load(_f)
                if _pesos_sel in _all_favs:
                    _tmp = _tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
                    _json.dump(_all_favs[_pesos_sel], _tmp, ensure_ascii=False)
                    _tmp.close()
                    cmd += ["--pesos_file", _tmp.name]
            # Añadir pesos físicos si hay favorito físico seleccionado
            _pesos_fis_sel = filtros.get("pesos_fisicos_sel")
            if _pesos_fis_sel and os.path.exists(RUTA_FAVORITOS_FIS):
                with open(RUTA_FAVORITOS_FIS, "r", encoding="utf-8") as _f2:
                    _all_favs_fis = _json.load(_f2)
                if _pesos_fis_sel in _all_favs_fis:
                    _tmp_fis = _tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
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


folder = "report_gen_comparative/ReportsGenerados"
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
