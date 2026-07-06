"""
Fuente: volumen mensual de exportaciones colombianas de café publicado por la FNC.

La salida usa el contrato numérico común y expresa el volumen en miles de sacos
de 60 kg de café verde equivalente. No se rellenan meses faltantes.
"""

from datetime import date
from io import BytesIO

import pandas as pd
from bs4 import BeautifulSoup

from config import (
    FNC_COLUMNA_FECHA_EXPORTACIONES,
    FNC_COLUMNA_VALOR_EXPORTACIONES,
    FNC_FILA_ENCABEZADO_EXPORTACIONES,
    FNC_PATRON_ARCHIVO_EXPORTACIONES,
    FNC_PREFIJO_HOJA_EXPORTACIONES_MENSUALES,
    GEOGRAFIA_PAIS,
    URL_PRECIO_INTERNO_FNC,
)
from fuentes import _fnc_comun

COLUMNAS = ["fecha", "geografia", "variable", "valor", "unidad", "fuente"]


def _normalizar(
    tabla: pd.DataFrame,
    desde: date | None = None,
    hasta: date | None = None,
) -> pd.DataFrame:
    """Adapta la hoja mensual al contrato numérico sin rellenar meses."""
    requeridas = {
        FNC_COLUMNA_FECHA_EXPORTACIONES,
        FNC_COLUMNA_VALOR_EXPORTACIONES,
    }
    if not requeridas.issubset(tabla.columns):
        return pd.DataFrame(columns=COLUMNAS)

    fechas = pd.to_datetime(
        tabla[FNC_COLUMNA_FECHA_EXPORTACIONES], errors="coerce"
    ).dt.date
    valores = pd.to_numeric(
        tabla[FNC_COLUMNA_VALOR_EXPORTACIONES], errors="coerce"
    )
    valido = fechas.notna() & valores.notna()
    if desde is not None and hasta is not None:
        valido &= fechas.between(desde, hasta)

    resultado = pd.DataFrame(
        {
            "fecha": fechas[valido],
            "geografia": GEOGRAFIA_PAIS,
            "variable": "exportaciones_cafe",
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
    """Devuelve el último mes disponible o la serie mensual solicitada."""
    if (desde is None) != (hasta is None):
        raise ValueError("exportaciones: desde y hasta deben proporcionarse juntos")
    if desde is not None and hasta is not None and desde > hasta:
        raise ValueError("exportaciones: desde no puede ser posterior a hasta")

    try:
        html = _fnc_comun.descargar_texto(URL_PRECIO_INTERNO_FNC)
        url_excel = _fnc_comun.buscar_url_excel(
            BeautifulSoup(html, "html.parser"), FNC_PATRON_ARCHIVO_EXPORTACIONES
        )
        if url_excel is None:
            print("  AVISO: no se encontró el Excel de exportaciones FNC.")
            return pd.DataFrame(columns=COLUMNAS)

        archivo = BytesIO(_fnc_comun.descargar_binario(url_excel))
        excel = pd.ExcelFile(archivo)
        hoja = _fnc_comun.buscar_hoja(
            excel.sheet_names, FNC_PREFIJO_HOJA_EXPORTACIONES_MENSUALES
        )
        if hoja is None:
            print("  AVISO: el Excel FNC no contiene la hoja de exportaciones esperada.")
            return pd.DataFrame(columns=COLUMNAS)

        archivo.seek(0)
        tabla = pd.read_excel(
            archivo,
            sheet_name=hoja,
            header=FNC_FILA_ENCABEZADO_EXPORTACIONES,
            usecols=[
                FNC_COLUMNA_FECHA_EXPORTACIONES,
                FNC_COLUMNA_VALOR_EXPORTACIONES,
            ],
        )
        resultado = _normalizar(tabla, desde, hasta)
        if desde is None and hasta is None:
            return resultado.tail(1).reset_index(drop=True)
        return resultado
    except Exception as error:
        print(f"  AVISO: error al obtener exportaciones FNC: {error}")
        return pd.DataFrame(columns=COLUMNAS)


if __name__ == "__main__":
    df = obtener()
    print("fuentes.exportaciones - resultado")
    print(f"  shape : {df.shape}")
    print(f"  tipos :\n{df.dtypes}")
    print(f"\n{df.head()}")
