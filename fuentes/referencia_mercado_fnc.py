"""
Referencia diaria coherente publicada por la FNC para calcular el precio interno.

La página de la FNC publica juntos, para una misma fecha, el precio interno,
el cierre de Coffee C y la tasa de cambio usados como referencias. Esta fuente
se conserva separada de Yahoo Finance porque mezclar cierres de proveedores y
horas distintas introduce error en la calibración del simulador.
"""

import re
from datetime import date

import pandas as pd
import requests
from bs4 import BeautifulSoup

from config import GEOGRAFIA_PAIS, URL_PRECIO_INTERNO_FNC


COLUMNAS = ["fecha", "geografia", "variable", "valor", "unidad", "fuente"]
_CABECERAS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _numero_colombiano(texto: str) -> float:
    """Convierte 3.435,99 o 276,40 al valor numérico correspondiente."""
    limpio = texto.strip().replace(".", "").replace(",", ".")
    return float(limpio)


def _parsear(texto: str) -> pd.DataFrame:
    """Extrae el trío FNC, Coffee C y TRM con la primera fecha publicada."""
    patrones = {
        "precio_interno_referencia": (
            r"Precio interno de referencia:\s*\$\s*([\d\.]+)",
            "COP/carga_125kg",
        ),
        "precio_cafe_fnc_calculo": (
            r"Bolsa de NY:\s*\$?\s*([\d\.,]+)",
            "USc/lb",
        ),
        "fx_fnc_calculo": (
            r"Tasa de cambio:\s*([\d\.,]+)",
            "COP/USD",
        ),
    }
    fecha_encontrada = re.search(r"Fecha:\s*(\d{4}-\d{2}-\d{2})", texto)
    if not fecha_encontrada:
        return pd.DataFrame(columns=COLUMNAS)
    fecha_dato = pd.to_datetime(fecha_encontrada.group(1)).date()

    filas = []
    for variable, (patron, unidad) in patrones.items():
        coincidencia = re.search(patron, texto, flags=re.IGNORECASE)
        if not coincidencia:
            return pd.DataFrame(columns=COLUMNAS)
        valor = _numero_colombiano(coincidencia.group(1))
        filas.append(
            {
                "fecha": fecha_dato,
                "geografia": GEOGRAFIA_PAIS,
                "variable": variable,
                "valor": valor,
                "unidad": unidad,
                "fuente": "FNC",
            }
        )
    return pd.DataFrame(filas, columns=COLUMNAS)


def obtener() -> pd.DataFrame:
    """Devuelve las tres referencias del día publicadas conjuntamente por la FNC."""
    try:
        respuesta = requests.get(URL_PRECIO_INTERNO_FNC, headers=_CABECERAS, timeout=30)
        respuesta.raise_for_status()
        sopa = BeautifulSoup(respuesta.text, "html.parser")
        return _parsear(sopa.get_text(separator=" "))
    except Exception as error:
        print(f"  AVISO: referencia de mercado FNC no disponible: {error}")
        return pd.DataFrame(columns=COLUMNAS)


if __name__ == "__main__":
    df = obtener()
    print("fuentes.referencia_mercado_fnc - resultado")
    print(f"  shape : {df.shape}")
    print(f"  tipos :\n{df.dtypes}")
    print(f"\n{df.head()}")
