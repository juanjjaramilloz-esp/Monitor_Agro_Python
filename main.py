"""
Orquestador del Monitor Agro Colombia.

Corre las fases en orden. Por ahora verifica que los módulos importan
correctamente y que cada obtener() cumple el contrato de columnas.
"""

import pandas as pd

from fuentes import cafe, clima, contexto, fx, noticias, precio_interno
from procesar import score, unir
from reporte import generar

# Columnas esperadas por el contrato numérico (CLAUDE.md, sección 4)
COLS_NUMERICAS = {"fecha", "geografia", "variable", "valor", "unidad", "fuente"}
COLS_NOTICIAS = {"fecha", "geografia", "titulo", "url", "fuente", "idioma", "tono", "categoria"}


def _validar(nombre: str, df: pd.DataFrame, esperadas: set[str]) -> None:
    faltantes = esperadas - set(df.columns)
    if faltantes:
        raise ValueError(f"{nombre}: faltan columnas {faltantes}")
    print(f"  OK {nombre:12s}  shape={df.shape}  cols OK")


def main() -> None:
    print("=== Monitor Agro Colombia — verificación de contratos ===\n")

    _validar("fx",             fx.obtener(),             COLS_NUMERICAS)
    _validar("cafe",           cafe.obtener(),           COLS_NUMERICAS)
    _validar("precio_interno", precio_interno.obtener(), COLS_NUMERICAS)
    _validar("clima",          clima.obtener(),          COLS_NUMERICAS)
    _validar("noticias",       noticias.obtener(),       COLS_NOTICIAS)
    _validar("contexto",       contexto.obtener(),       COLS_NUMERICAS)

    print("\nTodas las fuentes cumplen el contrato de columnas.")


if __name__ == "__main__":
    main()
