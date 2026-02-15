import streamlit as st
import pandas as pd
import io
from extractor import extraer_datos_190

st.set_page_config(page_title="Lector AEAT 190", layout="wide", page_icon="📂")

st.title("🚀 Extractor Modelo 190 Profesional")

# --- INICIALIZACIÓN DEL ESTADO ---
if 'datos_acumulados' not in st.session_state:
    st.session_state.datos_acumulados = []

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Configuración")
    
    # NUEVO: Cuadro para el año
    anio_input = st.number_input("Año del Modelo:", min_value=2000, max_value=2100, value=2024, step=1, format="%d")
    
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
        with st.spinner("Extrayendo información..."):
            temp_results = []
            for file in uploaded_files:
                try:
                    datos = extraer_datos_190(file)
                    
                    # NUEVO: Añadimos el año a cada registro antes de guardarlo
                    for d in datos:
                        d["Año"] = anio_input
                        
                    temp_results.extend(datos)
                except Exception as e:
                    st.error(f"Error en {file.name}: {e}")
            st.session_state.datos_acumulados = temp_results
            st.success(f"¡Hecho! {len(temp_results)} registros listos.")
    else:
        st.warning("Sube archivos primero.")

# --- SECCIÓN DE FILTROS CRUZADOS ---
if st.session_state.datos_acumulados:
    df = pd.DataFrame(st.session_state.datos_acumulados)
    
    # Reordenamos solo para que el Año sea la primera columna
    if "Año" in df.columns:
        cols = ["Año"] + [c for c in df.columns if c != "Año"]
        df = df[cols]
    
    st.divider()
    st.subheader("🎯 Filtros de Búsqueda")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Filtro de Clave
        claves_disponibles = sorted(df['Clave'].unique())
        claves_sel = st.multiselect("Filtrar por Clave:", options=claves_disponibles)
    
    # Aplicamos primer filtro de clave para que el buscador de nombres sea inteligente
    df_temp = df[df['Clave'].isin(claves_sel)] if claves_sel else df
    
    with col2:
        # Filtro de Nombres (basado en el filtro de clave previo)
        nombres_disponibles = sorted(df_temp['Nombre'].unique())
        nombres_sel = st.multiselect("Buscar/Seleccionar Nombres:", options=nombres_disponibles)

    # Aplicamos filtro final
    df_final = df_temp[df_temp['Nombre'].isin(nombres_sel)] if nombres_sel else df_temp
    
    # Mostrar tabla
    st.write(f"Mostrando {len(df_final)} registros.")
    st.dataframe(df_final, use_container_width=True)

    # Excel dinámico
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False, sheet_name='Resultado_190')
    
    st.download_button(
        label="📥 Descargar Excel Filtrado",
        data=output.getvalue(),
        file_name=f"extraccion_190_{anio_input}.xlsx", # Ahora el nombre del Excel incluye el año
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Sube los archivos y pulsa 'Procesar' para empezar.")