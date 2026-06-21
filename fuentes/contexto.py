"""
Fuente: indicadores macroeconómicos (Banco Mundial, sin key, frecuencia anual).

Contrato de salida (ver CLAUDE.md, sección 4):
    fecha    : date  — 1 de enero del año del dato
    pais     : str   — código ISO3
    variable : str   — p. ej. "pib_per_capita", "inflacion_anual"
    valor    : float
    unidad   : str   — p. ej. "USD", "%"
    fuente   : str   — "banco_mundial"

Limitación: es un telón de fondo anual; nunca usar como dato que "cambia"
semana a semana. Solo se incorpora en la Fase 7.
"""

import pandas as pd


COLUMNAS = ["fecha", "pais", "variable", "valor", "unidad", "fuente"]


def obtener() -> pd.DataFrame:
    """Devuelve indicadores macro anuales del Banco Mundial por país."""
    return pd.DataFrame(columns=COLUMNAS)


if __name__ == "__main__":
    df = obtener()
    print("fuentes.contexto — stub Fase 0")
    print(f"  shape : {df.shape}")
    print(f"  cols  : {list(df.columns)}")
    print(df.head())
