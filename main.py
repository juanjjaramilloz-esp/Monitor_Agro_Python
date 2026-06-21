"""
Orquestador del Monitor Agro LatAm.

Corre las fases en orden. En la Fase 0 solo verifica que los módulos
importan correctamente y que cada obtener() cumple el contrato de columnas.
"""

import pandas as pd

from fuentes import cafe, clima, contexto, fx, noticias
from procesar import score, unir
from reporte import generar

# Columnas esperadas por el contrato numérico (CLAUDE.md, sección 4)
COLS_NUMERICAS = {"fecha", "pais", "variable", "valor", "unidad", "fuente"}
COLS_NOTICIAS = {"fecha", "pais", "titulo", "url", "fuente", "idioma", "tono", "categoria"}


def _validar(nombre: str, df: pd.DataFrame, esperadas: set[str]) -> None:
    faltantes = esperadas - set(df.columns)
    if faltantes:
        raise ValueError(f"{nombre}: faltan columnas {faltantes}")
    print(f"  OK {nombre:12s}  shape={df.shape}  cols OK")


def main() -> None:
    print("=== Monitor Agro LatAm — Fase 0: verificación de stubs ===\n")

    _validar("fx",        fx.obtener(),        COLS_NUMERICAS)
    _validar("cafe",      cafe.obtener(),      COLS_NUMERICAS)
    _validar("clima",     clima.obtener(),     COLS_NUMERICAS)
    _validar("noticias",  noticias.obtener(),  COLS_NOTICIAS)
    _validar("contexto",  contexto.obtener(),  COLS_NUMERICAS)

    print("\nFase 0 completada. Todos los stubs cumplen el contrato de columnas.")


if __name__ == "__main__":
    main()
