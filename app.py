import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime
import uuid

APP_DIR = Path(__file__).parent
UPLOAD_DIR = APP_DIR / "fotos_reportes"
DB_PATH = APP_DIR / "reportes_mantaro.db"
UPLOAD_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Mantaro Vivo | Reportes", page_icon="🌱", layout="wide")

st.markdown("""
<style>
.main {background-color: #f7faf8;}
.hero {padding: 1.3rem 1.5rem; border-radius: 16px; background: linear-gradient(110deg,#075e54,#16806a); color:white;}
.hero h1 {color:white; margin-bottom:.25rem;}
.small-note {color:#52645f;font-size:.9rem;}
div[data-testid="stMetric"] {background:white;padding:12px;border-radius:12px;border:1px solid #e1ebe6;}
</style>
""", unsafe_allow_html=True)

def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reportes (
            id TEXT PRIMARY KEY,
            fecha TEXT NOT NULL,
            categoria TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            sector TEXT NOT NULL,
            referencia TEXT,
            latitud REAL,
            longitud REAL,
            nombre TEXT,
            contacto TEXT,
            foto TEXT,
            estado TEXT NOT NULL DEFAULT 'Pendiente'
        )
    """)
    conn.commit()
    return conn

def get_reports():
    with connect() as conn:
        return pd.read_sql_query("SELECT * FROM reportes ORDER BY fecha DESC", conn)

def save_report(values):
    with connect() as conn:
        conn.execute("""
            INSERT INTO reportes
            (id, fecha, categoria, descripcion, sector, referencia, latitud, longitud,
             nombre, contacto, foto, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)
        conn.commit()

def update_status(report_id, status):
    with connect() as conn:
        conn.execute("UPDATE reportes SET estado=? WHERE id=?", (status, report_id))
        conn.commit()

