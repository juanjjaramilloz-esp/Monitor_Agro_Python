"""
Fuente: precio interno de referencia de la FNC (Colombia).

Contrato de salida (ver CLAUDE.md, sección 4):
    fecha    : date  — fecha que publica la FNC junto al precio
    geografia: str   — "COLOMBIA"
    variable : str   — "precio_interno_referencia"
    valor    : int   — precio en COP por carga de 125 kg (entero)
    unidad   : str   — "COP/carga_125kg"
    fuente   : str   — "FNC"

Se raspa la página de estadísticas cafeteras de la Federación Nacional de
Cafeteros. El HTML lo entrega el servidor (no requiere JS): la página expone
el precio en el menú de cabecera ("Precio interno de referencia: $X.XXX.XXX")
y la fecha en un bloque "Fecha: AAAA-MM-DD".

Limitación conocida (misma fragilidad declarada que el café): esto es
scraping de una página que puede cambiar su maquetación sin aviso. Si la
descarga o el parseo fallan, se devuelve un DataFrame vacío con las columnas
correctas (regla del contrato), nunca una excepción sin manejar.

OJO con el formato colombiano: el valor viene como "$2.110.000". El punto es
separador de MILES, no decimal. Se limpia quitando "$" y los puntos para
obtener el entero 2110000. Interpretarlo como float decimal sería un bug.
"""

import re
from datetime import date
from io import BytesIO
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

from config import (
    FNC_COLUMNA_FECHA_HISTORICO,
    FNC_COLUMNA_PRECIO_HISTORICO,
    FNC_FILA_ENCABEZADO_HISTORICO,
    FNC_PATRON_ARCHIVO_HISTORICO,
    FNC_PREFIJO_HOJA_PRECIO_DIARIO,
    GEOGRAFIA_PAIS,
    URL_PRECIO_INTERNO_FNC,
)

COLUMNAS = ["fecha", "geografia", "variable", "valor", "unidad", "fuente"]

# Cabecera de navegador: algunos WAF rechazan el User-Agent por defecto de requests.
_CABECERAS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# Banda de plausibilidad para el precio (COP/carga). Defiende contra el bug
# clásico de leer "$2.110.000" como 2.11: ese valor caería fuera de la banda.
_PRECIO_MIN = 500_000
_PRECIO_MAX = 10_000_000


def _parsear_precio(texto: str) -> int | None:
    """Extrae 'Precio interno de referencia: $X.XXX.XXX' → entero en COP."""
    coincidencia = re.search(
        r"Precio interno de referencia:\s*\$\s*([\d\.]+)", texto
    )
    if not coincidencia:
        return None
    crudo = coincidencia.group(1)
    # El punto es separador de miles en formato colombiano: se elimina.
    entero = int(crudo.replace(".", ""))
    if not (_PRECIO_MIN <= entero <= _PRECIO_MAX):
        print(f"  AVISO: precio {entero} fuera de banda plausible; posible cambio de formato.")
        return None
    return entero


def _parsear_fecha(sopa: BeautifulSoup, texto: str) -> date | None:
    """Extrae la fecha que acompaña al precio (bloque 'Fecha: AAAA-MM-DD')."""
    # Vía preferida: la etiqueta <strong>Fecha:</strong> seguida del texto.
    etiqueta = sopa.find("strong", string=re.compile(r"Fecha", re.IGNORECASE))
    if etiqueta and etiqueta.next_sibling:
        candidato = str(etiqueta.next_sibling).strip()
        m = re.search(r"\d{4}-\d{2}-\d{2}", candidato)
        if m:
            return pd.to_datetime(m.group(), format="%Y-%m-%d").date()

    # Respaldo: buscar el patrón en el texto plano.
    m = re.search(r"Fecha:\s*(\d{4}-\d{2}-\d{2})", texto)
    if m:
        return pd.to_datetime(m.group(1), format="%Y-%m-%d").date()
    return None


def _buscar_url_historico(sopa: BeautifulSoup) -> str | None:
    """Encuentra el Excel de precios publicado en la página de estadísticas."""
    candidatos = []
    for enlace in sopa.find_all("a", href=True):
        href = str(enlace["href"])
        if FNC_PATRON_ARCHIVO_HISTORICO in href and ".xlsx" in href.lower():
            candidatos.append(urljoin(URL_PRECIO_INTERNO_FNC, href))
    return candidatos[-1] if candidatos else None


