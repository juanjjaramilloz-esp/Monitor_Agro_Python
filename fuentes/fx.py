"""
Fuente: tipos de cambio USD/moneda local.

Contrato de salida (ver CLAUDE.md, sección 4):
    fecha    : date
    pais     : str  — código ISO3
    variable : str  — "fx_usd_local"
    valor    : float
    unidad   : str  — "local/USD"
    fuente   : str  — "frankfurter" | "yfinance"

Limitación conocida (pendiente de validar en Fase 1a): la API Frankfurter/BCE
no cubre COP, PEN ni HNL. Para esas monedas se usará yfinance como respaldo.
"""

import pandas as pd


COLUMNAS = ["fecha", "pais", "variable", "valor", "unidad", "fuente"]


def obtener() -> pd.DataFrame:
    """Devuelve tipos de cambio USD→moneda local para cada país en config.PAISES."""
    return pd.DataFrame(columns=COLUMNAS)


if __name__ == "__main__":
    df = obtener()
    print("fuentes.fx — stub Fase 0")
    print(f"  shape : {df.shape}")
    print(f"  cols  : {list(df.columns)}")
    print(df.head())
