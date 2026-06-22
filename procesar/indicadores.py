"""Calcula tendencias y comparaciones descriptivas sobre el histórico semanal."""

from math import isfinite

import pandas as pd

from config import (
    DIR_HISTORICO,
    DIR_INDICADORES,
    GEOGRAFIA_PAIS,
    GEOGRAFIA_GLOBAL,
    GEOGRAFIA_PRIORITARIA,
    INDICADORES_MIN_OBS_ANOMALIA,
    INDICADORES_VENTANA_ANOMALIA,
    INDICADORES_VENTANA_CORTA,
    INDICADORES_VENTANA_LARGA,
    VARIABLES_CAMBIO_PORCENTUAL,
)
from procesar.calidad import (
    COLUMNAS_INDICADORES,
    VARIABLES_CLIMA,
    validar_historico_semanal,
    validar_indicadores,
)


RUTA_HISTORICO = DIR_HISTORICO / "historico_semanal.csv"
RUTA_INDICADORES = DIR_INDICADORES / "indicadores_semanales.csv"
RUTA_RESUMEN = DIR_INDICADORES / "resumen_ultima_semana.csv"


def _agregar_resultado(
    filas: list[dict],
    base: pd.DataFrame,
    valores: pd.Series,
    indicador: str,
    unidad: str,
    ventana: int,
    observaciones: int | pd.Series,
) -> None:
    """Convierte una serie derivada en filas tidy, omitiendo resultados inválidos."""
    for posicion, valor in valores.items():
        if pd.isna(valor) or not isfinite(float(valor)):
            continue
        observadas = (
            int(observaciones.loc[posicion])
            if isinstance(observaciones, pd.Series)
            else observaciones
        )
        fila_base = base.loc[posicion]
        filas.append(
            {
                "semana_fin": fila_base["semana_fin"],
                "geografia": fila_base["geografia"],
                "variable_base": fila_base["variable"],
                "indicador": indicador,
                "valor": round(float(valor), 6),
                "unidad": unidad,
                "ventana_semanas": ventana,
                "observaciones": observadas,
                "fuente": fila_base["fuente"],
            }
        )


def _calcular_series_temporales(tabla: pd.DataFrame) -> list[dict]:
    filas: list[dict] = []
    claves = ["geografia", "variable"]
    for _, grupo_original in tabla.groupby(claves, sort=True):
        grupo = grupo_original.sort_values("semana_fin").reset_index(drop=True)
        valores = grupo["valor"].astype(float)
        unidad = str(grupo.iloc[0]["unidad"])

        _agregar_resultado(
            filas,
            grupo,
            valores.diff(1),
            "cambio_1s_absoluto",
            unidad,
            1,
            2,
        )

        if grupo.iloc[0]["variable"] in VARIABLES_CAMBIO_PORCENTUAL:
            anterior_1s = valores.shift(1).replace(0, pd.NA)
            anterior_4s = valores.shift(INDICADORES_VENTANA_CORTA).replace(0, pd.NA)
            _agregar_resultado(
                filas,
                grupo,
                (valores / anterior_1s - 1) * 100,
                "cambio_1s_pct",
                "%",
                1,
                2,
            )
            _agregar_resultado(
                filas,
                grupo,
                (valores / anterior_4s - 1) * 100,
                "cambio_4s_pct",
                "%",
                INDICADORES_VENTANA_CORTA,
                INDICADORES_VENTANA_CORTA + 1,
            )

        for ventana, nombre in [
            (INDICADORES_VENTANA_CORTA, "promedio_movil_4s"),
            (INDICADORES_VENTANA_LARGA, "promedio_movil_12s"),
        ]:
            _agregar_resultado(
                filas,
                grupo,
                valores.rolling(ventana, min_periods=ventana).mean(),
                nombre,
                unidad,
                ventana,
                ventana,
            )

        historial = valores.shift(1).rolling(
            INDICADORES_VENTANA_ANOMALIA,
            min_periods=INDICADORES_MIN_OBS_ANOMALIA,
        )
        promedio_previo = historial.mean()
        desviacion_previa = historial.std(ddof=0).replace(0, pd.NA)
        _agregar_resultado(
            filas,
            grupo,
            (valores - promedio_previo) / desviacion_previa,
            "anomalia_z_52s",
            "desviaciones_estandar",
            INDICADORES_VENTANA_ANOMALIA,
            historial.count(),
        )
    return filas


