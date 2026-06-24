"""Prepara metadatos y series compactas para visualizaciones básicas."""

import pandas as pd

from config import (
    CADENCIAS_VARIABLES,
    CATALOGO_VARIABLES,
    DIR_HISTORICO,
    DIR_VISUALIZACION,
    GEOGRAFIA_GLOBAL,
    GEOGRAFIA_PAIS,
    ORDEN_GEOGRAFIAS,
    REGIONES_CAFE,
    UMBRAL_ANOMALIA_ALTA,
    UMBRAL_ANOMALIA_MODERADA,
    VARIABLES_INDICE_BASE_100,
)
from procesar.calidad import COLUMNAS_VISUALIZACION, validar_visualizacion
from procesar.indicadores import calcular


RUTA_HISTORICO = DIR_HISTORICO / "historico_semanal.csv"
RUTA_SERIES = DIR_VISUALIZACION / "series_visualizacion.csv"
RUTA_RESUMEN = DIR_VISUALIZACION / "resumen_visual.csv"
RUTA_CATALOGO = DIR_VISUALIZACION / "catalogo_variables.csv"


def _tipo_geografia(geografia: str) -> str:
    if geografia == GEOGRAFIA_GLOBAL:
        return "Global"
    if geografia == GEOGRAFIA_PAIS:
        return "Nacional"
    return "Departamental"


def _estado_anomalia(valor: float | None) -> str:
    if valor is None or pd.isna(valor):
        return "Sin historial suficiente"
    if valor >= UMBRAL_ANOMALIA_ALTA:
        return "Muy por encima de su historia"
    if valor >= UMBRAL_ANOMALIA_MODERADA:
        return "Por encima de su historia"
    if valor <= -UMBRAL_ANOMALIA_ALTA:
        return "Muy por debajo de su historia"
    if valor <= -UMBRAL_ANOMALIA_MODERADA:
        return "Por debajo de su historia"
    return "Dentro de su rango histórico"


def _direccion_cambio(valor: float | None) -> str:
    if valor is None or pd.isna(valor):
        return "Sin comparación"
    if valor > 0:
        return "Sube"
    if valor < 0:
        return "Baja"
    return "Sin cambio"


def crear_catalogo() -> pd.DataFrame:
    """Devuelve una tabla pequeña con etiquetas y formatos de cada variable."""
    filas = []
    for variable, metadatos in CATALOGO_VARIABLES.items():
        filas.append({"variable": variable, **metadatos})
    return pd.DataFrame(filas).sort_values("orden").reset_index(drop=True)


