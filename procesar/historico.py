"""Descarga, agrega y archiva el histórico diario y semanal del monitor."""

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from config import (
    DIR_HISTORICO,
    HISTORICO_FECHA_INICIO,
    HISTORICO_RETRASO_CLIMA_DIAS,
)
from fuentes import cafe, clima, fx, precio_interno
from procesar.calidad import (
    COLUMNAS_HISTORICO_DIARIO,
    COLUMNAS_HISTORICO_SEMANAL,
    generar_reporte_historico,
    validar_historico_diario,
    validar_historico_semanal,
)


RUTA_DIARIO = DIR_HISTORICO / "historico_diario.csv"
RUTA_SEMANAL = DIR_HISTORICO / "historico_semanal.csv"
VARIABLES_PUNTUALES = {
    "fx_usd_local",
    "precio_cafe_arabica",
    "precio_interno_referencia",
}


def _fin_semana(fecha: date) -> date:
    """Devuelve el domingo que cierra la semana de una fecha."""
    return fecha + timedelta(days=6 - fecha.weekday())


def descargar(desde: date, hasta: date) -> pd.DataFrame:
    """Consulta las cuatro fuentes en modo histórico y devuelve datos diarios."""
    if desde > hasta:
        raise ValueError("historico: desde no puede ser posterior a hasta")

    partes = [
        fx.obtener(desde, hasta),
        cafe.obtener(desde, hasta),
        precio_interno.obtener(desde, hasta),
        clima.obtener(desde, hasta),
    ]
    partes = [parte for parte in partes if not parte.empty]
    if not partes:
        return pd.DataFrame(columns=COLUMNAS_HISTORICO_DIARIO)

    tabla = pd.concat(partes, ignore_index=True)[COLUMNAS_HISTORICO_DIARIO]
    tabla = tabla.sort_values(["fecha", "geografia", "variable", "fuente"])
    tabla = tabla.drop_duplicates(
        ["fecha", "geografia", "variable", "fuente"], keep="last"
    ).reset_index(drop=True)
    validar_historico_diario(tabla, desde, hasta)
    return tabla


def _agregar_puntuales(tabla: pd.DataFrame) -> pd.DataFrame:
    puntuales = tabla[tabla["variable"].isin(VARIABLES_PUNTUALES)].copy()
    if puntuales.empty:
        return pd.DataFrame(columns=COLUMNAS_HISTORICO_SEMANAL)

    puntuales = puntuales.sort_values("fecha")
    claves = ["semana_fin", "geografia", "variable", "unidad", "fuente"]
    filas = []
    for valores_clave, grupo in puntuales.groupby(claves, sort=True):
        ultima = grupo.iloc[-1]
        fila = dict(zip(claves, valores_clave))
        fila.update(
            {
                "fecha_dato": ultima["fecha"],
                "valor": float(ultima["valor"]),
                "dias_observados": grupo["fecha"].nunique(),
            }
        )
        filas.append(fila)
    return pd.DataFrame(filas, columns=COLUMNAS_HISTORICO_SEMANAL)


def _agregar_clima(tabla: pd.DataFrame) -> pd.DataFrame:
    clima_diario = tabla[tabla["fuente"].eq("open-meteo")].copy()
    if clima_diario.empty:
        return pd.DataFrame(columns=COLUMNAS_HISTORICO_SEMANAL)

    ancho = clima_diario.pivot_table(
        index=["semana_fin", "fecha", "geografia"],
        columns="variable",
        values="valor",
        aggfunc="first",
    ).reset_index()
    filas = []
    for (semana, geografia), grupo in ancho.groupby(
        ["semana_fin", "geografia"], sort=True
    ):
        especificaciones = [
            ("precipitacion_semanal", "precipitacion", "sum", "mm"),
            ("temp_min_semanal", "temp_min", "min", "°C"),
            ("temp_max_semanal", "temp_max", "max", "°C"),
        ]
        for variable_salida, variable_entrada, operacion, unidad in especificaciones:
            if variable_entrada not in grupo or grupo[variable_entrada].dropna().empty:
                continue
            serie = grupo[variable_entrada].dropna()
            valor = serie.sum() if operacion == "sum" else getattr(serie, operacion)()
            fecha_variable = grupo.loc[serie.index, "fecha"].max()
            filas.append(
                {
                    "semana_fin": semana,
                    "fecha_dato": fecha_variable,
                    "geografia": geografia,
                    "variable": variable_salida,
                    "valor": round(float(valor), 4),
                    "unidad": unidad,
                    "fuente": "open-meteo",
                    "dias_observados": len(serie),
                }
            )

        if {"temp_min", "temp_max"}.issubset(grupo.columns):
            pares = grupo[["temp_min", "temp_max"]].dropna()
            if not pares.empty:
                medias = (pares["temp_min"] + pares["temp_max"]) / 2
                filas.append(
                    {
                        "semana_fin": semana,
                        "fecha_dato": grupo.loc[pares.index, "fecha"].max(),
                        "geografia": geografia,
                        "variable": "temp_promedio_semanal",
                        "valor": round(float(medias.mean()), 4),
                        "unidad": "°C",
                        "fuente": "open-meteo",
                        "dias_observados": len(medias),
                    }
                )

    return pd.DataFrame(filas, columns=COLUMNAS_HISTORICO_SEMANAL)


