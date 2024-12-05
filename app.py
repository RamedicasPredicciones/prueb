import pandas as pd
import streamlit as st
import io
import requests

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

# Configuración de la app
st.title("Consulta de Artículos y Lotes")

# Cargar la base de datos
base_df = cargar_base()

# Lista para almacenar las entradas
if "consultas" not in st.session_state:
    st.session_state.consultas = []

# Opciones de entrada
st.subheader("Buscar por código de barras (Pistola o Manual)")
codigo = st.text_input("Escanea o ingresa el código de barras:")

# Verificar si se ingresó un código
if codigo:
    # Buscar en la columna 'codbarras'
    barcode_results = base_df[base_df['codbarras'].str.contains(codigo, case=False, na=False)]

    if not barcode_results.empty:
        # Mostrar el código de barras y los datos asociados
        st.success(f"Código de barras detectado: {codigo}")
        codarticulo = barcode_results.iloc[0]['codarticulo']
        st.write(f"Código de artículo asociado: {codarticulo}")
        st.write("Detalles del artículo:")
        st.write(barcode_results[['codarticulo', 'articulo', 'presentacion', 'vencimiento']].drop_duplicates())

        # Seleccionar lote
        lotes = barcode_results['lote'].dropna().unique().tolist()
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
                    'codarticulo': codarticulo,
                    'articulo': barcode_results.iloc[0]['articulo'] if 'articulo' in barcode_results.columns else None,
                    'lote': nuevo_lote,
                    'codbarras': codigo,
                    'presentacion': barcode_results.iloc[0]['presentacion'] if 'presentacion' in barcode_results.columns else None,
                    'vencimiento': barcode_results.iloc[0]['vencimiento'] if 'vencimiento' in barcode_results.columns else None,
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
else:
    st.warning("No hay entradas guardadas.")
