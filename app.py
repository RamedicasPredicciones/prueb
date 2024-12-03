import pandas as pd
import streamlit as st
import io

# Función para cargar los datos desde Google Sheets
@st.cache_data
def cargar_base():
    url = "https://docs.google.com/spreadsheets/d/1Gd1NBBrSSQg5J8vSv-bZXyou3UX609Jd/export?format=xlsx"
    try:
        base = pd.read_excel(url)
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

# Configuración de la app
st.title("Consulta de Artículos y Lotes")

# Cargar la base de datos
base_df = cargar_base()

if base_df is not None:
    # Entrada del código de artículo
    codigo = st.text_input('Ingrese el código del artículo:')

    if codigo:
        # Filtrar los lotes del código de artículo ingresado
        search_results = base_df[base_df['codarticulo'].str.contains(codigo, case=False, na=False)]

        if not search_results.empty:
            # Selección de lotes
            lotes = search_results['lote'].dropna().unique().tolist()
            lotes.append('Otro')  # Opción para agregar un nuevo lote
            lote_seleccionado = st.selectbox('Seleccione un lote', lotes)

            # Campo para ingresar un nuevo lote
            if lote_seleccionado == 'Otro':
                nuevo_lote = st.text_input('Ingrese el nuevo número de lote:')
            else:
                nuevo_lote = lote_seleccionado

            # Campo opcional para ingresar la cantidad
            cantidad = st.text_input('Ingrese la cantidad (opcional):')

            # Guardar la selección en Excel
            if st.button('Guardar consulta'):
                if not nuevo_lote:  # Validar que se ingrese un lote válido
                    st.error("Debe ingresar un número de lote válido.")
                else:
                    # Crear un DataFrame con los datos seleccionados
                    consulta_data = {
                        'codarticulo': [codigo],
                        'lote': [nuevo_lote],
                        'codbarras': [search_results.iloc[0]['codbarras'] if 'codbarras' in search_results.columns else None],
                        'nombre': [search_results.iloc[0]['nombre'] if 'nombre' in search_results.columns else None],
                        'presentacion': [search_results.iloc[0]['presentacion'] if 'presentacion' in search_results.columns else None],
                        'vencimiento': [search_results.iloc[0]['vencimiento'] if 'vencimiento' in search_results.columns else None],
                        'cantidad': [cantidad if cantidad else None]
                    }

                    consulta_df = pd.DataFrame(consulta_data)

                    # Generar archivo Excel
                    consultas_excel = convertir_a_excel(consulta_df)

                    # Proveer opción de descarga
                    st.success("Consulta guardada con éxito!")
                    st.download_button(
                        label="Descargar Excel con la consulta guardada",
                        data=consultas_excel,
                        file_name='consulta_guardada.xlsx',
                        mime="application/vnd.ms-excel"
                    )
        else:
            st.error("Código de artículo no encontrado en la base de datos.")
else:
    st.error("No se pudo cargar la base de datos. Verifica la URL o el formato del archivo.")
