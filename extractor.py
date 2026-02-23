import pdfplumber
import re
import os


def limpiar_monto(texto):
    if not texto:
        return 0.0
    limpio = re.sub(r"[^0-9,.]", "", texto)
    if not limpio:
        return 0.0
    limpio = limpio.replace(".", "").replace(",", ".")
    try:
        return float(limpio)
    except:
        return 0.0


def extraer_por_instancia(bloque, etiqueta, instancia):
    try:
        matches = [m.start() for m in re.finditer(re.escape(etiqueta), bloque)]
        if len(matches) >= instancia:
            punto_inicio = matches[instancia - 1]
            fragmento = bloque[punto_inicio : punto_inicio + 200]
            num_match = re.search(r"(\d{1,3}(\.\d{3})*,\d{2})", fragmento)
            if num_match:
                return limpiar_monto(num_match.group(1))
    except:
        pass
    return 0.0


def _normaliza_espacios(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _clean_line(s: str) -> str:
    return _normaliza_espacios(s)


def extraer_declarante(texto: str):
    """
    Extrae CIF (NIF) y razón social del declarante.
    Robusto: trabaja por líneas y evita depender de regex multilinea frágil.
    """
    if not texto:
        return None, None

    lines = [_clean_line(l) for l in texto.splitlines()]
    lines = [l for l in lines if l]  # quitar vacías

    # --------------------------
    # 1) CIF declarante
    # --------------------------
    cif = None

    # Buscamos zona donde aparezca "NIF" / "identificación fiscal"
    for i, l in enumerate(lines):
        low = l.lower()
        if "identificación fiscal" in low or "(nif)" in low or " n i f" in low:
            # puede estar en la misma línea o en la siguiente
            cand = re.findall(r"\b([A-Z0-9][0-9A-Z]{7,8})\b", l)
            if not cand and i + 1 < len(lines):
                cand = re.findall(r"\b([A-Z0-9][0-9A-Z]{7,8})\b", lines[i + 1])
            if cand:
                cif = cand[0]
                break

    # Fallback: cerca de "Declarante"
    if not cif:
        for i, l in enumerate(lines):
            if "declarante" in l.lower():
                for j in range(i, min(i + 12, len(lines))):
                    cand = re.findall(r"\b([A-Z0-9][0-9A-Z]{7,8})\b", lines[j])
                    if cand:
                        cif = cand[0]
                        break
                if cif:
                    break

    # --------------------------
    # 2) Empresa declarante
    # --------------------------
    empresa = None
    stop_words = (
        "telemática",
        "telematica",
        "modalidad",
        "nº de justificante",
        "no de justificante",
        "número de justificante",
        "numero de justificante",
        "persona con la que relacionarse",
        "datos de contacto",
    )

    # Caso ideal: encontramos la etiqueta y cogemos la siguiente línea útil
    for i, l in enumerate(lines):
        low = l.lower()
        if ("razón social del declarante" in low) or ("razon social del declarante" in low):
            for j in range(i + 1, min(i + 8, len(lines))):
                cand = lines[j]
                clow = cand.lower()

                if any(sw in clow for sw in stop_words):
                    continue
                if "apellidos y nombre" in clow:
                    continue
                if cif and cif in cand:
                    continue
                # Evita coger cosas tipo "Telemática ... X"
                if "x" == cand.strip().lower():
                    continue

                if len(cand) >= 3:
                    empresa = cand
                    break
            break

    # Fallback: si no está la etiqueta, buscar tras "Declarante"
    if not empresa:
        for i, l in enumerate(lines):
            if l.strip().lower() == "declarante":
                for j in range(i + 1, min(i + 15, len(lines))):
                    cand = lines[j]
                    clow = cand.lower()

                    if any(sw in clow for sw in stop_words):
                        continue
                    if "apellidos y nombre" in clow or "identificación fiscal" in clow or "(nif)" in clow:
                        continue
                    if cif and cif in cand:
                        continue

                    # primera línea razonable con letras
                    if re.search(r"[A-ZÁÉÍÓÚÑ]", cand):
                        empresa = cand
                        break
                if empresa:
                    break

    return cif, empresa


def extraer_datos_190(file_object):
    resultados = []

    if hasattr(file_object, "name"):
        nombre_archivo = file_object.name
    else:
        nombre_archivo = os.path.basename(file_object)

    with pdfplumber.open(file_object) as pdf:

        # 1) Intento principal: página 2 (Hoja Resumen)
        texto_p2 = ""
        if len(pdf.pages) > 1:
            texto_p2 = pdf.pages[1].extract_text() or ""

        cif_empresa, empresa_declarante = extraer_declarante(texto_p2)

        # 2) Fallback: si no sale en p2, probamos en todo el PDF
        if not cif_empresa or not empresa_declarante:
            texto_completo = ""
            for page in pdf.pages:
                texto_completo += (page.extract_text() or "") + "\n"
            cif_f, emp_f = extraer_declarante(texto_completo)
            cif_empresa = cif_empresa or cif_f
            empresa_declarante = empresa_declarante or emp_f

        # 3) Tu extracción por páginas (igual que antes)
        for page in pdf.pages:
            texto = page.extract_text()
            if not texto:
                continue

            bloques = re.split(r"Percepción\s+\d+", texto)

            for bloque in bloques[1:]:
                # NIF/NIE del perceptor
                match_id = re.search(r"([A-Z0-9][0-9A-Z]{7,8})\s+(.*?)\s+(\d{2})", bloque)
                if not match_id:
                    continue

                nif = match_id.group(1)
                nombre = match_id.group(2).strip()

                clave_match = re.search(r"Clave:\s*([A-Z])", bloque)
                clave = clave_match.group(1) if clave_match else ""

                subclave_match = re.search(r"Subclave:\s*(\d{2})", bloque)
                subclave = subclave_match.group(1) if subclave_match else ""

                d_no_il = extraer_por_instancia(bloque, "Percepción íntegra", 1)
                e_no_il = extraer_por_instancia(bloque, "Valoración", 1)
                d_il = extraer_por_instancia(bloque, "Percepción íntegra", 2)
                e_il = extraer_por_instancia(bloque, "Valoración", 2)

                resultados.append(
                    {
                        "Archivo": nombre_archivo,
                        "CIF_EMPRESA": cif_empresa,
                        "EMPRESA": empresa_declarante,
                        "NIF": nif,
                        "Nombre": nombre,
                        "Clave": clave,
                        "Subclave": subclave,
                        "Dinerarias NO IL": d_no_il,
                        "Especie NO IL": e_no_il,
                        "Dinerarias IL": d_il,
                        "Especie IL": e_il,
                    }
                )

    return resultados