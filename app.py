import pandas as pd
import streamlit as st
import io
import requests
import cv2
from streamlit_webrtc import VideoTransformerBase, webrtc_streamer

# Función para cargar los datos desde Google Sheets
@st.cache_data
def cargar_base():
    url = "https://docs.google.com/spreadsheets/d/1Gnbn5Pn_tth_b1GdhJvoEbK7eIbRR8uy/export?format=xlsx"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Verificar si la solicitud fue exitosa
        base = pd.read_excel(io.BytesIO(response.content), sheet_name="OP's GHG")
        base.columns = base.columns.str.lower().str.strip()  # Normalizar nombres de columnas
        return base
    except Exception as e:
        st.error(f"Error al cargar la base de datos: {e}")
        return None

# Clase para transformar el video y detectar códigos de barras
class BarcodeReader(VideoTransformerBase):
    def transform(self, frame):
        # Convertir la imagen del video en un array de OpenCV
        img = frame.to_ndarray(format="bgr24")
        # Usar QRCodeDetector de OpenCV para detectar códigos de barras
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)
        # Si se detecta un código de barras, actualizar el código en el estado
        if data:
            st.session_state['barcode'] = data
            cv2.putText(img, f"Barcode: {data}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        return img

# Función para guardar datos en un archivo Excel
def convertir_a_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Consulta")
    output.seek(0)
    return output

# Configuración de la app
st.title("Consulta de Artículos y Lotes")

# Cargar la base de datos
base_df = cargar_base()

# Lista para almacenar las entradas
if "consultas" not in st.session_state:
    st.session_state.consultas = []

# Escanear código de barras con cámara
st.subheader("Escanear código de barras (Automático)")
webrtc_streamer(
    key="barcode-reader",
    video_transformer_factory=BarcodeReader,
    media_stream_constraints={"video": True, "audio": False}
)

# Opciones de entrada
st.subheader("Buscar por código (Manual o Escaneado)")
input_method = st.radio("Seleccione el método de entrada:", ("Manual", "Pistola (código de barras)"))

if input_method == "Manual":
    codigo = st.text_input("Ingrese el código del artículo:")
else:
    codigo = st.text_input("El código detectado por la pistola aparecerá aquí:", 
                           value=st.session_state.get('barcode', ''))

# Verificar si se ingresó o detectó un código
if codigo:
    if input_method == "Manual":
        search_results = base_df[base_df['codarticulo'].str.contains(codigo, case=False, na=False)]
    else:
        barcode_results = base_df[base_df['codbarras'].str.contains(codigo, case=False, na=False)]
        if not barcode_results.empty:
            codigo = barcode_results.iloc[0]['codarticulo']  # Obtener el codarticulo asociado
            search_results = base_df[base_df['codarticulo'].str.contains(codigo, case=False, na=False)]
        else:
            search_results = pd.DataFrame()

    if not search_results.empty:
        # Mostrar resultados y opciones
        st.write(f"Código detectado: {codigo}")
        st.write("Detalles del artículo:")
        st.write(search_results[['codarticulo', 'articulo', 'presentacion', 'vencimiento']].drop_duplicates())

        # Seleccionar lote
        lotes = search_results['lote'].dropna().unique().tolist()
        lotes.append('Otro')  # Opción para agregar un nuevo lote
        lote_seleccionado = st.selectbox("Seleccione un lote:", lotes)

        # Ingresar nuevo lote si se selecciona 'Otro'
        if lote_seleccionado == "Otro":
            nuevo_lote = st.text_input("Ingrese el nuevo número de lote:")
        else:
            nuevo_lote = lote_seleccionado

        # Ingresar cantidad y usuario
        cantidad = st.text_input("Ingrese la cantidad (opcional):")
        usuario = st.text_input("Ingrese su nombre (opcional):")

        # Botón para agregar entrada
        if st.button("Agregar entrada"):
            if not nuevo_lote:
                st.error("Debe ingresar un número de lote válido.")
            else:
                consulta_data = {
                    'codarticulo': codigo,
                    'articulo': search_results.iloc[0]['articulo'] if 'articulo' in search_results.columns else None,
                    'lote': nuevo_lote,
                    'codbarras': search_results.iloc[0]['codbarras'] if 'codbarras' in search_results.columns else None,
                    'presentacion': search_results.iloc[0]['presentacion'] if 'presentacion' in search_results.columns else None,
                    'vencimiento': search_results.iloc[0]['vencimiento'] if 'vencimiento' in search_results.columns else None,
                    'cantidad': cantidad if cantidad else None,
                    'usuario': usuario if usuario else None
                }
                st.session_state.consultas.append(consulta_data)
                st.success("Entrada agregada correctamente!")
    else:
        st.error("Código no encontrado en la base de datos.")

# Mostrar las entradas guardadas
if st.session_state.consultas:
    st.write("Entradas guardadas:")
    consultas_df = pd.DataFrame(st.session_state.consultas)
    st.dataframe(consultas_df)

    # Botón para descargar el archivo Excel
    consultas_excel = convertir_a_excel(consultas_df)
    st.download_button(
        label="Descargar Excel con todas las consultas",
        data=consultas_excel,
        file_name="consultas_guardadas.xlsx",
        mime="application/vnd.ms-excel"
    )
else:
    st.warning("No hay entradas guardadas.")
