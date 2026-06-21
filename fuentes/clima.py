"""
Fuente: clima en zonas cafeteras (Open-Meteo, sin key, solo uso no comercial).

Contrato de salida (ver CLAUDE.md, sección 4):
    fecha    : date
    pais     : str  — código ISO3
    variable : str  — "temp_min" | "temp_max" | "precipitacion"
    valor    : float
    unidad   : str  — "°C" | "mm"
    fuente   : str  — "open-meteo"

Las coordenadas de cada zona cafetera se leen de config.PAISES.
"""

import pandas as pd


COLUMNAS = ["fecha", "pais", "variable", "valor", "unidad", "fuente"]


def obtener() -> pd.DataFrame:
    """Devuelve variables climáticas diarias para cada zona cafetera."""
    return pd.DataFrame(columns=COLUMNAS)


if __name__ == "__main__":
    df = obtener()
    print("fuentes.clima — stub Fase 0")
    print(f"  shape : {df.shape}")
    print(f"  cols  : {list(df.columns)}")
    print(df.head())
