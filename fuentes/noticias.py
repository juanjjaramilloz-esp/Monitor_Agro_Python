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


COLUMNAS = ["fecha", "pais", "titulo", "url", "fuente", "idioma", "tono", "categoria"]


def obtener() -> pd.DataFrame:
    """Devuelve noticias recientes relacionadas con agroexportación por país."""
    return pd.DataFrame(columns=COLUMNAS)


if __name__ == "__main__":
    df = obtener()
    print("fuentes.noticias — stub Fase 0")
    print(f"  shape : {df.shape}")
    print(f"  cols  : {list(df.columns)}")
    print(df.head())
