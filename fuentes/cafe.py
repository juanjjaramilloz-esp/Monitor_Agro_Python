"""
Fuente: precio del café (futuro ICE Coffee C, arábica).

Contrato de salida (ver CLAUDE.md, sección 4):
    fecha    : date
    pais     : str  — "GLOBAL" (precio internacional, no por país)
    variable : str  — "precio_cafe_arabica"
    valor    : float
    unidad   : str  — "USc/lb"
    fuente   : str  — "yfinance"

Limitación conocida: yfinance raspa Yahoo Finance y puede romperse sin aviso.
Alpha Vantage cubre solo frecuencia mensual y requiere API key (.env).
"""

import pandas as pd


COLUMNAS = ["fecha", "pais", "variable", "valor", "unidad", "fuente"]


def obtener() -> pd.DataFrame:
    """Devuelve el precio semanal del café arábica (global)."""
    return pd.DataFrame(columns=COLUMNAS)


if __name__ == "__main__":
    df = obtener()
    print("fuentes.cafe — stub Fase 0")
    print(f"  shape : {df.shape}")
    print(f"  cols  : {list(df.columns)}")
    print(df.head())
