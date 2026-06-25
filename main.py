"""
Orquestador del Monitor Agro Colombia.

Corre las fases en orden. Por ahora verifica que los módulos importan
correctamente y que cada obtener() cumple el contrato de columnas.
"""

import pandas as pd

from fuentes import (
    cafe,
    clima,
    contexto,
    fx,
    noticias,
    precio_interno,
    produccion,
    referencia_mercado_fnc,
)
from procesar import score, unir
from reporte import generar

# Columnas esperadas por el contrato numérico (CLAUDE.md, sección 4)
COLS_NUMERICAS = {"fecha", "geografia", "variable", "valor", "unidad", "fuente"}
COLS_NOTICIAS = {"fecha", "geografia", "titulo", "url", "fuente", "idioma", "tono", "categoria"}


def _validar(nombre: str, df: pd.DataFrame, esperadas: set[str]) -> str:
    faltantes = esperadas - set(df.columns)
    adicionales = set(df.columns) - esperadas
    if faltantes or adicionales:
        raise ValueError(
            f"{nombre}: columnas incorrectas; faltan={faltantes}, "
            f"adicionales={adicionales}"
        )
    if df.empty:
        print(f"  VACIO {nombre:12s}  contrato OK, fuente sin datos")
        return "VACIO"
    fechas = pd.to_datetime(df["fecha"], errors="coerce")
    if fechas.isna().any():
        raise ValueError(f"{nombre}: hay fechas inválidas")
    claves = (
        ["fecha", "geografia", "variable"]
        if "variable" in df.columns
        else ["geografia", "url"]
    )
    if df.duplicated(subset=claves).any():
        raise ValueError(f"{nombre}: hay filas duplicadas")
    if "valor" in df.columns:
        valores = pd.to_numeric(df["valor"], errors="coerce")
        if valores.isna().any():
            raise ValueError(f"{nombre}: hay valores numéricos inválidos")
    print(f"  OK {nombre:12s}  shape={df.shape}  cols OK")
    return "OK"


def main() -> None:
    print("=== Monitor Agro Colombia — verificación de contratos ===\n")

    estados = [
        _validar("fx",             fx.obtener(),             COLS_NUMERICAS),
        _validar("cafe",           cafe.obtener(),           COLS_NUMERICAS),
        _validar("precio_interno", precio_interno.obtener(), COLS_NUMERICAS),
        _validar("referencia_fnc", referencia_mercado_fnc.obtener(), COLS_NUMERICAS),
        _validar("produccion",     produccion.obtener(),     COLS_NUMERICAS),
        _validar("clima",          clima.obtener(),          COLS_NUMERICAS),
        _validar("noticias",       noticias.obtener(),       COLS_NOTICIAS),
    ]
    _validar("contexto", contexto.obtener(), COLS_NUMERICAS)

    vacias = estados.count("VACIO")
    print("\nTodas las fuentes cumplen el contrato de columnas.")
    if vacias:
        print(f"ATENCION: {vacias} fuente(s) activas no entregaron datos.")


if __name__ == "__main__":
    main()
