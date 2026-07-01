"""Prepara metadatos y series compactas para visualizaciones básicas."""

from pathlib import Path

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
    VARIABLES_MENSUALES,
    VARIABLES_INDICE_BASE_100,
)
from procesar.calidad import COLUMNAS_VISUALIZACION, validar_visualizacion
from procesar.indicadores import calcular


RUTA_HISTORICO = DIR_HISTORICO / "historico_semanal.csv"
RUTA_SERIES = DIR_VISUALIZACION / "series_visualizacion.csv"
RUTA_RESUMEN = DIR_VISUALIZACION / "resumen_visual.csv"
RUTA_CATALOGO = DIR_VISUALIZACION / "catalogo_variables.csv"


def configuracion_eje_mensual(
    fechas: pd.Series,
    max_etiquetas: int = 12,
) -> dict[str, object]:
    """Etiqueta solo fechas con barras y reduce la densidad si hace falta."""
    if max_etiquetas < 2:
        raise ValueError("max_etiquetas debe ser al menos 2")
    fechas_unicas = sorted(pd.to_datetime(fechas).dropna().unique())
    if len(fechas_unicas) > max_etiquetas:
        ultimo = len(fechas_unicas) - 1
        indices = sorted(
            {round(indice * ultimo / (max_etiquetas - 1)) for indice in range(max_etiquetas)}
        )
        fechas_etiquetadas = [fechas_unicas[indice] for indice in indices]
    else:
        fechas_etiquetadas = fechas_unicas
    return {
        "showgrid": False,
        "title": None,
        "tickmode": "array",
        "tickvals": fechas_etiquetadas,
        "tickformat": "%b<br>%Y",
        "tickangle": 0,
        "automargin": True,
    }


def filtrar_periodo_visualizacion(
    tabla: pd.DataFrame,
    semanas: int | None,
) -> pd.DataFrame:
    """Filtra cada cadencia sin recortar meses publicados por fechas semanales.

    Las series semanales se anclan en el último cierre disponible. Para las
    mensuales, el equivalente de 3/6/12/36 meses se calcula desde el último mes
    publicado de cada variable, que puede tener rezago frente al mercado.
    """
    if semanas is None:
        return tabla.copy()
    if semanas < 1:
        raise ValueError("semanas debe ser al menos 1")

    resultado = tabla.copy()
    fechas_cierre = pd.to_datetime(resultado["semana_fin"])
    ultima = fechas_cierre.max()
    inicio = ultima - pd.Timedelta(weeks=semanas - 1)
    es_mensual = resultado["variable"].isin(VARIABLES_MENSUALES)
    semanales = resultado[~es_mensual & (fechas_cierre >= inicio)]

    cantidad_meses = max(1, round(semanas * 12 / 52))
    grupos_mensuales = []
    for _, grupo in resultado[es_mensual].groupby("variable", sort=False):
        meses = pd.to_datetime(grupo["fecha_dato"]).dt.to_period("M")
        ultimo_mes = meses.max()
        primer_mes = ultimo_mes - (cantidad_meses - 1)
        grupos_mensuales.append(grupo[meses >= primer_mes])

    mensuales = (
        pd.concat(grupos_mensuales, ignore_index=False)
        if grupos_mensuales
        else resultado.iloc[0:0]
    )
    return pd.concat([semanales, mensuales], ignore_index=False).sort_index().copy()


def preparar_flujos_mensuales(tabla: pd.DataFrame) -> pd.DataFrame:
    """Alinea producción y exportaciones por mes y calcula su diferencia."""
    mensuales = tabla[
        tabla["variable"].isin(["produccion_nacional", "exportaciones_cafe"])
    ][["fecha_dato", "variable", "valor"]].copy()
    if mensuales.empty:
        return pd.DataFrame(
            columns=[
                "mes",
                "fecha",
                "produccion_nacional",
                "exportaciones_cafe",
                "diferencia",
            ]
        )
    mensuales["mes"] = pd.to_datetime(mensuales["fecha_dato"]).dt.to_period("M")
    flujos = mensuales.pivot_table(
        index="mes",
        columns="variable",
        values="valor",
        aggfunc="last",
    ).reset_index()
    for variable in ("produccion_nacional", "exportaciones_cafe"):
        if variable not in flujos:
            flujos[variable] = pd.NA
    flujos["fecha"] = flujos["mes"].dt.to_timestamp()
    flujos["diferencia"] = (
        flujos["produccion_nacional"] - flujos["exportaciones_cafe"]
    )
    return flujos[
        [
            "mes",
            "fecha",
            "produccion_nacional",
            "exportaciones_cafe",
            "diferencia",
        ]
    ].sort_values("fecha").reset_index(drop=True)