def _normalizar_historico(
    tabla: pd.DataFrame,
    desde: date,
    hasta: date,
) -> pd.DataFrame:
    """Adapta la hoja diaria de la FNC al contrato numérico del proyecto."""
    if not {
        FNC_COLUMNA_FECHA_HISTORICO,
        FNC_COLUMNA_PRECIO_HISTORICO,
    }.issubset(tabla.columns):
        return pd.DataFrame(columns=COLUMNAS)

    fechas = pd.to_datetime(
        tabla[FNC_COLUMNA_FECHA_HISTORICO], errors="coerce"
    ).dt.date
    valores = pd.to_numeric(
        tabla[FNC_COLUMNA_PRECIO_HISTORICO], errors="coerce"
    )
    valido = fechas.notna() & valores.notna() & fechas.between(desde, hasta)

    resultado = pd.DataFrame(
        {
            "fecha": fechas[valido],
            "geografia": GEOGRAFIA_PAIS,
            "variable": "precio_interno_referencia",
            "valor": valores[valido].astype(float),
            "unidad": "COP/carga_125kg",
            "fuente": "FNC",
        }
    )
    return resultado.drop_duplicates(subset=["fecha"], keep="last")[COLUMNAS]


def _obtener_historico(
    sopa: BeautifulSoup,
    desde: date,
    hasta: date,
) -> pd.DataFrame:
    url_historico = _buscar_url_historico(sopa)
    if url_historico is None:
        print("  AVISO: no se encontró el Excel histórico de precios FNC.")
        return pd.DataFrame(columns=COLUMNAS)

    respuesta = requests.get(url_historico, headers=_CABECERAS, timeout=60)
    respuesta.raise_for_status()
    archivo = BytesIO(respuesta.content)
    excel = pd.ExcelFile(archivo)
    hoja = next(
        (
            nombre
            for nombre in excel.sheet_names
            if nombre.strip().startswith(FNC_PREFIJO_HOJA_PRECIO_DIARIO)
        ),
        None,
    )
    if hoja is None:
        print("  AVISO: el Excel FNC no contiene la hoja diaria esperada.")
        return pd.DataFrame(columns=COLUMNAS)

    archivo.seek(0)
    tabla = pd.read_excel(
        archivo,
        sheet_name=hoja,
        header=FNC_FILA_ENCABEZADO_HISTORICO,
        usecols=[FNC_COLUMNA_FECHA_HISTORICO, FNC_COLUMNA_PRECIO_HISTORICO],
    )
    return _normalizar_historico(tabla, desde, hasta)


def obtener(
    desde: date | None = None,
    hasta: date | None = None,
) -> pd.DataFrame:
    """Devuelve el precio FNC reciente o su serie diaria histórica."""
    if (desde is None) != (hasta is None):
        raise ValueError("precio_interno: desde y hasta deben proporcionarse juntos")
    if desde is not None and hasta is not None and desde > hasta:
        raise ValueError("precio_interno: desde no puede ser posterior a hasta")

    try:
        respuesta = requests.get(URL_PRECIO_INTERNO_FNC, headers=_CABECERAS, timeout=30)
        respuesta.raise_for_status()

        sopa = BeautifulSoup(respuesta.text, "html.parser")
        if desde is not None and hasta is not None:
            return _obtener_historico(sopa, desde, hasta)

        texto = sopa.get_text(separator=" ")

        valor = _parsear_precio(texto)
        fecha_dato = _parsear_fecha(sopa, texto)

        if valor is None or fecha_dato is None:
            print("  AVISO: no se pudo ubicar precio o fecha en la página FNC.")
            return pd.DataFrame(columns=COLUMNAS)

        fila = {
            "fecha": fecha_dato,
            "geografia": GEOGRAFIA_PAIS,
            "variable": "precio_interno_referencia",
            "valor": valor,
            "unidad": "COP/carga_125kg",
            "fuente": "FNC",
        }
        return pd.DataFrame([fila], columns=COLUMNAS)

    except Exception as e:
        print(f"  AVISO: error al raspar la página FNC: {e}")
        return pd.DataFrame(columns=COLUMNAS)


if __name__ == "__main__":
    df = obtener()
    print("fuentes.precio_interno - resultado")
    print(f"  shape : {df.shape}")
    print(f"  tipos :\n{df.dtypes}")
    print(f"\n{df.head()}")
