import pandas as pd
import streamlit as st
import io
import requests
import cv2
from pyzbar.pyzbar import decode
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

# Función para cargar los datos desde Google Sheets
@st.cache_data
def cargar_base():
    url = "https://docs.google.com/spreadsheets/d/1Gnbn5Pn_tth_b1GdhJvoEbK7eIbRR8uy/export?format=xlsx"
    try:
        response = requests.get(url)
        response.raise_for_status()
        base = pd.read_excel(io.BytesIO(response.content), sheet_name="OP's GHG")
        base.columns = base.columns.str.lower().str.strip()
        return base
    except Exception as e:
        st.error(f"Error al cargar la base de datos: {e}")
        return None

# Clase para transformar el video y detectar códigos de barras
class BarcodeReader(VideoTransformerBase):
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        decoded_objects = decode(img)  # Detectar códigos de barras

        for obj in decoded_objects:
            # Extraer datos del código de barras
            data = obj.data.decode("utf-8")
            # Dibujar un rectángulo alrededor del código detectado
            points = obj.polygon
            if len(points) == 4:
                pts = [(point.x, point.y) for point in points]
                cv2.polylines(img, [np.array(pts, dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=2)

            # Escribir el valor del código detectado en el video
            cv2.putText(img, f"Barcode: {data}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            # Guardar el código detectado en session_state
            st.session_state['barcode'] = data

        return img

# Configuración de la app
st.title("Consulta de Artículos y Lotes")

# Cargar la base de datos
base_df = cargar_base()

# Lista para almacenar las entradas
if "consultas" not in st.session_state:
    st.session_state.consultas = []

# Escanear código de barras
st.subheader("Escanear código de barras")
webrtc_streamer(
    key="barcode-reader",
    video_transformer_factory=BarcodeReader,
    media_stream_constraints={"video": True, "audio": False},
)

# Campo de entrada para el código del artículo
codigo = st.text_input("Ingrese el código del artículo:") if "barcode" not in st.session_state else st.session_state["barcode"]

if codigo:
    # Filtrar los datos según el código
    search_results = base_df[base_df["codarticulo"].str.contains(codigo, case=False, na=False)]

    if not search_results.empty:
        lotes = search_results["lote"].dropna().unique().tolist()
        lotes.append("Otro")
        lote_seleccionado = st.selectbox("Seleccione un lote", lotes)

        if lote_seleccionado == "Otro":
            nuevo_lote = st.text_input("Ingrese el nuevo número de lote:")
        else:
            nuevo_lote = lote_seleccionado

        cantidad = st.text_input("Ingrese la cantidad (opcional):")
        usuario = st.text_input("Ingrese su nombre:")

        if st.button("Agregar entrada"):
            if not nuevo_lote:
                st.error("Debe ingresar un número de lote válido.")
            else:
                consulta_data = {
                    "codarticulo": codigo,
                    "articulo": search_results.iloc[0].get("articulo", None),
                    "lote": nuevo_lote,
                    "codbarras": search_results.iloc[0].get("codbarras", None),
                    "presentacion": search_results.iloc[0].get("presentacion", None),
                    "vencimiento": search_results.iloc[0].get("vencimiento", None),
                    "cantidad": cantidad if cantidad else None,
                    "usuario": usuario if usuario else None,
                }
                st.session_state.consultas.append(consulta_data)
                st.success("Entrada agregada correctamente!")
    else:
        st.error("Código de artículo no encontrado en la base de datos.")

if st.session_state.consultas:
    st.write("Entradas guardadas:")
    consultas_df = pd.DataFrame(st.session_state.consultas)
    st.dataframe(consultas_df)

    # Descarga de archivo Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        consultas_df.to_excel(writer, index=False, sheet_name="Consulta")
    output.seek(0)

    st.download_button(
        label="Descargar Excel con todas las consultas",
        data=output,
        file_name="consultas_guardadas.xlsx",
        mime="application/vnd.ms-excel",
    )
else:
    st.warning("No hay entradas guardadas.")
