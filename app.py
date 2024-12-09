import pandas as pd
import streamlit as st
import io
import os
import requests

# Función para cargar los datos desde Google Sheets
def cargar_base(url, sheet_name):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Verificar si la solicitud fue exitosa
        base = pd.read_excel(io.BytesIO(response.content), sheet_name=sheet_name)
        base.columns = base.columns.str.lower().str.strip()  # Normalizar nombres de columnas
        return base
    except Exception as e:
        st.error(f"Error al cargar la base de datos desde {url}: {e}")
        return None

# Función para guardar el historial de consultas en un archivo Excel
def guardar_historial(consultas_df, filename="historial_consultas.xlsx"):
    if os.path.exists(filename):
        # Si el archivo ya existe, añadimos los nuevos datos al final
        consultas_df.to_excel(filename, index=False, mode='a', header=False)
    else:
        # Si no existe el archivo, lo creamos y escribimos los datos
        consultas_df.to_excel(filename, index=False)

# Función para cargar el historial de consultas desde un archivo Excel
def cargar_historial(filename="historial_consultas.xlsx"):
    if os.path.exists(filename):
        return pd.read_excel(filename)
    else:
        return pd.DataFrame()  # Retorna un DataFrame vacío si no existe el archivo

# Función para convertir DataFrame a un archivo Excel
def convertir_a_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Consulta")
    output.seek(0)
    return output

# Configuración de la app
st.title("Consulta de Artículos y Lotes")

# Cargar el historial de consultas desde el archivo
historial_df = cargar_historial()

# Mostrar el historial de consultas si existe
if not historial_df.empty:
    st.write("Historial de Consultas:")
    st.dataframe(historial_df)

# Cargar las bases de datos (evitando duplicar operaciones)
base_url = "https://docs.google.com/spreadsheets/d/1Gnbn5Pn_tth_b1GdhJvoEbK7eIbRR8uy/export?format=xlsx"
maestra_url = "https://docs.google.com/spreadsheets/d/19myWtMrvsor2P_XHiifPgn8YKdTWE39O/export?format=xlsx"

with st.spinner("Cargando bases de datos..."):
    base_df = cargar_base(base_url, sheet_name="OP's GHG")
    maestra_df = cargar_base(maestra_url, sheet_name="Hoja1")

# Verificar si las bases se cargaron correctamente
if base_df is None or maestra_df is None:
    st.stop()

# Lista para almacenar las entradas
if "consultas" not in st.session_state:
    st.session_state.consultas = []

# Seleccionar método de entrada
st.subheader("Buscar por código (Manual o Escaneado)")
input_method = st.radio("Seleccione el método de entrada:", ("Manual", "Pistola (código de barras)"))
codigo = st.text_input("Ingrese el código del artículo:" if input_method == "Manual" else "El código detectado por la pistola aparecerá aquí:")

search_results = pd.DataFrame()
if codigo:
    # Buscar en la base principal
    if input_method == "Manual":
        search_results = base_df.query("codarticulo.str.contains(@codigo, case=False, na=False)", engine="python")
    else:
        barcode_results = base_df.query("codbarras.str.contains(@codigo, case=False, na=False)", engine="python")
        if not barcode_results.empty:
            codigo = barcode_results.iloc[0]['codarticulo']
            search_results = base_df.query("codarticulo.str.contains(@codigo, case=False, na=False)", engine="python")
    
    # Si no se encuentra, buscar en la base maestra
    if search_results.empty:
        st.info("Código no encontrado en la base principal. Buscando en la base maestra...")
        if input_method == "Manual":
            search_results = maestra_df.query("codart.str.contains(@codigo, case=False, na=False)", engine="python")
        else:
            search_results = maestra_df.query("cod_barras.str.contains(@codigo, case=False, na=False)", engine="python")
        
        # Renombrar columnas si se encontraron resultados
        if not search_results.empty:
            search_results.rename(columns={
                'codart': 'codarticulo',
                'cod_barras': 'codbarras',
                'nomart': 'articulo',
                'presentación': 'presentacion',
                'fabr': 'lab'
            }, inplace=True)

# Si no se encuentra en ninguna base
if search_results.empty:
    st.warning("Código no encontrado en ninguna base. Ingrese los datos manualmente.")
    codarticulo_manual = st.text_input("Ingrese el código del artículo manualmente:")
    articulo = st.text_input("Ingrese el nombre del artículo:")
    presentacion = st.text_input("Ingrese la presentación del artículo:")
    vencimiento = st.date_input("Ingrese la fecha de vencimiento del artículo:")
else:
    st.write("Detalles del artículo encontrado:")
    st.write(search_results[['codarticulo', 'articulo', 'presentacion', 'lab']].drop_duplicates())
    vencimiento = st.date_input("Ingrese la fecha de vencimiento del artículo:")

# Ingresar lote
nuevo_lote = st.text_input("Ingrese el nuevo número de lote:")

# Ingresar los demás datos
cantidad = st.text_input("Ingrese la cantidad:")
bodega = st.selectbox("Seleccione la bodega:", ["A011", "C014", "D012", "D013"])
novedad = st.selectbox("Seleccione la novedad:", [
    "Vencido", "Avería", "Rayado", "Fecha corta", "Invima vencido",
    "Alerta sanitaria", "Comercial", "Cadena de frio"
])
usuario = st.text_input("Ingrese su nombre:")

# Guardar la entrada
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
            'vencimiento': vencimiento,
            'cantidad': cantidad if cantidad else None,
            'bodega': bodega,
            'novedad': novedad,
            'usuario': usuario if usuario else None,
            'lab': search_results.iloc[0]['lab'] if 'lab' in search_results.columns else None
        }
        st.session_state.consultas.append(consulta_data)
        st.success("Entrada agregada correctamente!")

        # Guardar en el historial
        consultas_df = pd.DataFrame(st.session_state.consultas)
        guardar_historial(consultas_df)

# Mostrar las entradas guardadas
if st.session_state.consultas:
    st.write("Entradas guardadas:")
    consultas_df = pd.DataFrame(st.session_state.consultas)
    st.dataframe(consultas_df)

    consultas_excel = convertir_a_excel(consultas_df)
    st.download_button(
        label="Descargar Excel con todas las consultas",
        data=consultas_excel,
        file_name="consultas_guardadas.xlsx",
        mime="application/vnd.ms-excel"
    )
else:
    st.warning("No hay entradas guardadas.")

