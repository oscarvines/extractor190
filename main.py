import streamlit as st
import pandas as pd
import io
# Importamos el nombre exacto de la función que tienes en extractor.py
from extractor import extraer_datos_190

# Configuración de la página
st.set_page_config(page_title="Lector AEAT 190", layout="wide", page_icon="📂")

st.title("🚀 Extractor Modelo 190")
st.markdown("""
Esta aplicación extrae los datos de los perceptores de los archivos PDF del Modelo 190.
""")

# Selector de archivos
uploaded_files = st.file_uploader("Sube tus archivos PDF del Modelo 190", type="pdf", accept_multiple_files=True)

if uploaded_files:
    consolidado = []
    
    # Barra de progreso para feedback visual
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, file in enumerate(uploaded_files):
        status_text.text(f"Procesando: {file.name}")
        
        try:
            # Llamada a la función de tu archivo extractor.py
            datos = extraer_datos_190(file)
            consolidado.extend(datos)
        except Exception as e:
            st.error(f"Error al procesar {file.name}: {e}")
        
        # Actualizar progreso
        progress_bar.progress((i + 1) / len(uploaded_files))

    status_text.text("¡Procesamiento completado!")

    if consolidado:
        df = pd.DataFrame(consolidado)
        
        # Mostrar vista previa de los datos detectados
        st.subheader("Vista previa de los datos")
        st.dataframe(df, use_container_width=True)

        # Crear el archivo Excel en memoria para la descarga
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Perceptores_190')
        
        st.download_button(
            label="📥 Descargar Excel Consolidado",
            data=output.getvalue(),
            file_name="datos_extraidos_modelo_190.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No se encontraron datos de perceptores en los archivos subidos.")