def _calcular_comparaciones(tabla: pd.DataFrame) -> list[dict]:
    filas: list[dict] = []
    clima = tabla[tabla["variable"].isin(VARIABLES_CLIMA)].copy()
    for _, grupo_original in clima.groupby(["semana_fin", "variable"], sort=True):
        grupo = grupo_original.reset_index(drop=True)
        valores = grupo["valor"].astype(float)
        observaciones = len(grupo)
        ranking = valores.rank(method="min", ascending=False)
        percentil = valores.rank(method="average", pct=True) * 100
        diferencia_mediana = valores - valores.median()

        _agregar_resultado(
            filas,
            grupo,
            ranking,
            "ranking_departamental",
            "posicion",
            1,
            observaciones,
        )
        _agregar_resultado(
            filas,
            grupo,
            percentil,
            "percentil_departamental",
            "%",
            1,
            observaciones,
        )
        _agregar_resultado(
            filas,
            grupo,
            diferencia_mediana,
            "diferencia_mediana_departamentos",
            str(grupo.iloc[0]["unidad"]),
            1,
            observaciones,
        )
    return filas


def calcular(tabla_historica: pd.DataFrame) -> pd.DataFrame:
    """Calcula indicadores temporales y comparaciones entre departamentos."""
    validar_historico_semanal(tabla_historica)
    tabla = tabla_historica.copy()
    tabla["semana_fin"] = pd.to_datetime(tabla["semana_fin"]).dt.date
    tabla["valor"] = pd.to_numeric(tabla["valor"])

    filas = _calcular_series_temporales(tabla)
    filas.extend(_calcular_comparaciones(tabla))
    resultado = pd.DataFrame(filas, columns=COLUMNAS_INDICADORES)
    resultado = resultado.sort_values(
        ["semana_fin", "geografia", "variable_base", "indicador"]
    ).reset_index(drop=True)
    validar_indicadores(resultado)
    return resultado


def crear_resumen(
    tabla_historica: pd.DataFrame,
    indicadores: pd.DataFrame,
) -> pd.DataFrame:
    """Crea una vista ancha y legible de la semana más reciente."""
    ultima_semana = pd.to_datetime(tabla_historica["semana_fin"]).max().date()
    base = tabla_historica[
        pd.to_datetime(tabla_historica["semana_fin"]).dt.date == ultima_semana
    ].copy()
    base["semana_fin"] = pd.to_datetime(base["semana_fin"]).dt.date
    base = base.rename(columns={"variable": "variable_base", "valor": "valor_actual"})
    base = base[
        ["semana_fin", "geografia", "variable_base", "valor_actual", "unidad", "fuente"]
    ]

    actuales = indicadores[indicadores["semana_fin"] == ultima_semana]
    ancho = actuales.pivot_table(
        index=["semana_fin", "geografia", "variable_base"],
        columns="indicador",
        values="valor",
        aggfunc="first",
    ).reset_index()
    resumen = base.merge(
        ancho,
        on=["semana_fin", "geografia", "variable_base"],
        how="left",
    )
    return resumen.sort_values(["geografia", "variable_base"]).reset_index(drop=True)


def ejecutar() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lee el histórico, calcula indicadores y guarda las salidas derivadas."""
    historico = pd.read_csv(RUTA_HISTORICO)
    indicadores = calcular(historico)
    resumen = crear_resumen(historico, indicadores)

    DIR_INDICADORES.mkdir(parents=True, exist_ok=True)
    indicadores.to_csv(RUTA_INDICADORES, index=False, encoding="utf-8")
    resumen.to_csv(RUTA_RESUMEN, index=False, encoding="utf-8")

    foco = resumen[
        resumen["geografia"].isin(
            [GEOGRAFIA_PRIORITARIA, GEOGRAFIA_PAIS, GEOGRAFIA_GLOBAL]
        )
    ]
    columnas = [
        "semana_fin",
        "geografia",
        "variable_base",
        "valor_actual",
        "unidad",
        "cambio_1s_pct",
        "cambio_4s_pct",
        "anomalia_z_52s",
        "ranking_departamental",
    ]
    columnas = [columna for columna in columnas if columna in foco.columns]
    print(f"  Indicadores: {RUTA_INDICADORES} ({len(indicadores)} filas)")
    print(f"  Resumen: {RUTA_RESUMEN} ({len(resumen)} filas)")
    print("\n  Última semana - foco Caldas y contexto de mercado:")
    print(foco[columnas].to_string(index=False))
    return indicadores, resumen


if __name__ == "__main__":
    ejecutar()
