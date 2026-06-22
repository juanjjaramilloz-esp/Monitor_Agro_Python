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

COLUMNAS_HISTORICO_DIARIO = [
    "fecha",
    "geografia",
    "variable",
    "valor",
    "unidad",
    "fuente",
]

COLUMNAS_HISTORICO_SEMANAL = [
    "semana_fin",
    "fecha_dato",
    "geografia",
    "variable",
    "valor",
    "unidad",
    "fuente",
    "dias_observados",
]

COLUMNAS_INDICADORES = [
    "semana_fin",
    "geografia",
    "variable_base",
    "indicador",
    "valor",
    "unidad",
    "ventana_semanas",
    "observaciones",
    "fuente",
]

COLUMNAS_VISUALIZACION = [
    "semana_fin",
    "anio",
    "mes",
    "semana_iso",
    "geografia",
    "tipo_geografia",
    "municipio_referencia",
    "orden_geografia",
    "categoria",
    "orden_variable",
    "variable",
    "etiqueta_variable",
    "descripcion_variable",
    "valor",
    "unidad",
    "decimales",
    "color",
    "fuente",
    "dias_observados",
    "indice_base_100",
    "cambio_1s_absoluto",
    "cambio_1s_pct",
    "cambio_4s_pct",
    "promedio_movil_4s",
    "promedio_movil_12s",
    "anomalia_z_52s",
    "estado_anomalia",
    "direccion_cambio",
    "ranking_departamental",
    "percentil_departamental",
    "diferencia_mediana_departamentos",
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


def validar_historico_diario(
    tabla: pd.DataFrame,
    desde: date,
    hasta: date,
) -> None:
    """Valida estructura, rango y unicidad de las observaciones históricas."""
    if list(tabla.columns) != COLUMNAS_HISTORICO_DIARIO:
        raise ValueError("historico diario: columnas incorrectas")
    if tabla.empty:
        raise ValueError("historico diario: no contiene datos")
    if tabla.isna().any().any():
        raise ValueError("historico diario: contiene valores nulos")

    fechas = pd.to_datetime(tabla["fecha"], errors="coerce").dt.date
    if fechas.isna().any():
        raise ValueError("historico diario: contiene fechas inválidas")
    if (fechas < desde).any() or (fechas > hasta).any():
        raise ValueError("historico diario: contiene fechas fuera del rango solicitado")
    if tabla.duplicated(["fecha", "geografia", "variable", "fuente"]).any():
        raise ValueError("historico diario: contiene observaciones duplicadas")
    if pd.to_numeric(tabla["valor"], errors="coerce").isna().any():
        raise ValueError("historico diario: contiene valores no numéricos")


def validar_historico_semanal(tabla: pd.DataFrame) -> None:
    """Valida la tabla semanal sin exigir que todas las fuentes estén disponibles."""
    if list(tabla.columns) != COLUMNAS_HISTORICO_SEMANAL:
        raise ValueError("historico semanal: columnas incorrectas")
    if tabla.empty:
        raise ValueError("historico semanal: no contiene semanas completas")
    if tabla.isna().any().any():
        raise ValueError("historico semanal: contiene valores nulos")
    if tabla.duplicated(["semana_fin", "geografia", "variable", "fuente"]).any():
        raise ValueError("historico semanal: contiene indicadores duplicados")

    semanas = pd.to_datetime(tabla["semana_fin"], errors="coerce").dt.date
    fechas = pd.to_datetime(tabla["fecha_dato"], errors="coerce").dt.date
    if semanas.isna().any() or fechas.isna().any():
        raise ValueError("historico semanal: contiene fechas inválidas")
    if any(semana.weekday() != 6 for semana in semanas):
        raise ValueError("historico semanal: semana_fin debe ser domingo")
    if (fechas > semanas).any():
        raise ValueError("historico semanal: fecha_dato posterior al cierre semanal")


def generar_reporte_historico(tabla: pd.DataFrame) -> pd.DataFrame:
    """Muestra cobertura de los 35 indicadores esperados en cada semana."""
    filas = []
    for semana, grupo in tabla.groupby("semana_fin", sort=True):
        esperadas = 3 + len(DEPARTAMENTOS) * len(VARIABLES_CLIMA)
        recibidas = len(grupo)
        dias_clima = grupo.loc[
            grupo["variable"].isin(VARIABLES_CLIMA), "dias_observados"
        ]
        dias_clima_minimos = int(dias_clima.min()) if not dias_clima.empty else 0
        completa = recibidas == esperadas and dias_clima_minimos >= 7
        filas.append(
            {
                "semana_fin": semana,
                "estado": "OK" if completa else "INCOMPLETO",
                "indicadores_recibidos": recibidas,
                "indicadores_esperados": esperadas,
                "departamentos_clima": grupo.loc[
                    grupo["variable"].isin(VARIABLES_CLIMA), "geografia"
                ].nunique(),
                "dias_clima_minimos": dias_clima_minimos,
            }
        )
    return pd.DataFrame(filas)


def validar_indicadores(tabla: pd.DataFrame) -> None:
    """Valida que la capa derivada sea tidy, numérica y reproducible."""
    if list(tabla.columns) != COLUMNAS_INDICADORES:
        raise ValueError("indicadores: columnas incorrectas")
    if tabla.empty:
        raise ValueError("indicadores: no contiene resultados")
    if tabla.isna().any().any():
        raise ValueError("indicadores: contiene valores nulos")
    claves = ["semana_fin", "geografia", "variable_base", "indicador"]
    if tabla.duplicated(claves).any():
        raise ValueError("indicadores: contiene filas duplicadas")

    fechas = pd.to_datetime(tabla["semana_fin"], errors="coerce")
    valores = pd.to_numeric(tabla["valor"], errors="coerce")
    observaciones = pd.to_numeric(tabla["observaciones"], errors="coerce")
    if fechas.isna().any() or valores.isna().any() or observaciones.isna().any():
        raise ValueError("indicadores: contiene fechas o valores inválidos")
    if (observaciones <= 0).any():
        raise ValueError("indicadores: observaciones debe ser positivo")


def validar_visualizacion(tabla: pd.DataFrame) -> None:
    """Valida claves y metadatos obligatorios de la tabla lista para gráficos."""
    if list(tabla.columns) != COLUMNAS_VISUALIZACION:
        raise ValueError("visualizacion: columnas incorrectas")
    if tabla.empty:
        raise ValueError("visualizacion: no contiene datos")
    claves = ["semana_fin", "geografia", "variable"]
    if tabla.duplicated(claves).any():
        raise ValueError("visualizacion: contiene series duplicadas")

    obligatorias = [
        "semana_fin",
        "geografia",
        "tipo_geografia",
        "municipio_referencia",
        "categoria",
        "variable",
        "etiqueta_variable",
        "descripcion_variable",
        "valor",
        "unidad",
        "color",
        "fuente",
    ]
    if tabla[obligatorias].isna().any().any():
        raise ValueError("visualizacion: faltan datos o metadatos obligatorios")
    if pd.to_datetime(tabla["semana_fin"], errors="coerce").isna().any():
        raise ValueError("visualizacion: contiene fechas inválidas")
    if pd.to_numeric(tabla["valor"], errors="coerce").isna().any():
        raise ValueError("visualizacion: contiene valores no numéricos")
