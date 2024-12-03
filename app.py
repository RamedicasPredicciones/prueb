import pandas as pd
import streamlit as st
import io

# Función para cargar la base de datos desde el enlace proporcionado
@st.cache_data
def cargar_base():
    url_base = "https://docs.google.com/spreadsheets/d/1Gd1NBBrSSQg5J8vSv-bZXyou3UX609Jd/export?format=xlsx"
    try:
        response = requests.get(url_base, verify=False)
        if response.status_code == 200:
            base_df = pd.read_excel(response.content)
            base_df.columns = base_df.columns.str.lower().str.strip()
            return base_df
        else:
            st.error("No se pudo cargar la base de datos. Verifica el enlace.")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error en la conexión: {e}")
        return None

# Función para guardar los datos seleccionados en un archivo Excel
def convertir_a_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Consultas")
    output.seek(0)
    return output.getvalue()

# Configuración de la página
st.title("Consulta de Artículos y Lotes")

# Cargar la base de datos
base_df = cargar_base()

if base_df is not None:
    # Formulario de búsqueda del código de artículo
    codigo = st.text_input('Ingrese el código del artículo:')

    if codigo:
        # Filtrar la base por el código de artículo ingresado
        search_results = base_df[base_df['codarticulo'].str.contains(codigo, case=False, na=False)]

        if not search_results.empty:
            # Mostrar los lotes disponibles para el código de artículo ingresado
            lotes = search_results['lote'].unique().tolist()
            lotes.append('Otro')  # Agregar la opción de "Otro" para escribir un nuevo lote
            lote_seleccionado = st.selectbox('Seleccione un lote', lotes)

            # Si el lote seleccionado es "Otro", permitir escribir uno nuevo
            if lote_seleccionado == 'Otro':
                nuevo_lote = st.text_input('Ingrese el nuevo número de lote:')
            else:
                nuevo_lote = lote_seleccionado

            # Campo para ingresar la cantidad (opcional)
            cantidad = st.text_input('Ingrese la cantidad (opcional):')

            # Botón para guardar la consulta
            if st.button('Guardar consulta'):
                if not nuevo_lote:  # Verificar si el nuevo lote está vacío
                    st.error("Debe ingresar un número de lote válido.")
                else:
                    # Obtener la primera fila correspondiente al código para extraer los datos
                    selected_row = search_results.iloc[0]

                    # Crear un DataFrame con los datos seleccionados
                    consulta_data = {
                        'codarticulo': [codigo],
                        'lote': [nuevo_lote],
                        'codbarras': [selected_row.get('codbarras')],
                        'Nombre': [selected_row.get('nombre')],
                        'presentacion': [selected_row.get('presentacion')],
                        'vencimiento': [selected_row.get('vencimiento')],
                        'cantidad': [cantidad]
                    }

                    consulta_df = pd.DataFrame(consulta_data)

                    # Crear archivo Excel en memoria
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