def faltan_variables_historicas(
    variables_historico: set[str],
    variables_series: set[str],
) -> bool:
    """Indica si el derivado visual omite alguna serie del histórico."""
    return not variables_historico.issubset(variables_series)


def incorporar_referencia_comercial_actual(
    tabla: pd.DataFrame,
    referencia: dict[str, tuple[float, pd.Timestamp]],
) -> pd.DataFrame:
    """Añade a las series semanales un punto comercial actual y coherente."""
    resultado = tabla.copy()
    resultado["semana_fin"] = pd.to_datetime(resultado["semana_fin"])
    resultado["fecha_dato"] = pd.to_datetime(resultado["fecha_dato"])
    filas = []
    for variable, (valor, fecha) in referencia.items():
        serie = resultado[resultado["variable"].eq(variable)].sort_values("fecha_dato")
        if serie.empty:
            continue
        fecha = pd.Timestamp(fecha)
        ultima = serie.iloc[-1].copy()
        valor_anterior = float(ultima["valor"])
        valor_base = float(serie.iloc[0]["valor"])
        ultima["semana_fin"] = fecha
        ultima["fecha_dato"] = fecha
        ultima["valor"] = float(valor)
        ultima["fuente"] = "FNC"
        ultima["cadencia"] = "Referencia oficial diaria más reciente"
        ultima["dias_observados"] = 1
        ultima["indice_base_100"] = (
            float(valor) / valor_base * 100 if valor_base else pd.NA
        )
        ultima["cambio_1s_absoluto"] = float(valor) - valor_anterior
        ultima["cambio_1s_pct"] = (
            (float(valor) / valor_anterior - 1) * 100 if valor_anterior else pd.NA
        )
        filas.append(ultima)

    if not filas:
        return resultado
    actuales = pd.DataFrame(filas, columns=resultado.columns)
    claves = ["fecha_dato", "geografia", "variable"]
    resultado = pd.concat([resultado, actuales], ignore_index=True)
    return (
        resultado.drop_duplicates(claves, keep="last")
        .sort_values(["semana_fin", "orden_geografia", "orden_variable"])
        .reset_index(drop=True)
    )


def series_necesitan_regenerarse(
    ruta_series: Path = RUTA_SERIES,
    ruta_historico: Path = RUTA_HISTORICO,
) -> bool:
    """Detecta un derivado ausente, desactualizado o incompleto."""
    if not ruta_series.exists():
        return True
    if ruta_historico.exists() and ruta_historico.stat().st_mtime > ruta_series.stat().st_mtime:
        return True
    try:
        variables_historico = set(
            pd.read_csv(ruta_historico, usecols=["variable"])["variable"]
        )
        variables_series = set(
            pd.read_csv(ruta_series, usecols=["variable"])["variable"]
        )
    except (OSError, ValueError, KeyError):
        return True
    return faltan_variables_historicas(variables_historico, variables_series)


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
        "cadencia",
        "cambio_1s_pct",
        "cambio_4s_pct",
        "cambio_1m_pct",
        "cambio_12m_pct",
        "indice_base_100",
        "fuente",
        "geografia",
    ]
    mercado = tabla[tabla["categoria"].isin(["Mercado", "Producción"])].copy()
    mercado = mercado[columnas].rename(
        columns={
            "semana_fin": "semana_cierre",
            "etiqueta_variable": "indicador",
            "cambio_1s_pct": "cambio_semanal_pct",
            "cambio_4s_pct": "cambio_4_semanas_pct",
            "cambio_1m_pct": "cambio_mensual_pct",
            "cambio_12m_pct": "cambio_interanual_pct",
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
