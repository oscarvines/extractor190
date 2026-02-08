import streamlit as st
import pandas as pd
import io
# Aquí es donde llamas a la versión que quieras
from extractor import procesar_pdf_190 

st.set_page_config(page_title="Lector AEAT 190", layout="wide")

st.title("🚀 Extractor de Perceptores - Modelo 190")
st.info("Sistema modular: Utilizando motor de extracción v5.0")

uploaded_files = st.file_uploader("Sube tus archivos PDF", type="pdf", accept_multiple_files=True)

if uploaded_files:
    consolidado = []
    for file in uploaded_files:
        # Llamada a la función del otro archivo
        datos = procesar_pdf_190(file)
        consolidado.extend(datos)
    
    if consolidado:
        df = pd.DataFrame(consolidado)
        st.dataframe(df)

        # Preparar descarga
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button(
            label="📊 Descargar Excel",
            data=output.getvalue(),
            file_name="datos_190.xlsx"
        )