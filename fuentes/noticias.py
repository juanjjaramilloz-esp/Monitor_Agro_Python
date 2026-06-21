"""
Fuente: noticias de agroexportación (GDELT DOC 2.0, sin key, multilingüe).

Contrato de salida (ver CLAUDE.md, sección 4 — contrato noticias):
    fecha     : date
    pais      : str   — código ISO3
    titulo    : str
    url       : str
    fuente    : str   — "gdelt"
    idioma    : str
    tono      : float — opcional (puede ser NaN en el stub y Fase 1d)
    categoria : str   — opcional; clasificación por IA añadida en fase posterior

Advertencia: GDELT mezcla fuentes confiables y obscuras. Nunca tomar una
noticia como hecho; usar solo como señal cualitativa.
"""

import pandas as pd
from gdeltdoc import Filters, GdeltDoc

from config import (
    IDIOMA_NOTICIAS,
    NOTICIAS_DIAS_ATRAS,
    NOTICIAS_MAX_REGISTROS,
    PAISES,
    TERMINOS_NOTICIAS,
)


COLUMNAS = ["fecha", "pais", "titulo", "url", "fuente", "idioma", "tono", "categoria"]


def _normalizar_fecha(serie: pd.Series) -> pd.Series:
    """Convierte fechas de GDELT a objetos date; valores invalidos quedan NaN."""
    return pd.to_datetime(serie, errors="coerce", utc=True).dt.date


def _normalizar_articulos(articulos: pd.DataFrame, iso3: str) -> pd.DataFrame:
    """Adapta las columnas de GDELT al contrato de noticias del proyecto."""
    if articulos.empty:
        return pd.DataFrame(columns=COLUMNAS)

    df = pd.DataFrame({
        "fecha": _normalizar_fecha(articulos.get("seendate", pd.Series(dtype=str))),
        "pais": iso3,
        "titulo": articulos.get("title", pd.Series(dtype=str)),
        "url": articulos.get("url", pd.Series(dtype=str)),
        "fuente": "gdelt",
        "idioma": articulos.get("language", pd.Series(dtype=str)),
        "tono": float("nan"),
        "categoria": pd.NA,
    })

    df = df.dropna(subset=["fecha", "titulo", "url"])
    return df[COLUMNAS]


def obtener() -> pd.DataFrame:
    """Devuelve noticias recientes relacionadas con agroexportación por país."""
    filas: list[pd.DataFrame] = []
    cliente = GdeltDoc()

    for pais in PAISES:
        iso3 = pais["iso3"]
        fips = pais["fips"]

        try:
            filtros = Filters(
                timespan=f"{NOTICIAS_DIAS_ATRAS}d",
                keyword=TERMINOS_NOTICIAS,
                country=fips,
                language=IDIOMA_NOTICIAS,
                num_records=NOTICIAS_MAX_REGISTROS,
            )
            articulos = cliente.article_search(filtros)
            filas.append(_normalizar_articulos(articulos, iso3))

        except Exception as e:
            # GDELT puede limitar peticiones o devolver mezclas ruidosas de fuentes.
            # En ese caso mantenemos el contrato y usamos noticias solo como senal.
            print(f"  AVISO: {iso3} - error al consultar GDELT ({type(e).__name__}): {e}")

    if not filas:
        return pd.DataFrame(columns=COLUMNAS)

    resultado = pd.concat(filas, ignore_index=True)
    resultado = resultado.drop_duplicates(subset=["pais", "url"])
    return resultado[COLUMNAS]


if __name__ == "__main__":
    df = obtener()
    print("fuentes.noticias - resultado")
    print(f"  shape : {df.shape}")
    print(f"  tipos :\n{df.dtypes}")
    print(f"\n{df.head(15)}")
