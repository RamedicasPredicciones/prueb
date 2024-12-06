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

# Función para guardar datos en un archivo Excel
def convertir_a_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Asegurarse de que la columna "vencimiento" esté en formato de fecha
        if "vencimiento" in df.columns:
            df["vencimiento"] = pd.to_datetime(df["vencimiento"], errors="coerce").dt.strftime("%Y-%m-%d")
        
        # Exportar en el orden deseado
        df.to_excel(
            writer, 
            index=False, 
            sheet_name="Consulta", 
            columns=[
                "codbarras", 
                "articulo", 
                "presentacion", 
                "cantidad", 
                "vencimiento", 
                "lote", 
                "novedad", 
                "bodega",
                "usuario"
            ]
        )
    output.seek(0)
    return output

# Configuración de la app
st.title("Consulta de Artículos y Lotes")

# Cargar la base de datos
base_df = cargar_base()

# Lista para almacenar las entradas
if "consultas" not in st.session_state:
    st.session_state.consultas = []

# Seleccionar método de entrada
st.subheader("Buscar por código (Manual o Escaneado)")

# Opción para elegir el método de entrada
input_method = st.radio("Seleccione el método de entrada:", ("Manual", "Pistola (código de barras)"))

# Campo para ingresar el código (se llenará dependiendo del método seleccionado)
if input_method == "Manual":
    codigo = st.text_input("Ingrese el código del artículo:")
else:
    # Si se selecciona pistola, se mostrará el código de barras detectado
    codigo = st.text_input("El código detectado por la pistola aparecerá aquí:", value=st.session_state.get('barcode', ''))

# Buscar el artículo basado en el código de barras o el código de artículo ingresado
search_results = pd.DataFrame()
if codigo:
    # Buscar por código de artículo si es ingresado manualmente
    if input_method == "Manual":
        search_results = base_df[base_df['codarticulo'].str.contains(codigo, case=False, na=False)]
    else:
        # Buscar por código de barras si es escaneado por la pistola
        barcode_results = base_df[base_df['codbarras'].str.contains(codigo, case=False, na=False)]
        if not barcode_results.empty:
            # Si encuentra el código de barras, obtiene el código de artículo
            codigo = barcode_results.iloc[0]['codarticulo']
            search_results = base_df[base_df['codarticulo'].str.contains(codigo, case=False, na=False)]
        else:
            search_results = pd.DataFrame()  # Si no encuentra nada

# Si no se encuentra el artículo o lote, permitir ingreso manual de los campos
if search_results.empty:
    st.warning("Código no encontrado. Ingrese los datos manualmente.")
    codarticulo_manual = st.text_input("Ingrese el código del artículo manualmente:")
    articulo = st.text_input("Ingrese el nombre del artículo:")
    presentacion = st.text_input("Ingrese la presentación del artículo:")
    vencimiento = st.date_input("Ingrese la fecha de vencimiento del artículo:")
else:
    # Mostrar detalles del artículo si se encuentra
    st.write("Detalles del artículo:")
    st.write(search_results[['codarticulo', 'articulo', 'presentacion', 'vencimiento']].drop_duplicates())

# Seleccionar lote
lotes = search_results['lote'].dropna().unique().tolist() if not search_results.empty else []
lotes.append('Otro')  # Opción para agregar un nuevo lote
lote_seleccionado = st.selectbox("Seleccione un lote:", lotes)

# Ingresar nuevo lote si se selecciona 'Otro'
if lote_seleccionado == "Otro":
    nuevo_lote = st.text_input("Ingrese el nuevo número de lote:")
else:
    nuevo_lote = lote_seleccionado

# Ingresar cantidad
cantidad = st.text_input("Ingrese la cantidad:")

# Seleccionar bodega
bodega = st.selectbox("Seleccione la bodega:", ["A011", "C014", "D012", "D013"])

# Seleccionar novedad
novedad = st.selectbox(
    "Seleccione la novedad:", 
    [
        "Vencido",
        "Avería",
        "Rayado",
        "Fecha corta",
        "Invima vencido",
        "Alerta sanitaria",
        "Comercial",
        "Cadena de frio"
    ]
)

# Ingresar usuario
usuario = st.text_input("Ingrese su nombre:")

# Botón para agregar entrada
if st.button("Agregar entrada"):
    if not nuevo_lote:
        st.error("Debe ingresar un número de lote válido.")
    else:
        consulta_data = {
            'codarticulo': codarticulo_manual if search_results.empty else search_results.iloc[0]['codarticulo'],
            'articulo': articulo if search_results.empty else search_results.iloc[0]['articulo'],
            'lote': nuevo_lote,
            'codbarras': search_results.iloc[0]['codbarras'] if 'codbarras' in search_results.columns else None,
            'presentacion': presentacion if search_results.empty else search_results.iloc[0]['presentacion'],
            'vencimiento': vencimiento if search_results.empty else search_results.iloc[0]['vencimiento'],
            'cantidad': cantidad if cantidad else None,
            'bodega': bodega,
            'novedad': novedad,
            'usuario': usuario if usuario else None
        }
        st.session_state.consultas.append(consulta_data)
        st.success("Entrada agregada correctamente!")

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