def agregar_semanal(tabla_diaria: pd.DataFrame, hasta: date) -> pd.DataFrame:
    """Agrega observaciones diarias usando solo semanas cerradas."""
    if tabla_diaria.empty:
        return pd.DataFrame(columns=COLUMNAS_HISTORICO_SEMANAL)

    tabla = tabla_diaria.copy()
    tabla["fecha"] = pd.to_datetime(tabla["fecha"]).dt.date
    tabla["semana_fin"] = tabla["fecha"].map(_fin_semana)
    primer_dia_disponible = tabla["fecha"].min()
    inicio_semana = tabla["semana_fin"].map(lambda fin: fin - timedelta(days=6))
    tabla = tabla[
        (tabla["semana_fin"] <= hasta)
        & (inicio_semana >= primer_dia_disponible)
    ]
    if tabla.empty:
        return pd.DataFrame(columns=COLUMNAS_HISTORICO_SEMANAL)

    partes = [_agregar_puntuales(tabla), _agregar_clima(tabla)]
    partes = [parte for parte in partes if not parte.empty]
    semanal = pd.concat(partes, ignore_index=True)[COLUMNAS_HISTORICO_SEMANAL]
    semanal = semanal.sort_values(
        ["semana_fin", "geografia", "variable", "fuente"]
    ).reset_index(drop=True)
    validar_historico_semanal(semanal)
    return semanal


def _combinar_historico(
    existente: pd.DataFrame,
    nuevos: pd.DataFrame,
    claves: list[str],
) -> pd.DataFrame:
    """Combina corridas sin duplicar observaciones ya descargadas."""
    combinado = pd.concat([existente, nuevos], ignore_index=True)
    for columna in {"fecha", "fecha_dato", "semana_fin"} & set(combinado.columns):
        combinado[columna] = pd.to_datetime(combinado[columna]).dt.strftime(
            "%Y-%m-%d"
        )
    combinado = combinado.drop_duplicates(claves, keep="last").sort_values(claves)
    return combinado.reset_index(drop=True)


def _actualizar_csv(
    nuevos: pd.DataFrame,
    ruta: Path,
    claves: list[str],
) -> pd.DataFrame:
    """Actualiza un CSV de forma idempotente, conservando la versión más reciente."""
    existente = pd.read_csv(ruta) if ruta.exists() else pd.DataFrame(columns=nuevos.columns)
    combinado = _combinar_historico(existente, nuevos, claves)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    combinado.to_csv(ruta, index=False, encoding="utf-8")
    return combinado


def ejecutar(
    desde: date = HISTORICO_FECHA_INICIO,
    hasta: date | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ejecuta el backfill y actualiza los archivos diario y semanal."""
    if hasta is None:
        hasta = date.today() - timedelta(days=HISTORICO_RETRASO_CLIMA_DIAS)
    diario_nuevo = descargar(desde, hasta)
    if diario_nuevo.empty:
        print("  AVISO: ninguna fuente entregó datos históricos; no se guardó nada.")
        return diario_nuevo, pd.DataFrame(columns=COLUMNAS_HISTORICO_SEMANAL)

    semanal_nuevo = agregar_semanal(diario_nuevo, hasta)
    diario = _actualizar_csv(
        diario_nuevo,
        RUTA_DIARIO,
        ["fecha", "geografia", "variable", "fuente"],
    )
    semanal = _actualizar_csv(
        semanal_nuevo,
        RUTA_SEMANAL,
        ["semana_fin", "geografia", "variable", "fuente"],
    )
    reporte = generar_reporte_historico(semanal_nuevo)
    print(f"  Histórico diario: {RUTA_DIARIO} ({len(diario)} filas)")
    print(f"  Histórico semanal: {RUTA_SEMANAL} ({len(semanal)} filas)")
    print("\n  Cobertura de las últimas semanas:")
    print(reporte.tail(8).to_string(index=False))
    return diario, semanal


def _parsear_fecha(valor: str) -> date:
    return datetime.strptime(valor, "%Y-%m-%d").date()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill histórico del monitor")
    parser.add_argument("--desde", type=_parsear_fecha, default=HISTORICO_FECHA_INICIO)
    parser.add_argument("--hasta", type=_parsear_fecha)
    argumentos = parser.parse_args()
    ejecutar(argumentos.desde, argumentos.hasta)
