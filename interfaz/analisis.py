"""Transformaciones comerciales puras usadas por la interfaz y los reportes."""

import pandas as pd

from config import FUENTES_COMERCIALES
from interfaz.formato import unidad_legible

VARIABLES_MERCADO = [
    "precio_interno_referencia",
    "precio_cafe_arabica",
    "fx_usd_local",
]


def comparar_produccion_exportaciones(tabla: pd.DataFrame) -> pd.DataFrame:
    """Empareja producción y exportaciones únicamente cuando comparten mes."""
    mensuales = tabla[
        tabla["variable"].isin(["produccion_nacional", "exportaciones_cafe"])
    ][["fecha_dato", "variable", "valor"]].copy()
    mensuales["mes"] = pd.to_datetime(mensuales["fecha_dato"]).dt.to_period("M")
    ancho = mensuales.pivot_table(
        index="mes",
        columns="variable",
        values="valor",
        aggfunc="last",
    ).dropna(subset=["produccion_nacional", "exportaciones_cafe"])
    ancho = ancho.reset_index()
    ancho["fecha"] = ancho["mes"].dt.to_timestamp()
    ancho["diferencia"] = ancho["produccion_nacional"] - ancho["exportaciones_cafe"]
    return ancho.sort_values("fecha").reset_index(drop=True)


def variaciones_mercado(tabla: pd.DataFrame) -> pd.DataFrame:
    """Resume cambios semanales, de 4 semanas y de 52 semanas sin causalidad."""
    filas = []
    for variable in VARIABLES_MERCADO:
        serie = tabla[tabla["variable"].eq(variable)].sort_values("semana_fin")
        if serie.empty:
            continue
        actual = serie.iloc[-1]

        def cambio(
            periodos: int,
            serie: pd.DataFrame = serie,
            actual: pd.Series = actual,
        ) -> float | None:
            if len(serie) <= periodos:
                return None
            anterior = float(serie.iloc[-periodos - 1]["valor"])
            if anterior == 0:
                return None
            return (float(actual["valor"]) / anterior - 1) * 100

        filas.append(
            {
                "Indicador": actual["etiqueta_variable"],
                "Semanal": cambio(1),
                "Mensual (4 sem.)": cambio(4),
                "Anual (52 sem.)": cambio(52),
            }
        )
    return pd.DataFrame(filas)

def resumen_fuentes_comerciales(tabla: pd.DataFrame) -> pd.DataFrame:
    """Resume cobertura y fecha real del último dato de cada serie comercial."""
    mercado = tabla[tabla["categoria"].isin(["Mercado", "Producción"])].copy()
    indices = mercado.groupby("variable")["semana_fin"].idxmax()
    ultimos = mercado.loc[indices]
    filas = []
    for _, fila in ultimos.iterrows():
        metadatos = FUENTES_COMERCIALES[fila["variable"]]
        fuente = (
            "Federación Nacional de Cafeteros (FNC)"
            if fila["fuente"] == "FNC"
            else metadatos["nombre"]
        )
        filas.append(
            {
                "Indicador": fila["etiqueta_variable"],
                "Último dato": pd.Timestamp(fila["fecha_dato"]).strftime("%d/%m/%Y"),
                "Unidad": unidad_legible(fila["unidad"]),
                "Fuente": fuente,
                "Alcance": metadatos["alcance"],
                "Cadencia": fila["cadencia"],
            }
        )
    return pd.DataFrame(filas)
