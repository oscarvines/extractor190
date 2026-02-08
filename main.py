import streamlit as st
import pandas as pd
import io
from extractor import extraer_datos_190

st.set_page_config(page_title="Lector AEAT 190", layout="wide", page_icon="📂")

st.title("🚀 Extractor Modelo 190 Profesional")

# --- INICIALIZACIÓN DEL ESTADO ---
# Esto permite que la app "recuerde" los datos aunque subas más archivos
if 'datos_acumulados' not in st.session_state:
    st.session_state.datos_acumulados = []

# --- BARRA LATERAL PARA CARGA Y CONTROL ---
with st.sidebar:
    st.header("Configuración")
    uploaded_files = st.file_uploader(
        "1. Selecciona los PDFs", 
        type="pdf", 
        accept_multiple_files=True
    )
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        boton_procesar = st.button("⚙️ Procesar", use_container_width=True)
    with col_btn2:
        if st.button("🗑️ Limpiar", use_container_width=True):
            st.session_state.datos_acumulados = []
            st.rerun()

# --- LÓGICA DE PROCESAMIENTO ---
if boton_procesar:
    if uploaded_files:
        with st.spinner("Extrayendo información de los PDFs..."):
            temp_results = []
            for file in uploaded_files:
                try:
                    datos = extraer_datos_190(file)
                    temp_results.extend(datos)
                except Exception as e:
                    st.error(f"Error en {file.name}: {e}")
            
            # Guardamos en el estado de la sesión para que no se borre al filtrar
            st.session_state.datos_acumulados = temp_results
            st.success(f"¡Hecho! Se han procesado {len(uploaded_files)} archivos.")
    else:
        st.warning("Por favor, sube algún archivo primero.")

# --- SECCIÓN DE FILTROS Y DESCARGA ---
if st.session_state.datos_acumulados:
    df = pd.DataFrame(st.session_state.datos_acumulados)
    
    st.divider()
    st.subheader("🎯 Selección y Búsqueda")
    
    # Multibúsqueda de nombres
    lista_nombres = sorted(df['Nombre'].unique())
    seleccionados = st.multiselect(
        "Busca y selecciona las personas para el Excel:",
        options=lista_nombres,
        placeholder="Escribe para buscar..."
    )

    # Filtrado dinámico
    df_mostrar = df[df['Nombre'].isin(seleccionados)] if seleccionados else df
    
    st.write(f"Mostrando {len(df_mostrar)} registros.")
    st.dataframe(df_mostrar, use_container_width=True)

    # Excel dinámico
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_mostrar.to_excel(writer, index=False, sheet_name='Resultado_190')
    
    label_boton = "📥 Descargar Selección" if seleccionados else "📥 Descargar Todo"
    st.download_button(
        label=label_boton,
        data=output.getvalue(),
        file_name="extraccion_190.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Sube los archivos en el menú lateral y pulsa 'Procesar'.")