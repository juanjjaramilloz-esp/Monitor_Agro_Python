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

import pandas as pd
import requests
from bs4 import BeautifulSoup

from config import URL_PRECIO_INTERNO_FNC

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


def obtener() -> pd.DataFrame:
    """Devuelve el precio interno de referencia de la FNC (una sola fila)."""
    try:
        respuesta = requests.get(URL_PRECIO_INTERNO_FNC, headers=_CABECERAS, timeout=30)
        respuesta.raise_for_status()

        sopa = BeautifulSoup(respuesta.text, "html.parser")
        texto = sopa.get_text(separator=" ")

        valor = _parsear_precio(texto)
        fecha_dato = _parsear_fecha(sopa, texto)

        if valor is None or fecha_dato is None:
            print("  AVISO: no se pudo ubicar precio o fecha en la página FNC.")
            return pd.DataFrame(columns=COLUMNAS)

        fila = {
            "fecha": fecha_dato,
            "geografia": "COLOMBIA",
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
