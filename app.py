import pandas as pd
import streamlit as st
import requests
import io

# Función para cargar la base de datos
@st.cache_data
def cargar_base():
    url_base = "https://docs.google.com/spreadsheets/d/1Gk-EUifL3fODSc5kJ52gsNsxY9-hC1j4/export?format=xlsx"
    response = requests.get(url_base, verify=False)
    if response.status_code == 200:
        data = response.content
        base_df = pd.read_excel(io.BytesIO(data))
        base_df.columns = base_df.columns.str.strip()  # Eliminar espacios en los nombres de columnas
        return base_df
    else:
        st.error(f"Error al cargar la base: {response.status_code}")
        return pd.DataFrame()

# Configuración inicial de la app
st.title("Registro de Artículos y Lotes")

# Cargar la base
base_df = cargar_base()

# Verificar nombres de columnas
st.write("Nombres de columnas en la base cargada:", base_df.columns.tolist())

# Contenedor para las entradas
registros = []

# Ingreso de datos
codigo = st.text_input('Ingrese el código del artículo (codart):')

if codigo:
    if 'codart' in base_df.columns:
        # Filtrar la base por el código ingresado
        search_results = base_df[base_df['codart'].astype(str).str.contains(codigo, case=False, na=False)]

        if not search_results.empty:
            # Selección del lote
            lotes = search_results['LOTE'].unique().tolist()
            lotes.append('Otro')
            lote_seleccionado = st.selectbox('Seleccione un lote', lotes)

            # Permitir ingreso de un nuevo lote si se selecciona "Otro"
            if lote_seleccionado == 'Otro':
                nuevo_lote = st.text_input('Ingrese el nuevo número de lote:')
            else:
                nuevo_lote = lote_seleccionado

            # Ingreso de cantidad
            cantidad = st.number_input('Ingrese la cantidad (puede quedar vacía):', min_value=0, step=1, value=0)

            # Guardar los datos ingresados
            if st.button('Agregar registro'):
                if not nuevo_lote:
                    st.error("Debe ingresar un número de lote válido.")
                else:
                    selected_row = search_results.iloc[0]
                    nuevo_registro = {
                        'codart': codigo,
                        'Descripción art': selected_row.get('Descripción art'),
                        'LOTE': nuevo_lote,
                        'cantidad': cantidad if cantidad > 0 else None,
                        'codbarras': selected_row.get('codbarras'),
                        'presentacion': selected_row.get('presentacion'),
                        'FECHA DE VENCIMIENTO': selected_row.get('FECHA DE VENCIMIENTO')
                    }
                    registros.append(nuevo_registro)
                    st.success("Registro agregado con éxito.")
        else:
            st.error("Código no encontrado en la base.")
    else:
        st.error("La columna 'codart' no está en la base. Verifique los nombres de las columnas.")

# Botón para descargar el archivo Excel con los registros
if registros:
    registros_df = pd.DataFrame(registros)
    registros_excel = convertir_a_excel(registros_df)
    st.download_button(
        label="Descargar Excel con los registros",
        data=registros_excel,
        file_name="registros_articulos.xlsx",
        mime="application/vnd.ms-excel"
    )

