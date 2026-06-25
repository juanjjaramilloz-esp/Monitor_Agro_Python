"""Estimación transparente del precio interno FNC y el margen."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import (
    ESTIMADOR_DECAIMIENTO_RECIENTE,
    ESTIMADOR_DIAS_CALIBRACION,
    ESTIMADOR_OBSERVACIONES_VALIDACION,
)


VARIABLES_BASE = {
    "precio_fnc": "precio_interno_referencia",
    "tasa_cambio": "fx_usd_local",
    "precio_ny": "precio_cafe_arabica",
}


@dataclass(frozen=True)
class BasesProyeccion:
    """Últimas observaciones disponibles para iniciar y comparar el escenario."""

    precio_fnc: float
    tasa_cambio: float
    precio_ny: float
    fecha_precio_fnc: pd.Timestamp
    fecha_tasa_cambio: pd.Timestamp
    fecha_precio_ny: pd.Timestamp


@dataclass(frozen=True)
class ModeloPrecioFNC:
    """Calibración reciente y calidad histórica del estimador."""

    coeficiente: float
    observaciones_calibracion: int
    fecha_inicio_calibracion: pd.Timestamp
    fecha_fin_calibracion: pd.Timestamp
    error_absoluto_medio: float
    error_porcentual_medio: float
    observaciones_validacion: int
    calibracion_oficial: bool = False


@dataclass(frozen=True)
class ResultadoEscenario:
    """Resultados económicos simples para un conjunto de supuestos."""

    precio_fnc_estimado: float
    diferencia_fnc_observado_pct: float
    ingreso_total: float
    costo_total: float
    margen_por_carga: float
    margen_total: float
    margen_sobre_ingreso_pct: float
    retorno_sobre_costo_pct: float


def obtener_bases(tabla: pd.DataFrame) -> BasesProyeccion:
    """Extrae la última observación válida de cada serie requerida."""
    columna_fecha = "fecha" if "fecha" in tabla.columns else "fecha_dato"
    valores: dict[str, tuple[float, pd.Timestamp]] = {}
    for nombre, variable in VARIABLES_BASE.items():
        serie = tabla[tabla["variable"].eq(variable)].copy()
        if serie.empty:
            raise ValueError(f"proyeccion: falta la serie {variable}")
        serie[columna_fecha] = pd.to_datetime(serie[columna_fecha], errors="coerce")
        serie["valor"] = pd.to_numeric(serie["valor"], errors="coerce")
        serie = serie.dropna(subset=[columna_fecha, "valor"]).sort_values(columna_fecha)
        if serie.empty:
            raise ValueError(f"proyeccion: la serie {variable} no tiene datos válidos")
        ultima = serie.iloc[-1]
        valores[nombre] = (float(ultima["valor"]), pd.Timestamp(ultima[columna_fecha]))

    return BasesProyeccion(
        precio_fnc=valores["precio_fnc"][0],
        tasa_cambio=valores["tasa_cambio"][0],
        precio_ny=valores["precio_ny"][0],
        fecha_precio_fnc=valores["precio_fnc"][1],
        fecha_tasa_cambio=valores["tasa_cambio"][1],
        fecha_precio_ny=valores["precio_ny"][1],
    )


def obtener_bases_calibracion(tabla: pd.DataFrame) -> BasesProyeccion | None:
    """Devuelve el último trío oficial guardado, si está completo y es válido."""
    requeridas = {"fecha", "precio_fnc", "tasa_cambio", "precio_ny"}
    if tabla.empty or not requeridas.issubset(tabla.columns):
        return None
    datos = tabla.copy()
    datos["fecha"] = pd.to_datetime(datos["fecha"], errors="coerce")
    for columna in ["precio_fnc", "tasa_cambio", "precio_ny"]:
        datos[columna] = pd.to_numeric(datos[columna], errors="coerce")
    datos = datos.dropna(subset=list(requeridas))
    datos = datos[
        (datos["precio_fnc"] > 0)
        & (datos["tasa_cambio"] > 0)
        & (datos["precio_ny"] > 0)
    ].sort_values("fecha")
    if datos.empty:
        return None
    ultima = datos.iloc[-1]
    fecha = pd.Timestamp(ultima["fecha"])
    return BasesProyeccion(
        precio_fnc=float(ultima["precio_fnc"]),
        tasa_cambio=float(ultima["tasa_cambio"]),
        precio_ny=float(ultima["precio_ny"]),
        fecha_precio_fnc=fecha,
        fecha_tasa_cambio=fecha,
        fecha_precio_ny=fecha,
    )


def _tabla_comparable(tabla: pd.DataFrame) -> pd.DataFrame:
    """Alinea FNC, TRM y Coffee C por fecha real, sin rellenar observaciones."""
    columna_fecha = "fecha" if "fecha" in tabla.columns else "fecha_dato"
    requeridas = {columna_fecha, "variable", "valor"}
    faltantes = requeridas.difference(tabla.columns)
    if faltantes:
        raise ValueError(f"estimador FNC: faltan columnas {sorted(faltantes)}")

    datos = tabla[tabla["variable"].isin(VARIABLES_BASE.values())].copy()
    datos[columna_fecha] = pd.to_datetime(datos[columna_fecha], errors="coerce")
    datos["valor"] = pd.to_numeric(datos["valor"], errors="coerce")
    datos = datos.dropna(subset=[columna_fecha, "valor"])
    pivote = (
        datos.pivot_table(
            index=columna_fecha,
            columns="variable",
            values="valor",
            aggfunc="last",
        )
        .dropna(subset=list(VARIABLES_BASE.values()))
        .sort_index()
    )
    pivote = pivote[(pivote[list(VARIABLES_BASE.values())] > 0).all(axis=1)]
    if len(pivote) < ESTIMADOR_DIAS_CALIBRACION + 1:
        raise ValueError("estimador FNC: no hay suficientes fechas comparables")
    return pivote


def _coeficiente_ponderado(tabla: pd.DataFrame) -> float:
    """Promedia la relación FNC/(TRM×Coffee C), priorizando datos recientes."""
    recientes = tabla.tail(ESTIMADOR_DIAS_CALIBRACION)
    denominador = recientes["fx_usd_local"] * recientes["precio_cafe_arabica"]
    razones = recientes["precio_interno_referencia"] / denominador
    pesos = np.exp(
        np.linspace(
            -ESTIMADOR_DECAIMIENTO_RECIENTE,
            0.0,
            len(razones),
        )
    )
    return float(np.average(razones.to_numpy(dtype=float), weights=pesos))


def calibrar_modelo(
    tabla: pd.DataFrame,
    calibracion_oficial: pd.DataFrame | None = None,
) -> ModeloPrecioFNC:
    """
    Calibra el estimador con datos diarios comparables y valida hacia adelante.

    Cada predicción de validación usa exclusivamente observaciones anteriores,
    evitando medir el modelo con información del mismo día que intenta estimar.
    """
    comparable = _tabla_comparable(tabla)
    inicio_validacion = max(
        ESTIMADOR_DIAS_CALIBRACION,
        len(comparable) - ESTIMADOR_OBSERVACIONES_VALIDACION,
    )
    errores_absolutos: list[float] = []
    errores_porcentuales: list[float] = []
    for posicion in range(inicio_validacion, len(comparable)):
        anteriores = comparable.iloc[:posicion]
        coeficiente = _coeficiente_ponderado(anteriores)
        actual = comparable.iloc[posicion]
        estimado = (
            float(actual["fx_usd_local"])
            * float(actual["precio_cafe_arabica"])
            * coeficiente
        )
        observado = float(actual["precio_interno_referencia"])
        error = abs(observado - estimado)
        errores_absolutos.append(error)
        errores_porcentuales.append(error / observado * 100)

    calibracion = comparable.tail(ESTIMADOR_DIAS_CALIBRACION)
    coeficiente = _coeficiente_ponderado(comparable)
    fecha_inicio = pd.Timestamp(calibracion.index.min())
    fecha_fin = pd.Timestamp(calibracion.index.max())
    observaciones_calibracion = len(calibracion)
    usa_calibracion_oficial = False
    if calibracion_oficial is not None and not calibracion_oficial.empty:
        oficial = calibracion_oficial.copy()
        oficial["fecha"] = pd.to_datetime(oficial["fecha"], errors="coerce")
        oficial["coeficiente_implicito"] = pd.to_numeric(
            oficial["coeficiente_implicito"], errors="coerce"
        )
        oficial = oficial.dropna(subset=["fecha", "coeficiente_implicito"])
        oficial = oficial[oficial["coeficiente_implicito"] > 0].sort_values("fecha")
        if not oficial.empty:
            ultima = oficial.iloc[-1]
            coeficiente = float(ultima["coeficiente_implicito"])
            fecha_inicio = pd.Timestamp(ultima["fecha"])
            fecha_fin = pd.Timestamp(ultima["fecha"])
            observaciones_calibracion = 1
            usa_calibracion_oficial = True

    return ModeloPrecioFNC(
        coeficiente=coeficiente,
        observaciones_calibracion=observaciones_calibracion,
        fecha_inicio_calibracion=fecha_inicio,
        fecha_fin_calibracion=fecha_fin,
        error_absoluto_medio=float(np.mean(errores_absolutos)),
        error_porcentual_medio=float(np.mean(errores_porcentuales)),
        observaciones_validacion=len(errores_absolutos),
        calibracion_oficial=usa_calibracion_oficial,
    )


def estimar_precio_fnc(
    modelo: ModeloPrecioFNC,
    tasa_cambio_escenario: float,
    precio_ny_escenario: float,
    factor_rendimiento: float | None = None,
    factor_referencia: float | None = None,
) -> float:
    """
    Estima el FNC a partir de TRM, Coffee C y la calibración histórica reciente.

    El precio FNC observado no es una entrada ni un piso. El coeficiente recoge
    conjuntamente los componentes no modelados por separado y se actualiza con
    los datos diarios disponibles. El factor de rendimiento sigue siendo un
    ajuste proporcional aproximado, no la fórmula oficial de la FNC.
    """
    valores = [modelo.coeficiente, tasa_cambio_escenario, precio_ny_escenario]
    if any(valor <= 0 for valor in valores):
        raise ValueError("proyeccion: todos los precios y tasas deben ser positivos")
    precio = tasa_cambio_escenario * precio_ny_escenario * modelo.coeficiente
    if factor_rendimiento is not None and factor_referencia is not None:
        if factor_rendimiento <= 0 or factor_referencia <= 0:
            raise ValueError("proyeccion: el factor de rendimiento debe ser positivo")
        precio *= factor_referencia / factor_rendimiento
    return float(precio)


def calcular_escenario(
    modelo: ModeloPrecioFNC,
    tasa_cambio_escenario: float,
    precio_ny_escenario: float,
    costo_produccion_carga: float,
    cargas: int,
    precio_fnc_observado: float | None = None,
    factor_rendimiento: float | None = None,
    factor_referencia: float | None = None,
) -> ResultadoEscenario:
    """Calcula precio estimado, ingresos, costos y margen bruto."""
    if costo_produccion_carga < 0:
        raise ValueError("proyeccion: el costo de producción no puede ser negativo")
    if cargas <= 0:
        raise ValueError("proyeccion: cargas debe ser positivo")

    precio = estimar_precio_fnc(
        modelo,
        tasa_cambio_escenario,
        precio_ny_escenario,
        factor_rendimiento,
        factor_referencia,
    )
    margen_carga = precio - costo_produccion_carga
    ingreso_total = precio * cargas
    costo_total = costo_produccion_carga * cargas
    margen_total = margen_carga * cargas
    diferencia_pct = (
        (precio / precio_fnc_observado - 1) * 100
        if precio_fnc_observado is not None and precio_fnc_observado > 0
        else float("nan")
    )
    margen_ingreso = margen_carga / precio * 100 if precio else 0.0
    retorno_costo = (
        margen_carga / costo_produccion_carga * 100
        if costo_produccion_carga
        else float("nan")
    )
    return ResultadoEscenario(
        precio_fnc_estimado=precio,
        diferencia_fnc_observado_pct=diferencia_pct,
        ingreso_total=ingreso_total,
        costo_total=costo_total,
        margen_por_carga=margen_carga,
        margen_total=margen_total,
        margen_sobre_ingreso_pct=margen_ingreso,
        retorno_sobre_costo_pct=retorno_costo,
    )


def crear_matriz_sensibilidad(
    modelo: ModeloPrecioFNC,
    tasas_cambio: list[float],
    precios_ny: list[float],
    factor_rendimiento: float | None = None,
    factor_referencia: float | None = None,
) -> pd.DataFrame:
    """Construye una matriz de precios FNC proyectados para dos variables."""
    filas = []
    for precio_ny in precios_ny:
        for tasa_cambio in tasas_cambio:
            filas.append(
                {
                    "precio_ny": float(precio_ny),
                    "tasa_cambio": float(tasa_cambio),
                    "precio_fnc_estimado": estimar_precio_fnc(
                        modelo,
                        tasa_cambio,
                        precio_ny,
                        factor_rendimiento,
                        factor_referencia,
                    ),
                }
            )
    return pd.DataFrame(filas)
