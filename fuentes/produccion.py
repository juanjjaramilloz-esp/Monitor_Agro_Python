"""
Fuente: producción nacional mensual de café registrada por la FNC.

Contrato de salida (ver CLAUDE.md, sección 4):
    fecha    : date  — primer día del mes publicado por la FNC
    geografia: str   — "COLOMBIA"
    variable : str   — "produccion_nacional"
    valor    : float — producción mensual
    unidad   : str   — "miles_sacos_60kg"
    fuente   : str   — "FNC"

La página de Estadísticas Cafeteras enlaza el Excel "Precios, área y
producción de café". La hoja de producción contiene una observación por mes
en miles de sacos de 60 kg de café verde equivalente.

Limitación conocida: la localización y estructura del Excel dependen de una
página y un archivo publicados por la FNC que pueden cambiar sin aviso. Si la
descarga o el parseo fallan, se devuelve un DataFrame vacío con las columnas
correctas.
"""

import unicodedata
from datetime import date
from io import BytesIO
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

from config import (
    FNC_COLUMNA_FECHA_PRODUCCION,
    FNC_COLUMNA_VALOR_PRODUCCION,
    FNC_FILA_ENCABEZADO_PRODUCCION,
    FNC_PATRON_ARCHIVO_HISTORICO,
    FNC_PREFIJO_HOJA_PRODUCCION_MENSUAL,
    GEOGRAFIA_PAIS,
    URL_PRECIO_INTERNO_FNC,
)


COLUMNAS = ["fecha", "geografia", "variable", "valor", "unidad", "fuente"]
_CABECERAS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _sin_tildes(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", texto)
    return "".join(caracter for caracter in normalizado if not unicodedata.combining(caracter))


def _buscar_url_excel(sopa: BeautifulSoup) -> str | None:
    """Encuentra el descargable oficial de precios, área y producción."""
    candidatos = []
    for enlace in sopa.find_all("a", href=True):
        href = str(enlace["href"])
        if FNC_PATRON_ARCHIVO_HISTORICO in href and ".xlsx" in href.lower():
            candidatos.append(urljoin(URL_PRECIO_INTERNO_FNC, href))
    return candidatos[-1] if candidatos else None


def _normalizar(
    tabla: pd.DataFrame,
    desde: date | None = None,
    hasta: date | None = None,
) -> pd.DataFrame:
    """Adapta la hoja mensual al contrato numérico sin rellenar meses."""
    requeridas = {FNC_COLUMNA_FECHA_PRODUCCION, FNC_COLUMNA_VALOR_PRODUCCION}
    if not requeridas.issubset(tabla.columns):
        return pd.DataFrame(columns=COLUMNAS)

    fechas = pd.to_datetime(tabla[FNC_COLUMNA_FECHA_PRODUCCION], errors="coerce").dt.date
    valores = pd.to_numeric(tabla[FNC_COLUMNA_VALOR_PRODUCCION], errors="coerce")
    valido = fechas.notna() & valores.notna()
    if desde is not None and hasta is not None:
        valido &= fechas.between(desde, hasta)

    resultado = pd.DataFrame(
        {
            "fecha": fechas[valido],
            "geografia": GEOGRAFIA_PAIS,
            "variable": "produccion_nacional",
            "valor": valores[valido].astype(float),
            "unidad": "miles_sacos_60kg",
            "fuente": "FNC",
        }
    )
    return (
        resultado.drop_duplicates(subset=["fecha"], keep="last")
        .sort_values("fecha")
        .reset_index(drop=True)[COLUMNAS]
    )


def obtener(
    desde: date | None = None,
    hasta: date | None = None,
) -> pd.DataFrame:
    """Devuelve el último mes disponible o la serie mensual del rango solicitado."""
    if (desde is None) != (hasta is None):
        raise ValueError("produccion: desde y hasta deben proporcionarse juntos")
    if desde is not None and hasta is not None and desde > hasta:
        raise ValueError("produccion: desde no puede ser posterior a hasta")

    try:
        respuesta_pagina = requests.get(
            URL_PRECIO_INTERNO_FNC,
            headers=_CABECERAS,
            timeout=30,
        )
        respuesta_pagina.raise_for_status()
        sopa = BeautifulSoup(respuesta_pagina.text, "html.parser")
        url_excel = _buscar_url_excel(sopa)
        if url_excel is None:
            print("  AVISO: no se encontró el Excel de producción FNC.")
            return pd.DataFrame(columns=COLUMNAS)

        respuesta_excel = requests.get(url_excel, headers=_CABECERAS, timeout=60)
        respuesta_excel.raise_for_status()
        archivo = BytesIO(respuesta_excel.content)
        excel = pd.ExcelFile(archivo)
        prefijo = _sin_tildes(FNC_PREFIJO_HOJA_PRODUCCION_MENSUAL).lower()
        hoja = next(
            (
                nombre
                for nombre in excel.sheet_names
                if _sin_tildes(nombre.strip()).lower().startswith(prefijo)
            ),
            None,
        )
        if hoja is None:
            print("  AVISO: el Excel FNC no contiene la hoja mensual esperada.")
            return pd.DataFrame(columns=COLUMNAS)

        archivo.seek(0)
        tabla = pd.read_excel(
            archivo,
            sheet_name=hoja,
            header=FNC_FILA_ENCABEZADO_PRODUCCION,
            usecols=[FNC_COLUMNA_FECHA_PRODUCCION, FNC_COLUMNA_VALOR_PRODUCCION],
        )
        resultado = _normalizar(tabla, desde, hasta)
        if desde is None and hasta is None:
            return resultado.tail(1).reset_index(drop=True)
        return resultado
    except Exception as error:
        print(f"  AVISO: error al obtener producción FNC: {error}")
        return pd.DataFrame(columns=COLUMNAS)


if __name__ == "__main__":
    df = obtener()
    print("fuentes.produccion - resultado")
    print(f"  shape : {df.shape}")
    print(f"  tipos :\n{df.dtypes}")
    print(f"\n{df.head()}")
