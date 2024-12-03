import pandas as pd
import streamlit as st
import io
import requests
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
from pyzbar.pyzbar import decode  # Biblioteca para decodificar códigos de barras

# Función para cargar los datos desde Google Sheets
@st.cache_data
def cargar_base():
    url = "https://docs.google.com/spreadsheets/d/1Gk-EUifL3fODSc5kJ52gsNsxY9-hC1j4/export?format=xlsx"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Verificar si la solicitud fue exitosa
        # Especificar la hoja a leer
        base = pd.read_excel(io.BytesIO(response.content), sheet_name="TP's GHG")
        base.columns = base.columns.str.lower().str.strip()  # Normalizar nombres de columnas
        return base
    except Exception as e:
        st.error(f"Error al cargar la base de datos: {e}")
        return None

# Función para guardar datos en un archivo Excel
def convertir_a_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Consulta")
    output.seek(0)
    return output

# Clase para procesar la cámara y leer códigos de barras
class BarcodeReader(VideoTransformerBase):
    def __init__(self):
        self.last_barcode = None  # Guardar el último código leído

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        decoded_objects = decode(img)  # Decodificar códigos de barras
        for obj in decoded_objects:
            self.last_barcode = obj.data.decode("utf-8")
            # Dibujar un rectángulo alrededor del código de barras
            points = obj.polygon
            if len(points) > 4:  # Si el polígono tiene más de 4 puntos
                hull = cv2.convexHull(np.array([p for p in points], dtype=np.float32))
                points = hull
            points = np.array(points, dtype=int)
            cv2.polylines(img, [points], isClosed=True, color=(0, 255, 0), thickness=2)
        return img

# Configuración de la app
st.title("Consulta de Artículos y Lotes")

# Cargar la base de datos
base_df = cargar_base()

# Lista para almacenar las entradas
if "consultas" not in st.session_state:
    st.session_state.consultas = []

if base_df is not None:
    # Buscar por código de artículo manualmente
    tab1, tab2 = st.tabs(["Buscar Manualmente", "Escanear Código de Barras"])

    with tab1:
        codigo = st.text_input('Ingrese el código del artículo:')
        if codigo:
            # Filtrar los lotes del código de artículo ingresado
            search_results = base_df[base_df['codarticulo'].str.contains(codigo, case=False, na=False)]
            if not search_results.empty:
                # Mostrar resultados
                st.write("Resultados encontrados:")
                st.dataframe(search_results)
            else:
                st.error("Código de artículo no encontrado en la base de datos.")

    with tab2:
        st.write("Activa la cámara para escanear un código de barras.")
        webrtc_ctx = webrtc_streamer(key="barcode-reader", video_transformer_factory=BarcodeReader)

        if webrtc_ctx.video_transformer:
            barcode = webrtc_ctx.video_transformer.last_barcode
            if barcode:
                st.write(f"Código de barras detectado: **{barcode}**")
                # Buscar en la base de datos
                search_results = base_df[base_df['codbarras'].str.contains(barcode, case=False, na=False)]
                if not search_results.empty:
                    st.write("Resultados encontrados:")
                    st.dataframe(search_results)
                else:
                    st.error("Código de barras no encontrado en la base de datos.")

else:
    st.error("No se pudo cargar la base de datos. Verifica la URL o el formato del archivo.")
