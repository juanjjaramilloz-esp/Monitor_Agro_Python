"""Validaciones y reporte de calidad para los snapshots semanales."""

from datetime import date

import pandas as pd

from config import DEPARTAMENTOS


COLUMNAS_SNAPSHOT = [
    "fecha_snapshot",
    "fecha_dato",
    "geografia",
    "variable",
    "valor",
    "unidad",
    "fuente",
]

VARIABLES_CLIMA = {
    "precipitacion_semanal",
    "temp_min_semanal",
    "temp_max_semanal",
    "temp_promedio_semanal",
}


def validar_snapshot(tabla: pd.DataFrame, fecha_snapshot: date) -> None:
    """Bloquea inconsistencias estructurales que volverían engañoso el histórico."""
    if list(tabla.columns) != COLUMNAS_SNAPSHOT:
        raise ValueError(
            "snapshot: columnas incorrectas; "
            f"esperadas={COLUMNAS_SNAPSHOT}, recibidas={list(tabla.columns)}"
        )
    if tabla.empty:
        raise ValueError("snapshot: no contiene datos")
    if tabla[COLUMNAS_SNAPSHOT].isna().any().any():
        columnas = tabla.columns[tabla.isna().any()].tolist()
        raise ValueError(f"snapshot: hay valores nulos en {columnas}")

    claves = ["fecha_snapshot", "geografia", "variable"]
    if tabla.duplicated(subset=claves).any():
        raise ValueError(f"snapshot: hay filas duplicadas según {claves}")

    fechas_snapshot = pd.to_datetime(tabla["fecha_snapshot"], errors="coerce").dt.date
    fechas_dato = pd.to_datetime(tabla["fecha_dato"], errors="coerce").dt.date
    if fechas_snapshot.isna().any() or fechas_dato.isna().any():
        raise ValueError("snapshot: hay fechas inválidas")
    if not (fechas_snapshot == fecha_snapshot).all():
        raise ValueError("snapshot: fecha_snapshot no coincide en todas las filas")
    if (fechas_dato > fecha_snapshot).any():
        raise ValueError("snapshot: contiene datos posteriores a fecha_snapshot")

    valores = pd.to_numeric(tabla["valor"], errors="coerce")
    if valores.isna().any():
        raise ValueError("snapshot: la columna valor contiene datos no numéricos")


def generar_reporte_calidad(tabla: pd.DataFrame, fecha_snapshot: date) -> pd.DataFrame:
    """Resume cobertura y frescura sin convertir una fuente caída en un falso OK."""
    componentes = [
        ("fx", tabla["variable"].eq("fx_usd_local"), 1),
        ("cafe", tabla["variable"].eq("precio_cafe_arabica"), 1),
        (
            "precio_interno",
            tabla["variable"].eq("precio_interno_referencia"),
            1,
        ),
        (
            "clima",
            tabla["geografia"].isin(DEPARTAMENTOS)
            & tabla["variable"].isin(VARIABLES_CLIMA),
            len(DEPARTAMENTOS) * len(VARIABLES_CLIMA),
        ),
    ]

    filas: list[dict] = []
    for componente, mascara, esperadas in componentes:
        parte = tabla.loc[mascara]
        recibidas = len(parte)
        if recibidas == esperadas:
            estado = "OK"
        elif recibidas == 0:
            estado = "VACIO"
        else:
            estado = "INCOMPLETO"

        fecha_mas_antigua = None
        antiguedad_maxima_dias = None
        if not parte.empty:
            fecha_mas_antigua = pd.to_datetime(parte["fecha_dato"]).dt.date.min()
            antiguedad_maxima_dias = (fecha_snapshot - fecha_mas_antigua).days
            if antiguedad_maxima_dias < 0:
                estado = "FECHA_FUTURA"

        filas.append(
            {
                "componente": componente,
                "estado": estado,
                "filas_recibidas": recibidas,
                "filas_esperadas": esperadas,
                "fecha_mas_antigua": fecha_mas_antigua,
                "antiguedad_maxima_dias": antiguedad_maxima_dias,
            }
        )

    return pd.DataFrame(filas)
