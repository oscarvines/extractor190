import streamlit as st
import pandas as pd
import io
from extractor import extraer_datos_190
from st_supabase_connection import SupabaseConnection

st.set_page_config(page_title="Lector AEAT 190", layout="wide", page_icon="📂")

st.title("🚀 Extractor Modelo 190 Profesional")

# --- INICIALIZACIÓN DEL ESTADO ---
if 'datos_acumulados' not in st.session_state:
    st.session_state.datos_acumulados = []

# --- BARRA LATERAL (Configuración y Datos del Cliente) ---
with st.sidebar:
    st.header("1. Carga de Archivos")
    uploaded_files = st.file_uploader(
        "Selecciona los PDFs del Modelo 190", 
        type="pdf", 
        accept_multiple_files=True
    )
    
    st.divider()
    st.header("2. Identificación del Cliente")
    # .strip().upper() asegura que los datos entren limpios a la BD
    cliente_nombre = st.text_input("Nombre de la Empresa:").strip().upper()
    cliente_nif = st.text_input("NIF de la Empresa:").strip().upper()
    
    st.divider()
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
                    temp_results.extend(datos)
                except Exception as e:
                    st.error(f"Error en {file.name}: {e}")
            st.session_state.datos_acumulados = temp_results
            st.success(f"¡Hecho! {len(temp_results)} registros listos.")
    else:
        st.warning("Sube archivos primero.")

# --- SECCIÓN DE FILTROS Y BASE DE DATOS ---
if st.session_state.datos_acumulados:
    df = pd.DataFrame(st.session_state.datos_acumulados)
    
    st.divider()
    st.subheader("🎯 Filtros de Búsqueda")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        claves_disponibles = sorted(df['Clave'].unique())
        claves_sel = st.multiselect("Filtrar por Clave:", options=claves_disponibles)
    
    df_temp = df[df['Clave'].isin(claves_sel)] if claves_sel else df
    
    with col2:
        nombres_disponibles = sorted(df_temp['Nombre'].unique())
        nombres_sel = st.multiselect("Buscar/Seleccionar Nombres:", options=nombres_disponibles)

    df_final = df_temp[df_temp['Nombre'].isin(nombres_sel)] if nombres_sel else df_temp
    
    st.write(f"Mostrando {len(df_final)} registros.")
    st.dataframe(df_final, use_container_width=True)

    # Botón Descarga Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False, sheet_name='Resultado_190')
    
    st.download_button(
        label="📥 Descargar Excel Filtrado",
        data=output.getvalue(),
        file_name="extraccion_190_filtrada.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- BLOQUE DE CONEXIÓN A SUPABASE ---
    st.divider()
    st.subheader("💾 Almacenamiento en Base de Datos Central")
    
    anualidad = st.selectbox(
        "📅 Selecciona el año del Modelo 190:",
        options=[2026, 2025, 2024, 2023],
        index=1
    )
    
    conn = st.connection("supabase", type=SupabaseConnection)

    if st.button("📤 Enviar estos datos a la BD General"):
        # Validación: Impedir envío si no hay datos del cliente
        if not cliente_nombre or not cliente_nif:
            st.error("⚠️ Error: Debes indicar el Nombre y el NIF de la empresa en la barra lateral.")
        else:
            with st.spinner("Sincronizando con Supabase..."):
                try:
                    df_db = df_final.copy()
                    
                    # Renombrar columnas para que coincidan con la tabla SQL
                    df_db = df_db.rename(columns={
                        "NIF": "nif",
                        "Nombre": "nombre",
                        "Clave": "clave",
                        "Subclave": "subclave",
                        "Dinerarias NO IL": "dinerarias_no_il",
                        "Especie NO IL": "especie_no_il",
                        "Dinerarias IL": "dinerarias_il",
                        "Especie IL": "especie_il",
                        "Archivo": "archivo_origen"
                    })
                    
                    # Inyectar datos del cliente y ejercicio
                    df_db['ejercicio'] = anualidad 
                    df_db['cliente'] = cliente_nombre
                    df_db['nif_empresa'] = cliente_nif
                    
                    # Ejecutar inserción
                    datos_dict = df_db.to_dict(orient='records')
                    conn.table("modelo_190_central").insert(datos_dict).execute()
                    
                    st.success(f"✅ ¡Éxito! Datos de {cliente_nombre} ({anualidad}) guardados correctamente.")
                except Exception as e:
                    st.error(f"Error crítico al guardar en la base de datos: {e}")
else:
    st.info("Sube los archivos y pulsa 'Procesar' para empezar.")