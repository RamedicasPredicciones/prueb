import sqlite3

# Crear o conectar a la base de datos SQLite
def crear_conexion():
    conn = sqlite3.connect("consultas.db")
    return conn

# Función para guardar los datos en SQLite
def guardar_en_db(consulta_data):
    conn = crear_conexion()
    cursor = conn.cursor()

    # Crear la tabla si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultas (
            codarticulo TEXT,
            articulo TEXT,
            lote TEXT,
            codbarras TEXT,
            presentacion TEXT,
            vencimiento TEXT,
            cantidad TEXT,
            bodega TEXT,
            novedad TEXT,
            usuario TEXT,
            lab TEXT
        )
    """)
    cursor.execute("""
        INSERT INTO consultas (codarticulo, articulo, lote, codbarras, presentacion, vencimiento, cantidad, bodega, novedad, usuario, lab)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (consulta_data['codarticulo'], consulta_data['articulo'], consulta_data['lote'], consulta_data['codbarras'],
          consulta_data['presentacion'], consulta_data['vencimiento'], consulta_data['cantidad'], consulta_data['bodega'],
          consulta_data['novedad'], consulta_data['usuario'], consulta_data['lab']))
    conn.commit()
    conn.close()

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

        # Guardar las consultas en la base de datos SQLite
        guardar_en_db(consulta_data)
