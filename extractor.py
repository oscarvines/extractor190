import pdfplumber
import pandas as pd
import re
import os

def limpiar_monto(texto):
    if not texto: return 0.0
    # Eliminamos cualquier carácter no numérico excepto punto y coma
    limpio = re.sub(r'[^0-9,.]', '', texto)
    if not limpio: return 0.0
    limpio = limpio.replace('.', '').replace(',', '.')
    try:
        return float(limpio)
    except:
        return 0.0

def extraer_por_instancia(bloque, etiqueta, instancia):
    """
    Busca la 1ª o 2ª vez que aparece una etiqueta y captura el número posterior.
    """
    try:
        # Buscamos todas las apariciones de la etiqueta (ej: 'Valoración')
        matches = [m.start() for m in re.finditer(re.escape(etiqueta), bloque)]
        
        if len(matches) >= instancia:
            punto_inicio = matches[instancia-1]
            # Ampliamos el rango a 200 caracteres para asegurar que llegamos al número
            fragmento = bloque[punto_inicio:punto_inicio+200]
            
            # Buscamos el patrón numérico xx.xxx,xx
            num_match = re.search(r'(\d{1,3}(\.\d{3})*,\d{2})', fragmento)
            if num_match:
                return limpiar_monto(num_match.group(1))
    except:
        pass
    return 0.0

def extraer_datos_190(file_object):
    """
    Versión compatible con Streamlit: acepta tanto rutas de archivos (str) 
    como objetos de archivo en memoria (UploadedFile).
    """
    resultados = []
    
    # Manejo del nombre del archivo según el origen (Streamlit o Local)
    if hasattr(file_object, 'name'):
        nombre_archivo = file_object.name
    else:
        nombre_archivo = os.path.basename(file_object)
    
    # Abrimos el PDF directamente desde el objeto (ruta o memoria)
    with pdfplumber.open(file_object) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if not texto: continue
            
            # Separamos por cada perceptor
            bloques = re.split(r'Percepción\s+\d+', texto)
            
            for bloque in bloques[1:]:
                # Identificación (NIF + Nombre)
                match_id = re.search(r'([0-9]{8}[A-Z])\s+(.*?)\s+(\d{2})', bloque)
                if not match_id: continue
                
                nif = match_id.group(1)
                nombre = match_id.group(2).strip()
                
                # --- ASIGNACIÓN POR ORDEN DE APARICIÓN ---
                
                # 1. Dinerarias NO IL -> Primera vez que sale "Percepción íntegra"
                d_no_il = extraer_por_instancia(bloque, "Percepción íntegra", 1)
                
                # 2. Especie NO IL -> Primera vez que sale "Valoración"
                e_no_il = extraer_por_instancia(bloque, "Valoración", 1)
                
                # 3. Dinerarias IL -> Segunda vez que sale "Percepción íntegra"
                d_il = extraer_por_instancia(bloque, "Percepción íntegra", 2)
                
                # 4. Especie IL -> Segunda vez que sale "Valoración"
                e_il = extraer_por_instancia(bloque, "Valoración", 2)

                resultados.append({
                    "Archivo": nombre_archivo,
                    "NIF": nif,
                    "Nombre": nombre,
                    "Dinerarias NO IL": d_no_il,
                    "Especie NO IL": e_no_il,
                    "Dinerarias IL": d_il,
                    "Especie IL": e_il
                })
    return resultados

# Nota: Hemos eliminado el bucle final 'os.listdir()' para evitar errores 
# de permisos y rutas en el servidor de Streamlit Cloud.