def safe_photo_name(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in [".jpg", ".jpeg", ".png", ".webp"]:
        suffix = ".jpg"
    return f"{uuid.uuid4().hex}{suffix}"

st.markdown("""
<div class="hero">
  <h1>🌱 Mantaro Vivo</h1>
  <div>Reportes ciudadanos de basura y contaminación en la ribera del río Mantaro</div>
</div>
""", unsafe_allow_html=True)
st.write("Ayúdanos a identificar puntos críticos y organizar mejor las acciones de recuperación ambiental.")
st.caption("Prototipo académico: los datos se guardan en la computadora donde se ejecuta la aplicación.")

tab_reportar, tab_panel, tab_mapa, tab_acerca = st.tabs([
    "📝 Registrar reporte", "📊 Panel de reportes", "🗺️ Mapa", "ℹ️ Acerca del proyecto"
])

with tab_reportar:
    st.subheader("Registrar un problema ambiental")
    with st.form("form_reporte", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            categoria = st.selectbox("Tipo de problema", [
                "Basura doméstica", "Desmonte / residuos de construcción",
                "Vertimiento de aguas residuales", "Quema de residuos",
                "Extracción de agregados", "Otro problema ambiental"
            ])
            sector = st.selectbox("Sector aproximado", [
                "El Tambo", "Cajas Chico", "Ribera del río Mantaro",
                "Chilca", "Huancayo", "Otro sector"
            ])
            referencia = st.text_input("Referencia del lugar", placeholder="Ej.: cerca del puente, camino o punto conocido")
            descripcion = st.text_area("Describe lo que observaste", placeholder="Indica qué ocurre, cantidad aproximada y desde cuándo...", max_chars=1000)
        with c2:
            st.markdown("**Ubicación (opcional, pero recomendada)**")
            st.caption("Puedes obtener las coordenadas desde Google Maps. No se detecta automáticamente tu ubicación.")
            latitud = st.number_input("Latitud", min_value=-90.0, max_value=90.0, value=-12.05, format="%.6f")
            longitud = st.number_input("Longitud", min_value=-180.0, max_value=180.0, value=-75.22, format="%.6f")
            nombre = st.text_input("Nombre (opcional)")
            contacto = st.text_input("Contacto (opcional; no publiques datos sensibles)")
            foto = st.file_uploader("Adjuntar fotografía (JPG, PNG o WEBP)", type=["jpg", "jpeg", "png", "webp"])
        consentimiento = st.checkbox("Confirmo que la información corresponde a una observación real y que puedo compartir esta fotografía.")
        enviado = st.form_submit_button("Enviar reporte", type="primary", use_container_width=True)

    if enviado:
        if not descripcion.strip():
            st.error("Escribe una descripción breve del problema.")
        elif not consentimiento:
            st.warning("Marca la casilla de confirmación para enviar el reporte.")
        else:
            foto_path = ""
            if foto is not None:
                photo_name = safe_photo_name(foto)
                full_path = UPLOAD_DIR / photo_name
                full_path.write_bytes(foto.getvalue())
                foto_path = str(full_path.name)
            report_id = "MV-" + datetime.now().strftime("%y%m%d") + "-" + uuid.uuid4().hex[:5].upper()
            save_report((
                report_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), categoria,
                descripcion.strip(), sector, referencia.strip(), float(latitud), float(longitud),
                nombre.strip(), contacto.strip(), foto_path, "Pendiente"
            ))
            st.success(f"Reporte registrado. Código: {report_id}")
            st.info("Guarda el código para identificar el reporte en el panel.")

with tab_panel:
    st.subheader("Panel de seguimiento")
    df = get_reports()
    if df.empty:
        st.info("Todavía no hay reportes. Registra el primero en la pestaña correspondiente.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", len(df))
        m2.metric("Pendientes", int((df["estado"] == "Pendiente").sum()))
        m3.metric("En proceso", int((df["estado"] == "En proceso").sum()))
        m4.metric("Atendidos", int((df["estado"] == "Atendido").sum()))
        f1, f2 = st.columns(2)
        with f1:
            filtro_estado = st.multiselect("Filtrar por estado", ["Pendiente", "En proceso", "Atendido"], default=["Pendiente", "En proceso", "Atendido"])
        with f2:
            filtro_sector = st.multiselect("Filtrar por sector", sorted(df["sector"].dropna().unique()), default=sorted(df["sector"].dropna().unique()))
        vista = df[df["estado"].isin(filtro_estado) & df["sector"].isin(filtro_sector)]
        st.dataframe(vista[["id", "fecha", "categoria", "sector", "referencia", "descripcion", "estado"]], use_container_width=True, hide_index=True)
        st.markdown("**Actualizar estado de un reporte**")
        ids = df["id"].tolist()
        selected_id = st.selectbox("Código del reporte", ids)
        new_status = st.selectbox("Nuevo estado", ["Pendiente", "En proceso", "Atendido"])
        if st.button("Guardar estado", type="primary"):
            update_status(selected_id, new_status)
            st.success("Estado actualizado.")
            st.rerun()
        selected = df[df["id"] == selected_id].iloc[0]
        if selected["foto"]:
            path = UPLOAD_DIR / selected["foto"]
            if path.exists():
                st.image(str(path), caption=f"Fotografía del reporte {selected_id}", width=450)
        st.download_button(
            "Descargar reportes en CSV",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="reportes_mantaro_vivo.csv",
            mime="text/csv"
        )

with tab_mapa:
    st.subheader("Ubicaciones reportadas")
    df = get_reports()
    if df.empty:
        st.info("Cuando existan reportes con coordenadas, aparecerán aquí.")
    else:
        map_df = df.dropna(subset=["latitud", "longitud"]).copy()
        map_df = map_df[(map_df["latitud"].between(-90, 90)) & (map_df["longitud"].between(-180, 180))]
        if map_df.empty:
            st.info("Todavía no hay coordenadas válidas.")
        else:
            st.map(map_df.rename(columns={"latitud": "latitude", "longitud": "longitude"})[["latitude", "longitude"]])
            st.dataframe(map_df[["id", "categoria", "sector", "referencia", "estado", "latitud", "longitud"]], use_container_width=True, hide_index=True)
            st.caption("Verifica las coordenadas antes de usar los puntos para una intervención real.")

with tab_acerca:
    st.subheader("Sobre Mantaro Vivo")
    st.write("""
    **Objetivo:** facilitar que vecinos y actores locales registren puntos críticos de residuos y contaminación
    en la ribera del río Mantaro, para apoyar la priorización, fiscalización y recuperación ambiental.
    """)
    st.markdown("""
    **Flujo propuesto**
    1. Un vecino identifica un problema y registra el reporte.
    2. El equipo revisa la descripción, fotografía y ubicación.
    3. El reporte se clasifica como pendiente, en proceso o atendido.
    4. Se coordina con las entidades competentes cuando corresponda.
    """)
    st.warning("Este prototipo no envía alertas a la Municipalidad ni a la ANA automáticamente. Los reportes son aportes ciudadanos y deben verificarse antes de actuar.")
    st.caption("Privacidad: evita publicar rostros, placas, teléfonos u otros datos personales sin autorización.")

st.divider()
st.caption("Mantaro Vivo · Prototipo universitario para el cuidado de la ribera del río Mantaro")