def preparar(
    historico: pd.DataFrame,
    indicadores: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Une valores, indicadores y metadatos en una fila por serie y semana."""
    if indicadores is None:
        indicadores = calcular(historico)

    base = historico.copy()
    base["semana_fin"] = pd.to_datetime(base["semana_fin"]).dt.date
    base["valor"] = pd.to_numeric(base["valor"])
    derivados = indicadores.copy()
    derivados["semana_fin"] = pd.to_datetime(derivados["semana_fin"]).dt.date
    ancho = derivados.pivot_table(
        index=["semana_fin", "geografia", "variable_base"],
        columns="indicador",
        values="valor",
        aggfunc="first",
    ).reset_index()
    ancho = ancho.rename(columns={"variable_base": "variable"})
    tabla = base.merge(ancho, on=["semana_fin", "geografia", "variable"], how="left")

    faltantes = set(tabla["variable"]) - set(CATALOGO_VARIABLES)
    if faltantes:
        raise ValueError(f"visualizacion: variables sin catálogo {sorted(faltantes)}")

    catalogo = crear_catalogo().rename(
        columns={
            "etiqueta": "etiqueta_variable",
            "descripcion": "descripcion_variable",
            "orden": "orden_variable",
        }
    )
    tabla = tabla.merge(catalogo, on="variable", how="left")
    tabla["cadencia"] = tabla["variable"].map(CADENCIAS_VARIABLES)

    municipios = {r["departamento"]: r["municipio"] for r in REGIONES_CAFE}
    orden_geografias = {nombre: posicion for posicion, nombre in enumerate(ORDEN_GEOGRAFIAS)}
    tabla["tipo_geografia"] = tabla["geografia"].map(_tipo_geografia)
    tabla["municipio_referencia"] = tabla["geografia"].map(municipios).fillna("No aplica")
    tabla["orden_geografia"] = tabla["geografia"].map(orden_geografias)

    fechas = pd.to_datetime(tabla["semana_fin"])
    tabla["anio"] = fechas.dt.year
    tabla["mes"] = fechas.dt.month
    tabla["semana_iso"] = fechas.dt.isocalendar().week.astype(int)

    tabla["indice_base_100"] = float("nan")
    mercado = tabla["variable"].isin(VARIABLES_INDICE_BASE_100)
    for _, indices in tabla[mercado].groupby(["geografia", "variable"]).groups.items():
        serie = tabla.loc[indices].sort_values("semana_fin")
        base_inicial = float(serie.iloc[0]["valor"])
        if base_inicial != 0:
            tabla.loc[serie.index, "indice_base_100"] = (
                serie["valor"] / base_inicial * 100
            )

    anomalias = (
        tabla["anomalia_z_52s"]
        if "anomalia_z_52s" in tabla
        else pd.Series(float("nan"), index=tabla.index)
    )
    cambios = (
        tabla["cambio_1s_absoluto"]
        if "cambio_1s_absoluto" in tabla
        else pd.Series(float("nan"), index=tabla.index)
    )
    tabla["estado_anomalia"] = anomalias.map(_estado_anomalia)
    tabla["direccion_cambio"] = cambios.map(_direccion_cambio)

    for columna in COLUMNAS_VISUALIZACION:
        if columna not in tabla:
            tabla[columna] = pd.NA
    tabla = tabla[COLUMNAS_VISUALIZACION].sort_values(
        ["semana_fin", "orden_geografia", "orden_variable"]
    ).reset_index(drop=True)
    validar_visualizacion(tabla)
    return tabla


def preparar_descarga_comercial(tabla: pd.DataFrame) -> pd.DataFrame:
    """Crea una tabla comercial legible y trazable para reutilización externa."""
    columnas = [
        "semana_fin",
        "fecha_dato",
        "variable",
        "etiqueta_variable",
        "valor",
        "unidad",
        "cambio_1s_pct",
        "cambio_4s_pct",
        "cambio_1m_pct",
        "cambio_12m_pct",
        "indice_base_100",
        "fuente",
        "geografia",
    ]
    mercado = tabla[tabla["categoria"].eq("Mercado")].copy()
    mercado = mercado[columnas].rename(
        columns={
            "semana_fin": "semana_cierre",
            "etiqueta_variable": "indicador",
            "cambio_1s_pct": "cambio_semanal_pct",
            "cambio_4s_pct": "cambio_4_semanas_pct",
            "geografia": "alcance_geografico",
        }
    )
    return mercado.sort_values(["semana_cierre", "variable"]).reset_index(drop=True)


def crear_resumen_visual(tabla: pd.DataFrame) -> pd.DataFrame:
    """Filtra la última semana conservando metadatos listos para tarjetas."""
    ultima = pd.to_datetime(tabla["semana_fin"]).max().date()
    return tabla[tabla["semana_fin"] == ultima].reset_index(drop=True)


def ejecutar() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Genera las tablas que consumirán las visualizaciones básicas."""
    historico = pd.read_csv(RUTA_HISTORICO)
    tabla = preparar(historico)
    resumen = crear_resumen_visual(tabla)
    catalogo = crear_catalogo()

    DIR_VISUALIZACION.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(RUTA_SERIES, index=False, encoding="utf-8")
    resumen.to_csv(RUTA_RESUMEN, index=False, encoding="utf-8")
    catalogo.to_csv(RUTA_CATALOGO, index=False, encoding="utf-8")

    print(f"  Series para gráficos: {RUTA_SERIES} ({len(tabla)} filas)")
    print(f"  Resumen visual: {RUTA_RESUMEN} ({len(resumen)} filas)")
    print(f"  Catálogo: {RUTA_CATALOGO} ({len(catalogo)} variables)")
    return tabla, resumen


if __name__ == "__main__":
    ejecutar()
